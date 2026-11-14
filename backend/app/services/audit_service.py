from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.financial_event import FinancialEvent, FinancialEventType
from app.models.audit_log import AuditLog
from app.services.id_generator import IDGenerator


def sanitize_json(val: Any) -> Any:
    """Recursively sanitize objects so they are natively JSON serializable."""
    if isinstance(val, dict):
        return {str(k): sanitize_json(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple, set)):
        return [sanitize_json(i) for i in val]
    elif isinstance(val, Decimal):
        return str(val)
    elif isinstance(val, (date, datetime)):
        return val.isoformat()
    elif isinstance(val, Enum):
        return val.value
    return val


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_financial_event(
        self,
        entity_type: str,
        entity_id: str,
        event_type: FinancialEventType,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        actor_id: Optional[int] = None,
        reference_id: Optional[str] = None,
        amount: Optional[Decimal] = None,
        currency: str = "INR",
        metadata: Optional[Dict[str, Any]] = None
    ) -> FinancialEvent:
        count = self.db.query(func.count(FinancialEvent.id)).scalar() or 0
        event = FinancialEvent(
            event_id=IDGenerator.event_id(count + 1),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            event_timestamp=datetime.now(timezone.utc),
            actor_id=actor_id,
            reference_id=reference_id,
            amount=amount,
            currency=currency,
            metadata_json=sanitize_json(metadata) if metadata else None
        )
        self.db.add(event)
        self.db.flush()
        return event

    def log_administrative_action(
        self,
        user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=sanitize_json(old_values) if old_values else None,
            new_values=sanitize_json(new_values) if new_values else None,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(log)
        self.db.flush()
        return log

    def log_action(
        self,
        actor_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Alias for log_administrative_action with actor_id parameter."""
        return self.log_administrative_action(
            user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address
        )

