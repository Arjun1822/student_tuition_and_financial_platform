import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_any_role, UserRole
from app.api.dependencies import get_current_user, PaginationParams
from app.models.program import Program, DegreeLevel, ProgramStatus
from app.models.user import User
from app.schemas.program import (
    ProgramCreate,
    ProgramUpdate,
    ProgramResponse,
    ProgramListResponse,
)
from app.repositories.program_repository import ProgramRepository
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=ProgramListResponse, summary="List academic programs")
def list_programs(
    department: Optional[str] = Query(None, description="Filter by department"),
    degree_level: Optional[DegreeLevel] = Query(None, description="Filter by degree level"),
    status_filter: Optional[ProgramStatus] = Query(None, alias="status", description="Filter by status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = ProgramRepository(db)
    items, total = repo.filter_programs(
        department=department,
        degree_level=degree_level,
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


@router.post("/", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED, summary="Create academic program")
def create_program(
    program_in: ProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = ProgramRepository(db)
    existing = repo.get_by_code(program_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Program with code '{program_in.code}' already exists."
        )

    program_id_str = repo.get_next_sequence_id()
    program = Program(
        program_id=program_id_str,
        name=program_in.name,
        code=program_in.code,
        department=program_in.department,
        degree_level=program_in.degree_level,
        duration_years=program_in.duration_years,
        total_credits=program_in.total_credits,
        status=program_in.status,
        description=program_in.description
    )
    repo.create(program)

    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="CREATE_PROGRAM",
        entity_type="PROGRAM",
        entity_id=program.program_id,
        new_values={"code": program.code, "name": program.name}
    )

    db.commit()
    db.refresh(program)
    return program


@router.get("/{id_or_code}", response_model=ProgramResponse, summary="Get program by ID or code")
def get_program(
    id_or_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = ProgramRepository(db)
    if id_or_code.isdigit():
        program = repo.get_by_id(int(id_or_code))
    else:
        program = repo.get_by_code(id_or_code) or repo.get_by_program_id(id_or_code)

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program '{id_or_code}' not found."
        )
    return program


@router.put("/{id_or_code}", response_model=ProgramResponse, summary="Update program")
def update_program(
    id_or_code: str,
    program_in: ProgramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = ProgramRepository(db)
    if id_or_code.isdigit():
        program = repo.get_by_id(int(id_or_code))
    else:
        program = repo.get_by_code(id_or_code) or repo.get_by_program_id(id_or_code)

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program '{id_or_code}' not found."
        )

    if program_in.code and program_in.code != program.code:
        existing = repo.get_by_code(program_in.code)
        if existing and existing.id != program.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Program code '{program_in.code}' already exists."
            )

    update_data = program_in.model_dump(exclude_unset=True)
    old_data = {k: getattr(program, k) for k in update_data.keys()}

    for field, value in update_data.items():
        setattr(program, field, value)

    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="UPDATE_PROGRAM",
        entity_type="PROGRAM",
        entity_id=program.program_id,
        old_values=old_data,
        new_values=update_data
    )

    db.commit()
    db.refresh(program)
    return program

