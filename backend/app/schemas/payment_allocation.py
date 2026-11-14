from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PaymentAllocationBase(BaseModel):
    payment_id: int
    invoice_line_id: int
    amount: Decimal = Field(..., gt=0)


class PaymentAllocationCreate(PaymentAllocationBase):
    pass


class PaymentAllocationResponse(PaymentAllocationBase):
    id: int
    allocation_id: str
    allocated_date: datetime
    created_at: datetime
    updated_at: datetime

    payment_business_id: Optional[str] = None
    invoice_id: Optional[int] = None
    invoice_business_id: Optional[str] = None
    fee_type: Optional[str] = None
    line_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

