from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.eligibility import Eligibility, EligibilityStatus
from app.repositories.base import BaseRepository


class EligibilityRepository(BaseRepository[Eligibility]):
    def __init__(self, db: Session):
        super().__init__(Eligibility, db)

    def get_by_eligibility_id(self, eligibility_id: str) -> Optional[Eligibility]:
        return (
            self.db.query(Eligibility)
            .options(
                joinedload(Eligibility.student),
                joinedload(Eligibility.scholarship),
                joinedload(Eligibility.enrollment)
            )
            .filter(Eligibility.eligibility_id == eligibility_id)
            .first()
        )

    def get_by_id_with_relations(self, id: int) -> Optional[Eligibility]:
        return (
            self.db.query(Eligibility)
            .options(
                joinedload(Eligibility.student),
                joinedload(Eligibility.scholarship),
                joinedload(Eligibility.enrollment)
            )
            .filter(Eligibility.id == id)
            .first()
        )

    def get_by_student_and_scholarship(
        self, student_id: int, scholarship_id: int, enrollment_id: Optional[int] = None
    ) -> Optional[Eligibility]:
        query = self.db.query(Eligibility).filter(
            Eligibility.student_id == student_id,
            Eligibility.scholarship_id == scholarship_id
        )
        if enrollment_id:
            query = query.filter(Eligibility.enrollment_id == enrollment_id)
        return query.first()

    def get_filtered(
        self,
        student_id: Optional[int] = None,
        scholarship_id: Optional[int] = None,
        status: Optional[EligibilityStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Eligibility]:
        query = (
            self.db.query(Eligibility)
            .options(
                joinedload(Eligibility.student),
                joinedload(Eligibility.scholarship),
                joinedload(Eligibility.enrollment)
            )
        )
        if student_id:
            query = query.filter(Eligibility.student_id == student_id)
        if scholarship_id:
            query = query.filter(Eligibility.scholarship_id == scholarship_id)
        if status:
            query = query.filter(Eligibility.status == status)
        return query.order_by(Eligibility.id.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        student_id: Optional[int] = None,
        scholarship_id: Optional[int] = None,
        status: Optional[EligibilityStatus] = None
    ) -> int:
        query = self.db.query(Eligibility)
        if student_id:
            query = query.filter(Eligibility.student_id == student_id)
        if scholarship_id:
            query = query.filter(Eligibility.scholarship_id == scholarship_id)
        if status:
            query = query.filter(Eligibility.status == status)
        return query.count()

