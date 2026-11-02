from fastapi import APIRouter
from pydantic import BaseModel, Field

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/assistant", tags=["HR assistant"])

class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    candidate_public_ids: list[str] = []
    job_public_id: str | None = None

@router.post("/query")
async def assistant_query(payload: AssistantRequest) -> dict[str, object]:
    del payload
    not_implemented("Read-only HR assistant query")

@router.post("/search-filters")
async def generate_search_filters(message: str) -> dict[str, object]:
    del message
    not_implemented("Natural-language search filters")

@router.post("/interview-questions")
async def suggest_interview_questions(candidate_public_id: str, job_public_id: str) -> dict[str, object]:
    del candidate_public_id, job_public_id
    not_implemented("Evidence-based interview questions")
