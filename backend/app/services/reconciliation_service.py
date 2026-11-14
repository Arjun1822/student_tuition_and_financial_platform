from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine
from app.models.payment_allocation import PaymentAllocation
from app.models.reconciliation import (
    ReconciliationRun,
    ReconciliationResult,
    ReconciliationRunStatus,
    ReconciliationStatus,
)
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService


class ReconciliationService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def run_reconciliation(
        self,
        term_id: Optional[int] = None,
        program_id: Optional[int] = None,
        actor_id: Optional[int] = None
    ) -> ReconciliationRun:
        """
        Executes a batch reconciliation run across student invoices.
        Expected Balance = Net Collectible Charges + Applicable Late Fees - Valid Allocations
        Compares expected balance against stored invoice.outstanding_balance.
        Produces deterministic reconciliation records and classifies discrepancies.
        """
        run_count = self.db.query(func.count(ReconciliationRun.id)).scalar() or 0
        run_b_id = IDGenerator.reconciliation_run_id(run_count + 1)

        run = ReconciliationRun(
            run_id=run_b_id,
            total_invoices=0,
            matched_count=0,
            mismatched_count=0,
            exception_count=0,
            status=ReconciliationRunStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        self.db.flush()

        # Query relevant invoices
        query = (
            self.db.query(Invoice)
            .options(joinedload(Invoice.lines).joinedload(InvoiceLine.allocations))
            .filter(Invoice.status != InvoiceStatus.CANCELLED)
        )
        if term_id:
            query = query.filter(Invoice.term_id == term_id)
        if program_id:
            query = query.filter(Invoice.program_id == program_id)

        invoices = query.all()
        run.total_invoices = len(invoices)

        matched = 0
        mismatched = 0
        exceptions = 0

        for inv in invoices:
            try:
                # Sum of valid line amounts
                gross_charges = sum((l.amount for l in inv.lines), Decimal("0.00"))
                net_collectible = max(Decimal("0.00"), gross_charges - inv.scholarship_amount)

                # Sum of valid allocations across lines
                valid_allocations = Decimal("0.00")
                for line in inv.lines:
                    valid_allocations += sum((a.amount for a in line.allocations), Decimal("0.00"))

                expected_balance = max(
                    Decimal("0.00"),
                    net_collectible + inv.late_fee_amount - valid_allocations
                )
                actual_balance = inv.outstanding_balance
                diff = actual_balance - expected_balance

                if abs(diff) < Decimal("0.01"):
                    rec_status = ReconciliationStatus.MATCHED
                    matched += 1
                    notes = "Expected balance perfectly matches stored invoice balance."
                    exc_type = None
                else:
                    rec_status = ReconciliationStatus.MISMATCHED
                    mismatched += 1
                    notes = f"Balance mismatch detected. Diff: {diff} INR."
                    exc_type = "BALANCE_DISCREPANCY"

                result = ReconciliationResult(
                    run_id=run.id,
                    invoice_id=inv.id,
                    entity_type="INVOICE",
                    entity_id=inv.invoice_id,
                    expected_amount=expected_balance,
                    actual_amount=actual_balance,
                    difference=diff,
                    status=rec_status,
                    exception_type=exc_type,
                    notes=notes
                )
                self.db.add(result)

            except Exception as e:
                exceptions += 1
                result = ReconciliationResult(
                    run_id=run.id,
                    invoice_id=inv.id,
                    entity_type="INVOICE",
                    entity_id=inv.invoice_id,
                    expected_amount=Decimal("0.00"),
                    actual_amount=inv.outstanding_balance,
                    difference=inv.outstanding_balance,
                    status=ReconciliationStatus.EXCEPTION,
                    exception_type="CALCULATION_EXCEPTION",
                    notes=str(e)
                )
                self.db.add(result)

        run.matched_count = matched
        run.mismatched_count = mismatched
        run.exception_count = exceptions
        run.status = ReconciliationRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)

        # Log Financial Event
        event_count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        evt = FinancialEvent(
            event_id=IDGenerator.event_id(event_count + 1),
            entity_type="RECONCILIATION_RUN",
            entity_id=run.run_id,
            event_type=FinancialEventType.RECONCILIATION_COMPLETED,
            actor_id=actor_id,
            metadata_json={
                "total": run.total_invoices,
                "matched": matched,
                "mismatched": mismatched,
                "exceptions": exceptions
            }
        )
        self.db.add(evt)

        # Audit Log
        self.audit_service.log_action(
            actor_id=actor_id,
            action="RUN_RECONCILIATION",
            entity_type="RECONCILIATION_RUN",
            entity_id=run.run_id,
            new_values={
                "matched": matched,
                "mismatched": mismatched,
                "exceptions": exceptions
            }
        )

        self.db.commit()
        self.db.refresh(run)
        return run

