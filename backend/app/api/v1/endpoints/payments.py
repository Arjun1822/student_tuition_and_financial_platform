from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.payment import PaymentStatus, PaymentMethod
from app.api.dependencies import get_current_active_user, require_permissions
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentAllocateRequest,
    PaymentReverseRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.payment_service import PaymentService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PaymentResponse])
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    status_filter: Optional[PaymentStatus] = Query(None, alias="status"),
    payment_method: Optional[PaymentMethod] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = PaymentRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(
        student_id=student_id,
        status=status_filter,
        payment_method=payment_method,
        skip=skip,
        limit=page_size
    )
    total = repo.count_filtered(
        student_id=student_id,
        status=status_filter,
        payment_method=payment_method
    )

    resp_items = []
    for item in items:
        resp = PaymentResponse.model_validate(item)
        if item.student:
            resp.student_name = item.student.full_name
            resp.student_business_id = item.student.student_id
        resp_items.append(resp)

    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=resp_items, total=total, page=page, page_size=page_size, pages=pages)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["PAYMENT_RECORD", "ADMIN_ACCESS"]))
):
    service = PaymentService(db)
    payment = service.record_payment(payment_in, actor_id=current_user.id)
    resp = PaymentResponse.model_validate(payment)
    if payment.student:
        resp.student_name = payment.student.full_name
        resp.student_business_id = payment.student.student_id
    return resp


@router.get("/{id_or_slug}", response_model=PaymentResponse)
def get_payment(
    id_or_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = PaymentRepository(db)
    if id_or_slug.isdigit():
        payment = repo.get_by_id_with_relations(int(id_or_slug))
    else:
        payment = repo.get_by_payment_id(id_or_slug)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment '{id_or_slug}' not found.")

    resp = PaymentResponse.model_validate(payment)
    if payment.student:
        resp.student_name = payment.student.full_name
        resp.student_business_id = payment.student.student_id
    return resp


@router.post("/{id}/allocate", response_model=PaymentResponse)
def allocate_payment(
    id: int,
    req: PaymentAllocateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["PAYMENT_ALLOCATE", "ADMIN_ACCESS"]))
):
    service = PaymentService(db)
    payment = service.allocate_payment(
        payment_id=id,
        allocations=req.allocations,
        auto_allocate=req.auto_allocate,
        target_invoice_id=req.invoice_id,
        actor_id=current_user.id
    )
    resp = PaymentResponse.model_validate(payment)
    if payment.student:
        resp.student_name = payment.student.full_name
        resp.student_business_id = payment.student.student_id
    return resp


@router.post("/{id}/reverse", response_model=PaymentResponse)
def reverse_payment(
    id: int,
    req: PaymentReverseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["PAYMENT_REVERSE", "ADMIN_ACCESS"]))
):
    service = PaymentService(db)
    payment = service.reverse_payment(
        payment_id=id,
        reason=req.reason,
        actor_id=current_user.id
    )
    resp = PaymentResponse.model_validate(payment)
    if payment.student:
        resp.student_name = payment.student.full_name
        resp.student_business_id = payment.student.student_id
    return resp

