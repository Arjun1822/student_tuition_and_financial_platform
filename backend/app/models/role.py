import enum
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class RoleEnum(str, enum.Enum):
    LEARNER = "LEARNER"
    INSTRUCTOR = "INSTRUCTOR"
    ACADEMIC_ADMIN = "ACADEMIC_ADMIN"
    SUPPORT_STAFF = "SUPPORT_STAFF"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    permissions_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

