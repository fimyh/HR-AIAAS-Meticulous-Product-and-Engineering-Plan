from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from hr_aiaas.api.dependencies import CurrentUser, DatabaseSession, require_csrf, require_permission
from hr_aiaas.api.schemas.users import PermissionResponse, RoleResponse, UserCreate, UserListResponse, UserResponse, UserUpdate
from hr_aiaas.repositories import users as repository
from hr_aiaas.services import users as service

router = APIRouter(prefix="/users", tags=["users and access"])
UsersRead = Annotated[CurrentUser, Depends(require_permission("users.read"))]
UsersWrite = Annotated[CurrentUser, Depends(require_permission("users.write"))]

@router.get("", response_model=UserListResponse)
async def list_users(current: UsersRead, db: DatabaseSession, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)) -> UserListResponse:
    del current
    return await service.list_users(db, limit, offset)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
async def create_user(payload: UserCreate, current: UsersWrite, db: DatabaseSession) -> UserResponse:
    return await service.create_user(db, payload, current.user.id)

# Static access routes must be registered before /{public_id}.
@router.get("/access/roles", response_model=list[RoleResponse])
async def list_roles(current: UsersRead, db: DatabaseSession) -> list[RoleResponse]:
    del current
    return [RoleResponse.model_validate(item) for item in await repository.list_roles(db)]

@router.get("/access/permissions", response_model=list[PermissionResponse])
async def list_permissions(current: UsersRead, db: DatabaseSession) -> list[PermissionResponse]:
    del current
    return [PermissionResponse.model_validate(item) for item in await repository.list_permissions(db)]

@router.get("/{public_id}", response_model=UserResponse)
async def get_user(public_id: str, current: UsersRead, db: DatabaseSession) -> UserResponse:
    del current
    return await service.get_user(db, public_id)

@router.patch("/{public_id}", response_model=UserResponse, dependencies=[Depends(require_csrf)])
async def update_user(public_id: str, payload: UserUpdate, current: UsersWrite, db: DatabaseSession) -> UserResponse:
    return await service.update_user(db, public_id, payload, current.user.id)
