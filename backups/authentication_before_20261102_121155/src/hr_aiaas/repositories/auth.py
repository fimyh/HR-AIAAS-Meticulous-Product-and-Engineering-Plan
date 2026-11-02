from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hr_aiaas.db.models.identity import Permission, Role, RolePermission, Session, User, UserRole

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email.lower()))

async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)

async def get_access(session: AsyncSession, user_id: int) -> tuple[list[str], list[str]]:
    roles = list((await session.scalars(select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id))).all())
    permissions = list((await session.scalars(select(Permission.code).join(RolePermission, RolePermission.permission_id == Permission.id).join(UserRole, UserRole.role_id == RolePermission.role_id).where(UserRole.user_id == user_id).distinct())).all())
    return roles, permissions

async def create_session(session: AsyncSession, user_id: int, token_hash: str, now: datetime, expires_at: datetime) -> Session:
    item = Session(user_id=user_id, token_hash=token_hash, expires_at=expires_at, last_activity_at=now, created_at=now)
    session.add(item)
    await session.flush()
    return item

async def get_active_session(session: AsyncSession, token_hash: str, now: datetime) -> Session | None:
    return await session.scalar(select(Session).where(Session.token_hash == token_hash, Session.revoked_at.is_(None), Session.expires_at > now))
