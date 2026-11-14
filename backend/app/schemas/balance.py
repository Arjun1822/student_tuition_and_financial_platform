from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class InvoiceBalanceSummary(BaseModel):
    invoice_id: str
    billing_cycle: str
    status: str
    gross_amount: Decimal
    scholarship_amount: Decimal
    net_amount: Decimal
    late_fee_amount: Decimal
    paid_amount: Decimal
    outstanding_balance: Decimal


class StudentBalanceStatement(BaseModel):
    student_id: int
    student_business_id: str
    student_name: str
    currency: str = "INR"
    gross_charges: Decimal
    approved_scholarships: Decimal
    net_collectible: Decimal
    assessed_late_fees: Decimal
    total_payments: Decimal
    total_allocated: Decimal
    total_unallocated: Decimal
    total_refunds: Decimal
    outstanding_balance: Decimal
    invoices: List[InvoiceBalanceSummary]

