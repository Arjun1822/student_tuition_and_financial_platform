from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.refund import RefundStatus
from app.api.dependencies import get_current_active_user, require_permissions
from app.repositories.refund_repository import RefundRepository
from app.schemas.refund import (
    RefundCreate,
    RefundApproveRequest,
    RefundRejectRequest,
    RefundResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.refund_service import RefundService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[RefundResponse])
def list_refunds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    payment_id: Optional[int] = None,
    status_filter: Optional[RefundStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = RefundRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(
        student_id=student_id,
        payment_id=payment_id,
        status=status_filter,
        skip=skip,
        limit=page_size
    )
    total = repo.count_filtered(
        student_id=student_id,
        payment_id=payment_id,
        status=status_filter
    )

    resp_items = []
    for item in items:
        resp = RefundResponse.model_validate(item)
        if item.student:
            resp.student_name = item.student.full_name
            resp.student_business_id = item.student.student_id
        if item.payment:
            resp.payment_business_id = item.payment.payment_id
        resp_items.append(resp)

    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=resp_items, total=total, page=page, page_size=page_size, pages=pages)


@router.post("", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def request_refund(
    refund_in: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["REFUND_REQUEST", "ADMIN_ACCESS"]))
):
    service = RefundService(db)
    refund = service.request_refund(refund_in, actor_id=current_user.id)
    resp = RefundResponse.model_validate(refund)
    if refund.student:
        resp.student_name = refund.student.full_name
        resp.student_business_id = refund.student.student_id
    if refund.payment:
        resp.payment_business_id = refund.payment.payment_id
    return resp


@router.get("/{id_or_slug}", response_model=RefundResponse)
def get_refund(
    id_or_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = RefundRepository(db)
    if id_or_slug.isdigit():
        refund = repo.get_by_id_with_relations(int(id_or_slug))
    else:
        refund = repo.get_by_refund_id(id_or_slug)
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Refund '{id_or_slug}' not found.")

    resp = RefundResponse.model_validate(refund)
    if refund.student:
        resp.student_name = refund.student.full_name
        resp.student_business_id = refund.student.student_id
    if refund.payment:
        resp.payment_business_id = refund.payment.payment_id
    return resp


@router.post("/{id}/approve", response_model=RefundResponse)
def approve_refund(
    id: int,
    req: RefundApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["REFUND_APPROVE", "ADMIN_ACCESS"]))
):
    service = RefundService(db)
    refund = service.approve_refund(refund_id=id, notes=req.notes, actor_id=current_user.id)
    resp = RefundResponse.model_validate(refund)
    if refund.student:
        resp.student_name = refund.student.full_name
        resp.student_business_id = refund.student.student_id
    if refund.payment:
        resp.payment_business_id = refund.payment.payment_id
    return resp


@router.post("/{id}/process", response_model=RefundResponse)
def process_refund(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["REFUND_PROCESS", "ADMIN_ACCESS"]))
):
    service = RefundService(db)
    refund = service.process_refund(refund_id=id, actor_id=current_user.id)
    resp = RefundResponse.model_validate(refund)
    if refund.student:
        resp.student_name = refund.student.full_name
        resp.student_business_id = refund.student.student_id
    if refund.payment:
        resp.payment_business_id = refund.payment.payment_id
    return resp


@router.post("/{id}/reject", response_model=RefundResponse)
def reject_refund(
    id: int,
    req: RefundRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["REFUND_APPROVE", "ADMIN_ACCESS"]))
):
    service = RefundService(db)
    refund = service.reject_refund(refund_id=id, reason=req.reason, actor_id=current_user.id)
    resp = RefundResponse.model_validate(refund)
    if refund.student:
        resp.student_name = refund.student.full_name
        resp.student_business_id = refund.student.student_id
    if refund.payment:
        resp.payment_business_id = refund.payment.payment_id
    return resp

