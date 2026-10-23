from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hr_aiaas.api.health import router as health_router
from hr_aiaas.api.router import api_router
from hr_aiaas.config import get_settings
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
        tags=["System"],
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
                "health": "/health/live",
                "readiness": "/health/ready",
            },
        }

    application.include_router(health_router)
    application.include_router(api_router)

    return application


app = create_application()
