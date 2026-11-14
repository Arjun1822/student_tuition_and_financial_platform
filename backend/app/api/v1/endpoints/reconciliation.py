from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.reconciliation import ReconciliationRunStatus, ReconciliationStatus
from app.api.dependencies import get_current_active_user, require_permissions
from app.repositories.reconciliation_repository import ReconciliationRepository
from app.schemas.reconciliation import (
    ReconciliationRunCreate,
    ReconciliationRunResponse,
    ReconciliationResultResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.reconciliation_service import ReconciliationService

router = APIRouter()


@router.post("/run", response_model=ReconciliationRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_reconciliation(
    req: ReconciliationRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["RECONCILIATION_RUN", "ADMIN_ACCESS"]))
):
    service = ReconciliationService(db)
    run = service.run_reconciliation(
        term_id=req.term_id,
        program_id=req.program_id,
        actor_id=current_user.id
    )
    return run


@router.get("/runs", response_model=PaginatedResponse[ReconciliationRunResponse])
def list_reconciliation_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ReconciliationRunStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = ReconciliationRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_filtered(status=status_filter, skip=skip, limit=page_size)
    total = repo.count_filtered(status=status_filter)
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/runs/{id}", response_model=ReconciliationRunResponse)
def get_reconciliation_run(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = ReconciliationRepository(db)
    run = repo.get_by_id_with_results(id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconciliation run {id} not found.")
    return run


@router.get("/runs/{id}/results", response_model=PaginatedResponse[ReconciliationResultResponse])
def get_reconciliation_results(
    id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ReconciliationStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    repo = ReconciliationRepository(db)
    skip = (page - 1) * page_size
    items = repo.get_results_filtered(run_id=id, status=status_filter, skip=skip, limit=page_size)
    total = repo.count_results_filtered(run_id=id, status=status_filter)
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)

