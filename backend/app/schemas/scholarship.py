from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.scholarship import ScholarshipType, ScholarshipStatus


class ScholarshipBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    scholarship_type: ScholarshipType
    percentage: Decimal = Field(..., ge=0, le=100)
    max_amount: Decimal = Field(..., ge=0)
    min_gpa: Optional[Decimal] = Field(None, ge=0, le=10)
    max_family_income_category: Optional[str] = Field(None, max_length=50)
    eligible_programs: Optional[List[str]] = None
    eligible_terms: Optional[List[str]] = None
    total_budget: Decimal = Field(..., ge=0)
    academic_year: str = Field(..., max_length=20)


class ScholarshipCreate(ScholarshipBase):
    pass


class ScholarshipUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    scholarship_type: Optional[ScholarshipType] = None
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    min_gpa: Optional[Decimal] = Field(None, ge=0, le=10)
    max_family_income_category: Optional[str] = None
    eligible_programs: Optional[List[str]] = None
    eligible_terms: Optional[List[str]] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    status: Optional[ScholarshipStatus] = None
    academic_year: Optional[str] = None


class ScholarshipResponse(ScholarshipBase):
    id: int
    scholarship_id: str
    awarded_amount: Decimal
    remaining_budget: Decimal
    status: ScholarshipStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScholarshipEvaluateRequest(BaseModel):
    student_id: int
    term_id: int
    scholarship_ids: Optional[List[int]] = None

