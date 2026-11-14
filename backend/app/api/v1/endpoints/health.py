from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/health", summary="Basic service health check")
async def health_check():
    """Returns basic service health status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/db", summary="Database connectivity health check")
def db_health_check(db: Session = Depends(get_db)):
    """Checks MySQL database connectivity and engine responsiveness."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
