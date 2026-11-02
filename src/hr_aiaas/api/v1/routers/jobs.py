from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/jobs", tags=["jobs and scorecards"])

class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    department: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=250)
    employment_type: str | None = Field(default=None, max_length=100)
    description: str | None = None

class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str | None = None
    status: str | None = None

@router.get("")
async def list_jobs(status_filter: str | None = Query(default=None, alias="status"), limit: int = Query(25, ge=1, le=100)) -> dict[str, object]:
    del status_filter, limit
    not_implemented("List jobs")

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate) -> dict[str, object]:
    del payload
    not_implemented("Create job")

@router.get("/{public_id}")
async def get_job(public_id: str) -> dict[str, object]:
    del public_id
    not_implemented("Get job")

@router.patch("/{public_id}")
async def update_job(public_id: str, payload: JobUpdate) -> dict[str, object]:
    del public_id, payload
    not_implemented("Update job")

@router.get("/{public_id}/requirements")
async def list_requirements(public_id: str) -> list[dict[str, object]]:
    del public_id
    not_implemented("List job requirements")

@router.put("/{public_id}/requirements")
async def replace_requirements(public_id: str, requirements: list[dict[str, object]]) -> list[dict[str, object]]:
    del public_id, requirements
    not_implemented("Replace job requirements")

@router.get("/{public_id}/scorecards")
async def list_scorecards(public_id: str) -> list[dict[str, object]]:
    del public_id
    not_implemented("List scorecards")

@router.post("/{public_id}/scorecards", status_code=status.HTTP_201_CREATED)
async def create_scorecard(public_id: str, payload: dict[str, object]) -> dict[str, object]:
    del public_id, payload
    not_implemented("Create scorecard version")

@router.post("/{public_id}/scorecards/{scorecard_id}/approve")
async def approve_scorecard(public_id: str, scorecard_id: int) -> dict[str, object]:
    del public_id, scorecard_id
    not_implemented("Approve scorecard")
