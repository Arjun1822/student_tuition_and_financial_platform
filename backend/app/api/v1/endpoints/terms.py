from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_any_role, UserRole
from app.api.dependencies import get_current_user
from app.models.term import Term
from app.models.user import User
from app.schemas.term import TermCreate, TermUpdate, TermResponse
from app.repositories.term_repository import TermRepository
from app.services.id_generator import IDGenerator
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=List[TermResponse], summary="List all academic terms")
def list_terms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = TermRepository(db)
    return repo.get_active_terms()


@router.post("/", response_model=TermResponse, status_code=status.HTTP_201_CREATED, summary="Create academic term")
def create_term(
    term_in: TermCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role([UserRole.ACADEMIC_ADMIN, UserRole.PLATFORM_ADMIN]))
) -> Any:
    repo = TermRepository(db)
    existing = repo.get_by_year_and_semester(term_in.year, term_in.semester)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Term {term_in.year} {term_in.semester.value} already exists."
        )

    if term_in.start_date >= term_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Term start_date must be strictly before end_date."
        )

    term_id_str = IDGenerator.term_id(term_in.year, term_in.semester.value)
    term = Term(
        term_id=term_id_str,
        name=term_in.name,
        year=term_in.year,
        semester=term_in.semester,
        start_date=term_in.start_date,
        end_date=term_in.end_date,
        is_active=term_in.is_active
    )
    repo.create(term)

    audit_service = AuditService(db)
    audit_service.log_administrative_action(
        user_id=current_user.id,
        action="CREATE_TERM",
        entity_type="TERM",
        entity_id=term.term_id,
        new_values={"name": term.name, "year": term.year, "semester": term.semester.value}
    )

    db.commit()
    db.refresh(term)
    return term


@router.get("/{id_or_term_id}", response_model=TermResponse, summary="Get term by ID or term_id")
def get_term(
    id_or_term_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = TermRepository(db)
    if id_or_term_id.isdigit():
        term = repo.get_by_id(int(id_or_term_id))
    else:
        term = repo.get_by_term_id(id_or_term_id)

    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Term '{id_or_term_id}' not found."
        )
    return term

