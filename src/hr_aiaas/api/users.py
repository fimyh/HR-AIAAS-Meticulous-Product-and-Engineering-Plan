from fastapi import APIRouter, status
from pydantic import BaseModel

from hr_aiaas.api.errors import not_implemented

router = APIRouter(tags=["matching and shortlists"])

class MatchRequest(BaseModel):
    job_public_id: str
    scorecard_id: int
    candidate_public_ids: list[str] | None = None

@router.post("/matches", status_code=status.HTTP_202_ACCEPTED)
async def run_match(payload: MatchRequest) -> dict[str, object]:
    del payload
    not_implemented("Run deterministic matching")

@router.get("/matches/{run_public_id}")
async def get_match_run(run_public_id: str) -> dict[str, object]:
    del run_public_id
    not_implemented("Get match run")

@router.get("/matches/{run_public_id}/scores")
async def list_match_scores(run_public_id: str) -> list[dict[str, object]]:
    del run_public_id
    not_implemented("List match scores")

@router.get("/matches/{run_public_id}/scores/{candidate_public_id}")
async def get_candidate_match(run_public_id: str, candidate_public_id: str) -> dict[str, object]:
    del run_public_id, candidate_public_id
    not_implemented("Get candidate match explanation")

@router.get("/jobs/{job_public_id}/shortlists")
async def list_shortlists(job_public_id: str) -> list[dict[str, object]]:
    del job_public_id
    not_implemented("List shortlists")

@router.post("/jobs/{job_public_id}/shortlists", status_code=status.HTTP_201_CREATED)
async def create_shortlist(job_public_id: str, name: str) -> dict[str, object]:
    del job_public_id, name
    not_implemented("Create shortlist")

@router.post("/shortlists/{shortlist_id}/candidates/{candidate_public_id}")
async def add_to_shortlist(shortlist_id: int, candidate_public_id: str, reason: str) -> dict[str, object]:
    del shortlist_id, candidate_public_id, reason
    not_implemented("Add candidate to shortlist")

@router.delete("/shortlists/{shortlist_id}/candidates/{candidate_public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_shortlist(shortlist_id: int, candidate_public_id: str) -> None:
    del shortlist_id, candidate_public_id
    not_implemented("Remove candidate from shortlist")
