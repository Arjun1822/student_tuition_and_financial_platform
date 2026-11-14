import enum
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SemesterEnum(str, enum.Enum):
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    FALL = "FALL"
    WINTER = "WINTER"


class Term(Base):
    __tablename__ = "terms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    term_id = Column(String(50), unique=True, nullable=False, index=True)  # TERM-2026-FALL
    name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False, index=True)
    semester = Column(SAEnum(SemesterEnum), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("year", "semester", name="uq_term_year_semester"),
    )

    # Relationships
    fee_schedules = relationship("FeeSchedule", back_populates="term")
    enrollments = relationship("Enrollment", back_populates="term")
    invoices = relationship("Invoice", back_populates="term")

    def __repr__(self):
        return f"<Term(id={self.id}, term_id='{self.term_id}', name='{self.name}')>"
