from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.invoice import InvoiceStatus
from app.models.invoice_line import FeeType
from app.schemas.student import StudentResponse
from app.schemas.term import TermResponse


class InvoiceGenerateRequest(BaseModel):
    enrollment_id: int
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)


class InvoiceLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_line_id: str
    fee_type: FeeType
    description: str
    amount: Decimal
    allocated_amount: Decimal
    remaining_amount: Decimal
    created_at: datetime


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: str
    enrollment_id: int
    student_id: int
    term_id: int
    invoice_date: date
    due_date: date
    gross_amount: Decimal
    scholarship_discount: Decimal
    net_amount: Decimal
    amount_paid: Decimal
    outstanding_balance: Decimal
    currency: str
    status: InvoiceStatus
    billing_cycle: str
    notes: Optional[str] = None
    student: Optional[StudentResponse] = None
    term: Optional[TermResponse] = None
    created_at: datetime
    updated_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    lines: List[InvoiceLineResponse] = []


class InvoiceListResponse(BaseModel):
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int

