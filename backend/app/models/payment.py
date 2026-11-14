import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    UPI = "UPI"
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    ONLINE = "ONLINE"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String(50), unique=True, nullable=False, index=True)  # PAY-2026-000001
    student_id = Column(Integer, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    amount = Column(DECIMAL(12, 2), nullable=False)
    allocated_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    unallocated_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    
    payment_date = Column(DateTime, server_default=func.now(), nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), nullable=False)
    reference_number = Column(String(100), nullable=True, index=True)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.COMPLETED, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="payments")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="payment")

    def __repr__(self):
        return f"<Payment(id={self.id}, payment_id='{self.payment_id}', amount={self.amount}, status='{self.status}')>"

