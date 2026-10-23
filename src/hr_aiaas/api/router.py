from fastapi import APIRouter

from hr_aiaas.config import get_settings


settings = get_settings()


api_router = APIRouter(
    prefix="/api/v1",
)


@api_router.get(
    "",
    tags=["API"],
    summary="API version information",
)
async def api_information():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "apiVersion": "v1",
        "environment": settings.app_env,
    }


@api_router.get(
    "/status",
    tags=["API"],
    summary="Frontend connection status",
)
async def api_status():
    return {
        "status": "connected",
        "application": settings.app_name,
        "version": settings.app_version,
        "apiVersion": "v1",
    }
