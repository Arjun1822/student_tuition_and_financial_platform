from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models.student import Student
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.refund import Refund, RefundStatus
from app.schemas.balance import StudentBalanceStatement, InvoiceBalanceSummary


class BalanceCalculationService:
    """
    Authoritative student financial balance calculation engine.
    Derives balances directly from verifiable transactional entities:
    Gross Charges = Sum of Valid Invoice Lines
    Net Collectible = Gross Charges - Approved Scholarship Discounts
    Outstanding Balance = Net Collectible + Valid Late Fees - Valid Allocated Payments
    """
    def __init__(self, db: Session):
        self.db = db

    def calculate_student_balance(self, student_id: int) -> StudentBalanceStatement:
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found."
            )

        # 1. Fetch all non-cancelled invoices
        invoices = (
            self.db.query(Invoice)
            .options(joinedload(Invoice.lines))
            .filter(
                Invoice.student_id == student.id,
                Invoice.status != InvoiceStatus.CANCELLED
            )
            .order_by(Invoice.invoice_date.asc())
            .all()
        )

        gross_charges = Decimal("0.00")
        approved_scholarships = Decimal("0.00")
        assessed_late_fees = Decimal("0.00")
        total_invoice_paid = Decimal("0.00")
        invoice_summaries = []

        for inv in invoices:
            gross_charges += inv.gross_amount
            approved_scholarships += inv.scholarship_amount
            assessed_late_fees += inv.late_fee_amount
            total_invoice_paid += inv.paid_amount

            invoice_summaries.append(
                InvoiceBalanceSummary(
                    invoice_id=inv.invoice_id,
                    billing_cycle=inv.billing_cycle,
                    status=inv.status.value,
                    gross_amount=inv.gross_amount,
                    scholarship_amount=inv.scholarship_amount,
                    net_amount=inv.net_amount,
                    late_fee_amount=inv.late_fee_amount,
                    paid_amount=inv.paid_amount,
                    outstanding_balance=inv.outstanding_balance
                )
            )

        net_collectible = gross_charges - approved_scholarships

        # 2. Fetch all completed payments
        payments = (
            self.db.query(Payment)
            .filter(
                Payment.student_id == student.id,
                Payment.status == PaymentStatus.COMPLETED
            )
            .all()
        )

        total_payments = sum((p.amount for p in payments), Decimal("0.00"))
        total_allocated = sum((p.allocated_amount for p in payments), Decimal("0.00"))
        total_unallocated = sum((p.unallocated_amount for p in payments), Decimal("0.00"))

        # 3. Fetch processed refunds
        refunds = (
            self.db.query(Refund)
            .filter(
                Refund.student_id == student.id,
                Refund.status == RefundStatus.PROCESSED
            )
            .all()
        )
        total_refunds = sum((r.amount for r in refunds), Decimal("0.00"))

        # Outstanding balance = Net Collectible + Late Fees - Allocated Payments
        outstanding_balance = max(
            Decimal("0.00"),
            net_collectible + assessed_late_fees - total_allocated
        )

        return StudentBalanceStatement(
            student_id=student.id,
            student_business_id=student.student_id,
            student_name=student.full_name,
            currency="INR",
            gross_charges=gross_charges,
            approved_scholarships=approved_scholarships,
            net_collectible=net_collectible,
            assessed_late_fees=assessed_late_fees,
            total_payments=total_payments,
            total_allocated=total_allocated,
            total_unallocated=total_unallocated,
            total_refunds=total_refunds,
            outstanding_balance=outstanding_balance,
            invoices=invoice_summaries
        )

