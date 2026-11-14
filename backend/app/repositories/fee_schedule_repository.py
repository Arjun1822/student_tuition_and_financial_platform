from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.fee_schedule import FeeSchedule
from app.repositories.base import BaseRepository


class FeeScheduleRepository(BaseRepository[FeeSchedule]):
    def __init__(self, db: Session):
        super().__init__(FeeSchedule, db)

    def get_by_program_and_term(self, program_id: int, term_id: int) -> Optional[FeeSchedule]:
        return (
            self.db.query(FeeSchedule)
            .options(joinedload(FeeSchedule.program), joinedload(FeeSchedule.term))
            .filter(FeeSchedule.program_id == program_id, FeeSchedule.term_id == term_id)
            .first()
        )

    def get_effective_schedule(self, program_id: int, term_id: int, effective_date: Optional[date] = None) -> Optional[FeeSchedule]:
        target_date = effective_date or date.today()
        return (
            self.db.query(FeeSchedule)
            .options(joinedload(FeeSchedule.program), joinedload(FeeSchedule.term))
            .filter(
                FeeSchedule.program_id == program_id,
                FeeSchedule.term_id == term_id,
                FeeSchedule.is_active.is_(True),
                FeeSchedule.effective_start_date <= target_date,
                FeeSchedule.effective_end_date >= target_date,
            )
            .first()
        )

    def get_next_sequence_id(self) -> str:
        count = self.db.query(func.count(FeeSchedule.id)).scalar() or 0
        return f"FEE-{count + 1:06d}"

    def filter_fee_schedules(
        self,
        program_id: Optional[int] = None,
        term_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[FeeSchedule], int]:
        q = self.db.query(FeeSchedule).options(
            joinedload(FeeSchedule.program),
            joinedload(FeeSchedule.term)
        )
        if program_id:
            q = q.filter(FeeSchedule.program_id == program_id)
        if term_id:
            q = q.filter(FeeSchedule.term_id == term_id)
        if is_active is not None:
            q = q.filter(FeeSchedule.is_active == is_active)
        total = q.count()
        items = q.order_by(FeeSchedule.id.desc()).offset(skip).limit(limit).all()
        return items, total

