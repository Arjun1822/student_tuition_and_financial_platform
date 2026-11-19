import pytest
from datetime import date, timedelta
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.models.student import Student, StudentStatus
from app.models.program import Program, DegreeLevel, ProgramStatus
from app.models.term import Term, SemesterEnum
from app.models.fee_schedule import FeeSchedule
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine, FeeType
from app.models.payment_allocation import PaymentAllocation
from app.services.anomaly_service import AnomalyDetectionService
from app.models.scholarship import Scholarship, ScholarshipType, ScholarshipStatus
from app.models.eligibility import Eligibility, EligibilityStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.refund import Refund, RefundStatus
from app.models.reconciliation import ReconciliationRun, ReconciliationStatus
from app.models.anomaly import AnomalyIssueType

TEST_DB_URI = settings.get_test_database_uri()
test_engine = create_engine(TEST_DB_URI, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()
    try:
        # 1. Admin user with ID 1
        admin_user = User(
            id=1,
            username="admin_user",
            email="admin@test.edu",
            password_hash=get_password_hash("Admin@2026Test"),
            full_name="Platform Administrator",
            role=RoleEnum.PLATFORM_ADMIN,
            is_active=True
        )
        db.add(admin_user)

        # 2. Program 1
        prog = Program(
            id=1,
            program_id="PRG-000001",
            name="Computer Science and Engineering",
            code="PRG-000001",
            department="Computer Science",
            degree_level=DegreeLevel.BACHELOR,
            duration_years=4,
            total_credits=120,
            status=ProgramStatus.ACTIVE
        )
        db.add(prog)

        # 3. Term 1
        term = Term(
            id=1,
            term_id="TERM-2026-FALL",
            name="Fall 2026",
            year=2026,
            semester=SemesterEnum.FALL,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 15),
            is_active=True
        )
        db.add(term)

        # 4. Fee Schedule 1
        fee_sch = FeeSchedule(
            id=1,
            fee_schedule_id="FEE-000001",
            program_id=1,
            term_id=1,
            tuition_fee=Decimal("50000.00"),
            registration_fee=Decimal("2000.00"),
            laboratory_fee=Decimal("5000.00"),
            examination_fee=Decimal("1500.00"),
            library_fee=Decimal("1000.00"),
            other_charges=Decimal("500.00"),
            currency="INR",
            effective_start_date=date(2026, 8, 1),
            effective_end_date=date(2026, 12, 15),
            is_active=True
        )
        db.add(fee_sch)

        # 5. Student 1
        student = Student(
            id=1,
            student_id="STU-000001",
            first_name="Aarav",
            last_name="Sharma",
            email="aarav.sharma@test.edu",
            phone="+919876543210",
            date_of_birth=date(2005, 1, 1),
            address="12 Brigade Road",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560001",
            family_income_category="MEDIUM",
            gpa=Decimal("9.15"),
            status=StudentStatus.ACTIVE
        )
        db.add(student)

        # 6. Enrollment 1
        enrollment = Enrollment(
            id=1,
            enrollment_id="ENR-000001",
            student_id=1,
            program_id=1,
            term_id=1,
            status=EnrollmentStatus.ACTIVE,
            enrollment_date=date(2026, 8, 1)
        )
        db.add(enrollment)

        db.commit()
    finally:
        db.close()

    def override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject=1, role="PLATFORM_ADMIN")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_scholarship_and_eligibility_lifecycle(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a merit scholarship
        sch_payload = {
            "name": "Merit Excellence Scholarship 2026",
            "description": "50% tuition waiver for high GPA students",
            "scholarship_type": "MERIT",
            "percentage": "50.00",
            "max_amount": "50000.00",
            "min_gpa": "8.50",
            "total_budget": "500000.00",
            "academic_year": "2026-2027"
        }
        res = await client.post("/api/v1/scholarships", json=sch_payload, headers=auth_headers)
        assert res.status_code == 201, res.text
        sch = res.json()
        sch_id = sch["id"]
        assert sch["name"] == "Merit Excellence Scholarship 2026"
        assert sch["awarded_amount"] == "0.00"

        # 2. Get student with GPA 9.15 (Aarav Sharma)
        stu_res = await client.get("/api/v1/students/STU-000001", headers=auth_headers)
        assert stu_res.status_code == 200, stu_res.text
        student = stu_res.json()
        student_id = student["id"]

        # Find or create active enrollment & invoice for STU-000001
        enr_res = await client.get(f"/api/v1/enrollments/?student_id={student_id}", headers=auth_headers)
        enrs = enr_res.json()["items"]
        assert len(enrs) >= 1
        enrollment = enrs[0]
        term_id = enrollment["term_id"]

        # Ensure invoice exists
        inv_res = await client.get(f"/api/v1/invoices/?student_id={student_id}", headers=auth_headers)
        invoices = inv_res.json()["items"]
        if not invoices:
            inv_post = await client.post(
                "/api/v1/invoices/generate",
                json={"enrollment_id": enrollment["id"]},
                headers=auth_headers
            )
            assert inv_post.status_code == 201, inv_post.text
            invoice = inv_post.json()
        else:
            invoice = invoices[0]

        # 3. Evaluate student for scholarship
        eval_res = await client.post(
            "/api/v1/scholarships/evaluate",
            json={"student_id": student_id, "term_id": term_id, "scholarship_ids": [sch_id]},
            headers=auth_headers
        )
        assert eval_res.status_code == 200, eval_res.text
        elig_list = eval_res.json()
        assert len(elig_list) >= 1
        elig = elig_list[0]
        assert elig["status"] == "PENDING"
        assert Decimal(elig["calculated_amount"]) > Decimal("0.00")

        # 4. Approve eligibility
        appr_res = await client.post(
            f"/api/v1/eligibilities/{elig['id']}/approve",
            json={"approved_amount": elig["calculated_amount"]},
            headers=auth_headers
        )
        assert appr_res.status_code == 200, appr_res.text
        approved_elig = appr_res.json()
        assert approved_elig["status"] == "APPROVED"

        # 5. Verify invoice discount updated
        inv_check = await client.get(f"/api/v1/invoices/{invoice['id']}", headers=auth_headers)
        assert inv_check.status_code == 200, inv_check.text
        updated_inv = inv_check.json()
        assert Decimal(updated_inv["scholarship_discount"]) == Decimal(approved_elig["approved_amount"])
        assert Decimal(updated_inv["net_amount"]) == Decimal(updated_inv["gross_amount"]) - Decimal(updated_inv["scholarship_discount"])


@pytest.mark.asyncio
async def test_payment_recording_allocation_and_reversal(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get student
        stu_res = await client.get("/api/v1/students/STU-000001", headers=auth_headers)
        student = stu_res.json()
        student_id = student["id"]

        # Record Payment of 10000 INR
        payment_payload = {
            "student_id": student_id,
            "amount": "10000.00",
            "payment_method": "UPI",
            "reference_number": "UPI-TEST-TXN-998877",
            "currency": "INR",
            "notes": "Tuition partial payment via UPI"
        }
        res = await client.post("/api/v1/payments", json=payment_payload, headers=auth_headers)
        assert res.status_code == 201, res.text
        payment = res.json()
        payment_id = payment["id"]
        assert payment["amount"] == "10000.00"
        assert payment["allocated_amount"] == "0.00"
        assert payment["unallocated_amount"] == "10000.00"
        assert payment["status"] == "COMPLETED"

        # Fetch student invoice and lines
        inv_res = await client.get(f"/api/v1/invoices/?student_id={student_id}", headers=auth_headers)
        invoices = inv_res.json()["items"]
        assert len(invoices) > 0
        target_inv = invoices[0]

        # Allocate payment automatically
        alloc_res = await client.post(
            f"/api/v1/payments/{payment_id}/allocate",
            json={"auto_allocate": True, "invoice_id": target_inv["id"]},
            headers=auth_headers
        )
        assert alloc_res.status_code == 200, alloc_res.text
        allocated_payment = alloc_res.json()
        assert Decimal(allocated_payment["allocated_amount"]) > Decimal("0.00")
        assert Decimal(allocated_payment["unallocated_amount"]) == Decimal("10000.00") - Decimal(allocated_payment["allocated_amount"])

        # Check invoice paid amount increased
        inv_after = await client.get(f"/api/v1/invoices/{target_inv['id']}", headers=auth_headers)
        inv_data = inv_after.json()
        assert Decimal(inv_data["amount_paid"]) >= Decimal(allocated_payment["allocated_amount"])

        # Reverse payment
        rev_res = await client.post(
            f"/api/v1/payments/{payment_id}/reverse",
            json={"reason": "Incorrect payment account source"},
            headers=auth_headers
        )
        assert rev_res.status_code == 200, rev_res.text
        rev_payment = rev_res.json()
        assert rev_payment["status"] == "REVERSED"
        assert rev_payment["allocated_amount"] == "0.00"


@pytest.mark.asyncio
async def test_balance_statement_and_reconciliation(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Check student balance statement
        stmt_res = await client.get("/api/v1/ledger/students/1/statement", headers=auth_headers)
        assert stmt_res.status_code == 200, stmt_res.text
        statement = stmt_res.json()
        assert "gross_charges" in statement
        assert "net_collectible" in statement
        assert "outstanding_balance" in statement
        assert Decimal(statement["outstanding_balance"]) >= Decimal("0.00")

        # 2. Trigger batch reconciliation
        rec_res = await client.post("/api/v1/reconciliation/run", json={"notes": "Nightly reconciliation"}, headers=auth_headers)
        assert rec_res.status_code == 201, rec_res.text
        run = rec_res.json()
        assert run["status"] == "COMPLETED"
        assert run["total_invoices"] >= 0

        # 3. Check reconciliation results
        results_res = await client.get(f"/api/v1/reconciliation/runs/{run['id']}/results", headers=auth_headers)
        assert results_res.status_code == 200, results_res.text
        results_data = results_res.json()
        assert "items" in results_data


@pytest.mark.asyncio
async def test_refund_lifecycle(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a fresh payment to refund
        pay_res = await client.post(
            "/api/v1/payments",
            json={
                "student_id": 1,
                "amount": "5000.00",
                "payment_method": "BANK_TRANSFER",
                "reference_number": "REFUND-SRC-TXN-123",
                "currency": "INR",
                "notes": "Payment for refund test"
            },
            headers=auth_headers
        )
        assert pay_res.status_code == 201, pay_res.text
        payment = pay_res.json()

        # Request refund
        ref_req = await client.post(
            "/api/v1/refunds",
            json={
                "payment_id": payment["id"],
                "student_id": 1,
                "amount": "5000.00",
                "reason": "Accidental double payment",
                "reference_number": "REF-REQ-123"
            },
            headers=auth_headers
        )
        assert ref_req.status_code == 201, ref_req.text
        refund = ref_req.json()
        assert refund["status"] == "REQUESTED"
        assert refund["amount"] == "5000.00"

        # Approve refund
        appr_res = await client.post(f"/api/v1/refunds/{refund['id']}/approve", json={"notes": "Approved by Bursar"}, headers=auth_headers)
        assert appr_res.status_code == 200, appr_res.text
        assert appr_res.json()["status"] == "APPROVED"

        # Process refund
        proc_res = await client.post(f"/api/v1/refunds/{refund['id']}/process", headers=auth_headers)
        assert proc_res.status_code == 200, proc_res.text
        assert proc_res.json()["status"] == "PROCESSED"

        # Verify financial event emitted with exact amount parity and refund entity reference
        events_res = await client.get("/api/v1/ledger/events", headers=auth_headers)
        assert events_res.status_code == 200, events_res.text
        events_list = events_res.json()["items"]
        matching_event = next(
            (e for e in events_list if e["entity_type"] == "REFUND" and e["entity_id"] == refund["refund_id"] and e["event_type"] == "REFUND_PROCESSED"),
            None
        )
        assert matching_event is not None, "REFUND_PROCESSED financial event must be logged"
        assert Decimal(matching_event["amount"]) == Decimal("5000.00"), "Event amount must match refund amount exactly"


@pytest.mark.asyncio
async def test_anomaly_detection_scan(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger scan
        scan_res = await client.post("/api/v1/anomalies/scan", headers=auth_headers)
        assert scan_res.status_code == 200, scan_res.text
        anomalies = scan_res.json()
        assert isinstance(anomalies, list)

        # List anomalies
        list_res = await client.get("/api/v1/anomalies", headers=auth_headers)
        assert list_res.status_code == 200, list_res.text
        assert "items" in list_res.json()


@pytest.mark.asyncio
async def test_anomaly_boundary_conditions(auth_headers):
    """
    Negative and boundary tests for all 5 anomaly detection rules.
    Verifies that:
    1. Normal records are NOT flagged (True Negatives / negative controls).
    2. Exact boundary conditions (allocated == amount, approved == eligible_fee, etc.) are NOT flagged.
    3. Over-boundary conditions (> threshold) ARE flagged (True Positives).
    4. CANCELLED invoices and REJECTED refunds are excluded from anomaly scans.
    """
    db = TestSessionLocal()
    try:
        detector = AnomalyDetectionService(db)

        # Ensure a base scholarship exists for FK
        sch = db.query(Scholarship).first()
        if not sch:
            sch = Scholarship(
                scholarship_id="SCH-BD-001",
                name="Boundary Scholarship",
                scholarship_type=ScholarshipType.MERIT,
                percentage=Decimal("50.00"),
                max_amount=Decimal("50000.00"),
                total_budget=Decimal("500000.00"),
                academic_year="2026-2027",
                status=ScholarshipStatus.ACTIVE
            )
            db.add(sch)
            db.flush()

        # Ensure a base invoice and line exist for FK
        base_inv = db.query(Invoice).first()
        if not base_inv:
            base_inv = Invoice(
                invoice_id="INV-PARENT-001",
                enrollment_id=1,
                student_id=1,
                term_id=1,
                invoice_date=date(2026, 1, 10),
                due_date=date(2026, 2, 10),
                gross_amount=Decimal("10000.00"),
                net_amount=Decimal("10000.00"),
                outstanding_balance=Decimal("10000.00"),
                billing_cycle="2026-BASE-CYCLE",
                status=InvoiceStatus.ISSUED
            )
            db.add(base_inv)
            db.flush()

        inv_line = db.query(InvoiceLine).first()
        if not inv_line:
            inv_line = InvoiceLine(
                invoice_line_id="INV-LINE-PARENT-001",
                invoice_id=base_inv.id,
                fee_type=FeeType.TUITION,
                description="Tuition Fee Base",
                amount=Decimal("10000.00"),
                allocated_amount=Decimal("0.00")
            )
            db.add(inv_line)
            db.flush()

        # Rule 1 Boundary: Payment exact vs over-allocated
        p_exact = Payment(
            payment_id="PAY-BD-EXACT",
            student_id=1,
            amount=Decimal("1000.00"),
            allocated_amount=Decimal("1000.00"),
            unallocated_amount=Decimal("0.00"),
            payment_method=PaymentMethod.UPI,
            status=PaymentStatus.COMPLETED
        )
        p_over = Payment(
            payment_id="PAY-BD-OVER",
            student_id=1,
            amount=Decimal("1000.00"),
            allocated_amount=Decimal("1000.01"),
            unallocated_amount=Decimal("0.00"),
            payment_method=PaymentMethod.UPI,
            status=PaymentStatus.COMPLETED
        )
        db.add_all([p_exact, p_over])
        db.flush()

        alloc_exact = PaymentAllocation(
            allocation_id="ALLOC-BD-EXACT",
            payment_id=p_exact.id,
            invoice_line_id=inv_line.id,
            amount=Decimal("1000.00")
        )
        alloc_over = PaymentAllocation(
            allocation_id="ALLOC-BD-OVER",
            payment_id=p_over.id,
            invoice_line_id=inv_line.id,
            amount=Decimal("1000.01")
        )
        db.add_all([alloc_exact, alloc_over])

        # Rule 2 Boundary: Scholarship exact vs over-awarded vs pending
        e_exact = Eligibility(
            eligibility_id="ELIG-BD-EXACT",
            student_id=1,
            scholarship_id=sch.id,
            eligible_fee_amount=Decimal("20000.00"),
            approved_amount=Decimal("20000.00"),
            status=EligibilityStatus.APPROVED,
            decision_reason="Exact fee match boundary"
        )
        e_pending = Eligibility(
            eligibility_id="ELIG-BD-PENDING",
            student_id=1,
            scholarship_id=sch.id,
            eligible_fee_amount=Decimal("20000.00"),
            approved_amount=Decimal("30000.00"),
            status=EligibilityStatus.PENDING,
            decision_reason="Pending must not trigger anomaly"
        )
        e_over = Eligibility(
            eligibility_id="ELIG-BD-OVER",
            student_id=1,
            scholarship_id=sch.id,
            eligible_fee_amount=Decimal("20000.00"),
            approved_amount=Decimal("20000.01"),
            status=EligibilityStatus.APPROVED,
            decision_reason="Over fee by 0.01"
        )
        db.add_all([e_exact, e_pending, e_over])

        # Rule 3 Boundary: Duplicate invoice with cancelled vs active duplicate
        inv_cancel = Invoice(
            invoice_id="INV-BD-CANCELLED",
            enrollment_id=1,
            student_id=1,
            term_id=1,
            invoice_date=date(2026, 1, 10),
            due_date=date(2026, 2, 10),
            gross_amount=Decimal("5000.00"),
            net_amount=Decimal("5000.00"),
            outstanding_balance=Decimal("0.00"),
            billing_cycle="2026-CYCLE-CANCELLED-TEST",
            status=InvoiceStatus.CANCELLED
        )
        inv_active = Invoice(
            invoice_id="INV-BD-ACTIVE",
            enrollment_id=1,
            student_id=1,
            term_id=1,
            invoice_date=date(2026, 1, 10),
            due_date=date(2026, 2, 10),
            gross_amount=Decimal("5000.00"),
            net_amount=Decimal("5000.00"),
            outstanding_balance=Decimal("5000.00"),
            billing_cycle="2026-CYCLE-CANCELLED-TEST",
            status=InvoiceStatus.ISSUED
        )
        # Active duplicate pair
        inv_dup1 = Invoice(
            invoice_id="INV-BD-DUP1",
            enrollment_id=1,
            student_id=1,
            term_id=1,
            invoice_date=date(2026, 1, 10),
            due_date=date(2026, 2, 10),
            gross_amount=Decimal("5000.00"),
            net_amount=Decimal("5000.00"),
            outstanding_balance=Decimal("5000.00"),
            billing_cycle="2026-CYCLE-DUP-TEST",
            status=InvoiceStatus.ISSUED
        )
        inv_dup2 = Invoice(
            invoice_id="INV-BD-DUP2",
            enrollment_id=1,
            student_id=1,
            term_id=1,
            invoice_date=date(2026, 1, 10),
            due_date=date(2026, 2, 10),
            gross_amount=Decimal("5000.00"),
            net_amount=Decimal("5000.00"),
            outstanding_balance=Decimal("5000.00"),
            billing_cycle="2026-CYCLE-DUP-TEST",
            status=InvoiceStatus.ISSUED
        )
        db.add_all([inv_cancel, inv_active, inv_dup1, inv_dup2])

        # Rule 4 Boundary: Refund exact vs rejected vs over
        p_ref = Payment(
            payment_id="PAY-BD-REFUND-SRC",
            student_id=1,
            amount=Decimal("5000.00"),
            allocated_amount=Decimal("0.00"),
            unallocated_amount=Decimal("5000.00"),
            payment_method=PaymentMethod.UPI,
            status=PaymentStatus.COMPLETED
        )
        db.add(p_ref)
        db.flush()

        ref_exact = Refund(
            refund_id="REF-BD-EXACT",
            payment_id=p_ref.id,
            student_id=1,
            amount=Decimal("5000.00"),
            reason="Full refund exact",
            status=RefundStatus.PROCESSED
        )
        # Another payment for rejected
        p_ref_rej = Payment(
            payment_id="PAY-BD-REFUND-REJ-SRC",
            student_id=1,
            amount=Decimal("2000.00"),
            allocated_amount=Decimal("0.00"),
            unallocated_amount=Decimal("2000.00"),
            payment_method=PaymentMethod.UPI,
            status=PaymentStatus.COMPLETED
        )
        db.add(p_ref_rej)
        db.flush()

        ref_rejected = Refund(
            refund_id="REF-BD-REJECTED",
            payment_id=p_ref_rej.id,
            student_id=1,
            amount=Decimal("99999.00"),
            reason="Rejected refund must not flag",
            status=RefundStatus.REJECTED
        )
        # Payment for over refund
        p_ref_over = Payment(
            payment_id="PAY-BD-REFUND-OVER-SRC",
            student_id=1,
            amount=Decimal("3000.00"),
            allocated_amount=Decimal("0.00"),
            unallocated_amount=Decimal("3000.00"),
            payment_method=PaymentMethod.UPI,
            status=PaymentStatus.COMPLETED
        )
        db.add(p_ref_over)
        db.flush()

        ref_over = Refund(
            refund_id="REF-BD-OVER",
            payment_id=p_ref_over.id,
            student_id=1,
            amount=Decimal("3000.01"),
            reason="Over refund by 0.01",
            status=RefundStatus.REQUESTED
        )
        db.add_all([ref_exact, ref_rejected, ref_over])

        # Rule 5 Boundary: Stored balance exact vs mismatched
        inv_bal_exact = Invoice(
            invoice_id="INV-BD-BAL-EXACT",
            enrollment_id=1,
            student_id=1,
            term_id=1,
            invoice_date=date(2026, 1, 10),
            due_date=date(2026, 2, 10),
            gross_amount=Decimal("10000.00"),
            scholarship_discount=Decimal("2000.00"),
            net_amount=Decimal("8000.00"),
            amount_paid=Decimal("3000.00"),
            outstanding_balance=Decimal("5000.00"),
            billing_cycle="2026-CYCLE-BAL-EXACT",
            status=InvoiceStatus.PARTIALLY_PAID
        )
        inv_bal_mismatch = Invoice(
            invoice_id="INV-BD-BAL-MISMATCH",
            enrollment_id=1,
            student_id=1,
            term_id=1,
            invoice_date=date(2026, 1, 10),
            due_date=date(2026, 2, 10),
            gross_amount=Decimal("10000.00"),
            scholarship_discount=Decimal("0.00"),
            net_amount=Decimal("10000.00"),
            amount_paid=Decimal("0.00"),
            outstanding_balance=Decimal("9999.99"),  # Missing 0.01
            billing_cycle="2026-CYCLE-BAL-MISMATCH",
            status=InvoiceStatus.ISSUED
        )
        db.add_all([inv_bal_exact, inv_bal_mismatch])
        db.commit()

        # Run Anomaly Detector
        detected = detector.scan_for_anomalies()
        detected_entity_ids = {a.entity_id for a in detected}

        # Rule 1 Verifications:
        assert "PAY-BD-EXACT" not in detected_entity_ids, "Exact allocation must not be flagged"
        assert "PAY-BD-OVER" in detected_entity_ids, "Over-allocated payment must be flagged"

        # Rule 2 Verifications:
        assert "ELIG-BD-EXACT" not in detected_entity_ids, "Exact fee eligibility must not be flagged"
        assert "ELIG-BD-PENDING" not in detected_entity_ids, "Pending eligibility must not be flagged"
        assert "ELIG-BD-OVER" in detected_entity_ids, "Over-awarded eligibility must be flagged"

        # Rule 3 Verifications:
        assert "INV-BD-CANCELLED" not in detected_entity_ids, "Cancelled invoice must not trigger duplicate"
        assert "INV-BD-ACTIVE" not in detected_entity_ids, "Active invoice paired with cancelled must not trigger duplicate"
        assert "INV-BD-DUP2" in detected_entity_ids, "Second active invoice in duplicate cycle must be flagged"

        # Rule 4 Verifications:
        assert "PAY-BD-REFUND-SRC" not in detected_entity_ids, "Exact refund must not trigger anomaly"
        assert "PAY-BD-REFUND-REJ-SRC" not in detected_entity_ids, "Rejected refund must not trigger anomaly"
        assert "PAY-BD-REFUND-OVER-SRC" in detected_entity_ids, "Over-refunded payment must be flagged"

        # Rule 5 Verifications:
        assert "INV-BD-BAL-EXACT" not in detected_entity_ids, "Exact balance invoice must not be flagged"
        assert "INV-BD-BAL-MISMATCH" in detected_entity_ids, "Mismatched balance invoice must be flagged"

    finally:
        db.close()
