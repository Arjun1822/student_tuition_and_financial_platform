from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FeeSchedule(Base):
    __tablename__ = "fee_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fee_schedule_id = Column(String(50), unique=True, nullable=False, index=True)  # FEE-000001
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False, index=True)
    term_id = Column(Integer, ForeignKey("terms.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Financial components using DECIMAL(12,2)
    tuition_fee = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    registration_fee = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    laboratory_fee = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    examination_fee = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    library_fee = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    other_charges = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    
    currency = Column(String(3), nullable=False, default="INR")
    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("program_id", "term_id", name="uq_fee_schedule_program_term"),
    )

    # Relationships
    program = relationship("Program", back_populates="fee_schedules")
    term = relationship("Term", back_populates="fee_schedules")

    @property
    def total_fee(self):
        return (
            self.tuition_fee +
            self.registration_fee +
            self.laboratory_fee +
            self.examination_fee +
            self.library_fee +
            self.other_charges
        )

    def __repr__(self):
        return f"<FeeSchedule(id={self.id}, fee_schedule_id='{self.fee_schedule_id}', total={self.total_fee})>"

