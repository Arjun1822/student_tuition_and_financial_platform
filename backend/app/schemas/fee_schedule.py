from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.program import ProgramResponse
from app.schemas.term import TermResponse


class FeeScheduleBase(BaseModel):
    program_id: int
    term_id: int
    tuition_fee: Decimal = Field(..., ge=Decimal("0.00"))
    registration_fee: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    laboratory_fee: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    examination_fee: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    library_fee: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    other_charges: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = Field("INR", max_length=3)
    effective_start_date: date
    effective_end_date: date
    is_active: bool = True


class FeeScheduleCreate(FeeScheduleBase):
    pass


class FeeScheduleUpdate(BaseModel):
    tuition_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    registration_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    laboratory_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    examination_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    library_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    other_charges: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    is_active: Optional[bool] = None


class FeeScheduleResponse(FeeScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fee_schedule_id: str
    total_fee: Decimal
    program: Optional[ProgramResponse] = None
    term: Optional[TermResponse] = None
    created_at: datetime
    updated_at: datetime


class FeeScheduleListResponse(BaseModel):
    items: List[FeeScheduleResponse]
    total: int
    page: int
    page_size: int
    pages: int

