from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_payment_id(self, payment_id: str) -> Optional[Payment]:
        return (
            self.db.query(Payment)
            .options(joinedload(Payment.student), joinedload(Payment.allocations))
            .filter(Payment.payment_id == payment_id)
            .first()
        )

    def get_by_id_with_relations(self, id: int) -> Optional[Payment]:
        return (
            self.db.query(Payment)
            .options(joinedload(Payment.student), joinedload(Payment.allocations))
            .filter(Payment.id == id)
            .first()
        )

    def get_by_reference(self, reference_number: str) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.reference_number == reference_number).first()

    def get_filtered(
        self,
        student_id: Optional[int] = None,
        status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Payment]:
        query = self.db.query(Payment).options(joinedload(Payment.student))
        if student_id:
            query = query.filter(Payment.student_id == student_id)
        if status:
            query = query.filter(Payment.status == status)
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        return query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        student_id: Optional[int] = None,
        status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None
    ) -> int:
        query = self.db.query(Payment)
        if student_id:
            query = query.filter(Payment.student_id == student_id)
        if status:
            query = query.filter(Payment.status == status)
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        return query.count()

