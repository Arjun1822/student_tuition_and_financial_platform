from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.repositories.base import BaseRepository


class FinancialEventRepository(BaseRepository[FinancialEvent]):
    def __init__(self, db: Session):
        super().__init__(FinancialEvent, db)

    def get_by_event_id(self, event_id: str) -> Optional[FinancialEvent]:
        return self.db.query(FinancialEvent).filter(FinancialEvent.event_id == event_id).first()

    def get_by_entity(self, entity_type: str, entity_id: str) -> List[FinancialEvent]:
        return (
            self.db.query(FinancialEvent)
            .filter(FinancialEvent.entity_type == entity_type, FinancialEvent.entity_id == entity_id)
            .order_by(FinancialEvent.event_timestamp.desc())
            .all()
        )

    def get_filtered(
        self,
        event_type: Optional[FinancialEventType] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[FinancialEvent]:
        query = self.db.query(FinancialEvent)
        if event_type:
            query = query.filter(FinancialEvent.event_type == event_type)
        if entity_type:
            query = query.filter(FinancialEvent.entity_type == entity_type)
        if entity_id:
            query = query.filter(FinancialEvent.entity_id == entity_id)
        return query.order_by(FinancialEvent.event_timestamp.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        event_type: Optional[FinancialEventType] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> int:
        query = self.db.query(FinancialEvent)
        if event_type:
            query = query.filter(FinancialEvent.event_type == event_type)
        if entity_type:
            query = query.filter(FinancialEvent.entity_type == entity_type)
        if entity_id:
            query = query.filter(FinancialEvent.entity_id == entity_id)
        return query.count()

