"""SQLAlchemy 2.0 Normalized Domain Models for Student Financial Platform."""

from app.models.role import Role, RoleEnum
from app.models.user import User
from app.models.program import Program, DegreeLevel, ProgramStatus
from app.models.term import Term, SemesterEnum
from app.models.fee_schedule import FeeSchedule
from app.models.student import Student, IncomeCategory, StudentStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine, FeeType
from app.models.scholarship import Scholarship, ScholarshipType, ScholarshipStatus
from app.models.eligibility import Eligibility, EligibilityStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.payment_allocation import PaymentAllocation
from app.models.refund import Refund, RefundStatus
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.models.reconciliation import (
    ReconciliationRun,
    ReconciliationRunStatus,
    ReconciliationResult,
    ReconciliationStatus,
)
from app.models.anomaly import (
    Anomaly,
    AnomalyIssueType,
    AnomalySeverity,
    AnomalyResolutionStatus,
)
from app.models.audit_log import AuditLog

__all__ = [
    # Role & User
    "Role",
    "RoleEnum",
    "User",
    # Academic Structure
    "Program",
    "DegreeLevel",
    "ProgramStatus",
    "Term",
    "SemesterEnum",
    "FeeSchedule",
    # Student & Enrollment
    "Student",
    "IncomeCategory",
    "StudentStatus",
    "Enrollment",
    "EnrollmentStatus",
    # Invoicing
    "Invoice",
    "InvoiceStatus",
    "InvoiceLine",
    "FeeType",
    # Scholarships
    "Scholarship",
    "ScholarshipType",
    "ScholarshipStatus",
    "Eligibility",
    "EligibilityStatus",
    # Payments & Allocations
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    "PaymentAllocation",
    # Refunds
    "Refund",
    "RefundStatus",
    # Auditing & Ledger
    "FinancialEvent",
    "FinancialEventType",
    "AuditLog",
    # Reconciliation & Anomalies
    "ReconciliationRun",
    "ReconciliationRunStatus",
    "ReconciliationResult",
    "ReconciliationStatus",
    "Anomaly",
    "AnomalyIssueType",
    "AnomalySeverity",
    "AnomalyResolutionStatus",
]

