from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, db: Session):
        super().__init__(Enrollment, db)

    def get_with_relations(self, enrollment_id: int) -> Optional[Enrollment]:
        return (
            self.db.query(Enrollment)
            .options(
                joinedload(Enrollment.student),
                joinedload(Enrollment.program),
                joinedload(Enrollment.term)
            )
            .filter(Enrollment.id == enrollment_id)
            .first()
        )

    def get_by_business_id(self, enrollment_id: str) -> Optional[Enrollment]:
        return (
            self.db.query(Enrollment)
            .options(
                joinedload(Enrollment.student),
                joinedload(Enrollment.program),
                joinedload(Enrollment.term)
            )
            .filter(Enrollment.enrollment_id == enrollment_id)
            .first()
        )

    def get_by_student_program_term(self, student_id: int, program_id: int, term_id: int) -> Optional[Enrollment]:
        return (
            self.db.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.program_id == program_id,
                Enrollment.term_id == term_id
            )
            .first()
        )

    def get_next_sequence_id(self) -> str:
        count = self.db.query(func.count(Enrollment.id)).scalar() or 0
        return f"ENR-{count + 1:06d}"

    def filter_enrollments(
        self,
        student_id: Optional[int] = None,
        program_id: Optional[int] = None,
        term_id: Optional[int] = None,
        status: Optional[EnrollmentStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Enrollment], int]:
        q = self.db.query(Enrollment).options(
            joinedload(Enrollment.student),
            joinedload(Enrollment.program),
            joinedload(Enrollment.term)
        )
        if student_id:
            q = q.filter(Enrollment.student_id == student_id)
        if program_id:
            q = q.filter(Enrollment.program_id == program_id)
        if term_id:
            q = q.filter(Enrollment.term_id == term_id)
        if status:
            q = q.filter(Enrollment.status == status)
        total = q.count()
        items = q.order_by(Enrollment.id.desc()).offset(skip).limit(limit).all()
        return items, total

