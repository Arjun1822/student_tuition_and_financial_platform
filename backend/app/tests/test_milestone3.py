import pytest
from datetime import date
from decimal import Decimal
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.main import app
from app.models.user import User, RoleEnum
from app.models.student import IncomeCategory, StudentStatus
from app.models.program import DegreeLevel, ProgramStatus
from app.models.term import SemesterEnum
from app.models.enrollment import EnrollmentStatus
from app.models.invoice import InvoiceStatus
from app.core.security import get_password_hash

# Dedicated test database
TEST_DB_URI = settings.get_test_database_uri()
test_engine = create_engine(TEST_DB_URI, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Seed an admin and a learner user into test db
    db = TestSessionLocal()
    admin_user = User(
        username="test_admin",
        email="test_admin@test.edu",
        password_hash=get_password_hash("Admin@2026Test"),
        full_name="Test Administrator",
        role=RoleEnum.PLATFORM_ADMIN,
        is_active=True
    )
    learner_user = User(
        username="test_learner",
        email="test_learner@test.edu",
        password_hash=get_password_hash("Learner@2026Test"),
        full_name="Test Learner",
        role=RoleEnum.LEARNER,
        is_active=True
    )
    db.add_all([admin_user, learner_user])
    db.commit()
    db.close()

    # Override app get_db to use TestSessionLocal during tests
    from app.core.database import get_db
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.mark.asyncio
async def test_auth_login(setup_test_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login with test_admin
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "test_admin", "password": "Admin@2026Test"}
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "PLATFORM_ADMIN"

        # 2. Login with incorrect password
        bad_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "test_admin", "password": "WrongPassword"}
        )
        assert bad_resp.status_code == 401


@pytest.mark.asyncio
async def test_student_crud_and_uniqueness(setup_test_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Get admin token
        auth_resp = await client.post("/api/v1/auth/login", data={"username": "test_admin", "password": "Admin@2026Test"})
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create student
        student_data = {
            "first_name": "Priya",
            "last_name": "Patel",
            "email": "priya.patel@test.edu",
            "phone": "+919876543210",
            "date_of_birth": "2005-04-12",
            "address": "45 MG Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India",
            "postal_code": "560001",
            "family_income_category": "MEDIUM",
            "gpa": "9.15",
            "status": "ACTIVE"
        }
        res = await client.post("/api/v1/students/", json=student_data, headers=headers)
        assert res.status_code == 201, res.text
        stu = res.json()
        assert stu["student_id"].startswith("STU-")
        assert stu["first_name"] == "Priya"

        # Duplicate email test
        dup_res = await client.post("/api/v1/students/", json=student_data, headers=headers)
        assert dup_res.status_code == 409

        # Get student by ID
        get_res = await client.get(f"/api/v1/students/{stu['id']}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["email"] == "priya.patel@test.edu"

        # Update student
        up_res = await client.put(
            f"/api/v1/students/{stu['id']}",
            json={"phone": "+919999988888", "gpa": "9.40"},
            headers=headers
        )
        assert up_res.status_code == 200
        assert up_res.json()["gpa"] == "9.40"
        assert up_res.json()["phone"] == "+919999988888"


@pytest.mark.asyncio
async def test_program_crud_and_uniqueness(setup_test_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        auth_resp = await client.post("/api/v1/auth/login", data={"username": "test_admin", "password": "Admin@2026Test"})
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create program
        prog_data = {
            "name": "B.Tech Computer Science",
            "code": "CS-TEST-BTECH",
            "department": "School of Computing",
            "degree_level": "BACHELOR",
            "duration_years": 4,
            "total_credits": 160,
            "status": "ACTIVE",
            "description": "Standard 4-year degree"
        }
        res = await client.post("/api/v1/programs/", json=prog_data, headers=headers)
        assert res.status_code == 201, res.text
        prog = res.json()
        assert prog["program_id"].startswith("PRG-")
        assert prog["code"] == "CS-TEST-BTECH"

        # Duplicate code test
        dup_res = await client.post("/api/v1/programs/", json=prog_data, headers=headers)
        assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_fee_schedule_management(setup_test_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        auth_resp = await client.post("/api/v1/auth/login", data={"username": "test_admin", "password": "Admin@2026Test"})
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create term
        term_data = {
            "name": "Spring Semester 2026",
            "year": 2026,
            "semester": "SPRING",
            "start_date": "2026-01-10",
            "end_date": "2026-05-20",
            "is_active": True
        }
        term_res = await client.post("/api/v1/terms/", json=term_data, headers=headers)
        assert term_res.status_code == 201, term_res.text
        term = term_res.json()

        # Get program created in previous test
        prog_res = await client.get("/api/v1/programs/CS-TEST-BTECH", headers=headers)
        prog = prog_res.json()

        # Create fee schedule
        fee_data = {
            "program_id": prog["id"],
            "term_id": term["id"],
            "tuition_fee": "80000.00",
            "registration_fee": "5000.00",
            "laboratory_fee": "15000.00",
            "examination_fee": "3000.00",
            "library_fee": "2000.00",
            "other_charges": "1000.00",
            "currency": "INR",
            "effective_start_date": "2026-01-10",
            "effective_end_date": "2026-05-20",
            "is_active": True
        }
        fee_res = await client.post("/api/v1/fee-schedules/", json=fee_data, headers=headers)
        assert fee_res.status_code == 201, fee_res.text
        fee = fee_res.json()
        assert fee["fee_schedule_id"].startswith("FEE-")
        assert Decimal(fee["total_fee"]) == Decimal("106000.00")

        # Conflict test: duplicate schedule for same program + term
        dup_fee = await client.post("/api/v1/fee-schedules/", json=fee_data, headers=headers)
        assert dup_fee.status_code == 409


@pytest.mark.asyncio
async def test_enrollment_and_invoice_workflow(setup_test_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        auth_resp = await client.post("/api/v1/auth/login", data={"username": "test_admin", "password": "Admin@2026Test"})
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Fetch student, program, term
        stu = (await client.get("/api/v1/students/priya.patel@test.edu", headers=headers)).json()
        prog = (await client.get("/api/v1/programs/CS-TEST-BTECH", headers=headers)).json()
        term = (await client.get("/api/v1/terms/TERM-2026-SPRING", headers=headers)).json()

        # 2. Create enrollment
        enr_data = {
            "student_id": stu["id"],
            "program_id": prog["id"],
            "term_id": term["id"],
            "enrollment_date": "2026-01-15"
        }
        enr_res = await client.post("/api/v1/enrollments/", json=enr_data, headers=headers)
        assert enr_res.status_code == 201, enr_res.text
        enr = enr_res.json()
        assert enr["enrollment_id"].startswith("ENR-")
        assert enr["status"] == "ACTIVE"

        # 3. Duplicate enrollment prevention test
        dup_enr = await client.post("/api/v1/enrollments/", json=enr_data, headers=headers)
        assert dup_enr.status_code == 409

        # 4. Generate invoice
        inv_data = {
            "enrollment_id": enr["id"],
            "notes": "Semester 1 tuition invoice"
        }
        inv_res = await client.post("/api/v1/invoices/generate", json=inv_data, headers=headers)
        assert inv_res.status_code == 201, inv_res.text
        inv = inv_res.json()
        assert inv["invoice_id"].startswith(f"INV-{stu['student_id']}-2026-")
        assert Decimal(inv["gross_amount"]) == Decimal("106000.00")
        assert Decimal(inv["net_amount"]) == Decimal("106000.00")
        assert Decimal(inv["outstanding_balance"]) == Decimal("106000.00")
        assert inv["status"] == "ISSUED"
        assert len(inv["lines"]) == 6

        # Verify lines sum equals gross amount
        line_sum = sum(Decimal(line["amount"]) for line in inv["lines"])
        assert line_sum == Decimal("106000.00")

        # 5. Duplicate invoice prevention for same enrollment & billing cycle
        dup_inv = await client.post("/api/v1/invoices/generate", json=inv_data, headers=headers)
        assert dup_inv.status_code == 409, "Must reject duplicate invoice for same enrollment and cycle"


@pytest.mark.asyncio
async def test_rbac_permissions(setup_test_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as learner
        auth_resp = await client.post("/api/v1/auth/login", data={"username": "test_learner", "password": "Learner@2026Test"})
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Learner cannot create a program (requires ACADEMIC_ADMIN or PLATFORM_ADMIN)
        prog_res = await client.post(
            "/api/v1/programs/",
            json={"name": "Forbidden Program", "code": "FORBID-01", "department": "Test", "degree_level": "BACHELOR"},
            headers=headers
        )
        assert prog_res.status_code == 403

        # Learner cannot create student
        stu_res = await client.post(
            "/api/v1/students/",
            json={"first_name": "Test", "last_name": "User", "email": "test@test.com", "date_of_birth": "2000-01-01"},
            headers=headers
        )
        assert stu_res.status_code == 403

