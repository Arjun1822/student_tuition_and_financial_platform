from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    students,
    programs,
    terms,
    fee_schedules,
    enrollments,
    invoices,
    scholarships,
    eligibilities,
    payments,
    payment_allocations,
    refunds,
    ledger,
    reconciliation,
    anomalies,
    reports,
)

api_router = APIRouter()

# Health & System
api_router.include_router(health.router, tags=["Health & System"])

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Academic Structure
api_router.include_router(programs.router, prefix="/programs", tags=["Programs"])
api_router.include_router(terms.router, prefix="/terms", tags=["Terms"])
api_router.include_router(fee_schedules.router, prefix="/fee-schedules", tags=["Fee Schedules"])

# Student & Enrollment Management
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])

# Invoicing
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])

# Scholarships & Eligibility (Milestone 4)
api_router.include_router(scholarships.router, prefix="/scholarships", tags=["Scholarships"])
api_router.include_router(eligibilities.router, prefix="/eligibilities", tags=["Eligibility"])

# Payments & Allocations (Milestone 4)
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(payment_allocations.router, prefix="/payment-allocations", tags=["Payment Allocations"])

# Refunds (Milestone 5)
api_router.include_router(refunds.router, prefix="/refunds", tags=["Refunds"])

# Financial Ledger, Balance Statements, Late Fees (Milestone 5)
api_router.include_router(ledger.router, prefix="/ledger", tags=["Ledger & Balances"])

# Reconciliation (Milestone 5)
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["Reconciliation"])

# Anomaly Detection (Milestone 6)
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])

# Reports & Dashboard (Milestone 7)
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Dashboard"])
