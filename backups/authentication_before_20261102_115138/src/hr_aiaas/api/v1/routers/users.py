from fastapi import APIRouter, Query, status
from pydantic import BaseModel, EmailStr, Field

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/users", tags=["users and access"])

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=256)
    role_ids: list[int] = []

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None
    role_ids: list[int] | None = None

@router.get("")
async def list_users(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)) -> dict[str, object]:
    del limit, offset
    not_implemented("List users")

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate) -> dict[str, object]:
    del payload
    not_implemented("Create user")

@router.get("/{public_id}")
async def get_user(public_id: str) -> dict[str, object]:
    del public_id
    not_implemented("Get user")

@router.patch("/{public_id}")
async def update_user(public_id: str, payload: UserUpdate) -> dict[str, object]:
    del public_id, payload
    not_implemented("Update user")

@router.get("/access/roles")
async def list_roles() -> list[dict[str, object]]:
    not_implemented("List roles")

@router.get("/access/permissions")
async def list_permissions() -> list[dict[str, object]]:
    not_implemented("List permissions")
