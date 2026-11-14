from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.term import SemesterEnum


class TermBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    year: int = Field(..., ge=2000, le=2100)
    semester: SemesterEnum
    start_date: date
    end_date: date
    is_active: bool = True


class TermCreate(TermBase):
    pass


class TermUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TermResponse(TermBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term_id: str
    created_at: datetime
    updated_at: datetime

