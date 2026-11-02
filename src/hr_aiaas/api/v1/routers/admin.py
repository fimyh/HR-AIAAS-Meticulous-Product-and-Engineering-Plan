from fastapi import APIRouter

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/admin", tags=["administration"])

@router.get("/models")
async def list_models() -> list[dict[str, object]]:
    not_implemented("List model registry")

@router.post("/models")
async def register_model(payload: dict[str, object]) -> dict[str, object]:
    del payload
    not_implemented("Register model")

@router.get("/prompts")
async def list_prompt_versions() -> list[dict[str, object]]:
    not_implemented("List prompt versions")

@router.post("/prompts")
async def create_prompt_version(payload: dict[str, object]) -> dict[str, object]:
    del payload
    not_implemented("Create prompt version")

@router.get("/retention-rules")
async def list_retention_rules() -> list[dict[str, object]]:
    not_implemented("List retention rules")

@router.put("/retention-rules/{resource_type}")
async def set_retention_rule(resource_type: str, retention_days: int) -> dict[str, object]:
    del resource_type, retention_days
    not_implemented("Set retention rule")

@router.get("/system/health")
async def system_health() -> dict[str, object]:
    not_implemented("Extended system health")
