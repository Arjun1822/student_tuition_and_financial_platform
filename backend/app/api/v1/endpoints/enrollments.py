from datetime import date
import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_any_role, UserRole
from app.api.dependencies import get_current_user, PaginationParams
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.student import Student
from app.models.program import Program
from app.models.term import Term
from app.models.user import User
from app.models.financial_event import FinancialEventType
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentActionRequest,
    EnrollmentResponse,
    EnrollmentListResponse,
)
from app.repositories.enrollment_repository import EnrollmentRepository
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=EnrollmentListResponse, summary="List enrollments with filters and pagination")
def list_enrollments(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    program_id: Optional[int] = Query(None, description="Filter by program ID"),
    term_id: Optional[int] = Query(None, description="Filter by term ID"),
    status_filter: Optional[EnrollmentStatus] = Query(None, alias="status", description="Filter by status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = EnrollmentRepository(db)
    items, total = repo.filter_enrollments(
        student_id=student_id,
        program_id=program_id,
        term_id=term_id,
        status=status_filter,
        skip=pagination.skip,
        limit=pagination.limit
    )
    pages = math.ceil(total / pagination.page_size) if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages
    }


@router.post("/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED, summary="Create student enrollment")
def create_enrollment(
    enrollment_in: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    # 1. Validate student exists
    student = db.query(Student).filter(Student.id == enrollment_in.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {enrollment_in.student_id} not found."
        )

    # 2. Validate program exists
    program = db.query(Program).filter(Program.id == enrollment_in.program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program with ID {enrollment_in.program_id} not found."
        )

    # 3. Validate term exists
    term = db.query(Term).filter(Term.id == enrollment_in.term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Term with ID {enrollment_in.term_id} not found."
        )

    # 4. Check for duplicate active/existing enrollment
    repo = EnrollmentRepository(db)
    existing = repo.get_by_student_program_term(
        student_id=enrollment_in.student_id,
        program_id=enrollment_in.program_id,
        term_id=enrollment_in.term_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Student '{student.student_id}' is already enrolled in "
                f"program '{program.code}' for term '{term.term_id}' (Status: {existing.status.value})."
            )
        )

    enrollment_id_str = repo.get_next_sequence_id()
    enrollment = Enrollment(
        enrollment_id=enrollment_id_str,
        student_id=enrollment_in.student_id,
        program_id=enrollment_in.program_id,
        term_id=enrollment_in.term_id,
        enrollment_date=enrollment_in.enrollment_date or date.today(),
        status=EnrollmentStatus.ACTIVE
    )
    repo.create(enrollment)

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="CREATE_ENROLLMENT",
        entity_type="ENROLLMENT",
        entity_id=enrollment.enrollment_id,
        new_values={
            "student": student.student_id,
            "program": program.code,
            "term": term.term_id
        }
    )

    db.commit()
    return repo.get_with_relations(enrollment.id)


@router.get("/{id_or_enr_id}", response_model=EnrollmentResponse, summary="Get enrollment by ID")
def get_enrollment(
    id_or_enr_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = EnrollmentRepository(db)
    if id_or_enr_id.isdigit():
        enrollment = repo.get_with_relations(int(id_or_enr_id))
    else:
        enrollment = repo.get_by_business_id(id_or_enr_id)

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment '{id_or_enr_id}' not found."
        )
    return enrollment


@router.post("/{id}/cancel", response_model=EnrollmentResponse, summary="Cancel enrollment")
def cancel_enrollment(
    id: int,
    action: EnrollmentActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = EnrollmentRepository(db)
    enrollment = repo.get_with_relations(id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment with ID {id} not found."
        )

    if enrollment.status in (EnrollmentStatus.CANCELLED, EnrollmentStatus.WITHDRAWN, EnrollmentStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel enrollment in terminal state '{enrollment.status.value}'."
        )

    prev_state = enrollment.status.value
    enrollment.status = EnrollmentStatus.CANCELLED
    enrollment.cancellation_date = date.today()
    enrollment.cancellation_reason = action.reason

    audit_service = AuditService(db)
    audit_service.log_financial_event(
        entity_type="ENROLLMENT",
        entity_id=enrollment.enrollment_id,
        event_type=FinancialEventType.ENROLLMENT_CANCELLED,
        previous_state=prev_state,
        new_state=EnrollmentStatus.CANCELLED.value,
        actor_id=current_user.id,
        reference_id=str(enrollment.id),
        metadata={"reason": action.reason}
    )

    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.post("/{id}/withdraw", response_model=EnrollmentResponse, summary="Withdraw student from term")
def withdraw_enrollment(
    id: int,
    action: EnrollmentActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = EnrollmentRepository(db)
    enrollment = repo.get_with_relations(id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment with ID {id} not found."
        )

    if enrollment.status != EnrollmentStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only ACTIVE enrollments can be withdrawn. Current state: '{enrollment.status.value}'."
        )

    prev_state = enrollment.status.value
    enrollment.status = EnrollmentStatus.WITHDRAWN
    enrollment.withdrawal_date = date.today()
    enrollment.withdrawal_reason = action.reason

    audit_service = AuditService(db)
    audit_service.log_financial_event(
        entity_type="ENROLLMENT",
        entity_id=enrollment.enrollment_id,
        event_type=FinancialEventType.STUDENT_WITHDRAWN,
        previous_state=prev_state,
        new_state=EnrollmentStatus.WITHDRAWN.value,
        actor_id=current_user.id,
        reference_id=str(enrollment.id),
        metadata={"reason": action.reason}
    )

    db.commit()
    db.refresh(enrollment)
    return enrollment

