from typing import List, Optional, Tuple
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from app.models.student import Student, StudentStatus
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self, db: Session):
        super().__init__(Student, db)

    def get_by_student_id(self, student_id: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.student_id == student_id).first()

    def get_by_email(self, email: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.email == email).first()

    def get_next_sequence_id(self) -> str:
        count = self.db.query(func.count(Student.id)).scalar() or 0
        return f"STU-{count + 1:06d}"

    def search_students(
        self,
        query_str: Optional[str] = None,
        status: Optional[StudentStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Student], int]:
        q = self.db.query(Student)
        if status:
            q = q.filter(Student.status == status)
        if query_str:
            term = f"%{query_str.strip()}%"
            q = q.filter(
                or_(
                    Student.first_name.ilike(term),
                    Student.last_name.ilike(term),
                    Student.email.ilike(term),
                    Student.student_id.ilike(term)
                )
            )
        total = q.count()
        items = q.order_by(Student.id.desc()).offset(skip).limit(limit).all()
        return items, total

