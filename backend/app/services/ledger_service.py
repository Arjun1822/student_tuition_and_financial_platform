from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.financial_event import FinancialEvent, FinancialEventType


class LedgerService:
    """
    Immutable Financial Event Ledger Service.
    Guarantees that all events recorded are strictly append-only,
    and provides unified historical auditing and reporting across transactions.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_ledger_history(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        event_type: Optional[FinancialEventType] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[FinancialEvent]:
        query = self.db.query(FinancialEvent)
        if entity_type:
            query = query.filter(FinancialEvent.entity_type == entity_type)
        if entity_id:
            query = query.filter(FinancialEvent.entity_id == entity_id)
        if event_type:
            query = query.filter(FinancialEvent.event_type == event_type)
        return query.order_by(FinancialEvent.event_timestamp.desc()).offset(skip).limit(limit).all()

    def count_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        event_type: Optional[FinancialEventType] = None
    ) -> int:
        query = self.db.query(FinancialEvent)
        if entity_type:
            query = query.filter(FinancialEvent.entity_type == entity_type)
        if entity_id:
            query = query.filter(FinancialEvent.entity_id == entity_id)
        if event_type:
            query = query.filter(FinancialEvent.event_type == event_type)
        return query.count()

