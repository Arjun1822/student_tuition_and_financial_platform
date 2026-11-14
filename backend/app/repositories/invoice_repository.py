from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_line import InvoiceLine
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: Session):
        super().__init__(Invoice, db)

    def get_by_invoice_id(self, invoice_id: str) -> Optional[Invoice]:
        return (
            self.db.query(Invoice)
            .options(
                joinedload(Invoice.lines),
                joinedload(Invoice.student),
                joinedload(Invoice.term)
            )
            .filter(Invoice.invoice_id == invoice_id)
            .first()
        )

    def get_with_details(self, id: int) -> Optional[Invoice]:
        return (
            self.db.query(Invoice)
            .options(
                joinedload(Invoice.lines),
                joinedload(Invoice.student),
                joinedload(Invoice.term)
            )
            .filter(Invoice.id == id)
            .first()
        )

    def check_duplicate(self, enrollment_id: int, billing_cycle: str) -> Optional[Invoice]:
        return (
            self.db.query(Invoice)
            .filter(
                Invoice.enrollment_id == enrollment_id,
                Invoice.billing_cycle == billing_cycle,
                Invoice.status != InvoiceStatus.CANCELLED
            )
            .first()
        )

    def get_next_sequence_number(self, student_business_id: str, year: int) -> str:
        count = (
            self.db.query(func.count(Invoice.id))
            .filter(Invoice.student_id.isnot(None))
            .scalar() or 0
        )
        return f"INV-{student_business_id}-{year}-{count + 1:06d}"

    def filter_invoices(
        self,
        student_id: Optional[int] = None,
        status: Optional[InvoiceStatus] = None,
        billing_cycle: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Invoice], int]:
        q = self.db.query(Invoice).options(
            joinedload(Invoice.student),
            joinedload(Invoice.term)
        )
        if student_id:
            q = q.filter(Invoice.student_id == student_id)
        if status:
            q = q.filter(Invoice.status == status)
        if billing_cycle:
            q = q.filter(Invoice.billing_cycle == billing_cycle)
        total = q.count()
        items = q.order_by(Invoice.id.desc()).offset(skip).limit(limit).all()
        return items, total

