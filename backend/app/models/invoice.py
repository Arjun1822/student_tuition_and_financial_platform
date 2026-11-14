import enum
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, DECIMAL, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(100), unique=True, nullable=False, index=True)  # INV-STU-000001-2026-000001
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    term_id = Column(Integer, ForeignKey("terms.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Financial calculations in DECIMAL(12,2)
    gross_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    scholarship_discount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    net_amount = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    amount_paid = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    outstanding_balance = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(SAEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.ISSUED, index=True)
    billing_cycle = Column(String(50), nullable=False, index=True)  # e.g., "2026-FALL"
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_invoice_enrollment_cycle", "enrollment_id", "billing_cycle"),
    )

    # Relationships
    enrollment = relationship("Enrollment", back_populates="invoices")
    student = relationship("Student", back_populates="invoices")
    term = relationship("Term", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="invoice")

    @property
    def scholarship_amount(self):
        return self.scholarship_discount or Decimal("0.00")

    @scholarship_amount.setter
    def scholarship_amount(self, value):
        self.scholarship_discount = value

    @property
    def paid_amount(self):
        return self.amount_paid or Decimal("0.00")

    @paid_amount.setter
    def paid_amount(self, value):
        self.amount_paid = value

    @property
    def late_fee_amount(self):
        return getattr(self, "_late_fee_amount", Decimal("0.00"))

    @late_fee_amount.setter
    def late_fee_amount(self, value):
        self._late_fee_amount = value

    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_id='{self.invoice_id}', net={self.net_amount}, status='{self.status}')>"

