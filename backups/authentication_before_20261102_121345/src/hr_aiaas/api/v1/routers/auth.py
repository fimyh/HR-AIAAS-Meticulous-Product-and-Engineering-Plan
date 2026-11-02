from fastapi import APIRouter, Depends, Response, status

from hr_aiaas.api.dependencies import CurrentUserDependency, DatabaseSession, require_csrf
from hr_aiaas.api.schemas.auth import LoginRequest, SessionResponse
from hr_aiaas.config import get_settings
from hr_aiaas.security.sessions import CSRF_COOKIE, SESSION_COOKIE, hash_session_token
from hr_aiaas.services import auth as service

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()

def cookie_secure() -> bool:
    return settings.is_production

@router.post("/login", response_model=SessionResponse)
async def login(payload: LoginRequest, response: Response, db: DatabaseSession) -> SessionResponse:
    token, csrf, result = await service.login(db, payload)
    max_age = settings.session_idle_minutes * 60
    response.set_cookie(SESSION_COOKIE, token, max_age=max_age, httponly=True, secure=cookie_secure(), samesite="lax", path="/")
    response.set_cookie(CSRF_COOKIE, csrf, max_age=max_age, httponly=False, secure=cookie_secure(), samesite="lax", path="/")
    return result

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
async def logout(response: Response, current: CurrentUserDependency, db: DatabaseSession) -> None:
    from datetime import datetime, timezone
    from hr_aiaas.db.models.identity import Session
    from sqlalchemy import select
    item = await db.scalar(select(Session).where(Session.token_hash == hash_session_token(current.session_token), Session.revoked_at.is_(None)))
    if item:
        item.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")

@router.get("/session", response_model=SessionResponse)
async def current_session(current: CurrentUserDependency, db: DatabaseSession) -> SessionResponse:
    from datetime import datetime, timezone
    from hr_aiaas.db.models.identity import Session
    from sqlalchemy import select
    item = await db.scalar(select(Session).where(Session.token_hash == hash_session_token(current.session_token), Session.revoked_at.is_(None)))
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Session not found.")
    return service.response_for(current, item.expires_at)
