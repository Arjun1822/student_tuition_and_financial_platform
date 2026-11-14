import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FinancialEventType(str, enum.Enum):
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_ISSUED = "INVOICE_ISSUED"
    INVOICE_CANCELLED = "INVOICE_CANCELLED"
    SCHOLARSHIP_APPROVED = "SCHOLARSHIP_APPROVED"
    SCHOLARSHIP_REJECTED = "SCHOLARSHIP_REJECTED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_ALLOCATED = "PAYMENT_ALLOCATED"
    PAYMENT_REVERSED = "PAYMENT_REVERSED"
    LATE_FEE_ASSESSED = "LATE_FEE_ASSESSED"
    ENROLLMENT_CANCELLED = "ENROLLMENT_CANCELLED"
    STUDENT_WITHDRAWN = "STUDENT_WITHDRAWN"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUND_APPROVED = "REFUND_APPROVED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    RECONCILIATION_COMPLETED = "RECONCILIATION_COMPLETED"


class FinancialEvent(Base):
    __tablename__ = "financial_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)  # EVT-000001
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., INVOICE, PAYMENT, ENROLLMENT
    entity_id = Column(String(100), nullable=False, index=True)  # Business identifier of target entity
    event_type = Column(SAEnum(FinancialEventType), nullable=False, index=True)
    
    previous_state = Column(String(50), nullable=True)
    new_state = Column(String(50), nullable=True)
    event_timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reference_id = Column(String(100), nullable=True, index=True)
    
    amount = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), nullable=False, default="INR")
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Actor relationship
    actor = relationship("User", foreign_keys=[actor_id])

    def __repr__(self):
        return f"<FinancialEvent(id={self.id}, event_id='{self.event_id}', type='{self.event_type}', entity='{self.entity_id}')>"
