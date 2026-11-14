from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.term import Term, SemesterEnum
from app.repositories.base import BaseRepository


class TermRepository(BaseRepository[Term]):
    def __init__(self, db: Session):
        super().__init__(Term, db)

    def get_by_term_id(self, term_id: str) -> Optional[Term]:
        return self.db.query(Term).filter(Term.term_id == term_id).first()

    def get_by_year_and_semester(self, year: int, semester: SemesterEnum) -> Optional[Term]:
        return self.db.query(Term).filter(Term.year == year, Term.semester == semester).first()

    def get_active_terms(self) -> List[Term]:
        return self.db.query(Term).filter(Term.is_active.is_(True)).order_by(Term.start_date.asc()).all()

