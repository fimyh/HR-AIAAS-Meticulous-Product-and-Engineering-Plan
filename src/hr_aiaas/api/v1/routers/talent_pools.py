from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/talent-pools", tags=["talent pools"])

class TalentPoolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None

@router.get("")
async def list_talent_pools() -> list[dict[str, object]]:
    not_implemented("List talent pools")

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_talent_pool(payload: TalentPoolCreate) -> dict[str, object]:
    del payload
    not_implemented("Create talent pool")

@router.get("/{pool_id}")
async def get_talent_pool(pool_id: int) -> dict[str, object]:
    del pool_id
    not_implemented("Get talent pool")

@router.post("/{pool_id}/candidates/{candidate_public_id}")
async def add_member(pool_id: int, candidate_public_id: str, reason: str) -> dict[str, object]:
    del pool_id, candidate_public_id, reason
    not_implemented("Add talent pool member")

@router.delete("/{pool_id}/candidates/{candidate_public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(pool_id: int, candidate_public_id: str) -> None:
    del pool_id, candidate_public_id
    not_implemented("Remove talent pool member")
