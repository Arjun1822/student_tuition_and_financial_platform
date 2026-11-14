import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AnomalyIssueType(str, enum.Enum):
    PAYMENT_OVER_ALLOCATED = "PAYMENT_OVER_ALLOCATED"
    SCHOLARSHIP_EXCEEDS_FEES = "SCHOLARSHIP_EXCEEDS_FEES"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    REFUND_EXCEEDS_PAID = "REFUND_EXCEEDS_PAID"
    BALANCE_MISMATCH = "BALANCE_MISMATCH"


class AnomalySeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyResolutionStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anomaly_id = Column(String(50), unique=True, nullable=False, index=True)  # ANM-000001
    issue_type = Column(SAEnum(AnomalyIssueType), nullable=False, index=True)
    
    entity_type = Column(String(50), nullable=False, index=True)  # INVOICE, PAYMENT, SCHOLARSHIP, REFUND, STUDENT
    entity_id = Column(String(100), nullable=False, index=True)  # Business identifier
    severity = Column(SAEnum(AnomalySeverity), nullable=False, default=AnomalySeverity.MEDIUM, index=True)
    
    detection_timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    expected_value = Column(DECIMAL(12, 2), nullable=True)
    actual_value = Column(DECIMAL(12, 2), nullable=True)
    explanation = Column(Text, nullable=False)
    
    # Ground-truth label strictly for synthetic evaluation benchmarking
    ground_truth_label = Column(String(100), nullable=True)
    
    resolution_status = Column(SAEnum(AnomalyResolutionStatus), nullable=False, default=AnomalyResolutionStatus.OPEN, index=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<Anomaly(id={self.id}, anomaly_id='{self.anomaly_id}', issue='{self.issue_type}', severity='{self.severity}')>"

