import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_any_role, UserRole
from app.api.dependencies import get_current_user, PaginationParams
from app.models.fee_schedule import FeeSchedule
from app.models.program import Program
from app.models.term import Term
from app.models.user import User
from app.schemas.fee_schedule import (
    FeeScheduleCreate,
    FeeScheduleUpdate,
    FeeScheduleResponse,
    FeeScheduleListResponse,
)
from app.repositories.fee_schedule_repository import FeeScheduleRepository
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=FeeScheduleListResponse, summary="List program fee schedules")
def list_fee_schedules(
    program_id: Optional[int] = Query(None, description="Filter by program ID"),
    term_id: Optional[int] = Query(None, description="Filter by term ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = FeeScheduleRepository(db)
    items, total = repo.filter_fee_schedules(
        program_id=program_id,
        term_id=term_id,
        is_active=is_active,
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


@router.post("/", response_model=FeeScheduleResponse, status_code=status.HTTP_201_CREATED, summary="Create fee schedule")
def create_fee_schedule(
    fee_in: FeeScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    # 1. Validate Program exists
    program = db.query(Program).filter(Program.id == fee_in.program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program with ID {fee_in.program_id} not found."
        )

    # 2. Validate Term exists
    term = db.query(Term).filter(Term.id == fee_in.term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Term with ID {fee_in.term_id} not found."
        )

    # 3. Check effective date ordering
    if fee_in.effective_start_date >= fee_in.effective_end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="effective_start_date must be strictly before effective_end_date."
        )

    # 4. Prevent conflicting fee schedule for same program and term
    repo = FeeScheduleRepository(db)
    existing = repo.get_by_program_and_term(fee_in.program_id, fee_in.term_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A fee schedule already exists for Program '{program.code}' in Term '{term.term_id}'."
        )

    fee_schedule_id = repo.get_next_sequence_id()
    fee_schedule = FeeSchedule(
        fee_schedule_id=fee_schedule_id,
        program_id=fee_in.program_id,
        term_id=fee_in.term_id,
        tuition_fee=fee_in.tuition_fee,
        registration_fee=fee_in.registration_fee,
        laboratory_fee=fee_in.laboratory_fee,
        examination_fee=fee_in.examination_fee,
        library_fee=fee_in.library_fee,
        other_charges=fee_in.other_charges,
        currency=fee_in.currency,
        effective_start_date=fee_in.effective_start_date,
        effective_end_date=fee_in.effective_end_date,
        is_active=fee_in.is_active
    )
    repo.create(fee_schedule)

    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="CREATE_FEE_SCHEDULE",
        entity_type="FEE_SCHEDULE",
        entity_id=fee_schedule.fee_schedule_id,
        new_values={"program": program.code, "term": term.term_id, "total": str(fee_schedule.total_fee)}
    )

    db.commit()
    db.refresh(fee_schedule)
    return fee_schedule


@router.get("/{id}", response_model=FeeScheduleResponse, summary="Get fee schedule by ID")
def get_fee_schedule(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = FeeScheduleRepository(db)
    schedule = repo.get_by_id(id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee schedule {id} not found."
        )
    return schedule


@router.put("/{id}", response_model=FeeScheduleResponse, summary="Update fee schedule")
def update_fee_schedule(
    id: int,
    fee_in: FeeScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = FeeScheduleRepository(db)
    schedule = repo.get_by_id(id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee schedule {id} not found."
        )

    update_data = fee_in.model_dump(exclude_unset=True)
    if "effective_start_date" in update_data and "effective_end_date" in update_data:
        if update_data["effective_start_date"] >= update_data["effective_end_date"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="effective_start_date must be strictly before effective_end_date."
            )

    old_data = {k: str(getattr(schedule, k)) for k in update_data.keys()}
    for k, v in update_data.items():
        setattr(schedule, k, v)

    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="UPDATE_FEE_SCHEDULE",
        entity_type="FEE_SCHEDULE",
        entity_id=schedule.fee_schedule_id,
        old_values=old_data,
        new_values={k: str(v) for k, v in update_data.items()}
    )

    db.commit()
    db.refresh(schedule)
    return schedule

