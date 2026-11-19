"""Validation Script for Deterministic Synthetic Data & Anomaly Detection.

Validates:
1. Schema & Referential Integrity (Primary keys, Foreign keys)
2. Financial Precision & Business Arithmetic (Decimal correctness, balances, allocations)
3. Controlled Anomaly Detection vs Ground Truth (Precision, Recall, F1 evaluation)
4. Emits structured JSON report and human-readable summary table.
"""

import argparse
import csv
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Tuple

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.anomaly_service import AnomalyDetectionService


def parse_decimal(val: Any) -> Decimal:
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


class DataValidator:
    def __init__(self, data_dir: str = "data/export", check_db: bool = False, report_path: Optional[str] = None):
        self.data_dir = data_dir
        self.check_db = check_db
        self.report_path = report_path or os.path.join(data_dir, "validation_report.json")
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _read_csv(self, filename: str) -> List[Dict[str, str]]:
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            self.errors.append(f"Missing required data file: {filename}")
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _read_json(self, filename: str) -> Any:
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            self.errors.append(f"Missing required JSON file: {filename}")
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self, db: Optional[Session] = None) -> Dict[str, Any]:
        print(f"=== Synthetic Data & Anomaly Validation (Directory: {self.data_dir}) ===")
        
        # 1. Load Files
        students = self._read_csv("students.csv")
        programs = self._read_csv("programs.csv")
        terms = self._read_csv("terms.csv")
        fee_schedules = self._read_csv("fee_schedules.csv")
        enrollments = self._read_csv("enrollments.csv")
        invoices = self._read_csv("invoices.csv")
        invoice_lines = self._read_csv("invoice_lines.csv")
        scholarships = self._read_csv("scholarships.csv")
        eligibilities = self._read_csv("eligibilities.csv")
        payments = self._read_csv("payments.csv")
        allocations = self._read_csv("payment_allocations.csv")
        refunds = self._read_csv("refunds.csv")
        financial_events = self._read_csv("financial_events.csv")
        ground_truth = self._read_json("ground_truth.json") or []

        # 2. Referential Integrity & Primary Key Checks
        ref_results = self._validate_referential_integrity(
            students, programs, terms, fee_schedules, enrollments,
            invoices, invoice_lines, scholarships, eligibilities,
            payments, allocations, refunds, financial_events
        )

        # 3. Enum domains and chronological date ordering
        enum_date_results = self._validate_enums_and_dates(
            terms, invoices, payments, refunds, enrollments,
            students, scholarships, eligibilities
        )

        # 4. Financial Arithmetic & Business Rules (including event amount parity)
        fin_results = self._validate_financial_arithmetic(
            invoices, invoice_lines, payments, allocations, scholarships, eligibilities, ground_truth,
            financial_events=financial_events, refunds=refunds
        )

        # 5. Anomaly Detection Ground Truth Evaluation (Per-category and overall)
        anomaly_results = self._evaluate_anomalies(
            db, ground_truth, payments, allocations, eligibilities,
            enrollments, invoices, invoice_lines, refunds
        )

        # Check export presence (CSV, JSON, SQL seed)
        export_checks = self._validate_export_manifest()

        # Overall Status
        passed = (
            len(self.errors) == 0 and
            ref_results["passed"] and
            enum_date_results["passed"] and
            fin_results["passed"] and
            anomaly_results["passed"]
        )

        report = {
            "validation_passed": passed,
            "data_directory": self.data_dir,
            "referential_integrity": ref_results,
            "enums_and_dates": enum_date_results,
            "financial_arithmetic": fin_results,
            "anomaly_evaluation": anomaly_results,
            "export_artifacts": export_checks,
            "errors": self.errors,
            "warnings": self.warnings,
        }

        # Save JSON Report
        os.makedirs(os.path.dirname(os.path.abspath(self.report_path)), exist_ok=True)
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"-> Validation report saved to {self.report_path}")

        # Summary output
        self._print_summary(report)

        return report

    def _validate_export_manifest(self) -> Dict[str, Any]:
        expected_csvs = [
            "students.csv", "programs.csv", "terms.csv", "fee_schedules.csv",
            "enrollments.csv", "scholarships.csv", "invoices.csv", "invoice_lines.csv",
            "eligibilities.csv", "payments.csv", "payment_allocations.csv",
            "refunds.csv", "financial_events.csv", "ground_truth.csv"
        ]
        expected_jsons = [
            "students.json", "programs.json", "terms.json", "fee_schedules.json",
            "enrollments.json", "scholarships.json", "invoices.json", "invoice_lines.json",
            "eligibilities.json", "payments.json", "payment_allocations.json",
            "refunds.json", "financial_events.json", "ground_truth.json", "generation_manifest.json"
        ]
        sql_seed = "seed_data.sql"

        csv_status = {f: os.path.exists(os.path.join(self.data_dir, f)) for f in expected_csvs}
        json_status = {f: os.path.exists(os.path.join(self.data_dir, f)) for f in expected_jsons}
        sql_exists = os.path.exists(os.path.join(self.data_dir, sql_seed))

        return {
            "all_csvs_present": all(csv_status.values()),
            "all_jsons_present": all(json_status.values()),
            "sql_seed_present": sql_exists,
            "csv_files": csv_status,
            "json_files": json_status,
        }

    def _validate_referential_integrity(
        self,
        students, programs, terms, fee_schedules, enrollments,
        invoices, invoice_lines, scholarships, eligibilities,
        payments, allocations, refunds, financial_events=None
    ) -> Dict[str, Any]:
        print("-> Checking schema constraints and referential integrity...")
        checks = {}

        # Collect Primary Key Sets
        student_ids = {s["id"] for s in students}
        program_ids = {p["id"] for p in programs}
        term_ids = {t["id"] for t in terms}
        enrollment_ids = {e["id"] for e in enrollments}
        invoice_ids = {inv["id"] for inv in invoices}
        invoice_line_ids = {line["id"] for line in invoice_lines}
        scholarship_ids = {sch["id"] for sch in scholarships}
        payment_ids = {pay["id"] for pay in payments}

        # Collect Business IDs for event entity resolution
        invoice_biz_ids = {inv["invoice_id"] for inv in invoices}
        payment_biz_ids = {pay["payment_id"] for pay in payments}
        allocation_biz_ids = {a["allocation_id"] for a in allocations}
        eligibility_biz_ids = {e["eligibility_id"] for e in eligibilities}
        refund_biz_ids = {r["refund_id"] for r in refunds}

        # Check PK Uniqueness
        def check_pk_uniqueness(name: str, records: List[Dict[str, str]], pk_col: str = "id") -> bool:
            ids = [r[pk_col] for r in records if pk_col in r]
            is_unique = len(ids) == len(set(ids))
            if not is_unique:
                self.errors.append(f"Primary key '{pk_col}' in {name} contains duplicate values!")
            return is_unique

        checks["pk_uniqueness"] = {
            "students": check_pk_uniqueness("students", students),
            "programs": check_pk_uniqueness("programs", programs),
            "terms": check_pk_uniqueness("terms", terms),
            "fee_schedules": check_pk_uniqueness("fee_schedules", fee_schedules),
            "enrollments": check_pk_uniqueness("enrollments", enrollments),
            "invoices": check_pk_uniqueness("invoices", invoices),
            "invoice_lines": check_pk_uniqueness("invoice_lines", invoice_lines),
            "scholarships": check_pk_uniqueness("scholarships", scholarships),
            "eligibilities": check_pk_uniqueness("eligibilities", eligibilities),
            "payments": check_pk_uniqueness("payments", payments),
            "payment_allocations": check_pk_uniqueness("payment_allocations", allocations),
            "refunds": check_pk_uniqueness("refunds", refunds),
        }
        if financial_events:
            checks["pk_uniqueness"]["financial_events_id"] = check_pk_uniqueness("financial_events", financial_events, "id")
            checks["pk_uniqueness"]["financial_events_event_id"] = check_pk_uniqueness("financial_events", financial_events, "event_id")

        # Check FK References
        def check_fk(name: str, records: List[Dict[str, str]], fk_col: str, parent_set: Set[str], parent_name: str) -> bool:
            missing = [r[fk_col] for r in records if r.get(fk_col) and r[fk_col] not in parent_set]
            if missing:
                self.errors.append(f"Foreign key {name}.{fk_col} references non-existent {parent_name}: {missing[:5]}")
                return False
            return True

        checks["foreign_keys"] = {
            "enrollments_to_students": check_fk("enrollments", enrollments, "student_id", student_ids, "students"),
            "enrollments_to_programs": check_fk("enrollments", enrollments, "program_id", program_ids, "programs"),
            "enrollments_to_terms": check_fk("enrollments", enrollments, "term_id", term_ids, "terms"),
            "fee_schedules_to_programs": check_fk("fee_schedules", fee_schedules, "program_id", program_ids, "programs"),
            "fee_schedules_to_terms": check_fk("fee_schedules", fee_schedules, "term_id", term_ids, "terms"),
            "invoices_to_enrollments": check_fk("invoices", invoices, "enrollment_id", enrollment_ids, "enrollments"),
            "invoices_to_students": check_fk("invoices", invoices, "student_id", student_ids, "students"),
            "invoices_to_terms": check_fk("invoices", invoices, "term_id", term_ids, "terms"),
            "invoice_lines_to_invoices": check_fk("invoice_lines", invoice_lines, "invoice_id", invoice_ids, "invoices"),
            "eligibilities_to_students": check_fk("eligibilities", eligibilities, "student_id", student_ids, "students"),
            "eligibilities_to_scholarships": check_fk("eligibilities", eligibilities, "scholarship_id", scholarship_ids, "scholarships"),
            "eligibilities_to_enrollments": check_fk("eligibilities", eligibilities, "enrollment_id", enrollment_ids, "enrollments"),
            "payments_to_students": check_fk("payments", payments, "student_id", student_ids, "students"),
            "allocations_to_payments": check_fk("payment_allocations", allocations, "payment_id", payment_ids, "payments"),
            "allocations_to_invoice_lines": check_fk("payment_allocations", allocations, "invoice_line_id", invoice_line_ids, "invoice_lines"),
            "refunds_to_payments": check_fk("refunds", refunds, "payment_id", payment_ids, "payments"),
            "refunds_to_students": check_fk("refunds", refunds, "student_id", student_ids, "students"),
        }

        # Check Financial Events Source Entity References
        if financial_events:
            orphan_events = 0
            for evt in financial_events:
                etype = evt.get("entity_type")
                eid = evt.get("entity_id")
                if etype == "INVOICE" and eid not in invoice_biz_ids:
                    self.errors.append(f"Event {evt.get('event_id')} references non-existent invoice: {eid}")
                    orphan_events += 1
                elif etype == "PAYMENT" and eid not in payment_biz_ids:
                    self.errors.append(f"Event {evt.get('event_id')} references non-existent payment: {eid}")
                    orphan_events += 1
                elif etype == "PAYMENT_ALLOCATION" and eid not in allocation_biz_ids:
                    self.errors.append(f"Event {evt.get('event_id')} references non-existent allocation: {eid}")
                    orphan_events += 1
                elif etype == "SCHOLARSHIP_ELIGIBILITY" and eid not in eligibility_biz_ids:
                    self.errors.append(f"Event {evt.get('event_id')} references non-existent eligibility: {eid}")
                    orphan_events += 1
                elif etype == "REFUND" and eid not in refund_biz_ids:
                    self.errors.append(f"Event {evt.get('event_id')} references non-existent refund: {eid}")
                    orphan_events += 1
            checks["foreign_keys"]["financial_events_source_references"] = (orphan_events == 0)

        all_passed = all(checks["pk_uniqueness"].values()) and all(checks["foreign_keys"].values())
        return {"passed": all_passed, "checks": checks}

    def _validate_financial_arithmetic(
        self,
        invoices: List[Dict[str, str]],
        invoice_lines: List[Dict[str, str]],
        payments: List[Dict[str, str]],
        allocations: List[Dict[str, str]],
        scholarships: List[Dict[str, str]],
        eligibilities: List[Dict[str, str]],
        ground_truth: List[Dict[str, Any]],
        financial_events: Optional[List[Dict[str, str]]] = None,
        refunds: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        print("-> Checking financial precision and business rules...")
        anomalous_entities = {gt["entity_id"] for gt in ground_truth}
        checks = {}

        # 1. Invoice Net and Balance Arithmetic
        inv_arithmetic_errors = 0
        lines_by_inv: Dict[str, List[Dict[str, str]]] = {}
        for l in invoice_lines:
            lines_by_inv.setdefault(l["invoice_id"], []).append(l)

        for inv in invoices:
            gross = parse_decimal(inv["gross_amount"])
            disc = parse_decimal(inv["scholarship_discount"])
            net = parse_decimal(inv["net_amount"])
            paid = parse_decimal(inv["amount_paid"])
            bal = parse_decimal(inv["outstanding_balance"])

            # Check gross - discount == net
            expected_net = max(Decimal("0.00"), gross - disc)
            if net != expected_net:
                self.errors.append(f"Invoice {inv['invoice_id']} net ({net}) != gross ({gross}) - discount ({disc})")
                inv_arithmetic_errors += 1

            # Check balance: net - paid == bal (for non-anomalous invoices)
            if inv["invoice_id"] not in anomalous_entities:
                expected_bal = max(Decimal("0.00"), net - paid)
                if bal != expected_bal:
                    self.errors.append(f"Invoice {inv['invoice_id']} balance ({bal}) != net ({net}) - paid ({paid})")
                    inv_arithmetic_errors += 1

            # Check sum of lines equals gross
            inv_lines = lines_by_inv.get(inv["id"], [])
            if inv_lines:
                lines_sum = sum(parse_decimal(l["amount"]) for l in inv_lines)
                if lines_sum != gross:
                    self.errors.append(f"Invoice {inv['invoice_id']} lines sum ({lines_sum}) != gross ({gross})")
                    inv_arithmetic_errors += 1

        checks["invoice_arithmetic_valid"] = (inv_arithmetic_errors == 0)

        # 2. Payment Allocations Arithmetic
        pay_arithmetic_errors = 0
        allocs_by_pay: Dict[str, List[Dict[str, str]]] = {}
        for a in allocations:
            allocs_by_pay.setdefault(a["payment_id"], []).append(a)

        for pay in payments:
            amt = parse_decimal(pay["amount"])
            alloc = parse_decimal(pay["allocated_amount"])
            unalloc = parse_decimal(pay["unallocated_amount"])

            if pay["payment_id"] not in anomalous_entities:
                if alloc > amt:
                    self.errors.append(f"Payment {pay['payment_id']} allocated ({alloc}) > amount ({amt})")
                    pay_arithmetic_errors += 1
                if unalloc + alloc != amt:
                    self.errors.append(f"Payment {pay['payment_id']} unalloc ({unalloc}) + alloc ({alloc}) != amt ({amt})")
                    pay_arithmetic_errors += 1

        checks["payment_arithmetic_valid"] = (pay_arithmetic_errors == 0)

        # 3. Scholarship Budget Checks
        sch_budget_errors = 0
        awarded_by_sch: Dict[str, Decimal] = {}
        for elig in eligibilities:
            if elig.get("status") == "APPROVED":
                sch_id = elig["scholarship_id"]
                awarded_by_sch[sch_id] = awarded_by_sch.get(sch_id, Decimal("0.00")) + parse_decimal(elig.get("approved_amount", "0.00"))

        for sch in scholarships:
            budget = parse_decimal(sch["total_budget"])
            awarded = awarded_by_sch.get(sch["id"], Decimal("0.00"))
            if awarded > budget:
                self.errors.append(f"Scholarship {sch['scholarship_id']} awarded ({awarded}) > budget ({budget})")
                sch_budget_errors += 1

        checks["scholarship_budgets_valid"] = (sch_budget_errors == 0)

        # 4. Financial Event Amount Parity and Type Matching
        event_parity_errors = 0
        if financial_events:
            invoices_by_id = {inv["invoice_id"]: inv for inv in invoices}
            payments_by_id = {pay["payment_id"]: pay for pay in payments}
            allocs_by_id = {a["allocation_id"]: a for a in allocations}
            eligs_by_id = {e["eligibility_id"]: e for e in eligibilities}
            refunds_by_id = {r["refund_id"]: r for r in refunds} if refunds else {}

            expected_event_types = {
                "INVOICE": "INVOICE_ISSUED",
                "PAYMENT": "PAYMENT_RECEIVED",
                "PAYMENT_ALLOCATION": "PAYMENT_ALLOCATED",
                "SCHOLARSHIP_ELIGIBILITY": "SCHOLARSHIP_APPROVED",
                "REFUND": "REFUND_PROCESSED",
            }

            for evt in financial_events:
                etype = evt.get("entity_type")
                eid = evt.get("entity_id")
                actual_event_type = evt.get("event_type")
                expected_type = expected_event_types.get(etype)

                if expected_type and actual_event_type != expected_type:
                    self.errors.append(f"Event {evt.get('event_id')} type '{actual_event_type}' does not match expected '{expected_type}' for {etype}")
                    event_parity_errors += 1

                evt_amt = parse_decimal(evt.get("amount", "0.00"))

                # Check amount against source transaction
                if etype == "INVOICE" and eid in invoices_by_id:
                    src_amt = parse_decimal(invoices_by_id[eid]["gross_amount"])
                    if evt_amt != src_amt:
                        self.errors.append(f"Event {evt.get('event_id')} amount ({evt_amt}) != Invoice {eid} gross ({src_amt})")
                        event_parity_errors += 1
                elif etype == "PAYMENT" and eid in payments_by_id:
                    src_amt = parse_decimal(payments_by_id[eid]["amount"])
                    if evt_amt != src_amt:
                        self.errors.append(f"Event {evt.get('event_id')} amount ({evt_amt}) != Payment {eid} amount ({src_amt})")
                        event_parity_errors += 1
                elif etype == "PAYMENT_ALLOCATION" and eid in allocs_by_id:
                    src_amt = parse_decimal(allocs_by_id[eid]["amount"])
                    if evt_amt != src_amt:
                        self.errors.append(f"Event {evt.get('event_id')} amount ({evt_amt}) != Allocation {eid} amount ({src_amt})")
                        event_parity_errors += 1
                elif etype == "SCHOLARSHIP_ELIGIBILITY" and eid in eligs_by_id:
                    # Note: for Anomaly 2, approved_amount was mutated from calculated_amount to exceed fees
                    # The event reflects the legitimate award amount calculated at event emission time
                    if eid not in anomalous_entities:
                        src_amt = parse_decimal(eligs_by_id[eid]["approved_amount"])
                        if evt_amt != src_amt:
                            self.errors.append(f"Event {evt.get('event_id')} amount ({evt_amt}) != Eligibility {eid} approved ({src_amt})")
                            event_parity_errors += 1
                elif etype == "REFUND" and eid in refunds_by_id:
                    src_amt = parse_decimal(refunds_by_id[eid]["amount"])
                    if evt_amt != src_amt:
                        self.errors.append(f"Event {evt.get('event_id')} amount ({evt_amt}) != Refund {eid} amount ({src_amt})")
                        event_parity_errors += 1

        checks["event_amount_parity_valid"] = (event_parity_errors == 0)

        passed = (
            inv_arithmetic_errors == 0 and
            pay_arithmetic_errors == 0 and
            sch_budget_errors == 0 and
            event_parity_errors == 0
        )
        return {"passed": passed, "checks": checks}

    def _validate_enums_and_dates(
        self,
        terms: List[Dict[str, str]],
        invoices: List[Dict[str, str]],
        payments: List[Dict[str, str]],
        refunds: List[Dict[str, str]],
        enrollments: List[Dict[str, str]],
        students: List[Dict[str, str]],
        scholarships: List[Dict[str, str]],
        eligibilities: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        print("-> Checking valid enum domains and chronological date ordering...")
        date_errors = 0
        enum_errors = 0

        # Allowed Enum Sets (aligned with actual SQLAlchemy model definitions)
        valid_student_statuses = {"ACTIVE", "INACTIVE", "GRADUATED", "SUSPENDED"}
        valid_enrollment_statuses = {"PENDING", "ACTIVE", "COMPLETED", "CANCELLED", "WITHDRAWN"}
        valid_invoice_statuses = {"DRAFT", "ISSUED", "PARTIALLY_PAID", "PAID", "OVERDUE", "CANCELLED", "REFUNDED"}
        valid_scholarship_statuses = {"ACTIVE", "INACTIVE", "EXHAUSTED"}
        valid_eligibility_statuses = {"PENDING", "APPROVED", "REJECTED", "REVOKED"}
        valid_payment_methods = {"UPI", "BANK_TRANSFER", "CREDIT_CARD", "DEBIT_CARD", "CASH", "CHEQUE", "ONLINE"}
        valid_payment_statuses = {"PENDING", "COMPLETED", "FAILED", "REVERSED", "REFUNDED"}
        valid_refund_statuses = {"REQUESTED", "APPROVED", "PROCESSED", "REJECTED"}

        # Validate Student Statuses
        for s in students:
            if s.get("status") and s["status"] not in valid_student_statuses:
                self.errors.append(f"Invalid Student status '{s['status']}' on student {s.get('student_id')}")
                enum_errors += 1

        # Validate Enrollment Statuses
        for e in enrollments:
            if e.get("status") and e["status"] not in valid_enrollment_statuses:
                self.errors.append(f"Invalid Enrollment status '{e['status']}' on enrollment {e.get('enrollment_id')}")
                enum_errors += 1

        # Validate Terms Date Ordering
        for t in terms:
            start = t.get("start_date")
            end = t.get("end_date")
            if start and end and start >= end:
                self.errors.append(f"Term {t.get('term_id')} start_date ({start}) >= end_date ({end})")
                date_errors += 1

        # Validate Invoices
        for inv in invoices:
            st = inv.get("status")
            if st and st not in valid_invoice_statuses:
                self.errors.append(f"Invalid Invoice status '{st}' on invoice {inv.get('invoice_id')}")
                enum_errors += 1
            inv_date = inv.get("invoice_date")
            due_date = inv.get("due_date")
            if inv_date and due_date and inv_date > due_date:
                self.errors.append(f"Invoice {inv.get('invoice_id')} date ({inv_date}) > due_date ({due_date})")
                date_errors += 1

        # Validate Payments
        for p in payments:
            m = p.get("payment_method")
            if m and m not in valid_payment_methods:
                self.errors.append(f"Invalid Payment method '{m}' on payment {p.get('payment_id')}")
                enum_errors += 1
            st = p.get("status")
            if st and st not in valid_payment_statuses:
                self.errors.append(f"Invalid Payment status '{st}' on payment {p.get('payment_id')}")
                enum_errors += 1

        # Validate Refunds
        for r in refunds:
            st = r.get("status")
            if st and st not in valid_refund_statuses:
                self.errors.append(f"Invalid Refund status '{st}' on refund {r.get('refund_id')}")
                enum_errors += 1

        # Validate Scholarships & Eligibilities
        for sch in scholarships:
            st = sch.get("status")
            if st and st not in valid_scholarship_statuses:
                self.errors.append(f"Invalid Scholarship status '{st}' on {sch.get('scholarship_id')}")
                enum_errors += 1

        for elig in eligibilities:
            st = elig.get("status")
            if st and st not in valid_eligibility_statuses:
                self.errors.append(f"Invalid Eligibility status '{st}' on {elig.get('eligibility_id')}")
                enum_errors += 1

        passed = (date_errors == 0 and enum_errors == 0)
        return {
            "passed": passed,
            "date_ordering_errors": date_errors,
            "enum_domain_errors": enum_errors,
        }

    def _evaluate_anomalies(
        self,
        db: Optional[Session],
        ground_truth: List[Dict[str, Any]],
        payments: List[Dict[str, str]],
        allocations: List[Dict[str, str]],
        eligibilities: List[Dict[str, str]],
        enrollments: List[Dict[str, str]],
        invoices: List[Dict[str, str]],
        invoice_lines: List[Dict[str, str]],
        refunds: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        print("-> Evaluating Anomaly Detection Engine against Ground Truth...")
        if not ground_truth:
            self.errors.append("No ground truth anomalies available for evaluation!")
            return {
                "status": "NOT RUN",
                "passed": False,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "true_negatives": 0,
            }

        detected: List[Dict[str, Any]] = []
        execution_mode = "DATASET_SCANNER"

        # If --check-db was requested, attempt to run via active MySQL database
        if self.check_db or db:
            execution_mode = "DATABASE_SERVICE"
            session = db or SessionLocal()
            try:
                detector = AnomalyDetectionService(session)
                detector.scan_for_anomalies()
                from app.models.anomaly import Anomaly, AnomalyResolutionStatus
                db_anomalies = session.query(Anomaly).filter(
                    Anomaly.resolution_status != AnomalyResolutionStatus.RESOLVED
                ).all()
                for anm in db_anomalies:
                    detected.append({
                        "issue_type": anm.issue_type.value if hasattr(anm.issue_type, "value") else str(anm.issue_type),
                        "entity_id": anm.entity_id,
                        "expected_value": float(anm.expected_value) if anm.expected_value is not None else None,
                        "actual_value": float(anm.actual_value) if anm.actual_value is not None else None,
                    })
            except Exception as e:
                err_msg = f"Database anomaly detection failed or blocked: {e}"
                self.errors.append(err_msg)
                return {
                    "status": "BLOCKED",
                    "execution_mode": execution_mode,
                    "passed": False,
                    "error": str(e),
                    "ground_truth_count": len(ground_truth),
                    "detected_count": 0,
                    "true_positives": 0,
                    "false_positives": 0,
                    "false_negatives": len(ground_truth),
                    "true_negatives": 0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "by_category": {},
                }
            finally:
                if not db:
                    session.close()
        else:
            # Standalone Dataset Detection Engine running authoritative business rules on records
            execution_mode = "DATASET_ENGINE"
            
            # Rule 1: PAYMENT_OVER_ALLOCATED
            allocs_by_pay: Dict[str, Decimal] = {}
            for a in allocations:
                pid = str(a.get("payment_id", ""))
                allocs_by_pay[pid] = allocs_by_pay.get(pid, Decimal("0.00")) + parse_decimal(a.get("amount", "0.00"))

            for p in payments:
                pid = str(p.get("id", ""))
                p_amt = parse_decimal(p.get("amount", "0.00"))
                p_alloc_field = parse_decimal(p.get("allocated_amount", "0.00"))
                p_alloc_sum = allocs_by_pay.get(pid, Decimal("0.00"))
                if p_alloc_sum > p_amt or p_alloc_field > p_amt:
                    detected.append({
                        "issue_type": "PAYMENT_OVER_ALLOCATED",
                        "entity_id": p.get("payment_id"),
                        "expected_value": float(p_amt),
                        "actual_value": float(max(p_alloc_sum, p_alloc_field)),
                    })

            # Rule 2: SCHOLARSHIP_EXCEEDS_FEES
            for elig in eligibilities:
                if elig.get("status") == "APPROVED":
                    appr = parse_decimal(elig.get("approved_amount", "0.00"))
                    elig_fee = parse_decimal(elig.get("eligible_fee_amount", "0.00"))
                    if appr > elig_fee:
                        detected.append({
                            "issue_type": "SCHOLARSHIP_EXCEEDS_FEES",
                            "entity_id": elig.get("eligibility_id"),
                            "expected_value": float(elig_fee),
                            "actual_value": float(appr),
                        })

            # Rule 3: DUPLICATE_INVOICE
            dup_groups: Dict[Tuple[str, str], List[Dict[str, str]]] = {}
            for inv in invoices:
                if inv.get("status") != "CANCELLED":
                    key = (str(inv.get("enrollment_id")), str(inv.get("billing_cycle")))
                    dup_groups.setdefault(key, []).append(inv)

            for key, group in dup_groups.items():
                if len(group) > 1:
                    for dup_inv in group[1:]:
                        detected.append({
                            "issue_type": "DUPLICATE_INVOICE",
                            "entity_id": dup_inv.get("invoice_id"),
                            "expected_value": 1.0,
                            "actual_value": float(len(group)),
                        })

            # Rule 4: REFUND_EXCEEDS_PAID
            refunds_by_pay: Dict[str, Decimal] = {}
            for r in refunds:
                if r.get("status") != "REJECTED":
                    pid = str(r.get("payment_id", ""))
                    refunds_by_pay[pid] = refunds_by_pay.get(pid, Decimal("0.00")) + parse_decimal(r.get("amount", "0.00"))

            for p in payments:
                pid = str(p.get("id", ""))
                p_amt = parse_decimal(p.get("amount", "0.00"))
                p_ref_sum = refunds_by_pay.get(pid, Decimal("0.00"))
                if p_ref_sum > p_amt:
                    detected.append({
                        "issue_type": "REFUND_EXCEEDS_PAID",
                        "entity_id": p.get("payment_id"),
                        "expected_value": float(p_amt),
                        "actual_value": float(p_ref_sum),
                    })

            # Rule 5: BALANCE_MISMATCH
            for inv in invoices:
                if inv.get("status") != "CANCELLED":
                    gross = parse_decimal(inv.get("gross_amount", "0.00"))
                    disc = parse_decimal(inv.get("scholarship_discount", "0.00"))
                    paid = parse_decimal(inv.get("amount_paid", "0.00"))
                    stored_bal = parse_decimal(inv.get("outstanding_balance", "0.00"))
                    expected_net = max(Decimal("0.00"), gross - disc)
                    expected_bal = max(Decimal("0.00"), expected_net - paid)
                    if abs(stored_bal - expected_bal) >= Decimal("0.01"):
                        detected.append({
                            "issue_type": "BALANCE_MISMATCH",
                            "entity_id": inv.get("invoice_id"),
                            "expected_value": float(expected_bal),
                            "actual_value": float(stored_bal),
                        })

        # Category candidates count for accurate True Negatives
        candidate_counts = {
            "PAYMENT_OVER_ALLOCATED": len(payments),
            "SCHOLARSHIP_EXCEEDS_FEES": len(eligibilities),
            "DUPLICATE_INVOICE": len(invoices),
            "REFUND_EXCEEDS_PAID": len(payments),
            "BALANCE_MISMATCH": len(invoices),
        }

        # Categories list
        categories = [
            "PAYMENT_OVER_ALLOCATED",
            "SCHOLARSHIP_EXCEEDS_FEES",
            "DUPLICATE_INVOICE",
            "REFUND_EXCEEDS_PAID",
            "BALANCE_MISMATCH",
        ]

        gt_map = {(gt["issue_type"], gt["entity_id"]): gt for gt in ground_truth}
        det_map = {(d["issue_type"], d["entity_id"]): d for d in detected}

        by_category = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_tn = 0
        matched_details = []

        for cat in categories:
            cat_gt = {gt["entity_id"]: gt for gt in ground_truth if gt["issue_type"] == cat}
            cat_det = {d["entity_id"]: d for d in detected if d["issue_type"] == cat}
            c_count = candidate_counts.get(cat, 0)

            c_tp = len(set(cat_gt.keys()) & set(cat_det.keys()))
            c_fp = len(set(cat_det.keys()) - set(cat_gt.keys()))
            c_fn = len(set(cat_gt.keys()) - set(cat_det.keys()))
            c_tn = max(0, c_count - (c_tp + c_fp + c_fn))

            total_tp += c_tp
            total_fp += c_fp
            total_fn += c_fn
            total_tn += c_tn

            # Zero denominator safe calculations
            c_prec = (c_tp / (c_tp + c_fp)) if (c_tp + c_fp) > 0 else 0.0
            c_rec = (c_tp / (c_tp + c_fn)) if (c_tp + c_fn) > 0 else 0.0
            c_f1 = (2 * c_prec * c_rec / (c_prec + c_rec)) if (c_prec + c_rec) > 0 else 0.0

            by_category[cat] = {
                "candidate_count": c_count,
                "ground_truth_count": len(cat_gt),
                "detected_count": len(cat_det),
                "true_positives": c_tp,
                "false_positives": c_fp,
                "false_negatives": c_fn,
                "true_negatives": c_tn,
                "precision": round(c_prec, 4),
                "recall": round(c_rec, 4),
                "f1_score": round(c_f1, 4),
            }

        for (itype, eid), det in det_map.items():
            if (itype, eid) in gt_map:
                gt = gt_map[(itype, eid)]
                matched_details.append({
                    "issue_type": itype,
                    "entity_id": eid,
                    "expected_value": gt.get("expected_value"),
                    "actual_value": det.get("actual_value"),
                    "match": True,
                })
            else:
                self.errors.append(f"False Positive detected: {itype} on {eid}")

        for (itype, eid), gt in gt_map.items():
            if (itype, eid) not in det_map:
                self.errors.append(f"False Negative (missed anomaly): {itype} on {eid}")

        # Overall Metrics with explicit zero-denominator handling
        overall_prec = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
        overall_rec = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
        overall_f1 = (2 * overall_prec * overall_rec / (overall_prec + overall_rec)) if (overall_prec + overall_rec) > 0 else 0.0

        all_categories_passed = all(
            cat_res["f1_score"] == 1.0 and cat_res["false_positives"] == 0 and cat_res["false_negatives"] == 0
            for cat_res in by_category.values()
        )
        passed = (
            total_tp == len(ground_truth) and
            total_fp == 0 and
            total_fn == 0 and
            all_categories_passed
        )

        return {
            "status": "COMPLETED",
            "execution_mode": execution_mode,
            "passed": passed,
            "ground_truth_count": len(ground_truth),
            "detected_count": len(detected),
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "true_negatives": total_tn,
            "precision": round(overall_prec, 4),
            "recall": round(overall_rec, 4),
            "f1_score": round(overall_f1, 4),
            "by_category": by_category,
            "matched_anomalies": matched_details,
        }

    def _print_summary(self, report: Dict[str, Any]):
        print("\n" + "=" * 80)
        print("                   SYNTHETIC DATA VALIDATION REPORT")
        print("=" * 80)
        status_str = "PASSED (100% COMPLIANT)" if report["validation_passed"] else "FAILED"
        print(f"Overall Status          : {status_str}")
        print(f"Referential Integrity   : {'PASSED' if report['referential_integrity']['passed'] else 'FAILED'}")
        print(f"Enum & Date Ordering    : {'PASSED' if report['enums_and_dates']['passed'] else 'FAILED'}")
        print(f"Financial Arithmetic    : {'PASSED' if report['financial_arithmetic']['passed'] else 'FAILED'}")
        
        art = report.get("export_artifacts", {})
        print(f"Export Artifacts        : CSVs: {'OK' if art.get('all_csvs_present') else 'MISSING'}, JSONs: {'OK' if art.get('all_jsons_present') else 'MISSING'}, SQL: {'OK' if art.get('sql_seed_present') else 'MISSING'}")

        anm = report["anomaly_evaluation"]
        print(f"Anomaly Detection       : {'PASSED' if anm['passed'] else 'FAILED'} (Mode: {anm.get('execution_mode')})")
        print(f"  - Ground Truth Count  : {anm.get('ground_truth_count')}")
        print(f"  - Detected Anomalies  : {anm.get('detected_count')}")
        print(f"  - Overall Precision   : {anm.get('precision', 0.0) * 100:.1f}%")
        print(f"  - Overall Recall      : {anm.get('recall', 0.0) * 100:.1f}%")
        print(f"  - Overall F1 Score    : {anm.get('f1_score', 0.0) * 100:.1f}%")
        print(f"  - Confusion Matrix    : TP={anm.get('true_positives')} | FP={anm.get('false_positives')} | FN={anm.get('false_negatives')} | TN={anm.get('true_negatives')}")
        
        if anm.get("by_category"):
            print("\n  Per-Category Anomaly Detection Metrics:")
            print("  " + "-" * 76)
            print(f"  {'Category':<28} | {'TP':<3} | {'FP':<3} | {'FN':<3} | {'TN':<5} | {'Prec':<6} | {'Rec':<6} | {'F1':<6}")
            print("  " + "-" * 76)
            for cat, m in anm["by_category"].items():
                print(f"  {cat:<28} | {m['true_positives']:<3} | {m['false_positives']:<3} | {m['false_negatives']:<3} | {m['true_negatives']:<5} | {m['precision']*100:>5.1f}% | {m['recall']*100:>5.1f}% | {m['f1_score']*100:>5.1f}%")
            print("  " + "-" * 76)

        if report["errors"]:
            print(f"\nErrors ({len(report['errors'])}):")
            for e in report["errors"][:5]:
                print(f"  [!] {e}")
        print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Validate Synthetic Data and Anomaly Detection Engine")
    parser.add_argument("--data-dir", default="data/export", help="Directory containing generated CSV and JSON files")
    parser.add_argument("--check-db", action="store_true", help="Validate against active MySQL database tables")
    parser.add_argument("--report-path", default=None, help="Output path for validation report JSON")
    args = parser.parse_args()

    validator = DataValidator(data_dir=args.data_dir, check_db=args.check_db, report_path=args.report_path)
    db = SessionLocal() if args.check_db else None
    try:
        report = validator.validate(db=db)
        if not report["validation_passed"]:
            sys.exit(1)
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    main()
