import enum
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class EnrollmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    WITHDRAWN = "WITHDRAWN"


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_id = Column(String(50), unique=True, nullable=False, index=True)  # ENR-000001
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False, index=True)
    term_id = Column(Integer, ForeignKey("terms.id", ondelete="RESTRICT"), nullable=False, index=True)
    enrollment_date = Column(Date, nullable=False)
    status = Column(SAEnum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.ACTIVE, index=True)
    
    # Cancellation & Withdrawal tracking
    cancellation_date = Column(Date, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    withdrawal_date = Column(Date, nullable=True)
    withdrawal_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "program_id", "term_id", name="uq_student_program_term_enrollment"),
    )

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    program = relationship("Program", back_populates="enrollments")
    term = relationship("Term", back_populates="enrollments")
    invoices = relationship("Invoice", back_populates="enrollment")
    eligibilities = relationship("Eligibility", back_populates="enrollment")

    def __repr__(self):
        return f"<Enrollment(id={self.id}, enrollment_id='{self.enrollment_id}', status='{self.status}')>"

