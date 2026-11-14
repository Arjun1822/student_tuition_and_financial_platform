from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.program import DegreeLevel, ProgramStatus


class ProgramBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    department: str = Field(..., min_length=2, max_length=100)
    degree_level: DegreeLevel = DegreeLevel.BACHELOR
    duration_years: int = Field(4, ge=1, le=8)
    total_credits: int = Field(120, ge=10, le=300)
    status: ProgramStatus = ProgramStatus.ACTIVE
    description: Optional[str] = None


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    degree_level: Optional[DegreeLevel] = None
    duration_years: Optional[int] = Field(None, ge=1, le=8)
    total_credits: Optional[int] = Field(None, ge=10, le=300)
    status: Optional[ProgramStatus] = None
    description: Optional[str] = None


class ProgramResponse(ProgramBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: str
    created_at: datetime
    updated_at: datetime


class ProgramListResponse(BaseModel):
    items: List[ProgramResponse]
    total: int
    page: int
    page_size: int
    pages: int

