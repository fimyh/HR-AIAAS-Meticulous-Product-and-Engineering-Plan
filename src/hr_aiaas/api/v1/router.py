from fastapi import APIRouter

from hr_aiaas.api.v1.routers import (
    admin,
    assistant,
    audit,
    auth,
    candidates,
    documents,
    health,
    jobs,
    matching,
    talent_pools,
    users,
)
from hr_aiaas.config import get_settings


settings = get_settings()


api_v1_router = APIRouter(
    prefix="/api/v1",
)


@api_v1_router.get(
    "",
    tags=["system"],
    summary="API v1 information",
)
async def api_information():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "apiVersion": "v1",
        "environment": settings.app_env,
    }


@api_v1_router.get(
    "/status",
    tags=["system"],
    summary="Frontend connection status",
)
async def api_status():
    return {
        "status": "connected",
        "application": settings.app_name,
        "version": settings.app_version,
        "apiVersion": "v1",
    }


api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(candidates.router)
api_v1_router.include_router(documents.router)
api_v1_router.include_router(jobs.router)
api_v1_router.include_router(matching.router)
api_v1_router.include_router(talent_pools.router)
api_v1_router.include_router(assistant.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(admin.router)
