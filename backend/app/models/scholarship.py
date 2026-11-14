import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ScholarshipType(str, enum.Enum):
    MERIT = "MERIT"
    NEED_BASED = "NEED_BASED"
    PROGRAM_SPECIFIC = "PROGRAM_SPECIFIC"
    ATHLETIC = "ATHLETIC"
    SPECIAL = "SPECIAL"


class ScholarshipStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXHAUSTED = "EXHAUSTED"


class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scholarship_id = Column(String(50), unique=True, nullable=False, index=True)  # SCH-2026-000001
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scholarship_type = Column(SAEnum(ScholarshipType), nullable=False, index=True)
    
    # Financial terms
    percentage = Column(DECIMAL(5, 2), nullable=False)  # e.g., 50.00 for 50%
    max_amount = Column(DECIMAL(12, 2), nullable=False)  # Cap on total award
    min_gpa = Column(DECIMAL(4, 2), nullable=True)
    max_family_income_category = Column(String(50), nullable=True)
    
    # Filter constraints stored as JSON lists
    eligible_programs = Column(JSON, nullable=True)  # list of program codes or IDs
    eligible_terms = Column(JSON, nullable=True)  # list of term IDs
    
    total_budget = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    awarded_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    status = Column(SAEnum(ScholarshipStatus), nullable=False, default=ScholarshipStatus.ACTIVE)
    academic_year = Column(String(20), nullable=False, index=True)  # e.g., "2026-2027"

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    eligibilities = relationship("Eligibility", back_populates="scholarship", cascade="all, delete-orphan")

    @property
    def remaining_budget(self):
        return self.total_budget - self.awarded_amount

    def __repr__(self):
        return f"<Scholarship(id={self.id}, scholarship_id='{self.scholarship_id}', name='{self.name}')>"

