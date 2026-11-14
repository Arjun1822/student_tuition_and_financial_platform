import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_any_role, UserRole
from app.api.dependencies import get_current_user, PaginationParams
from app.models.student import Student, StudentStatus
from app.models.user import User
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
)
from app.repositories.student_repository import StudentRepository
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=StudentListResponse, summary="List students with search and pagination")
@router.get("", response_model=StudentListResponse, include_in_schema=False)
def list_students(
    search: Optional[str] = Query(None, description="Search by name, email, or student ID"),
    status_filter: Optional[StudentStatus] = Query(None, alias="status", description="Filter by status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = StudentRepository(db)
    items, total = repo.search_students(
        query_str=search,
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


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, summary="Create student")
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = StudentRepository(db)
    existing = repo.get_by_email(student_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with email '{student_in.email}' already exists."
        )

    student_id_str = repo.get_next_sequence_id()
    student = Student(
        student_id=student_id_str,
        first_name=student_in.first_name,
        last_name=student_in.last_name,
        email=student_in.email,
        phone=student_in.phone,
        date_of_birth=student_in.date_of_birth,
        address=student_in.address,
        city=student_in.city,
        state=student_in.state,
        country=student_in.country,
        postal_code=student_in.postal_code,
        family_income_category=student_in.family_income_category,
        gpa=student_in.gpa,
        status=student_in.status
    )
    repo.create(student)
    
    # Audit log
    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="CREATE_STUDENT",
        entity_type="STUDENT",
        entity_id=student.student_id,
        new_values={"email": student.email, "name": student.full_name}
    )
    
    db.commit()
    db.refresh(student)
    return student


@router.get("/{id_or_slug}", response_model=StudentResponse, summary="Get student by ID, student_id, or email")
def get_student(
    id_or_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = StudentRepository(db)
    if id_or_slug.isdigit():
        student = repo.get_by_id(int(id_or_slug))
    else:
        student = repo.get_by_student_id(id_or_slug) or repo.get_by_email(id_or_slug)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{id_or_slug}' not found."
        )
    return student


@router.put("/{id_or_slug}", response_model=StudentResponse, summary="Update student")
def update_student(
    id_or_slug: str,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = StudentRepository(db)
    if id_or_slug.isdigit():
        student = repo.get_by_id(int(id_or_slug))
    else:
        student = repo.get_by_student_id(id_or_slug) or repo.get_by_email(id_or_slug)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{id_or_slug}' not found."
        )

    if student_in.email and student_in.email != student.email:
        existing = repo.get_by_email(student_in.email)
        if existing and existing.id != student.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{student_in.email}' is already in use by another student."
            )

    update_data = student_in.model_dump(exclude_unset=True)
    old_data = {k: getattr(student, k) for k in update_data.keys()}

    for field, value in update_data.items():
        setattr(student, field, value)

    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="UPDATE_STUDENT",
        entity_type="STUDENT",
        entity_id=student.student_id,
        old_values=old_data,
        new_values=update_data
    )

    db.commit()
    db.refresh(student)
    return student
