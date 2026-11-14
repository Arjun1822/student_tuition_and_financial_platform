from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.reconciliation import ReconciliationRunStatus, ReconciliationStatus


class ReconciliationRunCreate(BaseModel):
    notes: Optional[str] = None
    term_id: Optional[int] = None
    program_id: Optional[int] = None


class ReconciliationResultResponse(BaseModel):
    id: int
    run_id: int
    invoice_id: Optional[int] = None
    entity_type: str
    entity_id: str
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    status: ReconciliationStatus
    exception_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReconciliationRunResponse(BaseModel):
    id: int
    run_id: str
    run_date: datetime
    total_invoices: int
    matched_count: int
    mismatched_count: int
    exception_count: int
    status: ReconciliationRunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    results: Optional[List[ReconciliationResultResponse]] = None

    model_config = ConfigDict(from_attributes=True)

