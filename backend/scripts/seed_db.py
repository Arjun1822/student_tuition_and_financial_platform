import os
import sys
from datetime import date, datetime
from decimal import Decimal

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.role import Role, RoleEnum
from app.models.user import User
from app.models.program import Program, DegreeLevel, ProgramStatus
from app.models.term import Term, SemesterEnum
from app.models.fee_schedule import FeeSchedule


PROGRAMS_CATALOG = [
    ("Computer Science and Engineering", "CS-BTECH", "School of Computing", DegreeLevel.BACHELOR, 4, 160),
    ("Artificial Intelligence and Data Science", "AI-BTECH", "School of Computing", DegreeLevel.BACHELOR, 4, 160),
    ("Information Technology", "IT-BTECH", "School of Computing", DegreeLevel.BACHELOR, 4, 160),
    ("Software Engineering", "SE-MTECH", "School of Computing", DegreeLevel.MASTER, 2, 80),
    ("Cybersecurity and Forensics", "CY-MTECH", "School of Computing", DegreeLevel.MASTER, 2, 80),
    ("Data Science and Analytics", "DS-MS", "School of Computing", DegreeLevel.MASTER, 2, 75),
    ("Computer Science Research", "CS-PHD", "School of Computing", DegreeLevel.DOCTORATE, 4, 60),
    ("Electronics and Communication", "EC-BTECH", "School of Electrical", DegreeLevel.BACHELOR, 4, 160),
    ("Electrical and Electronics", "EE-BTECH", "School of Electrical", DegreeLevel.BACHELOR, 4, 160),
    ("VLSI Design and Embedded Systems", "VLSI-MTECH", "School of Electrical", DegreeLevel.MASTER, 2, 80),
    ("Mechanical Engineering", "ME-BTECH", "School of Mechanical", DegreeLevel.BACHELOR, 4, 160),
    ("Robotics and Mechatronics", "ROB-MTECH", "School of Mechanical", DegreeLevel.MASTER, 2, 80),
    ("Civil and Environmental Engineering", "CE-BTECH", "School of Civil", DegreeLevel.BACHELOR, 4, 160),
    ("Structural Engineering", "SE-CIVIL-MS", "School of Civil", DegreeLevel.MASTER, 2, 75),
    ("Biotechnology", "BT-BTECH", "School of BioSciences", DegreeLevel.BACHELOR, 4, 160),
    ("Bioinformatics", "BI-MS", "School of BioSciences", DegreeLevel.MASTER, 2, 75),
    ("Business Administration", "BBA-BACH", "School of Management", DegreeLevel.BACHELOR, 3, 120),
    ("Finance and Accounting", "MBA-FIN", "School of Management", DegreeLevel.MASTER, 2, 90),
    ("Business Analytics", "MBA-BA", "School of Management", DegreeLevel.MASTER, 2, 90),
    ("Diploma in Cloud Computing", "DIP-CC", "School of Continuing Education", DegreeLevel.DIPLOMA, 1, 40),
]

TERMS_CATALOG = [
    ("Spring Semester 2026", 2026, SemesterEnum.SPRING, date(2026, 1, 12), date(2026, 5, 20)),
    ("Summer Term 2026", 2026, SemesterEnum.SUMMER, date(2026, 6, 1), date(2026, 7, 31)),
    ("Fall Semester 2026", 2026, SemesterEnum.FALL, date(2026, 8, 17), date(2026, 12, 18)),
    ("Spring Semester 2027", 2027, SemesterEnum.SPRING, date(2027, 1, 11), date(2027, 5, 21)),
]


def seed_roles_and_users(db: Session):
    print("-> Seeding Roles and Users...")
    role_map = {}
    for role_enum in RoleEnum:
        existing_role = db.query(Role).filter(Role.name == role_enum.value).first()
        if not existing_role:
            role = Role(
                name=role_enum.value,
                description=f"Standard role for {role_enum.value.replace('_', ' ').title()}",
                permissions_json=None
            )
            db.add(role)
            db.flush()
            role_map[role_enum.value] = role
        else:
            role_map[role_enum.value] = existing_role

    demo_users = [
        ("admin", "admin@studentfin.edu", "Admin@2026Secure", "Platform Administrator", RoleEnum.PLATFORM_ADMIN),
        ("academic_admin", "academic@studentfin.edu", "Academic@2026Secure", "Academic Administrator", RoleEnum.ACADEMIC_ADMIN),
        ("support_staff", "support@studentfin.edu", "Support@2026Secure", "Senior Financial Counselor", RoleEnum.SUPPORT_STAFF),
        ("instructor", "instructor@studentfin.edu", "Faculty@2026Secure", "Prof. Vikram Sarabhai", RoleEnum.INSTRUCTOR),
        ("learner", "learner@studentfin.edu", "Student@2026Secure", "Aarav Sharma", RoleEnum.LEARNER),
    ]

    for username, email, raw_password, full_name, role_enum in demo_users:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                password_hash=get_password_hash(raw_password),
                full_name=full_name,
                role=role_enum,
                role_id=role_map[role_enum.value].id,
                is_active=True
            )
            db.add(user)
            print(f"   Created user: {username} ({role_enum.value})")
        else:
            # Update password hash if needed
            user.password_hash = get_password_hash(raw_password)
            user.role_id = role_map[role_enum.value].id
    db.flush()


def seed_programs(db: Session):
    print("-> Seeding 20 Academic Programs...")
    program_entities = []
    for idx, (name, code, dept, degree_level, duration, credits_) in enumerate(PROGRAMS_CATALOG, start=1):
        program_id = f"PRG-{idx:06d}"
        program = db.query(Program).filter(Program.code == code).first()
        if not program:
            program = Program(
                program_id=program_id,
                name=name,
                code=code,
                department=dept,
                degree_level=degree_level,
                duration_years=duration,
                total_credits=credits_,
                status=ProgramStatus.ACTIVE,
                description=f"{degree_level.value} degree program in {name} offering {credits_} credit curriculum."
            )
            db.add(program)
            db.flush()
            print(f"   Created Program: {program_id} ({code}) - {name}")
        program_entities.append(program)
    return program_entities


def seed_terms(db: Session):
    print("-> Seeding Academic Terms...")
    term_entities = []
    for name, year, semester, start_date, end_date in TERMS_CATALOG:
        term_id = f"TERM-{year}-{semester.value}"
        term = db.query(Term).filter(Term.term_id == term_id).first()
        if not term:
            term = Term(
                term_id=term_id,
                name=name,
                year=year,
                semester=semester,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            db.add(term)
            db.flush()
            print(f"   Created Term: {term_id} - {name}")
        term_entities.append(term)
    return term_entities


def seed_fee_schedules(db: Session, programs, terms):
    print("-> Seeding Program-Specific Fee Schedules...")
    fee_schedule_count = 0
    seq = 0
    for program in programs:
        for term in terms:
            seq += 1
            fee_schedule_id = f"FEE-{seq:06d}"
            existing = db.query(FeeSchedule).filter(
                FeeSchedule.program_id == program.id,
                FeeSchedule.term_id == term.id
            ).first()
            if not existing:
                # Differentiate tuition by degree level and department
                if program.degree_level == DegreeLevel.DOCTORATE:
                    tuition = Decimal("125000.00")
                    lab_fee = Decimal("25000.00")
                elif program.degree_level == DegreeLevel.MASTER:
                    tuition = Decimal("95000.00")
                    lab_fee = Decimal("18000.00") if "Computing" in program.department or "Electrical" in program.department else Decimal("10000.00")
                elif program.degree_level == DegreeLevel.DIPLOMA:
                    tuition = Decimal("35000.00")
                    lab_fee = Decimal("8000.00")
                else:  # BACHELOR
                    tuition = Decimal("75000.00")
                    lab_fee = Decimal("15000.00") if "Computing" in program.department or "Mechanical" in program.department or "Bio" in program.department else Decimal("5000.00")

                reg_fee = Decimal("5000.00")
                exam_fee = Decimal("4000.00")
                lib_fee = Decimal("3000.00")
                other_fee = Decimal("2000.00")

                fee_schedule = FeeSchedule(
                    fee_schedule_id=fee_schedule_id,
                    program_id=program.id,
                    term_id=term.id,
                    tuition_fee=tuition,
                    registration_fee=reg_fee,
                    laboratory_fee=lab_fee,
                    examination_fee=exam_fee,
                    library_fee=lib_fee,
                    other_charges=other_fee,
                    currency="INR",
                    effective_start_date=term.start_date,
                    effective_end_date=term.end_date,
                    is_active=True
                )
                db.add(fee_schedule)
                fee_schedule_count += 1
    db.flush()
    print(f"   Created {fee_schedule_count} fee schedule configurations.")


def run_seed():
    db = SessionLocal()
    try:
        print("==================================================")
        print("Starting Idempotent Database Seed Operation")
        print("==================================================")
        seed_roles_and_users(db)
        programs = seed_programs(db)
        terms = seed_terms(db)
        seed_fee_schedules(db, programs, terms)
        db.commit()
        print("==================================================")
        print("Database Seed Completed Successfully!")
        print("==================================================")
        print("\nDemo Credentials:")
        print("  Platform Admin:      admin           / Admin@2026Secure")
        print("  Academic Admin:      academic_admin  / Academic@2026Secure")
        print("  Support Staff:       support_staff   / Support@2026Secure")
        print("  Instructor:          instructor      / Faculty@2026Secure")
        print("  Learner:             learner         / Student@2026Secure")
        print("==================================================")
    except Exception as e:
        db.rollback()
        print(f"ERROR during database seed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

