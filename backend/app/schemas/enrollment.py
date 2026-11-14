from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enrollment import EnrollmentStatus
from app.schemas.student import StudentResponse
from app.schemas.program import ProgramResponse
from app.schemas.term import TermResponse


class EnrollmentCreate(BaseModel):
    student_id: int
    program_id: int
    term_id: int
    enrollment_date: Optional[date] = None


class EnrollmentActionRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for cancellation or withdrawal")


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enrollment_id: str
    student_id: int
    program_id: int
    term_id: int
    enrollment_date: date
    status: EnrollmentStatus
    cancellation_date: Optional[date] = None
    cancellation_reason: Optional[str] = None
    withdrawal_date: Optional[date] = None
    withdrawal_reason: Optional[str] = None
    student: Optional[StudentResponse] = None
    program: Optional[ProgramResponse] = None
    term: Optional[TermResponse] = None
    created_at: datetime
    updated_at: datetime


class EnrollmentListResponse(BaseModel):
    items: List[EnrollmentResponse]
    total: int
    page: int
    page_size: int
    pages: int

