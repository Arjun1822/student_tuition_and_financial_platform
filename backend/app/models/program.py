import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DegreeLevel(str, enum.Enum):
    CERTIFICATE = "CERTIFICATE"
    DIPLOMA = "DIPLOMA"
    BACHELOR = "BACHELOR"
    MASTER = "MASTER"
    DOCTORATE = "DOCTORATE"


class ProgramStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_id = Column(String(50), unique=True, nullable=False, index=True)  # PRG-000001
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    degree_level = Column(SAEnum(DegreeLevel), nullable=False, default=DegreeLevel.BACHELOR)
    duration_years = Column(Integer, nullable=False, default=4)
    total_credits = Column(Integer, nullable=False, default=120)
    status = Column(SAEnum(ProgramStatus), nullable=False, default=ProgramStatus.ACTIVE)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="program")
    fee_schedules = relationship("FeeSchedule", back_populates="program")

    def __repr__(self):
        return f"<Program(id={self.id}, program_id='{self.program_id}', code='{self.code}')>"

