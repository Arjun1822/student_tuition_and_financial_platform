from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.anomaly import Anomaly, AnomalyIssueType, AnomalySeverity, AnomalyResolutionStatus
from app.repositories.base import BaseRepository


class AnomalyRepository(BaseRepository[Anomaly]):
    def __init__(self, db: Session):
        super().__init__(Anomaly, db)

    def get_by_anomaly_id(self, anomaly_id: str) -> Optional[Anomaly]:
        return self.db.query(Anomaly).filter(Anomaly.anomaly_id == anomaly_id).first()

    def get_filtered(
        self,
        issue_type: Optional[AnomalyIssueType] = None,
        severity: Optional[AnomalySeverity] = None,
        resolution_status: Optional[AnomalyResolutionStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Anomaly]:
        query = self.db.query(Anomaly)
        if issue_type:
            query = query.filter(Anomaly.issue_type == issue_type)
        if severity:
            query = query.filter(Anomaly.severity == severity)
        if resolution_status:
            query = query.filter(Anomaly.resolution_status == resolution_status)
        return query.order_by(Anomaly.detection_timestamp.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        issue_type: Optional[AnomalyIssueType] = None,
        severity: Optional[AnomalySeverity] = None,
        resolution_status: Optional[AnomalyResolutionStatus] = None
    ) -> int:
        query = self.db.query(Anomaly)
        if issue_type:
            query = query.filter(Anomaly.issue_type == issue_type)
        if severity:
            query = query.filter(Anomaly.severity == severity)
        if resolution_status:
            query = query.filter(Anomaly.resolution_status == resolution_status)
        return query.count()

