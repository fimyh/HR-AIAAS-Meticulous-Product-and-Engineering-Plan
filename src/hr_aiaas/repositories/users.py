from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hr_aiaas.db.models.identity import Permission, Role, User, UserRole

async def list_users(session: AsyncSession, limit: int, offset: int) -> tuple[list[User], int]:
    items = list((await session.scalars(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset))).all())
    total = int((await session.scalar(select(func.count()).select_from(User))) or 0)
    return items, total

async def get_user_by_public_id(session: AsyncSession, public_id: str) -> User | None:
    return await session.scalar(select(User).where(User.public_id == public_id))

async def email_exists(session: AsyncSession, email: str) -> bool:
    return bool(await session.scalar(select(User.id).where(User.email == email.lower())))

async def replace_roles(session: AsyncSession, user_id: int, role_ids: list[int], actor_id: int, now: datetime) -> None:
    existing = list((await session.scalars(select(UserRole).where(UserRole.user_id == user_id))).all())
    for item in existing:
        await session.delete(item)
    for role_id in sorted(set(role_ids)):
        session.add(UserRole(user_id=user_id, role_id=role_id, assigned_by_id=actor_id, assigned_at=now))

async def list_roles(session: AsyncSession) -> list[Role]:
    return list((await session.scalars(select(Role).order_by(Role.name))).all())

async def list_permissions(session: AsyncSession) -> list[Permission]:
    return list((await session.scalars(select(Permission).order_by(Permission.resource, Permission.action))).all())
