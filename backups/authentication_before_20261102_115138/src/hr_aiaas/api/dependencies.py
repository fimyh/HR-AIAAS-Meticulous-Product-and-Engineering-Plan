from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hr_aiaas.db.session import get_db_session

DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


async def require_request_id(
    x_request_id: Annotated[str | None, Header()] = None,
) -> str:
    return x_request_id or "unassigned"


async def require_authenticated_user() -> None:
    # Replace with the real session resolver before protecting production data.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "AUTH_NOT_IMPLEMENTED",
            "message": "Authentication middleware is not implemented yet.",
        },
    )
