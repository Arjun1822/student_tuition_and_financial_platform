from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.anomaly import (
    Anomaly,
    AnomalyIssueType,
    AnomalySeverity,
    AnomalyResolutionStatus,
)
from app.api.dependencies import get_current_active_user, require_permissions
from app.repositories.anomaly_repository import AnomalyRepository
from app.schemas.anomaly import AnomalyResponse, AnomalyResolveRequest
from app.schemas.common import PaginatedResponse
from app.services.anomaly_service import AnomalyDetectionService
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AnomalyResponse])
def list_anomalies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    issue_type: Optional[AnomalyIssueType] = None,
    severity: Optional[AnomalySeverity] = None,
    resolution_status: Optional[AnomalyResolutionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = AnomalyRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(
        issue_type=issue_type,
        severity=severity,
        resolution_status=resolution_status,
        skip=skip,
        limit=page_size
    )
    total = repo.count_filtered(
        issue_type=issue_type,
        severity=severity,
        resolution_status=resolution_status
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.post("/scan", response_model=List[AnomalyResponse])
def trigger_anomaly_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["ANOMALY_SCAN", "ADMIN_ACCESS"]))
):
    service = AnomalyDetectionService(db)
    anomalies = service.scan_for_anomalies(actor_id=current_user.id)
    return anomalies


@router.get("/{id_or_slug}", response_model=AnomalyResponse)
def get_anomaly(
    id_or_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = AnomalyRepository(db)
    if id_or_slug.isdigit():
        anm = repo.get(int(id_or_slug))
    else:
        anm = repo.get_by_anomaly_id(id_or_slug)
    if not anm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Anomaly '{id_or_slug}' not found.")
    return anm


@router.post("/{id}/resolve", response_model=AnomalyResponse)
def resolve_anomaly(
    id: int,
    req: AnomalyResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["ANOMALY_RESOLVE", "ADMIN_ACCESS"]))
):
    repo = AnomalyRepository(db)
    anm = repo.get(id)
    if not anm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Anomaly with ID {id} not found.")

    anm.resolution_status = req.resolution_status
    anm.resolution_notes = req.resolution_notes
    anm.resolved_by = current_user.id
    from datetime import datetime, timezone
    anm.resolved_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(anm)

    AuditService(db).log_action(
        actor_id=current_user.id,
        action="RESOLVE_ANOMALY",
        entity_type="ANOMALY",
        entity_id=anm.anomaly_id,
        new_values={"status": anm.resolution_status.value, "notes": req.resolution_notes}
    )
    return anm

