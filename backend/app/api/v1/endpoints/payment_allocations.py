from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_active_user
from app.repositories.payment_allocation_repository import PaymentAllocationRepository
from app.schemas.payment_allocation import PaymentAllocationResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PaymentAllocationResponse])
@router.get("/", response_model=PaginatedResponse[PaymentAllocationResponse], include_in_schema=False)
def list_payment_allocations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    payment_id: Optional[int] = None,
    invoice_line_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = PaymentAllocationRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(
        payment_id=payment_id,
        invoice_line_id=invoice_line_id,
        skip=skip,
        limit=page_size
    )
    total = repo.count_filtered(
        payment_id=payment_id,
        invoice_line_id=invoice_line_id
    )

    resp_items = []
    for item in items:
        resp = PaymentAllocationResponse.model_validate(item)
        if item.payment:
            resp.payment_business_id = item.payment.payment_id
        if item.invoice_line:
            resp.fee_type = item.invoice_line.fee_type.value
            resp.line_description = item.invoice_line.description
            if item.invoice_line.invoice:
                resp.invoice_id = item.invoice_line.invoice.id
                resp.invoice_business_id = item.invoice_line.invoice.invoice_id
        resp_items.append(resp)

    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=resp_items, total=total, page=page, page_size=page_size, pages=pages)

