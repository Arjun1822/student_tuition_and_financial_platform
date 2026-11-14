from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.anomaly import (
    Anomaly,
    AnomalyIssueType,
    AnomalySeverity,
    AnomalyResolutionStatus,
)
from app.models.payment import Payment, PaymentStatus
from app.models.payment_allocation import PaymentAllocation
from app.models.eligibility import Eligibility, EligibilityStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine
from app.models.refund import Refund, RefundStatus
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService


class AnomalyDetectionService:
    """
    Automated Financial Anomaly Detection Engine.
    Detects 5 mandatory negative anomaly scenarios:
    1. PAYMENT_OVER_ALLOCATED
    2. SCHOLARSHIP_EXCEEDS_FEES
    3. DUPLICATE_INVOICE
    4. REFUND_EXCEEDS_PAID
    5. BALANCE_MISMATCH
    """
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def scan_for_anomalies(self, actor_id: Optional[int] = None) -> List[Anomaly]:
        detected_anomalies: List[Anomaly] = []
        seq = self.db.query(func.count(Anomaly.id)).scalar() or 0

        # Helper to check if anomaly already exists for entity and issue
        def already_logged(issue: AnomalyIssueType, entity_id: str) -> bool:
            return (
                self.db.query(Anomaly)
                .filter(
                    Anomaly.issue_type == issue,
                    Anomaly.entity_id == entity_id,
                    Anomaly.resolution_status != AnomalyResolutionStatus.RESOLVED
                )
                .first()
                is not None
            )

        # -------------------------------------------------------------
        # 1. PAYMENT_OVER_ALLOCATED
        # -------------------------------------------------------------
        payments = self.db.query(Payment).all()
        for p in payments:
            alloc_sum = self.db.query(func.coalesce(func.sum(PaymentAllocation.amount), Decimal("0.00"))).filter(
                PaymentAllocation.payment_id == p.id
            ).scalar() or Decimal("0.00")

            if alloc_sum > p.amount or p.allocated_amount > p.amount:
                if not already_logged(AnomalyIssueType.PAYMENT_OVER_ALLOCATED, p.payment_id):
                    seq += 1
                    anm = Anomaly(
                        anomaly_id=IDGenerator.anomaly_id(seq),
                        issue_type=AnomalyIssueType.PAYMENT_OVER_ALLOCATED,
                        entity_type="PAYMENT",
                        entity_id=p.payment_id,
                        severity=AnomalySeverity.CRITICAL,
                        expected_value=p.amount,
                        actual_value=max(alloc_sum, p.allocated_amount),
                        explanation=(
                            f"Payment {p.payment_id} total allocations ({alloc_sum}) exceed "
                            f"original payment amount ({p.amount})."
                        ),
                        resolution_status=AnomalyResolutionStatus.OPEN
                    )
                    self.db.add(anm)
                    detected_anomalies.append(anm)

        # -------------------------------------------------------------
        # 2. SCHOLARSHIP_EXCEEDS_FEES
        # -------------------------------------------------------------
        eligibilities = (
            self.db.query(Eligibility)
            .filter(Eligibility.status == EligibilityStatus.APPROVED)
            .all()
        )
        for elig in eligibilities:
            if elig.approved_amount > elig.eligible_fee_amount:
                if not already_logged(AnomalyIssueType.SCHOLARSHIP_EXCEEDS_FEES, elig.eligibility_id):
                    seq += 1
                    anm = Anomaly(
                        anomaly_id=IDGenerator.anomaly_id(seq),
                        issue_type=AnomalyIssueType.SCHOLARSHIP_EXCEEDS_FEES,
                        entity_type="SCHOLARSHIP_ELIGIBILITY",
                        entity_id=elig.eligibility_id,
                        severity=AnomalySeverity.HIGH,
                        expected_value=elig.eligible_fee_amount,
                        actual_value=elig.approved_amount,
                        explanation=(
                            f"Approved scholarship amount ({elig.approved_amount}) exceeds "
                            f"eligible fee charges ({elig.eligible_fee_amount})."
                        ),
                        resolution_status=AnomalyResolutionStatus.OPEN
                    )
                    self.db.add(anm)
                    detected_anomalies.append(anm)

        # -------------------------------------------------------------
        # 3. DUPLICATE_INVOICE
        # -------------------------------------------------------------
        duplicate_groups = (
            self.db.query(Invoice.enrollment_id, Invoice.billing_cycle, func.count(Invoice.id).label("count"))
            .filter(Invoice.status != InvoiceStatus.CANCELLED)
            .group_by(Invoice.enrollment_id, Invoice.billing_cycle)
            .having(func.count(Invoice.id) > 1)
            .all()
        )
        for grp in duplicate_groups:
            dup_invoices = (
                self.db.query(Invoice)
                .filter(
                    Invoice.enrollment_id == grp.enrollment_id,
                    Invoice.billing_cycle == grp.billing_cycle,
                    Invoice.status != InvoiceStatus.CANCELLED
                )
                .all()
            )
            for dup_inv in dup_invoices[1:]:
                if not already_logged(AnomalyIssueType.DUPLICATE_INVOICE, dup_inv.invoice_id):
                    seq += 1
                    anm = Anomaly(
                        anomaly_id=IDGenerator.anomaly_id(seq),
                        issue_type=AnomalyIssueType.DUPLICATE_INVOICE,
                        entity_type="INVOICE",
                        entity_id=dup_inv.invoice_id,
                        severity=AnomalySeverity.HIGH,
                        expected_value=Decimal("1.00"),
                        actual_value=Decimal(str(grp.count)),
                        explanation=(
                            f"Multiple non-cancelled invoices exist for enrollment ID {grp.enrollment_id} "
                            f"and billing cycle {grp.billing_cycle}."
                        ),
                        resolution_status=AnomalyResolutionStatus.OPEN
                    )
                    self.db.add(anm)
                    detected_anomalies.append(anm)

        # -------------------------------------------------------------
        # 4. REFUND_EXCEEDS_PAID
        # -------------------------------------------------------------
        for p in payments:
            refund_sum = self.db.query(func.coalesce(func.sum(Refund.amount), Decimal("0.00"))).filter(
                Refund.payment_id == p.id,
                Refund.status != RefundStatus.REJECTED
            ).scalar() or Decimal("0.00")

            if refund_sum > p.amount:
                if not already_logged(AnomalyIssueType.REFUND_EXCEEDS_PAID, p.payment_id):
                    seq += 1
                    anm = Anomaly(
                        anomaly_id=IDGenerator.anomaly_id(seq),
                        issue_type=AnomalyIssueType.REFUND_EXCEEDS_PAID,
                        entity_type="PAYMENT",
                        entity_id=p.payment_id,
                        severity=AnomalySeverity.CRITICAL,
                        expected_value=p.amount,
                        actual_value=refund_sum,
                        explanation=(
                            f"Total refunds requested/processed ({refund_sum}) exceed original "
                            f"payment amount ({p.amount}) for payment {p.payment_id}."
                        ),
                        resolution_status=AnomalyResolutionStatus.OPEN
                    )
                    self.db.add(anm)
                    detected_anomalies.append(anm)

        # -------------------------------------------------------------
        # 5. BALANCE_MISMATCH
        # -------------------------------------------------------------
        invoices = self.db.query(Invoice).options(joinedload(Invoice.lines)).filter(Invoice.status != InvoiceStatus.CANCELLED).all()
        for inv in invoices:
            expected_net = max(Decimal("0.00"), inv.gross_amount - inv.scholarship_amount)
            expected_balance = max(Decimal("0.00"), expected_net + inv.late_fee_amount - inv.paid_amount)
            if abs(inv.outstanding_balance - expected_balance) >= Decimal("0.01"):
                if not already_logged(AnomalyIssueType.BALANCE_MISMATCH, inv.invoice_id):
                    seq += 1
                    anm = Anomaly(
                        anomaly_id=IDGenerator.anomaly_id(seq),
                        issue_type=AnomalyIssueType.BALANCE_MISMATCH,
                        entity_type="INVOICE",
                        entity_id=inv.invoice_id,
                        severity=AnomalySeverity.MEDIUM,
                        expected_value=expected_balance,
                        actual_value=inv.outstanding_balance,
                        explanation=(
                            f"Invoice {inv.invoice_id} stored balance ({inv.outstanding_balance}) disagrees with "
                            f"calculated balance ({expected_balance})."
                        ),
                        resolution_status=AnomalyResolutionStatus.OPEN
                    )
                    self.db.add(anm)
                    detected_anomalies.append(anm)

        if detected_anomalies:
            self.db.commit()
            for a in detected_anomalies:
                self.db.refresh(a)

        return detected_anomalies

