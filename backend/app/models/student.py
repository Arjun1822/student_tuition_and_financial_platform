import enum
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class IncomeCategory(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    GRADUATED = "GRADUATED"
    SUSPENDED = "SUSPENDED"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), unique=True, nullable=False, index=True)  # STU-000001
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, default="India")
    postal_code = Column(String(20), nullable=True)
    family_income_category = Column(SAEnum(IncomeCategory), nullable=False, default=IncomeCategory.MEDIUM)
    gpa = Column(DECIMAL(4, 2), nullable=False, default=0.00)
    status = Column(SAEnum(StudentStatus), nullable=False, default=StudentStatus.ACTIVE, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="student")
    payments = relationship("Payment", back_populates="student")
    eligibilities = relationship("Eligibility", back_populates="student")
    refunds = relationship("Refund", back_populates="student")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.full_name}')>"
