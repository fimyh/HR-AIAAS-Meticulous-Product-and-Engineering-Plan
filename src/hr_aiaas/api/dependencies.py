from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hr_aiaas.db.models.identity import User
from hr_aiaas.db.session import get_db_session
from hr_aiaas.repositories.auth import get_access, get_active_session, get_user_by_id
from hr_aiaas.security.sessions import CSRF_COOKIE, SESSION_COOKIE, csrf_is_valid, hash_session_token

DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]

@dataclass(frozen=True, slots=True)
class CurrentUser:
    user: User
    roles: frozenset[str]
    permissions: frozenset[str]
    session_token: str

async def get_current_user(
    db: DatabaseSession,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> CurrentUser:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "NOT_AUTHENTICATED", "message": "Authentication is required."})
    now = datetime.now(timezone.utc)
    db_session = await get_active_session(db, hash_session_token(session_token), now)
    if not db_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_SESSION", "message": "The session is invalid or expired."})
    user = await get_user_by_id(db, db_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INACTIVE_USER", "message": "The account is unavailable."})
    roles, permissions = await get_access(db, user.id)
    return CurrentUser(user=user, roles=frozenset(roles), permissions=frozenset(permissions), session_token=session_token)

CurrentUserDependency = Annotated[CurrentUser, Depends(get_current_user)]

def require_permission(code: str):
    async def dependency(current: CurrentUserDependency) -> CurrentUser:
        if current.user.is_superuser or code in current.permissions:
            return current
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "FORBIDDEN", "message": "The requested operation is not permitted."})
    return dependency

async def require_csrf(
    current: CurrentUserDependency,
    csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_COOKIE)] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    if not csrf_is_valid(current.session_token, csrf_cookie, csrf_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "CSRF_VALIDATION_FAILED", "message": "CSRF validation failed."})
