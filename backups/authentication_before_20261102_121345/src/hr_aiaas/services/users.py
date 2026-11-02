from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hr_aiaas.api.schemas.users import UserCreate, UserListResponse, UserResponse, UserUpdate
from hr_aiaas.db.models.identity import User
from hr_aiaas.repositories import auth as auth_repository
from hr_aiaas.repositories import users as repository
from hr_aiaas.security.passwords import hash_password

async def as_response(db: AsyncSession, user: User) -> UserResponse:
    roles, _ = await auth_repository.get_access(db, user.id)
    return UserResponse(public_id=user.public_id, email=user.email, full_name=user.full_name, is_active=user.is_active, is_superuser=user.is_superuser, last_login_at=user.last_login_at, created_at=user.created_at, updated_at=user.updated_at, roles=roles)

async def list_users(db: AsyncSession, limit: int, offset: int) -> UserListResponse:
    items, total = await repository.list_users(db, limit, offset)
    return UserListResponse(items=[await as_response(db, item) for item in items], total=total, limit=limit, offset=offset)

async def create_user(db: AsyncSession, payload: UserCreate, actor_id: int) -> UserResponse:
    email = str(payload.email).lower()
    if await repository.email_exists(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "EMAIL_EXISTS", "message": "A user with this email already exists."})
    now = datetime.now(timezone.utc)
    user = User(public_id=str(uuid4()), email=email, password_hash=hash_password(payload.password), full_name=payload.full_name.strip(), is_active=True, is_superuser=False, created_at=now, updated_at=now)
    db.add(user)
    await db.flush()
    await repository.replace_roles(db, user.id, payload.role_ids, actor_id, now)
    await db.commit()
    return await as_response(db, user)

async def get_user(db: AsyncSession, public_id: str) -> UserResponse:
    user = await repository.get_user_by_public_id(db, public_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "USER_NOT_FOUND", "message": "User was not found."})
    return await as_response(db, user)

async def update_user(db: AsyncSession, public_id: str, payload: UserUpdate, actor_id: int) -> UserResponse:
    user = await repository.get_user_by_public_id(db, public_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "USER_NOT_FOUND", "message": "User was not found."})
    now = datetime.now(timezone.utc)
    if payload.full_name is not None: user.full_name = payload.full_name.strip()
    if payload.is_active is not None: user.is_active = payload.is_active
    if payload.role_ids is not None: await repository.replace_roles(db, user.id, payload.role_ids, actor_id, now)
    user.updated_at = now
    await db.commit()
    return await as_response(db, user)
