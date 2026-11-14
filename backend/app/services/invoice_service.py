from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.fee_schedule import FeeSchedule
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine, FeeType
from app.models.financial_event import FinancialEventType
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def generate_invoice_for_enrollment(
        self,
        enrollment_id: int,
        due_date: Optional[date] = None,
        notes: Optional[str] = None,
        actor_id: Optional[int] = None
    ) -> Invoice:
        """
        Generates a tuition invoice from an active enrollment and program fee schedule.
        Enforces duplicate invoice prevention, arithmetic consistency, and ledger auditing.
        """
        # 1. Fetch enrollment with related student, program, and term
        enrollment = (
            self.db.query(Enrollment)
            .options(
                joinedload(Enrollment.student),
                joinedload(Enrollment.program),
                joinedload(Enrollment.term)
            )
            .filter(Enrollment.id == enrollment_id)
            .first()
        )
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment with ID {enrollment_id} not found."
            )

        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot generate invoice for enrollment with status '{enrollment.status.value}'. Must be ACTIVE."
            )

        # 2. Derive billing cycle from term
        billing_cycle = f"{enrollment.term.year}-{enrollment.term.semester.value}"

        # 3. Check for duplicate invoice in the same billing cycle
        existing_invoice = (
            self.db.query(Invoice)
            .filter(
                Invoice.enrollment_id == enrollment.id,
                Invoice.billing_cycle == billing_cycle,
                Invoice.status != InvoiceStatus.CANCELLED
            )
            .first()
        )
        if existing_invoice:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Duplicate invoice detected. Invoice '{existing_invoice.invoice_id}' "
                    f"already exists for enrollment {enrollment.enrollment_id} and cycle {billing_cycle}."
                )
            )

        # 4. Fetch fee schedule for program and term
        fee_schedule = (
            self.db.query(FeeSchedule)
            .filter(
                FeeSchedule.program_id == enrollment.program_id,
                FeeSchedule.term_id == enrollment.term_id,
                FeeSchedule.is_active.is_(True)
            )
            .first()
        )
        if not fee_schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No active fee schedule configured for program '{enrollment.program.code}' "
                    f"in term '{enrollment.term.term_id}'."
                )
            )

        # 5. Build invoice lines and compute gross total
        today = date.today()
        invoice_due = due_date or (today + timedelta(days=30))
        lines_data = []

        fee_mapping = [
            (FeeType.TUITION, f"Tuition Fee - {enrollment.program.name}", fee_schedule.tuition_fee),
            (FeeType.REGISTRATION, "Semester Registration Fee", fee_schedule.registration_fee),
            (FeeType.LABORATORY, "Laboratory and Facilities Fee", fee_schedule.laboratory_fee),
            (FeeType.EXAMINATION, "Examination and Assessment Fee", fee_schedule.examination_fee),
            (FeeType.LIBRARY, "Library and Digital Resources Fee", fee_schedule.library_fee),
            (FeeType.OTHER, "Campus Amenities and Student Services", fee_schedule.other_charges),
        ]

        gross_amount = Decimal("0.00")
        line_count = self.db.query(func.count(InvoiceLine.id)).scalar() or 0

        for fee_type, description, amount in fee_mapping:
            if amount and amount > Decimal("0.00"):
                line_count += 1
                inv_line = InvoiceLine(
                    invoice_line_id=IDGenerator.invoice_line_id(line_count),
                    fee_type=fee_type,
                    description=description,
                    amount=amount,
                    allocated_amount=Decimal("0.00")
                )
                lines_data.append(inv_line)
                gross_amount += amount

        if gross_amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configured fee schedule contains zero collectible fees."
            )

        # 6. Generate deterministic invoice business ID
        inv_count = self.db.query(func.count(Invoice.id)).scalar() or 0
        invoice_business_id = IDGenerator.invoice_id(
            student_business_id=enrollment.student.student_id,
            year=enrollment.term.year,
            sequence_num=inv_count + 1
        )

        scholarship_discount = Decimal("0.00")
        net_payable = gross_amount - scholarship_discount
        outstanding_balance = net_payable

        invoice = Invoice(
            invoice_id=invoice_business_id,
            enrollment_id=enrollment.id,
            student_id=enrollment.student_id,
            term_id=enrollment.term_id,
            invoice_date=today,
            due_date=invoice_due,
            gross_amount=gross_amount,
            scholarship_discount=scholarship_discount,
            net_amount=net_payable,
            amount_paid=Decimal("0.00"),
            outstanding_balance=outstanding_balance,
            currency="INR",
            status=InvoiceStatus.ISSUED,
            billing_cycle=billing_cycle,
            notes=notes
        )
        self.db.add(invoice)
        self.db.flush()

        for line in lines_data:
            line.invoice_id = invoice.id
            self.db.add(line)
        self.db.flush()

        # 7. Record financial events in the ledger
        self.audit_service.log_financial_event(
            entity_type="INVOICE",
            entity_id=invoice.invoice_id,
            event_type=FinancialEventType.INVOICE_CREATED,
            previous_state=None,
            new_state=InvoiceStatus.DRAFT.value,
            actor_id=actor_id,
            reference_id=enrollment.enrollment_id,
            amount=gross_amount,
            metadata={"billing_cycle": billing_cycle, "gross_amount": str(gross_amount)}
        )

        self.audit_service.log_financial_event(
            entity_type="INVOICE",
            entity_id=invoice.invoice_id,
            event_type=FinancialEventType.INVOICE_ISSUED,
            previous_state=InvoiceStatus.DRAFT.value,
            new_state=InvoiceStatus.ISSUED.value,
            actor_id=actor_id,
            reference_id=enrollment.enrollment_id,
            amount=net_payable,
            metadata={"due_date": invoice_due.isoformat(), "net_payable": str(net_payable)}
        )

        return invoice

    def cancel_invoice(self, invoice_id: int, reason: str, actor_id: Optional[int] = None) -> Invoice:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found."
            )

        if invoice.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.REFUNDED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel invoice in '{invoice.status.value}' state."
            )

        if invoice.amount_paid > Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel invoice with allocated payments. Process refunds or payment reversals first."
            )

        previous_state = invoice.status.value
        invoice.status = InvoiceStatus.CANCELLED
        invoice.notes = f"{invoice.notes or ''} [Cancelled: {reason}]".strip()
        self.db.flush()

        self.audit_service.log_financial_event(
            entity_type="INVOICE",
            entity_id=invoice.invoice_id,
            event_type=FinancialEventType.INVOICE_CANCELLED,
            previous_state=previous_state,
            new_state=InvoiceStatus.CANCELLED.value,
            actor_id=actor_id,
            reference_id=str(invoice.id),
            amount=invoice.net_amount,
            metadata={"reason": reason}
        )

        return invoice

