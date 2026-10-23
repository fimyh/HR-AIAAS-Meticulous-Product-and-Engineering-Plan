from fastapi import APIRouter, HTTPException, status

from hr_aiaas.db.health import check_database_health


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "/live",
    summary="Application liveness",
)
async def liveness():
    return {
        "status": "ok",
    }


@router.get(
    "/ready",
    summary="Application readiness",
)
async def readiness():
    try:
        database = await check_database_health()
    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready.",
        ) from exception

    database_ready = (
        database.foreign_keys
        and database.journal_mode == "wal"
        and database.busy_timeout_ms >= 5000
    )

    if not database_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database configuration is not ready.",
        )

    return {
        "status": "ready",
        "services": {
            "database": {
                "status": database.status,
                "foreignKeys": database.foreign_keys,
                "journalMode": database.journal_mode,
                "busyTimeoutMs": database.busy_timeout_ms,
            },
        },
    }
