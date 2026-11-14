from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.refund import Refund, RefundStatus
from app.repositories.base import BaseRepository


class RefundRepository(BaseRepository[Refund]):
    def __init__(self, db: Session):
        super().__init__(Refund, db)

    def get_by_refund_id(self, refund_id: str) -> Optional[Refund]:
        return (
            self.db.query(Refund)
            .options(
                joinedload(Refund.student),
                joinedload(Refund.payment),
                joinedload(Refund.invoice)
            )
            .filter(Refund.refund_id == refund_id)
            .first()
        )

    def get_by_id_with_relations(self, id: int) -> Optional[Refund]:
        return (
            self.db.query(Refund)
            .options(
                joinedload(Refund.student),
                joinedload(Refund.payment),
                joinedload(Refund.invoice)
            )
            .filter(Refund.id == id)
            .first()
        )

    def get_by_payment(self, payment_id: int) -> List[Refund]:
        return self.db.query(Refund).filter(Refund.payment_id == payment_id).all()

    def get_filtered(
        self,
        student_id: Optional[int] = None,
        payment_id: Optional[int] = None,
        status: Optional[RefundStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Refund]:
        query = (
            self.db.query(Refund)
            .options(
                joinedload(Refund.student),
                joinedload(Refund.payment),
                joinedload(Refund.invoice)
            )
        )
        if student_id:
            query = query.filter(Refund.student_id == student_id)
        if payment_id:
            query = query.filter(Refund.payment_id == payment_id)
        if status:
            query = query.filter(Refund.status == status)
        return query.order_by(Refund.requested_date.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        student_id: Optional[int] = None,
        payment_id: Optional[int] = None,
        status: Optional[RefundStatus] = None
    ) -> int:
        query = self.db.query(Refund)
        if student_id:
            query = query.filter(Refund.student_id == student_id)
        if payment_id:
            query = query.filter(Refund.payment_id == payment_id)
        if status:
            query = query.filter(Refund.status == status)
        return query.count()

