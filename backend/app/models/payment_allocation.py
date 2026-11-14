from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    allocation_id = Column(String(100), unique=True, nullable=False, index=True)  # ALLOC-PAY-2026-000001-01
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_line_id = Column(Integer, ForeignKey("invoice_lines.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    allocated_date = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("payment_id", "invoice_line_id", name="uq_payment_invoice_line_allocation"),
    )

    # Relationships
    payment = relationship("Payment", back_populates="allocations")
    invoice_line = relationship("InvoiceLine", back_populates="allocations")

    def __repr__(self):
        return f"<PaymentAllocation(id={self.id}, allocation_id='{self.allocation_id}', amount={self.amount})>"

