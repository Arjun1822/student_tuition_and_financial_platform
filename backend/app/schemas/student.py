from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.student import IncomeCategory, StudentStatus


class StudentBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: date
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: str = Field("India", max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    family_income_category: IncomeCategory = IncomeCategory.MEDIUM
    gpa: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("10.00"))
    status: StudentStatus = StudentStatus.ACTIVE


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    family_income_category: Optional[IncomeCategory] = None
    gpa: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("10.00"))
    status: Optional[StudentStatus] = None


class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: str
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class StudentListResponse(BaseModel):
    items: List[StudentResponse]
    total: int
    page: int
    page_size: int
    pages: int

