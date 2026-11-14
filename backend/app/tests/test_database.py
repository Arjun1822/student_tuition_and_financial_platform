import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import Base
from app.models import (
    Role,
    RoleEnum,
    User,
    Program,
    DegreeLevel,
    ProgramStatus,
    Term,
    SemesterEnum,
    FeeSchedule,
    Student,
    IncomeCategory,
    StudentStatus,
    Enrollment,
    EnrollmentStatus,
    Invoice,
    InvoiceStatus,
    InvoiceLine,
    FeeType,
    Payment,
    PaymentMethod,
    PaymentStatus,
    PaymentAllocation,
    Scholarship,
    ScholarshipType,
    ScholarshipStatus,
    Eligibility,
    EligibilityStatus,
    Refund,
    RefundStatus,
    FinancialEvent,
    FinancialEventType,
    ReconciliationRun,
    ReconciliationRunStatus,
    ReconciliationResult,
    ReconciliationStatus,
    Anomaly,
    AnomalyIssueType,
    AnomalySeverity,
    AuditLog,
)

# Connect to the dedicated test database
TEST_DB_URI = settings.get_test_database_uri()
test_engine = create_engine(TEST_DB_URI, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def setup_test_database():
    """Setup test database schema once for this test module."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    # Cleanup after test run
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(setup_test_database):
    """Provides a fresh transactional session for each test function."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_database_connection(db_session):
    """Verify live connectivity and version of the separate test database."""
    result = db_session.execute(text("SELECT 1, DATABASE(), VERSION()")).fetchone()
    assert result[0] == 1
    assert result[1] == "student_finance_test_db"
    assert "8.0" in result[2]


def test_model_creation_and_attributes(db_session):
    """Verify creating core entities and retrieving them."""
    program = Program(
        program_id="PRG-TEST-01",
        name="Test Program in Software Engineering",
        code="TEST-SE",
        department="Computer Science",
        degree_level=DegreeLevel.BACHELOR,
        duration_years=4,
        total_credits=160,
        status=ProgramStatus.ACTIVE
    )
    db_session.add(program)
    db_session.commit()

    retrieved = db_session.query(Program).filter(Program.code == "TEST-SE").first()
    assert retrieved is not None
    assert retrieved.program_id == "PRG-TEST-01"
    assert retrieved.degree_level == DegreeLevel.BACHELOR
    assert retrieved.total_credits == 160


def test_decimal_precision(db_session):
    """Verify monetary values strictly maintain DECIMAL(12,2) precision with no float drift."""
    program = db_session.query(Program).filter(Program.code == "TEST-SE").first()
    term = Term(
        term_id="TERM-2026-TEST",
        name="Test Term 2026",
        year=2026,
        semester=SemesterEnum.SPRING,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 30),
        is_active=True
    )
    db_session.add(term)
    db_session.commit()

    fee_schedule = FeeSchedule(
        fee_schedule_id="FEE-TEST-01",
        program_id=program.id,
        term_id=term.id,
        tuition_fee=Decimal("75123.45"),
        registration_fee=Decimal("5000.10"),
        laboratory_fee=Decimal("12000.55"),
        examination_fee=Decimal("3500.00"),
        library_fee=Decimal("2500.00"),
        other_charges=Decimal("1000.00"),
        currency="INR",
        effective_start_date=term.start_date,
        effective_end_date=term.end_date,
        is_active=True
    )
    db_session.add(fee_schedule)
    db_session.commit()

    retrieved = db_session.query(FeeSchedule).filter(FeeSchedule.fee_schedule_id == "FEE-TEST-01").first()
    assert retrieved.tuition_fee == Decimal("75123.45")
    assert retrieved.registration_fee == Decimal("5000.10")
    assert retrieved.laboratory_fee == Decimal("12000.55")
    expected_total = Decimal("75123.45") + Decimal("5000.10") + Decimal("12000.55") + Decimal("3500.00") + Decimal("2500.00") + Decimal("1000.00")
    assert retrieved.total_fee == expected_total


def test_foreign_key_integrity(db_session):
    """Verify that foreign key constraints reject non-existent parent references."""
    invalid_enrollment = Enrollment(
        enrollment_id="ENR-INVALID-01",
        student_id=999999,  # Non-existent student
        program_id=999999,  # Non-existent program
        term_id=999999,     # Non-existent term
        enrollment_date=date(2026, 1, 15),
        status=EnrollmentStatus.ACTIVE
    )
    db_session.add(invalid_enrollment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_constraints(db_session):
    """Verify unique constraints reject duplicate identifiers and codes."""
    # Program code is unique
    duplicate_program = Program(
        program_id="PRG-TEST-DUPE",
        name="Duplicate Program Code",
        code="TEST-SE",  # Already exists from previous test
        department="Engineering",
        degree_level=DegreeLevel.BACHELOR
    )
    db_session.add(duplicate_program)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_relationship_loading(db_session):
    """Verify ORM relationships load parent and child associations correctly."""
    # Create student
    student = Student(
        student_id="STU-TEST-001",
        first_name="Rohan",
        last_name="Gupta",
        email="rohan.gupta@test.edu",
        date_of_birth=date(2004, 3, 15),
        family_income_category=IncomeCategory.MEDIUM,
        gpa=Decimal("8.75"),
        status=StudentStatus.ACTIVE
    )
    db_session.add(student)
    db_session.commit()

    program = db_session.query(Program).filter(Program.code == "TEST-SE").first()
    term = db_session.query(Term).filter(Term.term_id == "TERM-2026-TEST").first()

    enrollment = Enrollment(
        enrollment_id="ENR-TEST-001",
        student_id=student.id,
        program_id=program.id,
        term_id=term.id,
        enrollment_date=date(2026, 1, 15),
        status=EnrollmentStatus.ACTIVE
    )
    db_session.add(enrollment)
    db_session.commit()

    # Verify bidirectional relationship
    db_session.refresh(student)
    assert len(student.enrollments) == 1
    assert student.enrollments[0].program.name == "Test Program in Software Engineering"
    assert student.enrollments[0].term.name == "Test Term 2026"


def test_invoice_and_payment_allocation_models(db_session):
    """Verify Invoice, InvoiceLines, Payment, and PaymentAllocation integrity and arithmetic."""
    student = db_session.query(Student).filter(Student.student_id == "STU-TEST-001").first()
    enrollment = db_session.query(Enrollment).filter(Enrollment.enrollment_id == "ENR-TEST-001").first()
    term = db_session.query(Term).filter(Term.term_id == "TERM-2026-TEST").first()

    # Create Invoice
    invoice = Invoice(
        invoice_id="INV-STU-001-2026-000001",
        enrollment_id=enrollment.id,
        student_id=student.id,
        term_id=term.id,
        invoice_date=date(2026, 1, 15),
        due_date=date(2026, 2, 15),
        gross_amount=Decimal("50000.00"),
        scholarship_discount=Decimal("10000.00"),
        net_amount=Decimal("40000.00"),
        amount_paid=Decimal("0.00"),
        outstanding_balance=Decimal("40000.00"),
        currency="INR",
        status=InvoiceStatus.ISSUED,
        billing_cycle="2026-SPRING"
    )
    db_session.add(invoice)
    db_session.flush()

    line1 = InvoiceLine(
        invoice_line_id="INVL-TEST-01",
        invoice_id=invoice.id,
        fee_type=FeeType.TUITION,
        description="Tuition Fee",
        amount=Decimal("40000.00"),
        allocated_amount=Decimal("0.00")
    )
    line2 = InvoiceLine(
        invoice_line_id="INVL-TEST-02",
        invoice_id=invoice.id,
        fee_type=FeeType.REGISTRATION,
        description="Registration Fee",
        amount=Decimal("10000.00"),
        allocated_amount=Decimal("0.00")
    )
    db_session.add_all([line1, line2])
    db_session.flush()

    # Create Payment
    payment = Payment(
        payment_id="PAY-2026-TEST-01",
        student_id=student.id,
        amount=Decimal("40000.00"),
        allocated_amount=Decimal("40000.00"),
        unallocated_amount=Decimal("0.00"),
        payment_method=PaymentMethod.UPI,
        reference_number="UPI-REF-998877",
        currency="INR",
        status=PaymentStatus.COMPLETED
    )
    db_session.add(payment)
    db_session.flush()

    # Allocate payment to invoice lines
    alloc1 = PaymentAllocation(
        allocation_id="ALLOC-PAY-TEST-01",
        payment_id=payment.id,
        invoice_line_id=line1.id,
        amount=Decimal("30000.00")
    )
    alloc2 = PaymentAllocation(
        allocation_id="ALLOC-PAY-TEST-02",
        payment_id=payment.id,
        invoice_line_id=line2.id,
        amount=Decimal("10000.00")
    )
    db_session.add_all([alloc1, alloc2])
    db_session.commit()

    # Retrieve and verify allocations
    allocations = db_session.query(PaymentAllocation).filter(PaymentAllocation.payment_id == payment.id).all()
    assert len(allocations) == 2
    total_allocated = sum(a.amount for a in allocations)
    assert total_allocated == Decimal("40000.00")


def test_transaction_rollback(db_session):
    """Verify that aborted operations roll back without leaving orphaned records."""
    count_before = db_session.query(Role).count()

    # Start a nested savepoint
    savepoint = db_session.begin_nested()
    temp_role = Role(name="TEMPORARY_TEST_ROLE", description="Should be rolled back")
    db_session.add(temp_role)
    db_session.flush()

    # Roll back savepoint
    savepoint.rollback()

    count_after = db_session.query(Role).count()
    assert count_before == count_after
    assert db_session.query(Role).filter(Role.name == "TEMPORARY_TEST_ROLE").first() is None
