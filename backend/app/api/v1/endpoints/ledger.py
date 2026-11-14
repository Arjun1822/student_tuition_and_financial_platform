from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.financial_event import FinancialEventType
from app.api.dependencies import get_current_active_user, require_permissions
from app.repositories.financial_event_repository import FinancialEventRepository
from app.schemas.financial_event import FinancialEventResponse
from app.schemas.balance import StudentBalanceStatement
from app.schemas.invoice import InvoiceResponse
from app.schemas.common import PaginatedResponse
from app.services.balance_service import BalanceCalculationService
from app.services.late_fee_service import LateFeeService

router = APIRouter()


class LateFeeAssessRequest(BaseModel):
    fixed_amount: Optional[Decimal] = None
    percentage_rate: Optional[Decimal] = None
    max_cap: Decimal = Decimal("2500.00")
    grace_days: int = 15


@router.get("/events", response_model=PaginatedResponse[FinancialEventResponse])
@router.get("/events/", response_model=PaginatedResponse[FinancialEventResponse], include_in_schema=False)
def list_financial_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[FinancialEventType] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = FinancialEventRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=page_size
    )
    total = repo.count_filtered(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/students/{student_id}/statement", response_model=StudentBalanceStatement)
def get_student_balance_statement(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = BalanceCalculationService(db)
    statement = service.calculate_student_balance(student_id)
    return statement


@router.post("/invoices/{invoice_id}/late-fee", response_model=InvoiceResponse)
def assess_late_fee(
    invoice_id: int,
    req: LateFeeAssessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["INVOICE_EDIT", "ADMIN_ACCESS"]))
):
    service = LateFeeService(db)
    invoice = service.assess_late_fee_for_invoice(
        invoice_id=invoice_id,
        fixed_amount=req.fixed_amount,
        percentage_rate=req.percentage_rate,
        max_cap=req.max_cap,
        grace_days=req.grace_days,
        actor_id=current_user.id
    )
    return invoice

