from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)

class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    email: EmailStr
    full_name: str
    is_superuser: bool
    roles: list[str]
    permissions: list[str]

class SessionResponse(BaseModel):
    user: AuthenticatedUser
    expires_at: datetime
