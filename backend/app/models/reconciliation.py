import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ReconciliationRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReconciliationStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    MISMATCHED = "MISMATCHED"
    EXCEPTION = "EXCEPTION"
    PENDING = "PENDING"


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), unique=True, nullable=False, index=True)  # REC-000001
    run_date = Column(DateTime, server_default=func.now(), nullable=False)
    
    total_invoices = Column(Integer, nullable=False, default=0)
    matched_count = Column(Integer, nullable=False, default=0)
    mismatched_count = Column(Integer, nullable=False, default=0)
    exception_count = Column(Integer, nullable=False, default=0)
    
    status = Column(SAEnum(ReconciliationRunStatus), nullable=False, default=ReconciliationRunStatus.PENDING)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    results = relationship("ReconciliationResult", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ReconciliationRun(id={self.id}, run_id='{self.run_id}', status='{self.status}', total={self.total_invoices})>"


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    
    entity_type = Column(String(50), nullable=False, default="INVOICE")
    entity_id = Column(String(100), nullable=False, index=True)  # Business identifier
    
    expected_amount = Column(DECIMAL(12, 2), nullable=False)
    actual_amount = Column(DECIMAL(12, 2), nullable=False)
    difference = Column(DECIMAL(12, 2), nullable=False)
    
    status = Column(SAEnum(ReconciliationStatus), nullable=False, index=True)
    exception_type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    run = relationship("ReconciliationRun", back_populates="results")
    invoice = relationship("Invoice")

    def __repr__(self):
        return f"<ReconciliationResult(id={self.id}, entity_id='{self.entity_id}', diff={self.difference}, status='{self.status}')>"

