from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.scholarship import Scholarship, ScholarshipStatus, ScholarshipType
from app.repositories.base import BaseRepository


class ScholarshipRepository(BaseRepository[Scholarship]):
    def __init__(self, db: Session):
        super().__init__(Scholarship, db)

    def get_by_scholarship_id(self, scholarship_id: str) -> Optional[Scholarship]:
        return self.db.query(Scholarship).filter(Scholarship.scholarship_id == scholarship_id).first()

    def get_active_scholarships(self, academic_year: Optional[str] = None) -> List[Scholarship]:
        query = self.db.query(Scholarship).filter(Scholarship.status == ScholarshipStatus.ACTIVE)
        if academic_year:
            query = query.filter(Scholarship.academic_year == academic_year)
        return query.all()

    def get_filtered(
        self,
        scholarship_type: Optional[ScholarshipType] = None,
        status: Optional[ScholarshipStatus] = None,
        academic_year: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Scholarship]:
        query = self.db.query(Scholarship)
        if scholarship_type:
            query = query.filter(Scholarship.scholarship_type == scholarship_type)
        if status:
            query = query.filter(Scholarship.status == status)
        if academic_year:
            query = query.filter(Scholarship.academic_year == academic_year)
        return query.order_by(Scholarship.id.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        scholarship_type: Optional[ScholarshipType] = None,
        status: Optional[ScholarshipStatus] = None,
        academic_year: Optional[str] = None
    ) -> int:
        query = self.db.query(Scholarship)
        if scholarship_type:
            query = query.filter(Scholarship.scholarship_type == scholarship_type)
        if status:
            query = query.filter(Scholarship.status == status)
        if academic_year:
            query = query.filter(Scholarship.academic_year == academic_year)
        return query.count()

