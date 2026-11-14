from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.anomaly import AnomalyIssueType, AnomalySeverity, AnomalyResolutionStatus


class AnomalyResponse(BaseModel):
    id: int
    anomaly_id: str
    issue_type: AnomalyIssueType
    entity_type: str
    entity_id: str
    severity: AnomalySeverity
    detection_timestamp: datetime
    expected_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    explanation: str
    ground_truth_label: Optional[str] = None
    resolution_status: AnomalyResolutionStatus
    resolution_notes: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyResolveRequest(BaseModel):
    resolution_status: AnomalyResolutionStatus = AnomalyResolutionStatus.RESOLVED
    resolution_notes: str = Field(..., min_length=3)

