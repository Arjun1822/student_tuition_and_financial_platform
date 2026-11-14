from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.student import Student, StudentStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.scholarship import Scholarship, ScholarshipStatus
from app.models.eligibility import Eligibility, EligibilityStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.financial_event import FinancialEventType, FinancialEvent
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService


class ScholarshipEligibilityService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def evaluate_student(
        self,
        student_id: int,
        term_id: int,
        scholarship_ids: Optional[List[int]] = None,
        actor_id: Optional[int] = None
    ) -> List[Eligibility]:
        """
        Evaluates a student's eligibility for available scholarships in an academic term.
        Calculated Award = min(Eligible Fee Amount * Award Percentage, Scholarship Cap)
        Enforces budget constraints, program constraints, GPA criteria, and duplicate prevention.
        """
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found."
            )

        if student.status != StudentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student status is '{student.status.value}'. Must be ACTIVE for scholarship evaluation."
            )

        # 1. Fetch active enrollment for student and term
        enrollment = (
            self.db.query(Enrollment)
            .options(joinedload(Enrollment.program), joinedload(Enrollment.term))
            .filter(
                Enrollment.student_id == student.id,
                Enrollment.term_id == term_id,
                Enrollment.status == EnrollmentStatus.ACTIVE
            )
            .first()
        )
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active enrollment found for student {student.student_id} in term ID {term_id}."
            )

        # 2. Fetch invoice for this enrollment to determine eligible fee amount (gross tuition)
        invoice = (
            self.db.query(Invoice)
            .filter(
                Invoice.enrollment_id == enrollment.id,
                Invoice.status != InvoiceStatus.CANCELLED
            )
            .first()
        )
        eligible_fee = invoice.gross_amount if invoice else Decimal("0.00")
        if eligible_fee <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student has no issued invoice or eligible fees for this enrollment."
            )

        # 3. Retrieve scholarships to evaluate
        query = self.db.query(Scholarship).filter(Scholarship.status == ScholarshipStatus.ACTIVE)
        if scholarship_ids:
            query = query.filter(Scholarship.id.in_(scholarship_ids))
        scholarships = query.all()

        if not scholarships:
            return []

        # Count total existing eligibilities to generate sequential IDs
        eligibility_count = self.db.query(func.count(Eligibility.id)).scalar() or 0
        results: List[Eligibility] = []

        for sch in scholarships:
            # Check for existing duplicate award/application
            existing = (
                self.db.query(Eligibility)
                .filter(
                    Eligibility.student_id == student.id,
                    Eligibility.scholarship_id == sch.id,
                    Eligibility.enrollment_id == enrollment.id,
                    Eligibility.status.in_([EligibilityStatus.PENDING, EligibilityStatus.APPROVED])
                )
                .first()
            )
            if existing:
                continue  # Skip already evaluated or awarded

            # Determine eligibility criteria
            rejection_reasons = []

            # A. Program check
            if sch.eligible_programs:
                prog_code = getattr(enrollment.program, "code", getattr(enrollment.program, "program_code", ""))
                if (prog_code not in sch.eligible_programs and
                    str(enrollment.program_id) not in sch.eligible_programs):
                    rejection_reasons.append(f"Program '{prog_code}' not eligible for {sch.name}")

            # B. Term check
            if sch.eligible_terms:
                if (enrollment.term.term_id not in sch.eligible_terms and
                    str(enrollment.term_id) not in sch.eligible_terms):
                    rejection_reasons.append(f"Term '{enrollment.term.term_id}' not eligible for {sch.name}")

            # C. GPA check
            if sch.min_gpa is not None:
                student_gpa = student.gpa or Decimal("0.00")
                if student_gpa < sch.min_gpa:
                    rejection_reasons.append(f"Student GPA ({student_gpa}) is below minimum requirement ({sch.min_gpa})")

            # D. Budget check
            remaining_budget = sch.total_budget - sch.awarded_amount
            if remaining_budget <= Decimal("0.00"):
                rejection_reasons.append(f"Scholarship budget is exhausted ({sch.awarded_amount}/{sch.total_budget})")

            # Calculate theoretical award
            percentage_decimal = sch.percentage / Decimal("100.00")
            raw_award = (eligible_fee * percentage_decimal).quantize(Decimal("0.01"))
            calculated_amount = min(raw_award, sch.max_amount, eligible_fee)

            eligibility_count += 1
            b_id = IDGenerator.eligibility_id(eligibility_count)

            if rejection_reasons:
                elig = Eligibility(
                    eligibility_id=b_id,
                    student_id=student.id,
                    scholarship_id=sch.id,
                    enrollment_id=enrollment.id,
                    eligible_fee_amount=eligible_fee,
                    scholarship_percentage=sch.percentage,
                    calculated_amount=Decimal("0.00"),
                    approved_amount=Decimal("0.00"),
                    status=EligibilityStatus.REJECTED,
                    decision_reason="; ".join(rejection_reasons),
                    criteria_version="1.0",
                    evaluated_by=actor_id
                )
            else:
                # Also cap by remaining budget if remaining is less than calculated
                capped_amount = min(calculated_amount, remaining_budget)
                elig = Eligibility(
                    eligibility_id=b_id,
                    student_id=student.id,
                    scholarship_id=sch.id,
                    enrollment_id=enrollment.id,
                    eligible_fee_amount=eligible_fee,
                    scholarship_percentage=sch.percentage,
                    calculated_amount=capped_amount,
                    approved_amount=Decimal("0.00"),
                    status=EligibilityStatus.PENDING,
                    decision_reason=f"Eligible for {sch.percentage}% award capped at {sch.max_amount} INR.",
                    criteria_version="1.0",
                    evaluated_by=actor_id
                )

            self.db.add(elig)
            self.db.flush()
            results.append(elig)

        self.db.commit()
        return results

    def approve_eligibility(
        self,
        eligibility_id: int,
        approved_amount: Optional[Decimal] = None,
        notes: Optional[str] = None,
        actor_id: Optional[int] = None
    ) -> Eligibility:
        """
        Approves a pending scholarship eligibility, commits the award to the scholarship budget,
        applies the financial discount to the student's invoice, and logs an immutable ledger event.
        """
        elig = (
            self.db.query(Eligibility)
            .options(
                joinedload(Eligibility.scholarship),
                joinedload(Eligibility.student),
                joinedload(Eligibility.enrollment)
            )
            .filter(Eligibility.id == eligibility_id)
            .first()
        )
        if not elig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Eligibility with ID {eligibility_id} not found."
            )

        if elig.status != EligibilityStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve eligibility in status '{elig.status.value}'. Must be PENDING."
            )

        amount_to_approve = approved_amount if approved_amount is not None else elig.calculated_amount
        if amount_to_approve <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approved amount must be greater than zero."
            )

        if amount_to_approve > elig.eligible_fee_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approved amount ({amount_to_approve}) cannot exceed eligible fee amount ({elig.eligible_fee_amount})."
            )

        sch = elig.scholarship
        remaining_budget = sch.total_budget - sch.awarded_amount
        if amount_to_approve > remaining_budget:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approved amount ({amount_to_approve}) exceeds remaining scholarship budget ({remaining_budget})."
            )

        # 1. Update scholarship record
        sch.awarded_amount += amount_to_approve
        if sch.awarded_amount >= sch.total_budget:
            sch.status = ScholarshipStatus.EXHAUSTED

        # 2. Update eligibility record
        elig.status = EligibilityStatus.APPROVED
        elig.approved_amount = amount_to_approve
        elig.approved_by = actor_id
        elig.approved_date = datetime.now(timezone.utc)
        if notes:
            elig.decision_reason += f" | Approval note: {notes}"

        # 3. Apply discount to invoice
        if elig.enrollment_id:
            invoice = (
                self.db.query(Invoice)
                .filter(
                    Invoice.enrollment_id == elig.enrollment_id,
                    Invoice.status != InvoiceStatus.CANCELLED
                )
                .first()
            )
            if invoice:
                old_net = invoice.net_amount
                invoice.scholarship_amount += amount_to_approve
                invoice.net_amount = max(Decimal("0.00"), invoice.gross_amount - invoice.scholarship_amount)
                invoice.outstanding_balance = max(
                    Decimal("0.00"),
                    invoice.net_amount + invoice.late_fee_amount - invoice.paid_amount
                )
                if invoice.outstanding_balance == Decimal("0.00") and invoice.paid_amount > Decimal("0.00"):
                    invoice.status = InvoiceStatus.PAID

                # Record Financial Event for scholarship application
                event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
                evt = FinancialEvent(
                    event_id=IDGenerator.event_id(event_count + 1),
                    entity_type="INVOICE",
                    entity_id=invoice.invoice_id,
                    event_type=FinancialEventType.SCHOLARSHIP_APPROVED,
                    previous_state=str(old_net),
                    new_state=str(invoice.net_amount),
                    actor_id=actor_id,
                    reference_id=elig.eligibility_id,
                    amount=amount_to_approve,
                    currency="INR",
                    metadata_json={
                        "scholarship_id": sch.scholarship_id,
                        "scholarship_name": sch.name,
                        "student_id": elig.student.student_id,
                        "eligibility_id": elig.eligibility_id
                    }
                )
                self.db.add(evt)

        # Audit log
        self.audit_service.log_action(
            actor_id=actor_id,
            action="APPROVE_SCHOLARSHIP_ELIGIBILITY",
            entity_type="ELIGIBILITY",
            entity_id=elig.eligibility_id,
            new_values={
                "status": elig.status.value,
                "approved_amount": str(amount_to_approve),
                "scholarship_id": sch.scholarship_id
            }
        )

        self.db.commit()
        self.db.refresh(elig)
        return elig

    def reject_eligibility(
        self,
        eligibility_id: int,
        reason: str,
        actor_id: Optional[int] = None
    ) -> Eligibility:
        """Rejects a scholarship eligibility with mandatory decision reason."""
        elig = self.db.query(Eligibility).filter(Eligibility.id == eligibility_id).first()
        if not elig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Eligibility with ID {eligibility_id} not found."
            )

        if elig.status != EligibilityStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject eligibility in status '{elig.status.value}'. Must be PENDING."
            )

        elig.status = EligibilityStatus.REJECTED
        elig.decision_reason = f"Rejected: {reason}"
        elig.approved_by = actor_id
        elig.approved_date = datetime.now(timezone.utc)

        self.audit_service.log_action(
            actor_id=actor_id,
            action="REJECT_SCHOLARSHIP_ELIGIBILITY",
            entity_type="ELIGIBILITY",
            entity_id=elig.eligibility_id,
            new_values={"status": elig.status.value, "reason": reason}
        )

        self.db.commit()
        self.db.refresh(elig)
        return elig

