from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.student import Student
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.payment_allocation import PaymentAllocation
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.schemas.payment import PaymentCreate, AllocationItemRequest
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def record_payment(
        self,
        payment_in: PaymentCreate,
        actor_id: Optional[int] = None
    ) -> Payment:
        """
        Records a new student payment into the ledger.
        Optionally triggers auto-allocation to the student's oldest outstanding invoices.
        """
        # 1. Validate student
        student = self.db.query(Student).filter(Student.id == payment_in.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {payment_in.student_id} not found."
            )

        # 2. Validate amount
        if payment_in.amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than zero."
            )

        # 3. Check reference number uniqueness if provided
        if payment_in.reference_number:
            existing = self.db.query(Payment).filter(
                Payment.reference_number == payment_in.reference_number
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Payment reference '{payment_in.reference_number}' has already been processed."
                )

        current_year = datetime.now(timezone.utc).year
        payment_count = self.db.query(func.count(Payment.id)).scalar() or 0
        payment_b_id = IDGenerator.payment_id(current_year, payment_count + 1)

        payment = Payment(
            payment_id=payment_b_id,
            student_id=student.id,
            amount=payment_in.amount,
            allocated_amount=Decimal("0.00"),
            unallocated_amount=payment_in.amount,
            payment_method=payment_in.payment_method,
            reference_number=payment_in.reference_number,
            currency=payment_in.currency or "INR",
            status=PaymentStatus.COMPLETED,
            notes=payment_in.notes
        )
        self.db.add(payment)
        self.db.flush()

        # Record Financial Event for payment receipt
        event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        evt = FinancialEvent(
            event_id=IDGenerator.event_id(event_count + 1),
            entity_type="PAYMENT",
            entity_id=payment.payment_id,
            event_type=FinancialEventType.PAYMENT_RECEIVED,
            new_state=PaymentStatus.COMPLETED.value,
            actor_id=actor_id,
            reference_id=payment.reference_number,
            amount=payment.amount,
            currency=payment.currency,
            metadata_json={
                "student_id": student.student_id,
                "payment_method": payment.payment_method.value,
                "amount": str(payment.amount)
            }
        )
        self.db.add(evt)

        # Audit log
        self.audit_service.log_action(
            actor_id=actor_id,
            action="RECORD_PAYMENT",
            entity_type="PAYMENT",
            entity_id=payment.payment_id,
            new_values={
                "amount": str(payment.amount),
                "student_id": student.student_id,
                "payment_method": payment.payment_method.value
            }
        )

        self.db.commit()

        # 4. Optional Auto-Allocation
        if payment_in.auto_allocate:
            self.allocate_payment(
                payment_id=payment.id,
                allocations=None,
                auto_allocate=True,
                target_invoice_id=payment_in.invoice_id,
                actor_id=actor_id
            )

        self.db.refresh(payment)
        return payment

    def allocate_payment(
        self,
        payment_id: int,
        allocations: Optional[List[AllocationItemRequest]] = None,
        auto_allocate: bool = False,
        target_invoice_id: Optional[int] = None,
        actor_id: Optional[int] = None
    ) -> Payment:
        """
        Allocates available funds from a payment to invoice line items.
        Enforces strict mathematical boundaries:
        - Available Payment = Payment Amount - Existing Allocations - Reversed Amounts
        - Remaining Invoice Line = Collectible Line Amount - Existing Allocations
        - Cross-student invoice line allocation is strictly prohibited.
        """
        payment = (
            self.db.query(Payment)
            .options(joinedload(Payment.student))
            .filter(Payment.id == payment_id)
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with ID {payment_id} not found."
            )

        if payment.status != PaymentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment status is '{payment.status.value}'. Must be COMPLETED to allocate."
            )

        available_funds = payment.amount - payment.allocated_amount
        if available_funds <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment {payment.payment_id} is already fully allocated."
            )

        alloc_seq = self.db.query(func.count(PaymentAllocation.id)).filter(
            PaymentAllocation.payment_id == payment.id
        ).scalar() or 0

        affected_invoices = set()

        if auto_allocate:
            # Auto allocate against student's outstanding invoices (oldest first)
            inv_query = (
                self.db.query(Invoice)
                .options(joinedload(Invoice.lines))
                .filter(
                    Invoice.student_id == payment.student_id,
                    Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID]),
                    Invoice.outstanding_balance > Decimal("0.00")
                )
            )
            if target_invoice_id:
                inv_query = inv_query.filter(Invoice.id == target_invoice_id)
            invoices = inv_query.order_by(Invoice.invoice_date.asc(), Invoice.id.asc()).all()

            for inv in invoices:
                for line in inv.lines:
                    if available_funds <= Decimal("0.00"):
                        break
                    remaining_line = line.amount - line.allocated_amount
                    if remaining_line <= Decimal("0.00"):
                        continue

                    alloc_amount = min(available_funds, remaining_line)

                    alloc_seq += 1
                    alloc_b_id = IDGenerator.allocation_id(payment.payment_id, alloc_seq)

                    # Check if allocation already exists between this payment and line
                    existing_alloc = self.db.query(PaymentAllocation).filter(
                        PaymentAllocation.payment_id == payment.id,
                        PaymentAllocation.invoice_line_id == line.id
                    ).first()

                    if existing_alloc:
                        existing_alloc.amount += alloc_amount
                    else:
                        new_alloc = PaymentAllocation(
                            allocation_id=alloc_b_id,
                            payment_id=payment.id,
                            invoice_line_id=line.id,
                            amount=alloc_amount
                        )
                        self.db.add(new_alloc)

                    line.allocated_amount += alloc_amount
                    payment.allocated_amount += alloc_amount
                    available_funds -= alloc_amount
                    affected_invoices.add(inv)

                    # Log Financial Event
                    event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
                    evt = FinancialEvent(
                        event_id=IDGenerator.event_id(event_count + 1),
                        entity_type="PAYMENT_ALLOCATION",
                        entity_id=alloc_b_id,
                        event_type=FinancialEventType.PAYMENT_ALLOCATED,
                        actor_id=actor_id,
                        reference_id=inv.invoice_id,
                        amount=alloc_amount,
                        currency=payment.currency,
                        metadata_json={
                            "payment_id": payment.payment_id,
                            "invoice_id": inv.invoice_id,
                            "line_id": line.invoice_line_id,
                            "amount": str(alloc_amount)
                        }
                    )
                    self.db.add(evt)

        elif allocations:
            # Manual allocation to specified line items
            for alloc_item in allocations:
                if available_funds <= Decimal("0.00"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Requested allocations exceed remaining unallocated payment amount."
                    )

                line = (
                    self.db.query(InvoiceLine)
                    .options(joinedload(InvoiceLine.invoice))
                    .filter(InvoiceLine.id == alloc_item.invoice_line_id)
                    .first()
                )
                if not line:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Invoice line with ID {alloc_item.invoice_line_id} not found."
                    )

                inv = line.invoice
                # Check cross-student isolation!
                if inv.student_id != payment.student_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Cross-student allocation forbidden: Payment belongs to student {payment.student_id}, "
                            f"but invoice belongs to student {inv.student_id}."
                        )
                    )

                if inv.status == InvoiceStatus.CANCELLED:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot allocate payment to CANCELLED invoice '{inv.invoice_id}'."
                    )

                remaining_line = line.amount - line.allocated_amount
                if alloc_item.amount > remaining_line:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Allocation amount {alloc_item.amount} exceeds remaining line collectible {remaining_line} "
                            f"for line {line.invoice_line_id}."
                        )
                    )

                if alloc_item.amount > available_funds:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Allocation amount {alloc_item.amount} exceeds available payment balance {available_funds}."
                        )
                    )

                alloc_seq += 1
                alloc_b_id = IDGenerator.allocation_id(payment.payment_id, alloc_seq)

                existing_alloc = self.db.query(PaymentAllocation).filter(
                    PaymentAllocation.payment_id == payment.id,
                    PaymentAllocation.invoice_line_id == line.id
                ).first()

                if existing_alloc:
                    existing_alloc.amount += alloc_item.amount
                else:
                    new_alloc = PaymentAllocation(
                        allocation_id=alloc_b_id,
                        payment_id=payment.id,
                        invoice_line_id=line.id,
                        amount=alloc_item.amount
                    )
                    self.db.add(new_alloc)

                line.allocated_amount += alloc_item.amount
                payment.allocated_amount += alloc_item.amount
                available_funds -= alloc_item.amount
                affected_invoices.add(inv)

                # Financial Event
                event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
                evt = FinancialEvent(
                    event_id=IDGenerator.event_id(event_count + 1),
                    entity_type="PAYMENT_ALLOCATION",
                    entity_id=alloc_b_id,
                    event_type=FinancialEventType.PAYMENT_ALLOCATED,
                    actor_id=actor_id,
                    reference_id=inv.invoice_id,
                    amount=alloc_item.amount,
                    currency=payment.currency,
                    metadata_json={
                        "payment_id": payment.payment_id,
                        "invoice_id": inv.invoice_id,
                        "line_id": line.invoice_line_id,
                        "amount": str(alloc_item.amount)
                    }
                )
                self.db.add(evt)

        # Update unallocated payment balance
        payment.unallocated_amount = payment.amount - payment.allocated_amount

        # Update all affected invoices
        for inv in affected_invoices:
            # Recompute total paid amount from all line allocations
            total_lines_paid = sum((l.allocated_amount for l in inv.lines), Decimal("0.00"))
            inv.paid_amount = total_lines_paid
            inv.outstanding_balance = max(
                Decimal("0.00"),
                inv.net_amount + inv.late_fee_amount - inv.paid_amount
            )

            if inv.outstanding_balance == Decimal("0.00"):
                inv.status = InvoiceStatus.PAID
            elif inv.paid_amount > Decimal("0.00"):
                inv.status = InvoiceStatus.PARTIALLY_PAID

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def reverse_payment(
        self,
        payment_id: int,
        reason: str,
        actor_id: Optional[int] = None
    ) -> Payment:
        """
        Reverses a completed payment, rolling back all line-item allocations,
        restoring invoice balances, and logging immutable ledger events.
        """
        payment = (
            self.db.query(Payment)
            .options(
                joinedload(Payment.allocations).joinedload(PaymentAllocation.invoice_line).joinedload(InvoiceLine.invoice)
            )
            .filter(Payment.id == payment_id)
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with ID {payment_id} not found."
            )

        if payment.status == PaymentStatus.REVERSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment {payment.payment_id} is already REVERSED."
            )

        old_status = payment.status.value
        affected_invoices = set()

        # Roll back line-item allocations
        for alloc in list(payment.allocations):
            line = alloc.invoice_line
            if line:
                line.allocated_amount = max(Decimal("0.00"), line.allocated_amount - alloc.amount)
                if line.invoice:
                    affected_invoices.add(line.invoice)
            self.db.delete(alloc)

        payment.allocated_amount = Decimal("0.00")
        payment.unallocated_amount = Decimal("0.00")
        payment.status = PaymentStatus.REVERSED
        payment.notes = f"{payment.notes or ''} | Reversal Reason: {reason}".strip(" |")

        # Recompute invoice balances
        for inv in affected_invoices:
            total_lines_paid = sum((l.allocated_amount for l in inv.lines), Decimal("0.00"))
            inv.paid_amount = total_lines_paid
            inv.outstanding_balance = max(
                Decimal("0.00"),
                inv.net_amount + inv.late_fee_amount - inv.paid_amount
            )
            if inv.outstanding_balance > Decimal("0.00") and inv.paid_amount == Decimal("0.00"):
                inv.status = InvoiceStatus.ISSUED
            elif inv.paid_amount > Decimal("0.00"):
                inv.status = InvoiceStatus.PARTIALLY_PAID

        # Ledger Event
        event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        evt = FinancialEvent(
            event_id=IDGenerator.event_id(event_count + 1),
            entity_type="PAYMENT",
            entity_id=payment.payment_id,
            event_type=FinancialEventType.PAYMENT_REVERSED,
            previous_state=old_status,
            new_state=PaymentStatus.REVERSED.value,
            actor_id=actor_id,
            amount=payment.amount,
            currency=payment.currency,
            metadata_json={"reversal_reason": reason}
        )
        self.db.add(evt)

        # Audit Log
        self.audit_service.log_action(
            actor_id=actor_id,
            action="REVERSE_PAYMENT",
            entity_type="PAYMENT",
            entity_id=payment.payment_id,
            old_values={"status": old_status},
            new_values={"status": PaymentStatus.REVERSED.value, "reason": reason}
        )

        self.db.commit()
        self.db.refresh(payment)
        return payment

