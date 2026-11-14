from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.payment_allocation import PaymentAllocation
from app.models.invoice_line import InvoiceLine
from app.repositories.base import BaseRepository


class PaymentAllocationRepository(BaseRepository[PaymentAllocation]):
    def __init__(self, db: Session):
        super().__init__(PaymentAllocation, db)

    def get_by_allocation_id(self, allocation_id: str) -> Optional[PaymentAllocation]:
        return (
            self.db.query(PaymentAllocation)
            .options(
                joinedload(PaymentAllocation.payment),
                joinedload(PaymentAllocation.invoice_line)
            )
            .filter(PaymentAllocation.allocation_id == allocation_id)
            .first()
        )

    def get_by_payment(self, payment_id: int) -> List[PaymentAllocation]:
        return (
            self.db.query(PaymentAllocation)
            .options(joinedload(PaymentAllocation.invoice_line))
            .filter(PaymentAllocation.payment_id == payment_id)
            .all()
        )

    def get_by_invoice_line(self, invoice_line_id: int) -> List[PaymentAllocation]:
        return (
            self.db.query(PaymentAllocation)
            .options(joinedload(PaymentAllocation.payment))
            .filter(PaymentAllocation.invoice_line_id == invoice_line_id)
            .all()
        )

    def get_filtered(
        self,
        payment_id: Optional[int] = None,
        invoice_line_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[PaymentAllocation]:
        query = (
            self.db.query(PaymentAllocation)
            .options(
                joinedload(PaymentAllocation.payment),
                joinedload(PaymentAllocation.invoice_line).joinedload(InvoiceLine.invoice)
            )
        )
        if payment_id:
            query = query.filter(PaymentAllocation.payment_id == payment_id)
        if invoice_line_id:
            query = query.filter(PaymentAllocation.invoice_line_id == invoice_line_id)
        return query.order_by(PaymentAllocation.id.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        payment_id: Optional[int] = None,
        invoice_line_id: Optional[int] = None
    ) -> int:
        query = self.db.query(PaymentAllocation)
        if payment_id:
            query = query.filter(PaymentAllocation.payment_id == payment_id)
        if invoice_line_id:
            query = query.filter(PaymentAllocation.invoice_line_id == invoice_line_id)
        return query.count()

