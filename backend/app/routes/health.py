from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime, timezone
from ..config import settings
from ..models.run_log import RunLogEntry
from ..services.notion_service import notion_service

router = APIRouter(prefix="/api", tags=["System & Health"])


@router.get("/health", summary="Health Check and Diagnostics")
async def health_check() -> Dict[str, Any]:
    """Returns the operational health and configuration state of Campus Ops AI backend."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notion": {
            "configured": settings.is_notion_configured,
            "requests_db_set": bool(settings.NOTION_REQUESTS_DATABASE_ID and not settings.NOTION_REQUESTS_DATABASE_ID.startswith("placeholder")),
            "run_log_db_set": bool(settings.NOTION_RUN_LOG_DATABASE_ID and not settings.NOTION_RUN_LOG_DATABASE_ID.startswith("placeholder")),
            "mode": "live" if settings.is_notion_configured else "simulation/offline"
        },
        "cors": {
            "allowed_origins": settings.cors_origins_list
        }
    }


@router.get("/logs", response_model=List[RunLogEntry], summary="Get Recent Run Logs")
async def get_recent_logs(limit: int = 20) -> List[RunLogEntry]:
    """Retrieves recent execution and ingestion events recorded in the Run Log."""
    return notion_service.get_recent_logs(limit=limit)
