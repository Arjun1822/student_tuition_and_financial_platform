from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.student import Student
from app.models.payment import Payment, PaymentStatus
from app.models.refund import Refund, RefundStatus
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.schemas.refund import RefundCreate
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService


class RefundService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def request_refund(
        self,
        refund_in: RefundCreate,
        actor_id: Optional[int] = None
    ) -> Refund:
        """
        Creates a new refund request for a student payment.
        Validates that refund amount does not exceed net refundable payment amount.
        """
        payment = (
            self.db.query(Payment)
            .filter(Payment.id == refund_in.payment_id)
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with ID {refund_in.payment_id} not found."
            )

        if payment.student_id != refund_in.student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment does not belong to the specified student."
            )

        if payment.status in [PaymentStatus.FAILED, PaymentStatus.REVERSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot refund payment in status '{payment.status.value}'."
            )

        # Calculate previously processed or approved refunds
        existing_refunds_sum = self.db.query(func.coalesce(func.sum(Refund.amount), Decimal("0.00"))).filter(
            Refund.payment_id == payment.id,
            Refund.status.in_([RefundStatus.REQUESTED, RefundStatus.APPROVED, RefundStatus.PROCESSED])
        ).scalar() or Decimal("0.00")

        max_refundable = payment.amount - existing_refunds_sum
        if refund_in.amount > max_refundable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Requested refund amount ({refund_in.amount}) exceeds maximum refundable amount "
                    f"({max_refundable}) for payment {payment.payment_id}."
                )
            )

        current_year = datetime.now(timezone.utc).year
        refund_count = self.db.query(func.count(Refund.id)).scalar() or 0
        refund_b_id = IDGenerator.refund_id(current_year, refund_count + 1)

        refund = Refund(
            refund_id=refund_b_id,
            payment_id=payment.id,
            student_id=refund_in.student_id,
            invoice_id=refund_in.invoice_id,
            amount=refund_in.amount,
            currency="INR",
            reason=refund_in.reason,
            status=RefundStatus.REQUESTED,
            reference_number=refund_in.reference_number,
            notes=refund_in.notes
        )
        self.db.add(refund)
        self.db.flush()

        # Financial Event
        event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        evt = FinancialEvent(
            event_id=IDGenerator.event_id(event_count + 1),
            entity_type="REFUND",
            entity_id=refund.refund_id,
            event_type=FinancialEventType.REFUND_REQUESTED,
            actor_id=actor_id,
            amount=refund.amount,
            currency=refund.currency,
            metadata_json={"payment_id": payment.payment_id, "reason": refund.reason}
        )
        self.db.add(evt)

        # Audit Log
        self.audit_service.log_action(
            actor_id=actor_id,
            action="REQUEST_REFUND",
            entity_type="REFUND",
            entity_id=refund.refund_id,
            new_values={"amount": str(refund.amount), "payment_id": payment.payment_id}
        )

        self.db.commit()
        self.db.refresh(refund)
        return refund

    def approve_refund(
        self,
        refund_id: int,
        notes: Optional[str] = None,
        actor_id: Optional[int] = None
    ) -> Refund:
        refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Refund with ID {refund_id} not found."
            )

        if refund.status != RefundStatus.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve refund in status '{refund.status.value}'. Must be REQUESTED."
            )

        refund.status = RefundStatus.APPROVED
        refund.approved_by = actor_id
        refund.approved_date = datetime.now(timezone.utc)
        if notes:
            refund.notes = f"{refund.notes or ''} | Approval: {notes}".strip(" |")

        # Financial Event
        event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        evt = FinancialEvent(
            event_id=IDGenerator.event_id(event_count + 1),
            entity_type="REFUND",
            entity_id=refund.refund_id,
            event_type=FinancialEventType.REFUND_APPROVED,
            actor_id=actor_id,
            amount=refund.amount,
            currency=refund.currency
        )
        self.db.add(evt)

        self.audit_service.log_action(
            actor_id=actor_id,
            action="APPROVE_REFUND",
            entity_type="REFUND",
            entity_id=refund.refund_id,
            new_values={"status": refund.status.value}
        )

        self.db.commit()
        self.db.refresh(refund)
        return refund

    def process_refund(
        self,
        refund_id: int,
        reference_number: Optional[str] = None,
        actor_id: Optional[int] = None
    ) -> Refund:
        """Processes an approved refund and settles payment allocations."""
        refund = (
            self.db.query(Refund)
            .options(joinedload(Refund.payment))
            .filter(Refund.id == refund_id)
            .first()
        )
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Refund with ID {refund_id} not found."
            )

        if refund.status != RefundStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot process refund in status '{refund.status.value}'. Must be APPROVED."
            )

        payment = refund.payment
        if payment.unallocated_amount >= refund.amount:
            payment.unallocated_amount -= refund.amount
        else:
            # Consume remaining unallocated amount
            payment.unallocated_amount = Decimal("0.00")

        refund.status = RefundStatus.PROCESSED
        refund.processed_date = datetime.now(timezone.utc)
        if reference_number:
            refund.reference_number = reference_number

        # If total refunds equal original payment amount, set payment status to REFUNDED
        all_processed = self.db.query(func.sum(Refund.amount)).filter(
            Refund.payment_id == payment.id,
            Refund.status == RefundStatus.PROCESSED
        ).scalar() or Decimal("0.00")

        if all_processed >= payment.amount:
            payment.status = PaymentStatus.REFUNDED

        # Financial Event
        event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        evt = FinancialEvent(
            event_id=IDGenerator.event_id(event_count + 1),
            entity_type="REFUND",
            entity_id=refund.refund_id,
            event_type=FinancialEventType.REFUND_PROCESSED,
            actor_id=actor_id,
            amount=refund.amount,
            currency=refund.currency,
            reference_id=reference_number
        )
        self.db.add(evt)

        self.audit_service.log_action(
            actor_id=actor_id,
            action="PROCESS_REFUND",
            entity_type="REFUND",
            entity_id=refund.refund_id,
            new_values={"status": refund.status.value}
        )

        self.db.commit()
        self.db.refresh(refund)
        return refund

    def reject_refund(
        self,
        refund_id: int,
        reason: str,
        actor_id: Optional[int] = None
    ) -> Refund:
        refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Refund with ID {refund_id} not found."
            )

        if refund.status != RefundStatus.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject refund in status '{refund.status.value}'. Must be REQUESTED."
            )

        refund.status = RefundStatus.REJECTED
        refund.notes = f"{refund.notes or ''} | Rejected: {reason}".strip(" |")

        self.audit_service.log_action(
            actor_id=actor_id,
            action="REJECT_REFUND",
            entity_type="REFUND",
            entity_id=refund.refund_id,
            new_values={"status": refund.status.value, "reason": reason}
        )

        self.db.commit()
        self.db.refresh(refund)
        return refund

