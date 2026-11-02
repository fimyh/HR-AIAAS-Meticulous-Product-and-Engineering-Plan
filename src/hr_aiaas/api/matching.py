from fastapi import APIRouter, HTTPException, status

from hr_aiaas.config import get_settings
from hr_aiaas.db.health import check_database_health

router = APIRouter(tags=["system"])
settings = get_settings()


@router.get("", summary="API v1 information")
async def api_information() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "apiVersion": "v1",
        "environment": settings.app_env,
    }


@router.get("/status", summary="Frontend connection status")
async def api_status() -> dict[str, str]:
    return {"status": "connected", "application": settings.app_name, "apiVersion": "v1"}


@router.get("/health/live", summary="Process liveness")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Application readiness")
async def readiness() -> dict[str, object]:
    try:
        database = await check_database_health()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not ready.") from exc
    ready = database.foreign_keys and database.journal_mode == "wal" and database.busy_timeout_ms >= 5000
    if not ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database configuration is not ready.")
    return {
        "status": "ready",
        "database": {
            "status": database.status,
            "foreignKeys": database.foreign_keys,
            "journalMode": database.journal_mode,
            "busyTimeoutMs": database.busy_timeout_ms,
        },
    }
