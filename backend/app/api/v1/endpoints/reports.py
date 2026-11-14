from decimal import Decimal
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.student import Student, StudentStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.scholarship import Scholarship
from app.models.payment import Payment, PaymentStatus
from app.models.refund import Refund, RefundStatus
from app.models.reconciliation import ReconciliationRun, ReconciliationStatus, ReconciliationResult
from app.models.anomaly import Anomaly, AnomalyResolutionStatus, AnomalyIssueType
from app.models.program import Program
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    # Counts
    total_students = db.query(func.count(Student.id)).scalar() or 0
    active_enrollments = db.query(func.count(Enrollment.id)).filter(
        Enrollment.status == EnrollmentStatus.ACTIVE
    ).scalar() or 0

    # Invoice metrics
    invoice_totals = db.query(
        func.coalesce(func.sum(Invoice.gross_amount), Decimal("0.00")),
        func.coalesce(func.sum(Invoice.scholarship_amount), Decimal("0.00")),
        func.coalesce(func.sum(Invoice.net_amount), Decimal("0.00")),
        func.coalesce(func.sum(Invoice.paid_amount), Decimal("0.00")),
        func.coalesce(func.sum(Invoice.outstanding_balance), Decimal("0.00")),
        func.coalesce(func.sum(Invoice.late_fee_amount), Decimal("0.00"))
    ).filter(Invoice.status != InvoiceStatus.CANCELLED).first()

    total_invoice_value = invoice_totals[0]
    total_scholarships = invoice_totals[1]
    net_collectible = invoice_totals[2]
    total_paid = invoice_totals[3]
    total_outstanding = invoice_totals[4]
    total_late_fees = invoice_totals[5]

    overdue_invoices_count = db.query(func.count(Invoice.id)).filter(
        Invoice.status == InvoiceStatus.OVERDUE
    ).scalar() or 0

    # Payments & Refunds
    total_payments_collected = db.query(
        func.coalesce(func.sum(Payment.amount), Decimal("0.00"))
    ).filter(Payment.status == PaymentStatus.COMPLETED).scalar() or Decimal("0.00")

    total_refunds_processed = db.query(
        func.coalesce(func.sum(Refund.amount), Decimal("0.00"))
    ).filter(Refund.status == RefundStatus.PROCESSED).scalar() or Decimal("0.00")

    # Reconciliation
    reconciliation_matched = db.query(func.count(ReconciliationResult.id)).filter(
        ReconciliationResult.status == ReconciliationStatus.MATCHED
    ).scalar() or 0
    reconciliation_mismatched = db.query(func.count(ReconciliationResult.id)).filter(
        ReconciliationResult.status == ReconciliationStatus.MISMATCHED
    ).scalar() or 0

    # Anomalies
    total_anomalies = db.query(func.count(Anomaly.id)).scalar() or 0
    resolved_anomalies = db.query(func.count(Anomaly.id)).filter(
        Anomaly.resolution_status == AnomalyResolutionStatus.RESOLVED
    ).scalar() or 0
    unresolved_anomalies = total_anomalies - resolved_anomalies

    # Charts: Invoices by Status
    invoice_status_dist = db.query(
        Invoice.status, func.count(Invoice.id)
    ).group_by(Invoice.status).all()
    invoices_by_status = [{"status": s.value, "count": c} for s, c in invoice_status_dist]

    # Charts: Payments by Status
    payment_status_dist = db.query(
        Payment.status, func.count(Payment.id)
    ).group_by(Payment.status).all()
    payments_by_status = [{"status": s.value, "count": c} for s, c in payment_status_dist]

    # Charts: Anomalies by Type
    anomaly_type_dist = db.query(
        Anomaly.issue_type, func.count(Anomaly.id)
    ).group_by(Anomaly.issue_type).all()
    anomalies_by_type = [{"issue_type": t.value, "count": c} for t, c in anomaly_type_dist]

    # Outstanding by Program
    prog_outstanding = (
        db.query(
            Program.program_code,
            func.coalesce(func.sum(Invoice.outstanding_balance), Decimal("0.00"))
        )
        .join(Invoice, Invoice.program_id == Program.id)
        .filter(Invoice.status != InvoiceStatus.CANCELLED)
        .group_by(Program.program_code)
        .order_by(func.sum(Invoice.outstanding_balance).desc())
        .limit(10)
        .all()
    )
    outstanding_by_program = [{"program": p, "outstanding": float(o)} for p, o in prog_outstanding]

    return {
        "kpis": {
            "total_students": total_students,
            "active_enrollments": active_enrollments,
            "total_invoice_value": float(total_invoice_value),
            "scholarships_awarded": float(total_scholarships),
            "payments_collected": float(total_payments_collected),
            "outstanding_balance": float(total_outstanding),
            "overdue_invoices": overdue_invoices_count,
            "late_fees_assessed": float(total_late_fees),
            "refunds_processed": float(total_refunds_processed),
            "reconciliation_matched": reconciliation_matched,
            "reconciliation_mismatched": reconciliation_mismatched,
            "total_anomalies": total_anomalies,
            "resolved_anomalies": resolved_anomalies,
            "unresolved_anomalies": unresolved_anomalies,
        },
        "charts": {
            "invoices_by_status": invoices_by_status,
            "payments_by_status": payments_by_status,
            "anomalies_by_type": anomalies_by_type,
            "outstanding_by_program": outstanding_by_program,
        }
    }

