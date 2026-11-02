from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hr_aiaas.api.dependencies import CurrentUser
from hr_aiaas.api.schemas.auth import AuthenticatedUser, LoginRequest, SessionResponse
from hr_aiaas.config import get_settings
from hr_aiaas.repositories import auth as repository
from hr_aiaas.security.passwords import verify_password
from hr_aiaas.security.sessions import csrf_token_for, hash_session_token, new_session_token

settings = get_settings()

def response_for(current: CurrentUser, expires_at: datetime) -> SessionResponse:
    return SessionResponse(user=AuthenticatedUser(public_id=current.user.public_id, email=current.user.email, full_name=current.user.full_name, is_superuser=current.user.is_superuser, roles=sorted(current.roles), permissions=sorted(current.permissions)), expires_at=expires_at)

async def login(db: AsyncSession, payload: LoginRequest) -> tuple[str, str, SessionResponse]:
    user = await repository.get_user_by_email(db, str(payload.email))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."})
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.session_idle_minutes)
    token = new_session_token()
    await repository.create_session(db, user.id, hash_session_token(token), now, expires)
    user.last_login_at = now
    await db.commit()
    roles, permissions = await repository.get_access(db, user.id)
    current = CurrentUser(user=user, roles=frozenset(roles), permissions=frozenset(permissions), session_token=token)
    return token, csrf_token_for(token), response_for(current, expires)
