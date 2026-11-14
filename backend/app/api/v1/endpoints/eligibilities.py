from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.eligibility import EligibilityStatus
from app.api.dependencies import get_current_active_user, require_permissions
from app.repositories.eligibility_repository import EligibilityRepository
from app.schemas.eligibility import (
    EligibilityResponse,
    EligibilityApproveRequest,
    EligibilityRejectRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.scholarship_eligibility_service import ScholarshipEligibilityService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EligibilityResponse])
def list_eligibilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    scholarship_id: Optional[int] = None,
    status_filter: Optional[EligibilityStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = EligibilityRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(
        student_id=student_id,
        scholarship_id=scholarship_id,
        status=status_filter,
        skip=skip,
        limit=page_size
    )
    total = repo.count_filtered(
        student_id=student_id,
        scholarship_id=scholarship_id,
        status=status_filter
    )

    # Populate nested names
    resp_items = []
    for item in items:
        resp = EligibilityResponse.model_validate(item)
        if item.student:
            resp.student_name = item.student.full_name
            resp.student_business_id = item.student.student_id
        if item.scholarship:
            resp.scholarship_name = item.scholarship.name
            resp.scholarship_business_id = item.scholarship.scholarship_id
        resp_items.append(resp)

    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=resp_items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{id_or_slug}", response_model=EligibilityResponse)
def get_eligibility(
    id_or_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = EligibilityRepository(db)
    if id_or_slug.isdigit():
        elig = repo.get_by_id_with_relations(int(id_or_slug))
    else:
        elig = repo.get_by_eligibility_id(id_or_slug)
    if not elig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Eligibility '{id_or_slug}' not found.")

    resp = EligibilityResponse.model_validate(elig)
    if elig.student:
        resp.student_name = elig.student.full_name
        resp.student_business_id = elig.student.student_id
    if elig.scholarship:
        resp.scholarship_name = elig.scholarship.name
        resp.scholarship_business_id = elig.scholarship.scholarship_id
    return resp


@router.post("/{id}/approve", response_model=EligibilityResponse)
def approve_eligibility(
    id: int,
    req: EligibilityApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["SCHOLARSHIP_APPROVE", "ADMIN_ACCESS"]))
):
    service = ScholarshipEligibilityService(db)
    elig = service.approve_eligibility(
        eligibility_id=id,
        approved_amount=req.approved_amount,
        notes=req.notes,
        actor_id=current_user.id
    )
    resp = EligibilityResponse.model_validate(elig)
    if elig.student:
        resp.student_name = elig.student.full_name
        resp.student_business_id = elig.student.student_id
    if elig.scholarship:
        resp.scholarship_name = elig.scholarship.name
        resp.scholarship_business_id = elig.scholarship.scholarship_id
    return resp


@router.post("/{id}/reject", response_model=EligibilityResponse)
def reject_eligibility(
    id: int,
    req: EligibilityRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["SCHOLARSHIP_APPROVE", "ADMIN_ACCESS"]))
):
    service = ScholarshipEligibilityService(db)
    elig = service.reject_eligibility(
        eligibility_id=id,
        reason=req.reason,
        actor_id=current_user.id
    )
    resp = EligibilityResponse.model_validate(elig)
    if elig.student:
        resp.student_name = elig.student.full_name
        resp.student_business_id = elig.student.student_id
    if elig.scholarship:
        resp.scholarship_name = elig.scholarship.name
        resp.scholarship_business_id = elig.scholarship.scholarship_id
    return resp

