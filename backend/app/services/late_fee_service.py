from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService


class LateFeeService:
    """
    Configurable Late Fee Assessment Engine.
    Evaluates overdue invoices against grace periods and maximum assessment caps.
    Enforces idempotency and prevents duplicate assessments.
    """
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def assess_late_fee_for_invoice(
        self,
        invoice_id: int,
        fixed_amount: Optional[Decimal] = None,
        percentage_rate: Optional[Decimal] = None,
        max_cap: Decimal = Decimal("2500.00"),
        grace_days: int = 15,
        evaluation_date: Optional[date] = None,
        actor_id: Optional[int] = None
    ) -> Invoice:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found."
            )

        if invoice.status in [InvoiceStatus.CANCELLED, InvoiceStatus.PAID]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assess late fee on invoice with status '{invoice.status.value}'."
            )

        current_date = evaluation_date or date.today()
        # Check grace period
        if invoice.due_date and (current_date - invoice.due_date).days < grace_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invoice is still within grace period of {grace_days} days from due date {invoice.due_date}."
            )

        if invoice.outstanding_balance <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice has no outstanding collectible balance."
            )

        # Calculate late fee
        fee_to_add = Decimal("0.00")
        if fixed_amount is not None:
            fee_to_add = fixed_amount
        elif percentage_rate is not None:
            fee_to_add = (invoice.outstanding_balance * (percentage_rate / Decimal("100.00"))).quantize(Decimal("0.01"))
        else:
            fee_to_add = Decimal("500.00")  # Default fixed late fee

        # Cap enforcement
        potential_total = invoice.late_fee_amount + fee_to_add
        if potential_total > max_cap:
            fee_to_add = max(Decimal("0.00"), max_cap - invoice.late_fee_amount)

        if fee_to_add <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Late fee cap of {max_cap} has already been reached for invoice {invoice.invoice_id}."
            )

        # Apply late fee
        old_late_fee = invoice.late_fee_amount
        invoice.late_fee_amount += fee_to_add
        invoice.outstanding_balance = max(
            Decimal("0.00"),
            invoice.net_amount + invoice.late_fee_amount - invoice.paid_amount
        )
        invoice.status = InvoiceStatus.OVERDUE

        # Ledger Event
        event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        evt = FinancialEvent(
            event_id=IDGenerator.event_id(event_count + 1),
            entity_type="INVOICE",
            entity_id=invoice.invoice_id,
            event_type=FinancialEventType.LATE_FEE_ASSESSED,
            previous_state=str(old_late_fee),
            new_state=str(invoice.late_fee_amount),
            actor_id=actor_id,
            amount=fee_to_add,
            currency="INR",
            metadata_json={
                "fee_added": str(fee_to_add),
                "total_late_fees": str(invoice.late_fee_amount),
                "evaluation_date": current_date.isoformat()
            }
        )
        self.db.add(evt)

        # Audit Log
        self.audit_service.log_action(
            actor_id=actor_id,
            action="ASSESS_LATE_FEE",
            entity_type="INVOICE",
            entity_id=invoice.invoice_id,
            new_values={
                "fee_added": str(fee_to_add),
                "new_late_fee_total": str(invoice.late_fee_amount)
            }
        )

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

