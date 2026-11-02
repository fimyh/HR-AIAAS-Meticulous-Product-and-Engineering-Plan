from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/candidates", tags=["candidates"])

class CandidateCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    professional_summary: str | None = None
    source_language: str | None = Field(default=None, max_length=20)

class CandidateUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    professional_summary: str | None = None
    profile_status: str | None = Field(default=None, max_length=50)

@router.get("")
async def list_candidates(
    query: str | None = None, status_filter: str | None = Query(default=None, alias="status"),
    skill: list[str] = Query(default=[]), limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    del query, status_filter, skill, limit, offset
    not_implemented("List and search candidates")

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_candidate(payload: CandidateCreate) -> dict[str, object]:
    del payload
    not_implemented("Create candidate")

@router.get("/{public_id}")
async def get_candidate(public_id: str) -> dict[str, object]:
    del public_id
    not_implemented("Get candidate")

@router.patch("/{public_id}")
async def update_candidate(public_id: str, payload: CandidateUpdate) -> dict[str, object]:
    del public_id, payload
    not_implemented("Update candidate")

@router.post("/{public_id}/archive")
async def archive_candidate(public_id: str) -> dict[str, object]:
    del public_id
    not_implemented("Archive candidate")

@router.post("/{public_id}/merge")
async def merge_candidate(public_id: str, source_public_id: str) -> dict[str, object]:
    del public_id, source_public_id
    not_implemented("Merge candidates")

@router.get("/{public_id}/facts")
async def list_candidate_facts(public_id: str, review_status: str | None = None) -> list[dict[str, object]]:
    del public_id, review_status
    not_implemented("List extracted candidate facts")

@router.post("/{public_id}/facts/{fact_id}/confirm")
async def confirm_fact(public_id: str, fact_id: int) -> dict[str, object]:
    del public_id, fact_id
    not_implemented("Confirm extracted fact")

@router.post("/{public_id}/facts/{fact_id}/correct")
async def correct_fact(public_id: str, fact_id: int, value: object, reason: str) -> dict[str, object]:
    del public_id, fact_id, value, reason
    not_implemented("Correct extracted fact")

@router.get("/{public_id}/export")
async def export_candidate(public_id: str) -> dict[str, object]:
    del public_id
    not_implemented("Export candidate data")

@router.post("/{public_id}/deletion-requests", status_code=status.HTTP_202_ACCEPTED)
async def request_deletion(public_id: str, reason: str) -> dict[str, object]:
    del public_id, reason
    not_implemented("Request candidate deletion")
