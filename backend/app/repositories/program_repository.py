from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.program import Program, DegreeLevel, ProgramStatus
from app.repositories.base import BaseRepository


class ProgramRepository(BaseRepository[Program]):
    def __init__(self, db: Session):
        super().__init__(Program, db)

    def get_by_code(self, code: str) -> Optional[Program]:
        return self.db.query(Program).filter(Program.code == code).first()

    def get_by_program_id(self, program_id: str) -> Optional[Program]:
        return self.db.query(Program).filter(Program.program_id == program_id).first()

    def get_next_sequence_id(self) -> str:
        count = self.db.query(func.count(Program.id)).scalar() or 0
        return f"PRG-{count + 1:06d}"

    def filter_programs(
        self,
        department: Optional[str] = None,
        degree_level: Optional[DegreeLevel] = None,
        status: Optional[ProgramStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Program], int]:
        q = self.db.query(Program)
        if department:
            q = q.filter(Program.department == department)
        if degree_level:
            q = q.filter(Program.degree_level == degree_level)
        if status:
            q = q.filter(Program.status == status)
        total = q.count()
        items = q.order_by(Program.id.asc()).offset(skip).limit(limit).all()
        return items, total

