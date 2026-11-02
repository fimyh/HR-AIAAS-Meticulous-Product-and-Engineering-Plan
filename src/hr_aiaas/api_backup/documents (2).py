from fastapi import APIRouter, Response, status
from pydantic import BaseModel, EmailStr, Field

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)

class LoginResponse(BaseModel):
    user_public_id: str
    expires_at: str

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    del payload
    not_implemented("Login")

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> Response:
    not_implemented("Logout")

@router.get("/session")
async def current_session() -> dict[str, object]:
    not_implemented("Current session")
