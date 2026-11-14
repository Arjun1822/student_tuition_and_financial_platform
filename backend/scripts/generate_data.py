"""Deterministic Synthetic Data Generator for Student Financial Platform.
Fixed Random Seed: 20261022
Supports:
  - Scales: 'starter' (fast local validation) and 'full' (10,000 students, 30,000 invoices, etc.)
  - Deterministic Business IDs conforming to nomenclature
  - Generation in Foreign-Key Dependency Order
  - Injected Anomaly Scenarios (1-5) strictly labelled in separate ground truth
  - Exports: CSV, JSON, SQL seed files, ground_truth.csv, ground_truth.json
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.role import Role, RoleEnum
from app.models.user import User
from app.models.program import Program, DegreeLevel, ProgramStatus
from app.models.term import Term, SemesterEnum
from app.models.fee_schedule import FeeSchedule
from app.models.student import Student, StudentStatus, IncomeCategory
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine, FeeType
from app.models.scholarship import Scholarship, ScholarshipType, ScholarshipStatus
from app.models.eligibility import Eligibility, EligibilityStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.payment_allocation import PaymentAllocation
from app.models.refund import Refund, RefundStatus
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.models.anomaly import Anomaly, AnomalyIssueType, AnomalySeverity, AnomalyResolutionStatus
from app.models.reconciliation import ReconciliationRun, ReconciliationResult
from app.services.id_generator import IDGenerator


FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Dhruv", "Kabir", "Rohan", "Ananya", "Diya", "Gauri", "Isha", "Kavya", "Khushi",
    "Meera", "Myra", "Navya", "Pari", "Prisha", "Riya", "Saanvi", "Sara", "Siya", "Tanvi"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Mehta", "Joshi", "Kumar", "Singh", "Nair", "Iyer",
    "Rao", "Reddy", "Choudhury", "Bose", "Mukherjee", "Chatterjee", "Banerjee", "Das", "Dutta", "Sengupta"
]

CITIES_STATES = [
    ("Bengaluru", "Karnataka", "560001"),
    ("Mumbai", "Maharashtra", "400001"),
    ("Delhi", "Delhi", "110001"),
    ("Hyderabad", "Telangana", "500001"),
    ("Chennai", "Tamil Nadu", "600001"),
    ("Kolkata", "West Bengal", "700001"),
    ("Pune", "Maharashtra", "411001"),
    ("Ahmedabad", "Gujarat", "380001"),
]

PROGRAMS_SPECS = [
    ("Computer Science and Engineering", "CS-BTECH", "School of Computing", DegreeLevel.BACHELOR, 4, 160, Decimal("60000.00")),
    ("Artificial Intelligence and Data Science", "AI-BTECH", "School of Computing", DegreeLevel.BACHELOR, 4, 160, Decimal("65000.00")),
    ("Information Technology", "IT-BTECH", "School of Computing", DegreeLevel.BACHELOR, 4, 160, Decimal("55000.00")),
    ("Software Engineering", "SE-MTECH", "School of Computing", DegreeLevel.MASTER, 2, 80, Decimal("70000.00")),
    ("Cybersecurity and Forensics", "CY-MTECH", "School of Computing", DegreeLevel.MASTER, 2, 80, Decimal("70000.00")),
    ("Data Science and Analytics", "DS-MS", "School of Computing", DegreeLevel.MASTER, 2, 75, Decimal("68000.00")),
    ("Computer Science Research", "CS-PHD", "School of Computing", DegreeLevel.DOCTORATE, 4, 60, Decimal("40000.00")),
    ("Electronics and Communication", "EC-BTECH", "School of Electrical", DegreeLevel.BACHELOR, 4, 160, Decimal("55000.00")),
    ("Electrical and Electronics", "EE-BTECH", "School of Electrical", DegreeLevel.BACHELOR, 4, 160, Decimal("50000.00")),
    ("VLSI Design and Embedded Systems", "VLSI-MTECH", "School of Electrical", DegreeLevel.MASTER, 2, 80, Decimal("65000.00")),
    ("Mechanical Engineering", "ME-BTECH", "School of Mechanical", DegreeLevel.BACHELOR, 4, 160, Decimal("48000.00")),
    ("Robotics and Mechatronics", "ROB-MTECH", "School of Mechanical", DegreeLevel.MASTER, 2, 80, Decimal("62000.00")),
    ("Civil and Environmental Engineering", "CE-BTECH", "School of Civil", DegreeLevel.BACHELOR, 4, 160, Decimal("45000.00")),
    ("Structural Engineering", "SE-CIVIL-MS", "School of Civil", DegreeLevel.MASTER, 2, 75, Decimal("55000.00")),
    ("Biotechnology", "BT-BTECH", "School of BioSciences", DegreeLevel.BACHELOR, 4, 160, Decimal("52000.00")),
    ("Bioinformatics", "BI-MS", "School of BioSciences", DegreeLevel.MASTER, 2, 75, Decimal("58000.00")),
    ("Business Administration", "BBA-BACH", "School of Management", DegreeLevel.BACHELOR, 3, 120, Decimal("45000.00")),
    ("Finance and Accounting", "MBA-FIN", "School of Management", DegreeLevel.MASTER, 2, 90, Decimal("75000.00")),
    ("Business Analytics", "MBA-BA", "School of Management", DegreeLevel.MASTER, 2, 90, Decimal("80000.00")),
    ("Diploma in Cloud Computing", "DIP-CC", "School of Continuing Education", DegreeLevel.DIPLOMA, 1, 40, Decimal("30000.00")),
]

TERMS_SPECS = [
    ("Fall Semester 2025", 2025, SemesterEnum.FALL, date(2025, 8, 18), date(2025, 12, 19), "2025-FALL"),
    ("Spring Semester 2026", 2026, SemesterEnum.SPRING, date(2026, 1, 12), date(2026, 5, 20), "2026-SPRING"),
    ("Summer Term 2026", 2026, SemesterEnum.SUMMER, date(2026, 6, 1), date(2026, 7, 31), "2026-SUMMER"),
    ("Fall Semester 2026", 2026, SemesterEnum.FALL, date(2026, 8, 17), date(2026, 12, 18), "2026-FALL"),
]


class SyntheticDataGenerator:
    def __init__(self, seed: int = 20261022, scale: str = "starter", export_dir: str = "data/export"):
        self.seed = seed
        self.rng = random.Random(seed)
        self.scale = scale
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)

        if scale == "starter":
            self.target_students = 100
            self.target_invoices = 300
            self.target_scholarships = 150
            self.target_payments = 500
        else:  # full
            self.target_students = 10000
            self.target_invoices = 30000
            self.target_scholarships = 15000
            self.target_payments = 50000

        # Ground truth tracking (isolated completely from detection input)
        self.ground_truth: List[Dict[str, Any]] = []

    def generate(self, db: Optional[Session] = None) -> Dict[str, Any]:
        start_time = time.time()
        print(f"=== Synthetic Data Generator (Scale: {self.scale}, Seed: {self.seed}) ===")

        # 1. Programs (20)
        programs = self._generate_programs()
        # 2. Terms (4)
        terms = self._generate_terms()
        # 3. Fee Schedules (20 * 4 = 80)
        fee_schedules = self._generate_fee_schedules(programs, terms)
        # 4. Students
        students = self._generate_students()
        # 5. Enrollments
        enrollments = self._generate_enrollments(students, programs, terms)
        # 6. Scholarships & Budgets
        scholarships = self._generate_scholarships()
        # 7. Invoices & Lines
        invoices, invoice_lines = self._generate_invoices(enrollments, fee_schedules)
        # 8. Eligibilities
        eligibilities = self._generate_eligibilities(students, enrollments, scholarships, invoices)
        # 9. Payments & Allocations
        payments, allocations = self._generate_payments(students, invoices, invoice_lines)
        # 10. Refunds
        refunds = self._generate_refunds(payments)
        # 11. Financial Events
        events = self._generate_financial_events(invoices, payments, refunds)

        # 12. Controlled Injected Anomalies (The 5 Mandatory Scenarios)
        self._inject_anomalies(payments, allocations, eligibilities, enrollments, invoices, invoice_lines, refunds)

        manifest = {
            "scale": self.scale,
            "seed": self.seed,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.time() - start_time, 2),
            "counts": {
                "programs": len(programs),
                "terms": len(terms),
                "fee_schedules": len(fee_schedules),
                "students": len(students),
                "enrollments": len(enrollments),
                "scholarships": len(scholarships),
                "invoices": len(invoices),
                "invoice_lines": len(invoice_lines),
                "eligibilities": len(eligibilities),
                "payments": len(payments),
                "payment_allocations": len(allocations),
                "refunds": len(refunds),
                "financial_events": len(events),
                "injected_anomalies": len(self.ground_truth),
            },
        }

        # Persist to database if provided
        if db:
            self._persist_to_db(
                db,
                programs, terms, fee_schedules, students, enrollments,
                scholarships, invoices, invoice_lines, eligibilities,
                payments, allocations, refunds, events
            )

        # Export to files
        self._export_files(
            programs, terms, fee_schedules, students, enrollments,
            scholarships, invoices, invoice_lines, eligibilities,
            payments, allocations, refunds, events, manifest
        )

        print(f"Generated dataset in {manifest['duration_seconds']}s.")
        print(f"Counts: {manifest['counts']}")
        return manifest

    def _generate_programs(self) -> List[Dict[str, Any]]:
        programs = []
        for i, (name, code, dept, degree, dur, credits_count, tuition) in enumerate(PROGRAMS_SPECS):
            p_id = IDGenerator.program_id(i + 1)
            programs.append({
                "id": i + 1,
                "program_id": p_id,
                "name": name,
                "code": code,
                "department": dept,
                "degree_level": degree,
                "duration_years": dur,
                "total_credits": credits_count,
                "status": ProgramStatus.ACTIVE,
                "description": f"Standard curriculum for {name}.",
                "tuition_base": tuition,
            })
        return programs

    def _generate_terms(self) -> List[Dict[str, Any]]:
        terms = []
        for i, (name, year, sem, start, end, cycle) in enumerate(TERMS_SPECS):
            terms.append({
                "id": i + 1,
                "term_id": f"TERM-{year}-{sem.value}",
                "name": name,
                "year": year,
                "semester": sem,
                "start_date": start,
                "end_date": end,
                "is_active": True,
                "billing_cycle": cycle,
            })
        return terms

    def _generate_fee_schedules(self, programs: List[Dict[str, Any]], terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        schedules = []
        seq = 0
        for p in programs:
            for t in terms:
                seq += 1
                tuition = p["tuition_base"]
                reg = Decimal("2000.00")
                lab = Decimal("5000.00") if p["degree_level"] in [DegreeLevel.BACHELOR, DegreeLevel.MASTER] else Decimal("2000.00")
                exam = Decimal("1500.00")
                lib = Decimal("1000.00")
                other = Decimal("500.00")
                total = tuition + reg + lab + exam + lib + other

                schedules.append({
                    "id": seq,
                    "fee_schedule_id": IDGenerator.fee_schedule_id(seq),
                    "program_id": p["id"],
                    "term_id": t["id"],
                    "tuition_fee": tuition,
                    "registration_fee": reg,
                    "laboratory_fee": lab,
                    "examination_fee": exam,
                    "library_fee": lib,
                    "other_charges": other,
                    "currency": "INR",
                    "effective_start_date": t["start_date"],
                    "effective_end_date": t["end_date"],
                    "is_active": True,
                    "total_fee": total,
                })
        return schedules

    def _generate_students(self) -> List[Dict[str, Any]]:
        students = []
        income_cats = [IncomeCategory.LOW, IncomeCategory.MEDIUM, IncomeCategory.HIGH, IncomeCategory.VERY_HIGH]
        income_weights = [0.25, 0.50, 0.20, 0.05]

        for i in range(1, self.target_students + 1):
            fn = self.rng.choice(FIRST_NAMES)
            ln = self.rng.choice(LAST_NAMES)
            city, state, postal = self.rng.choice(CITIES_STATES)
            gpa = Decimal(str(round(self.rng.triangular(6.0, 9.8, 8.2), 2)))
            inc_cat = self.rng.choices(income_cats, weights=income_weights)[0]
            email = f"{fn.lower()}.{ln.lower()}{i}@university.edu"

            students.append({
                "id": i,
                "student_id": IDGenerator.student_id(i),
                "first_name": fn,
                "last_name": ln,
                "email": email,
                "phone": f"+91{self.rng.randint(7000000000, 9999999999)}",
                "date_of_birth": date(2003 + (i % 4), (i % 12) + 1, (i % 27) + 1),
                "address": f"{self.rng.randint(1, 999)}, MG Road",
                "city": city,
                "state": state,
                "country": "India",
                "postal_code": postal,
                "family_income_category": inc_cat.value,
                "gpa": gpa,
                "status": StudentStatus.ACTIVE,
            })
        return students

    def _generate_enrollments(self, students: List[Dict[str, Any]], programs: List[Dict[str, Any]], terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enrollments = []
        seq = 0
        terms_to_enroll = terms[:3]  # Enroll students across first 3 terms

        for s in students:
            # Assign primary program based on student index
            prog = programs[(s["id"] - 1) % len(programs)]
            for t in terms_to_enroll:
                seq += 1
                enrollments.append({
                    "id": seq,
                    "enrollment_id": IDGenerator.enrollment_id(seq),
                    "student_id": s["id"],
                    "program_id": prog["id"],
                    "term_id": t["id"],
                    "enrollment_date": t["start_date"],
                    "status": EnrollmentStatus.ACTIVE,
                    "billing_cycle": t["billing_cycle"],
                })
        return enrollments

    def _generate_scholarships(self) -> List[Dict[str, Any]]:
        budget_mult = Decimal("100.0") if self.scale == "full" else Decimal("1.0")
        specs = [
            ("Merit Academic Excellence Award", ScholarshipType.MERIT, Decimal("50.00"), Decimal("50000.00"), Decimal("8.50"), Decimal("10000000.00") * budget_mult),
            ("Need-Based Tuition Assistance", ScholarshipType.NEED_BASED, Decimal("40.00"), Decimal("35000.00"), Decimal("6.50"), Decimal("8000000.00") * budget_mult),
            ("Women in STEM Leadership Grant", ScholarshipType.SPECIAL, Decimal("60.00"), Decimal("60000.00"), Decimal("7.50"), Decimal("5000000.00") * budget_mult),
            ("Computer Science Department Honors", ScholarshipType.PROGRAM_SPECIFIC, Decimal("30.00"), Decimal("25000.00"), Decimal("8.00"), Decimal("4000000.00") * budget_mult),
            ("Athletic Champions Scholarship", ScholarshipType.ATHLETIC, Decimal("50.00"), Decimal("40000.00"), Decimal("6.00"), Decimal("3000000.00") * budget_mult),
        ]
        scholarships = []
        for i, (name, stype, pct, max_amt, min_gpa, budget) in enumerate(specs):
            sch_id = IDGenerator.scholarship_id(2026, i + 1)
            scholarships.append({
                "id": i + 1,
                "scholarship_id": sch_id,
                "name": name,
                "description": f"Institutional funding program: {name}",
                "scholarship_type": stype,
                "percentage": pct,
                "max_amount": max_amt,
                "min_gpa": min_gpa,
                "max_family_income_category": "LOW" if stype == ScholarshipType.NEED_BASED else None,
                "total_budget": budget,
                "awarded_amount": Decimal("0.00"),
                "status": ScholarshipStatus.ACTIVE,
                "academic_year": "2026-2027",
            })
        return scholarships

    def _generate_invoices(self, enrollments: List[Dict[str, Any]], fee_schedules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        invoices = []
        invoice_lines = []
        line_seq = 0

        fee_lookup = {(fs["program_id"], fs["term_id"]): fs for fs in fee_schedules}

        for i, enr in enumerate(enrollments):
            fs = fee_lookup.get((enr["program_id"], enr["term_id"]))
            if not fs:
                continue

            inv_id = IDGenerator.invoice_id(f"STU-{enr['student_id']:06d}", 2026, i + 1)
            gross = fs["total_fee"]

            invoice = {
                "id": i + 1,
                "invoice_id": inv_id,
                "enrollment_id": enr["id"],
                "student_id": enr["student_id"],
                "term_id": enr["term_id"],
                "invoice_date": enr["enrollment_date"],
                "due_date": enr["enrollment_date"] + timedelta(days=30),
                "gross_amount": gross,
                "scholarship_discount": Decimal("0.00"),
                "net_amount": gross,
                "amount_paid": Decimal("0.00"),
                "outstanding_balance": gross,
                "currency": "INR",
                "status": InvoiceStatus.ISSUED,
                "billing_cycle": enr["billing_cycle"],
                "notes": "Tuition and standard institutional charges.",
            }
            invoices.append(invoice)

            # Lines: Tuition, Registration, Lab, Exam, Library, Other
            charges = [
                (FeeType.TUITION, "Tuition Fee", fs["tuition_fee"]),
                (FeeType.REGISTRATION, "Registration Fee", fs["registration_fee"]),
                (FeeType.LABORATORY, "Laboratory Fee", fs["laboratory_fee"]),
                (FeeType.EXAMINATION, "Examination Fee", fs["examination_fee"]),
                (FeeType.LIBRARY, "Library Fee", fs["library_fee"]),
                (FeeType.OTHER, "Campus Amenities", fs["other_charges"]),
            ]
            for fee_type, desc, amt in charges:
                line_seq += 1
                invoice_lines.append({
                    "id": line_seq,
                    "invoice_line_id": IDGenerator.invoice_line_id(line_seq),
                    "invoice_id": invoice["id"],
                    "fee_type": fee_type,
                    "description": desc,
                    "amount": amt,
                    "allocated_amount": Decimal("0.00"),
                })

        return invoices, invoice_lines

    def _generate_eligibilities(
        self,
        students: List[Dict[str, Any]],
        enrollments: List[Dict[str, Any]],
        scholarships: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        eligibilities = []
        seq = 0
        stu_lookup = {s["id"]: s for s in students}
        inv_lookup = {inv["enrollment_id"]: inv for inv in invoices}

        # Award scholarships to ~50% of enrollments
        for enr in enrollments:
            if seq >= self.target_scholarships:
                break

            student = stu_lookup.get(enr["student_id"])
            invoice = inv_lookup.get(enr["id"])
            if not student or not invoice:
                continue

            # Pick matching scholarship
            for sch in scholarships:
                if student["gpa"] >= (sch["min_gpa"] or Decimal("0.00")):
                    eligible_fee = invoice["gross_amount"]
                    pct = sch["percentage"] / Decimal("100.00")
                    calc_amt = min(eligible_fee * pct, sch["max_amount"]).quantize(Decimal("0.01"))
                    if sch["awarded_amount"] + calc_amt > sch["total_budget"]:
                        continue

                    seq += 1
                    appr_amt = calc_amt

                    # Apply to invoice
                    invoice["scholarship_discount"] = appr_amt
                    invoice["net_amount"] = max(Decimal("0.00"), invoice["gross_amount"] - appr_amt)
                    invoice["outstanding_balance"] = invoice["net_amount"]
                    sch["awarded_amount"] += appr_amt

                    eligibilities.append({
                        "id": seq,
                        "eligibility_id": IDGenerator.eligibility_id(seq),
                        "student_id": student["id"],
                        "scholarship_id": sch["id"],
                        "enrollment_id": enr["id"],
                        "evaluation_date": enr["enrollment_date"],
                        "eligible_fee_amount": eligible_fee,
                        "scholarship_percentage": sch["percentage"],
                        "calculated_amount": calc_amt,
                        "approved_amount": appr_amt,
                        "status": EligibilityStatus.APPROVED,
                        "decision_reason": f"Met GPA threshold {sch['min_gpa']}.",
                        "criteria_version": "1.0",
                    })
                    break

        return eligibilities

    def _generate_payments(
        self,
        students: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        invoice_lines: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        payments = []
        allocations = []
        pay_seq = 0
        alloc_seq = 0

        lines_by_inv = {}
        for l in invoice_lines:
            lines_by_inv.setdefault(l["invoice_id"], []).append(l)

        methods = [PaymentMethod.UPI, PaymentMethod.BANK_TRANSFER, PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]

        for inv in invoices:
            if pay_seq >= self.target_payments:
                break

            remaining_inv_balance = inv["outstanding_balance"]
            if remaining_inv_balance <= Decimal("0.00"):
                continue

            # Generate 1 or 2 payments per invoice
            pay_amt = remaining_inv_balance if (pay_seq % 2 == 0) else (remaining_inv_balance / Decimal("2.00")).quantize(Decimal("0.01"))
            pay_seq += 1
            p_id = IDGenerator.payment_id(2026, pay_seq)

            payment = {
                "id": pay_seq,
                "payment_id": p_id,
                "student_id": inv["student_id"],
                "amount": pay_amt,
                "allocated_amount": Decimal("0.00"),
                "unallocated_amount": pay_amt,
                "payment_date": inv["invoice_date"] + timedelta(days=10),
                "payment_method": self.rng.choice(methods),
                "reference_number": f"REF-TXN-{pay_seq:07d}",
                "currency": "INR",
                "status": PaymentStatus.COMPLETED,
                "notes": "Tuition settlement.",
            }
            payments.append(payment)

            # Allocate funds across invoice lines
            inv_lines = lines_by_inv.get(inv["id"], [])
            avail = pay_amt
            for l in inv_lines:
                if avail <= Decimal("0.00"):
                    break
                rem_line = l["amount"] - l["allocated_amount"]
                if rem_line <= Decimal("0.00"):
                    continue

                alloc_amt = min(avail, rem_line)
                alloc_seq += 1
                allocations.append({
                    "id": alloc_seq,
                    "allocation_id": IDGenerator.allocation_id(payment["payment_id"], alloc_seq % 100 + 1),
                    "payment_id": payment["id"],
                    "invoice_line_id": l["id"],
                    "amount": alloc_amt,
                    "allocated_date": payment["payment_date"],
                })

                l["allocated_amount"] += alloc_amt
                payment["allocated_amount"] += alloc_amt
                avail -= alloc_amt

            payment["unallocated_amount"] = payment["amount"] - payment["allocated_amount"]
            inv["amount_paid"] += payment["allocated_amount"]
            inv["outstanding_balance"] = max(Decimal("0.00"), inv["net_amount"] - inv["amount_paid"])
            if inv["outstanding_balance"] == Decimal("0.00"):
                inv["status"] = InvoiceStatus.PAID
            elif inv["amount_paid"] > Decimal("0.00"):
                inv["status"] = InvoiceStatus.PARTIALLY_PAID

        return payments, allocations

    def _generate_refunds(self, payments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        refunds = []
        ref_seq = 0
        # Create a small number of legitimate refunds (e.g. 5% of payments with unallocated balances)
        for p in payments:
            if p["unallocated_amount"] >= Decimal("1000.00") and (p["id"] % 20 == 0):
                ref_seq += 1
                amt = Decimal("1000.00")
                p["unallocated_amount"] -= amt
                refunds.append({
                    "id": ref_seq,
                    "refund_id": IDGenerator.refund_id(2026, ref_seq),
                    "payment_id": p["id"],
                    "student_id": p["student_id"],
                    "invoice_id": None,
                    "amount": amt,
                    "currency": "INR",
                    "reason": "Overpayment excess refund requested by student.",
                    "status": RefundStatus.PROCESSED,
                    "requested_date": p["payment_date"] + timedelta(days=5),
                    "reference_number": f"REF-PROCESSED-{ref_seq:06d}",
                })
        return refunds

    def _generate_financial_events(
        self,
        invoices: List[Dict[str, Any]],
        payments: List[Dict[str, Any]],
        refunds: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        events = []
        evt_seq = 0
        for inv in invoices[:500]:
            evt_seq += 1
            events.append({
                "id": evt_seq,
                "event_id": IDGenerator.event_id(evt_seq),
                "entity_type": "INVOICE",
                "entity_id": inv["invoice_id"],
                "event_type": FinancialEventType.INVOICE_ISSUED,
                "amount": inv["gross_amount"],
                "currency": "INR",
                "event_timestamp": datetime.combine(inv["invoice_date"], datetime.min.time(), tzinfo=timezone.utc),
            })
        for p in payments[:500]:
            evt_seq += 1
            events.append({
                "id": evt_seq,
                "event_id": IDGenerator.event_id(evt_seq),
                "entity_type": "PAYMENT",
                "entity_id": p["payment_id"],
                "event_type": FinancialEventType.PAYMENT_RECEIVED,
                "amount": p["amount"],
                "currency": "INR",
                "event_timestamp": datetime.combine(p["payment_date"], datetime.min.time(), tzinfo=timezone.utc),
            })
        return events

    def _inject_anomalies(
        self,
        payments: List[Dict[str, Any]],
        allocations: List[Dict[str, Any]],
        eligibilities: List[Dict[str, Any]],
        enrollments: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        invoice_lines: List[Dict[str, Any]],
        refunds: List[Dict[str, Any]]
    ):
        """
        Injects controlled, labelled instances of the 5 mandatory anomaly scenarios:
        1. PAYMENT_OVER_ALLOCATED
        2. SCHOLARSHIP_EXCEEDS_FEES
        3. DUPLICATE_INVOICE
        4. REFUND_EXCEEDS_PAID
        5. BALANCE_MISMATCH
        Strictly records expected ground truth into separate evaluation dataset.
        """
        # 1. PAYMENT_OVER_ALLOCATED
        if payments:
            target_p = payments[0]
            extra_alloc = Decimal("5000.00")
            target_p["allocated_amount"] += extra_alloc  # causes allocated > amount!
            existing_lines = {a["invoice_line_id"] for a in allocations if a["payment_id"] == target_p["id"]}
            target_line_id = next((l["id"] for l in invoice_lines if l["id"] not in existing_lines), 2)
            alloc_seq = len(allocations) + 1
            allocations.append({
                "id": alloc_seq,
                "allocation_id": IDGenerator.allocation_id(target_p["payment_id"], 99),
                "payment_id": target_p["id"],
                "invoice_line_id": target_line_id,
                "amount": extra_alloc,
                "allocated_date": target_p["payment_date"],
            })
            self.ground_truth.append({
                "anomaly_id": "GT-ANM-000001",
                "issue_type": AnomalyIssueType.PAYMENT_OVER_ALLOCATED.value,
                "entity_type": "PAYMENT",
                "entity_id": target_p["payment_id"],
                "expected_value": float(target_p["amount"]),
                "actual_value": float(target_p["allocated_amount"]),
                "explanation": f"Payment {target_p['payment_id']} allocations exceed available amount.",
            })

        # 2. SCHOLARSHIP_EXCEEDS_FEES
        if eligibilities:
            target_e = eligibilities[0]
            excess_award = target_e["eligible_fee_amount"] + Decimal("15000.00")
            target_e["approved_amount"] = excess_award
            self.ground_truth.append({
                "anomaly_id": "GT-ANM-000002",
                "issue_type": AnomalyIssueType.SCHOLARSHIP_EXCEEDS_FEES.value,
                "entity_type": "SCHOLARSHIP_ELIGIBILITY",
                "entity_id": target_e["eligibility_id"],
                "expected_value": float(target_e["eligible_fee_amount"]),
                "actual_value": float(excess_award),
                "explanation": f"Approved scholarship {target_e['eligibility_id']} exceeds eligible tuition fee.",
            })

        # 3. DUPLICATE_INVOICE
        if len(invoices) >= 2:
            base_inv = invoices[1]
            dup_id = f"{base_inv['invoice_id']}-DUP"
            dup_inv = dict(base_inv)
            dup_inv["id"] = len(invoices) + 1
            dup_inv["invoice_id"] = dup_id
            invoices.append(dup_inv)
            self.ground_truth.append({
                "anomaly_id": "GT-ANM-000003",
                "issue_type": AnomalyIssueType.DUPLICATE_INVOICE.value,
                "entity_type": "INVOICE",
                "entity_id": dup_id,
                "expected_value": 1.0,
                "actual_value": 2.0,
                "explanation": f"Duplicate invoice {dup_id} generated for same enrollment cycle.",
            })

        # 4. REFUND_EXCEEDS_PAID
        if len(payments) >= 2:
            target_p2 = payments[1]
            excess_refund = target_p2["amount"] + Decimal("2000.00")
            ref_id = IDGenerator.refund_id(2026, 9999)
            refunds.append({
                "id": len(refunds) + 1,
                "refund_id": ref_id,
                "payment_id": target_p2["id"],
                "student_id": target_p2["student_id"],
                "invoice_id": None,
                "amount": excess_refund,
                "currency": "INR",
                "reason": "Controlled test refund exceeding payment.",
                "status": RefundStatus.PROCESSED,
                "requested_date": datetime.combine(target_p2["payment_date"] + timedelta(days=5), datetime.min.time(), tzinfo=timezone.utc),
            })
            self.ground_truth.append({
                "anomaly_id": "GT-ANM-000004",
                "issue_type": AnomalyIssueType.REFUND_EXCEEDS_PAID.value,
                "entity_type": "PAYMENT",
                "entity_id": target_p2["payment_id"],
                "expected_value": float(target_p2["amount"]),
                "actual_value": float(excess_refund),
                "explanation": f"Refund sum {excess_refund} exceeds payment amount {target_p2['amount']}.",
            })

        # 5. BALANCE_MISMATCH
        if len(invoices) >= 3:
            target_inv = invoices[2]
            stored_wrong_bal = target_inv["outstanding_balance"] + Decimal("4500.00")
            target_inv["outstanding_balance"] = stored_wrong_bal
            self.ground_truth.append({
                "anomaly_id": "GT-ANM-000005",
                "issue_type": AnomalyIssueType.BALANCE_MISMATCH.value,
                "entity_type": "INVOICE",
                "entity_id": target_inv["invoice_id"],
                "expected_value": float(target_inv["net_amount"] - target_inv["amount_paid"]),
                "actual_value": float(stored_wrong_bal),
                "explanation": f"Invoice {target_inv['invoice_id']} stored balance disagrees with arithmetic.",
            })

    def _persist_to_db(self, db: Session, programs, terms, fee_schedules, students, enrollments, scholarships, invoices, invoice_lines, eligibilities, payments, allocations, refunds, events):
        print("-> Inserting generated entities into database...")
        # Clear operational tables to ensure idempotency
        db.query(ReconciliationResult).delete()
        db.query(ReconciliationRun).delete()
        db.query(Anomaly).delete()
        db.query(FinancialEvent).delete()
        db.query(Refund).delete()
        db.query(PaymentAllocation).delete()
        db.query(Payment).delete()
        db.query(Eligibility).delete()
        db.query(Scholarship).delete()
        db.query(InvoiceLine).delete()
        db.query(Invoice).delete()
        db.query(Enrollment).delete()
        db.query(Student).delete()
        db.query(FeeSchedule).delete()
        db.query(Term).delete()
        db.query(Program).delete()
        db.commit()

        # Batch insert helper
        def bulk_add(model_cls, dict_list, batch_size=1000):
            col_names = set(model_cls.__table__.columns.keys())
            for i in range(0, len(dict_list), batch_size):
                chunk = dict_list[i:i + batch_size]
                clean_chunk = [{k: v for k, v in d.items() if k in col_names} for d in chunk]
                db.bulk_insert_mappings(model_cls, clean_chunk)
                db.commit()

        bulk_add(Program, programs)
        bulk_add(Term, terms)
        bulk_add(FeeSchedule, fee_schedules)
        bulk_add(Student, students)
        bulk_add(Enrollment, enrollments)
        bulk_add(Scholarship, scholarships)
        bulk_add(Invoice, invoices)
        bulk_add(InvoiceLine, invoice_lines)
        bulk_add(Eligibility, eligibilities)
        bulk_add(Payment, payments)
        bulk_add(PaymentAllocation, allocations)
        bulk_add(Refund, refunds)
        bulk_add(FinancialEvent, events)
        print("-> Database population complete.")

    def _export_files(self, programs, terms, fee_schedules, students, enrollments, scholarships, invoices, invoice_lines, eligibilities, payments, allocations, refunds, events, manifest):
        print(f"-> Exporting files to {self.export_dir}...")

        # Helper to dump CSV
        def write_csv(filename, dict_list):
            if not dict_list:
                return
            keys = list(dict_list[0].keys())
            with open(os.path.join(self.export_dir, filename), "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for row in dict_list:
                    # Convert dates and Decimals to string
                    clean_row = {}
                    for k, v in row.items():
                        if isinstance(v, (Decimal, date, datetime)):
                            clean_row[k] = str(v)
                        elif isinstance(v, (list, dict)):
                            clean_row[k] = json.dumps(v)
                        else:
                            clean_row[k] = v
                    writer.writerow(clean_row)

        write_csv("students.csv", students)
        write_csv("programs.csv", programs)
        write_csv("terms.csv", terms)
        write_csv("fee_schedules.csv", fee_schedules)
        write_csv("enrollments.csv", enrollments)
        write_csv("scholarships.csv", scholarships)
        write_csv("invoices.csv", invoices)
        write_csv("invoice_lines.csv", invoice_lines)
        write_csv("eligibilities.csv", eligibilities)
        write_csv("payments.csv", payments)
        write_csv("payment_allocations.csv", allocations)
        write_csv("refunds.csv", refunds)
        write_csv("financial_events.csv", events)
        write_csv("ground_truth.csv", self.ground_truth)

        # JSON exports
        with open(os.path.join(self.export_dir, "ground_truth.json"), "w", encoding="utf-8") as f:
            json.dump(self.ground_truth, f, indent=2)

        with open(os.path.join(self.export_dir, "generation_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print("-> Export files written successfully.")


def main():
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Data Generator")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale")
    parser.add_argument("--seed", type=int, default=20261022, help="Fixed random seed")
    parser.add_argument("--export-dir", default="data/export", help="Output export directory")
    parser.add_argument("--persist-db", action="store_true", help="Insert records into active database")
    args = parser.parse_args()

    generator = SyntheticDataGenerator(seed=args.seed, scale=args.scale, export_dir=args.export_dir)
    db = SessionLocal() if args.persist_db else None
    try:
        generator.generate(db=db)
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    main()
