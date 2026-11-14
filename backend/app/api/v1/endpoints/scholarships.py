from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.scholarship import Scholarship, ScholarshipStatus, ScholarshipType
from app.api.dependencies import get_current_active_user, require_permissions
from app.repositories.scholarship_repository import ScholarshipRepository
from app.schemas.scholarship import (
    ScholarshipCreate,
    ScholarshipUpdate,
    ScholarshipResponse,
    ScholarshipEvaluateRequest,
)
from app.schemas.eligibility import EligibilityResponse
from app.schemas.common import PaginatedResponse
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService
from app.services.scholarship_eligibility_service import ScholarshipEligibilityService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ScholarshipResponse])
def list_scholarships(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scholarship_type: Optional[ScholarshipType] = None,
    status_filter: Optional[ScholarshipStatus] = Query(None, alias="status"),
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = ScholarshipRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(
        scholarship_type=scholarship_type,
        status=status_filter,
        academic_year=academic_year,
        skip=skip,
        limit=page_size
    )
    total = repo.count_filtered(
        scholarship_type=scholarship_type,
        status=status_filter,
        academic_year=academic_year
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.post("", response_model=ScholarshipResponse, status_code=status.HTTP_201_CREATED)
def create_scholarship(
    sch_in: ScholarshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["SCHOLARSHIP_CREATE", "ADMIN_ACCESS"]))
):
    current_year = datetime.now(timezone.utc).year
    count = db.query(func.count(Scholarship.id)).scalar() or 0
    b_id = IDGenerator.scholarship_id(current_year, count + 1)

    sch = Scholarship(
        scholarship_id=b_id,
        name=sch_in.name,
        description=sch_in.description,
        scholarship_type=sch_in.scholarship_type,
        percentage=sch_in.percentage,
        max_amount=sch_in.max_amount,
        min_gpa=sch_in.min_gpa,
        max_family_income_category=sch_in.max_family_income_category,
        eligible_programs=sch_in.eligible_programs,
        eligible_terms=sch_in.eligible_terms,
        total_budget=sch_in.total_budget,
        awarded_amount=0,
        status=ScholarshipStatus.ACTIVE,
        academic_year=sch_in.academic_year
    )
    db.add(sch)
    db.commit()
    db.refresh(sch)

    AuditService(db).log_action(
        actor_id=current_user.id,
        action="CREATE_SCHOLARSHIP",
        entity_type="SCHOLARSHIP",
        entity_id=sch.scholarship_id,
        new_values={"name": sch.name, "budget": str(sch.total_budget)}
    )
    return sch


@router.get("/{id_or_slug}", response_model=ScholarshipResponse)
def get_scholarship(
    id_or_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = ScholarshipRepository(db)
    if id_or_slug.isdigit():
        sch = repo.get(int(id_or_slug))
    else:
        sch = repo.get_by_scholarship_id(id_or_slug)
    if not sch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scholarship '{id_or_slug}' not found.")
    return sch


@router.put("/{id}", response_model=ScholarshipResponse)
def update_scholarship(
    id: int,
    sch_in: ScholarshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["SCHOLARSHIP_EDIT", "ADMIN_ACCESS"]))
):
    repo = ScholarshipRepository(db)
    sch = repo.get(id)
    if not sch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scholarship with ID {id} not found.")

    update_data = sch_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(sch, field, val)

    db.commit()
    db.refresh(sch)
    AuditService(db).log_action(
        actor_id=current_user.id,
        action="UPDATE_SCHOLARSHIP",
        entity_type="SCHOLARSHIP",
        entity_id=sch.scholarship_id,
        new_values={k: str(v) for k, v in update_data.items()}
    )
    return sch


@router.post("/evaluate", response_model=List[EligibilityResponse])
def evaluate_scholarships(
    req: ScholarshipEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["SCHOLARSHIP_EVALUATE", "ADMIN_ACCESS"]))
):
    service = ScholarshipEligibilityService(db)
    results = service.evaluate_student(
        student_id=req.student_id,
        term_id=req.term_id,
        scholarship_ids=req.scholarship_ids,
        actor_id=current_user.id
    )
    return results

