from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.eligibility import EligibilityStatus


class EligibilityBase(BaseModel):
    student_id: int
    scholarship_id: int
    enrollment_id: Optional[int] = None
    eligible_fee_amount: Decimal = Field(..., ge=0)
    scholarship_percentage: Decimal = Field(..., ge=0, le=100)
    calculated_amount: Decimal = Field(..., ge=0)
    decision_reason: str
    criteria_version: str = "1.0"


class EligibilityCreate(EligibilityBase):
    pass


class EligibilityApproveRequest(BaseModel):
    approved_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class EligibilityRejectRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class EligibilityResponse(EligibilityBase):
    id: int
    eligibility_id: str
    approved_amount: Decimal
    status: EligibilityStatus
    evaluation_date: datetime
    evaluated_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Display / nested names if joined
    student_name: Optional[str] = None
    student_business_id: Optional[str] = None
    scholarship_name: Optional[str] = None
    scholarship_business_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

