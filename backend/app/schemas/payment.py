from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.payment import PaymentMethod, PaymentStatus


class AllocationItemRequest(BaseModel):
    invoice_line_id: int
    amount: Decimal = Field(..., gt=0)


class PaymentAllocateRequest(BaseModel):
    allocations: Optional[List[AllocationItemRequest]] = None
    auto_allocate: bool = False
    invoice_id: Optional[int] = None


class PaymentReverseRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class PaymentBase(BaseModel):
    student_id: int
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    reference_number: Optional[str] = Field(None, max_length=100)
    currency: str = Field("INR", max_length=3)
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    auto_allocate: bool = False
    invoice_id: Optional[int] = None


class PaymentResponse(PaymentBase):
    id: int
    payment_id: str
    allocated_amount: Decimal
    unallocated_amount: Decimal
    payment_date: datetime
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    student_name: Optional[str] = None
    student_business_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

