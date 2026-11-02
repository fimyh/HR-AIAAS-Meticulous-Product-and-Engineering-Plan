from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=256)
    role_ids: list[int] = Field(default_factory=list)

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None
    role_ids: list[int] | None = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    roles: list[str] = Field(default_factory=list)

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    limit: int
    offset: int

class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None

class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    resource: str
    action: str
    description: str | None
