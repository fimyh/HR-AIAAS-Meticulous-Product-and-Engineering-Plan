from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from hr_aiaas.api.v1 import api_v1_router
from hr_aiaas.config import get_settings
from hr_aiaas.db.health import check_database_health
from hr_aiaas.db.session import dispose_engine


settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application startup and shutdown."""
    del application

    settings.create_storage_directories()

    yield

    await dispose_engine()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.app_debug,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url=(
            "/openapi.json"
            if settings.is_development
            else None
        ),
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.frontend_origin,
        ],
        allow_credentials=True,
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-CSRF-Token",
            "X-Request-ID",
        ],
        expose_headers=[
            "X-Request-ID",
        ],
    )

    @application.get(
        "/",
        tags=["system"],
        summary="Application information",
    )
    async def root():
        return {
            "application": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "status": "running",
            "api": {
                "version": "v1",
                "baseUrl": "/api/v1",
                "documentation": "/docs",
                "liveness": "/health/live",
                "readiness": "/health/ready",
            },
        }

    @application.get(
        "/health/live",
        tags=["system"],
        summary="Process liveness",
    )
    async def liveness():
        return {
            "status": "ok",
        }

    @application.get(
        "/health/ready",
        tags=["system"],
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
            "database": {
                "status": database.status,
                "foreignKeys": database.foreign_keys,
                "journalMode": database.journal_mode,
                "busyTimeoutMs": database.busy_timeout_ms,
            },
        }

    application.include_router(api_v1_router)

    return application


app = create_application()
