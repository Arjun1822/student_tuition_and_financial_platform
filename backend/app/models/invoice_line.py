import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FeeType(str, enum.Enum):
    TUITION = "TUITION"
    REGISTRATION = "REGISTRATION"
    LABORATORY = "LABORATORY"
    EXAMINATION = "EXAMINATION"
    LIBRARY = "LIBRARY"
    OTHER = "OTHER"
    LATE_FEE = "LATE_FEE"


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_line_id = Column(String(50), unique=True, nullable=False, index=True)  # INVL-000001
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_type = Column(SAEnum(FeeType), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    allocated_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")
    allocations = relationship("PaymentAllocation", back_populates="invoice_line", cascade="all, delete-orphan")

    @property
    def remaining_amount(self):
        return self.amount - self.allocated_amount

    @property
    def line_id(self):
        return self.invoice_line_id

    def __repr__(self):
        return f"<InvoiceLine(id={self.id}, line_id='{self.invoice_line_id}', fee_type='{self.fee_type}', amount={self.amount})>"

