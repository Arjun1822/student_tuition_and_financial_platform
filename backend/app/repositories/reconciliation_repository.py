from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.reconciliation import ReconciliationRun, ReconciliationResult, ReconciliationRunStatus, ReconciliationStatus
from app.repositories.base import BaseRepository


class ReconciliationRepository(BaseRepository[ReconciliationRun]):
    def __init__(self, db: Session):
        super().__init__(ReconciliationRun, db)

    def get_by_run_id(self, run_id: str) -> Optional[ReconciliationRun]:
        return (
            self.db.query(ReconciliationRun)
            .options(joinedload(ReconciliationRun.results))
            .filter(ReconciliationRun.run_id == run_id)
            .first()
        )

    def get_by_id_with_results(self, id: int) -> Optional[ReconciliationRun]:
        return (
            self.db.query(ReconciliationRun)
            .options(joinedload(ReconciliationRun.results))
            .filter(ReconciliationRun.id == id)
            .first()
        )

    def get_filtered(
        self,
        status: Optional[ReconciliationRunStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ReconciliationRun]:
        query = self.db.query(ReconciliationRun)
        if status:
            query = query.filter(ReconciliationRun.status == status)
        return query.order_by(ReconciliationRun.id.desc()).offset(skip).limit(limit).all()

    def count_filtered(self, status: Optional[ReconciliationRunStatus] = None) -> int:
        query = self.db.query(ReconciliationRun)
        if status:
            query = query.filter(ReconciliationRun.status == status)
        return query.count()

    def get_results_filtered(
        self,
        run_id: int,
        status: Optional[ReconciliationStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ReconciliationResult]:
        query = self.db.query(ReconciliationResult).filter(ReconciliationResult.run_id == run_id)
        if status:
            query = query.filter(ReconciliationResult.status == status)
        return query.order_by(ReconciliationResult.id.asc()).offset(skip).limit(limit).all()

    def count_results_filtered(
        self,
        run_id: int,
        status: Optional[ReconciliationStatus] = None
    ) -> int:
        query = self.db.query(ReconciliationResult).filter(ReconciliationResult.run_id == run_id)
        if status:
            query = query.filter(ReconciliationResult.status == status)
        return query.count()

