from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.refund import RefundStatus


class RefundCreate(BaseModel):
    payment_id: int
    student_id: int
    invoice_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=5)
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class RefundApproveRequest(BaseModel):
    notes: Optional[str] = None


class RefundRejectRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class RefundResponse(BaseModel):
    id: int
    refund_id: str
    payment_id: int
    student_id: int
    invoice_id: Optional[int] = None
    amount: Decimal
    currency: str = "INR"
    reason: str
    status: RefundStatus
    requested_date: datetime
    approved_by: Optional[int] = None
    approved_date: Optional[datetime] = None
    processed_date: Optional[datetime] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    student_name: Optional[str] = None
    student_business_id: Optional[str] = None
    payment_business_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

