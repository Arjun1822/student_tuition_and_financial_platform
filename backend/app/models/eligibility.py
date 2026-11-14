import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class EligibilityStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class Eligibility(Base):
    __tablename__ = "eligibilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    eligibility_id = Column(String(50), unique=True, nullable=False, index=True)  # ELIG-000001
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    scholarship_id = Column(Integer, ForeignKey("scholarships.id", ondelete="RESTRICT"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    evaluation_date = Column(DateTime, server_default=func.now(), nullable=False)
    eligible_fee_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    scholarship_percentage = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    calculated_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    approved_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    
    status = Column(SAEnum(EligibilityStatus), nullable=False, default=EligibilityStatus.PENDING, index=True)
    decision_reason = Column(Text, nullable=False)
    criteria_version = Column(String(50), nullable=False, default="1.0")
    
    evaluated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="eligibilities")
    scholarship = relationship("Scholarship", back_populates="eligibilities")
    enrollment = relationship("Enrollment", back_populates="eligibilities")
    evaluator = relationship("User", foreign_keys=[evaluated_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<Eligibility(id={self.id}, eligibility_id='{self.eligibility_id}', status='{self.status}', approved={self.approved_amount})>"
