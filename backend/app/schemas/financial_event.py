from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from app.models.financial_event import FinancialEventType


class FinancialEventResponse(BaseModel):
    id: int
    event_id: str
    entity_type: str
    entity_id: str
    event_type: FinancialEventType
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    event_timestamp: datetime
    actor_id: Optional[int] = None
    reference_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: str = "INR"
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

