import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RefundStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    refund_id = Column(String(50), unique=True, nullable=False, index=True)  # REF-2026-000001
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    reason = Column(Text, nullable=False)
    status = Column(SAEnum(RefundStatus), nullable=False, default=RefundStatus.REQUESTED, index=True)
    
    requested_date = Column(DateTime, server_default=func.now(), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_date = Column(DateTime, nullable=True)
    processed_date = Column(DateTime, nullable=True)
    
    reference_number = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    student = relationship("Student", back_populates="refunds")
    invoice = relationship("Invoice", back_populates="refunds")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<Refund(id={self.id}, refund_id='{self.refund_id}', amount={self.amount}, status='{self.status}')>"
