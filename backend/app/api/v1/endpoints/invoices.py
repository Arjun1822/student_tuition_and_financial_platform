import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_any_role, UserRole
from app.api.dependencies import get_current_user, PaginationParams
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas.invoice import (
    InvoiceGenerateRequest,
    InvoiceCancelRequest,
    InvoiceResponse,
    InvoiceDetailResponse,
    InvoiceListResponse,
)
from app.repositories.invoice_repository import InvoiceRepository
from app.services.invoice_service import InvoiceService

router = APIRouter()


@router.get("/", response_model=InvoiceListResponse, summary="List invoices with filters and pagination")
@router.get("", response_model=InvoiceListResponse, include_in_schema=False)
def list_invoices(
    student_id: Optional[int] = Query(None, description="Filter by student database ID"),
    status_filter: Optional[InvoiceStatus] = Query(None, alias="status", description="Filter by invoice status"),
    billing_cycle: Optional[str] = Query(None, description="Filter by billing cycle, e.g. 2026-FALL"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = InvoiceRepository(db)
    items, total = repo.filter_invoices(
        student_id=student_id,
        status=status_filter,
        billing_cycle=billing_cycle,
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


@router.post("/generate", response_model=InvoiceDetailResponse, status_code=status.HTTP_201_CREATED, summary="Generate invoice from enrollment")
def generate_invoice(
    request: InvoiceGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    service = InvoiceService(db)
    invoice = service.generate_invoice_for_enrollment(
        enrollment_id=request.enrollment_id,
        due_date=request.due_date,
        notes=request.notes,
        actor_id=current_user.id
    )
    db.commit()
    repo = InvoiceRepository(db)
    return repo.get_with_details(invoice.id)


@router.get("/{id_or_invoice_id}", response_model=InvoiceDetailResponse, summary="Get invoice details with line items")
def get_invoice(
    id_or_invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = InvoiceRepository(db)
    if id_or_invoice_id.isdigit():
        invoice = repo.get_with_details(int(id_or_invoice_id))
    else:
        invoice = repo.get_by_invoice_id(id_or_invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{id_or_invoice_id}' not found."
        )
    return invoice


@router.post("/{id}/cancel", response_model=InvoiceDetailResponse, summary="Cancel invoice")
def cancel_invoice(
    id: int,
    request: InvoiceCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    service = InvoiceService(db)
    invoice = service.cancel_invoice(
        invoice_id=id,
        reason=request.reason,
        actor_id=current_user.id
    )
    db.commit()
    repo = InvoiceRepository(db)
    return repo.get_with_details(invoice.id)

