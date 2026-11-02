from fastapi import APIRouter, Query

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/audit-events", tags=["audit and privacy"])

@router.get("")
async def list_audit_events(
    resource_type: str | None = None, user_public_id: str | None = None,
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
) -> dict[str, object]:
    del resource_type, user_public_id, limit, offset
    not_implemented("List audit events")

@router.get("/{event_id}")
async def get_audit_event(event_id: int) -> dict[str, object]:
    del event_id
    not_implemented("Get audit event")

@router.get("/privacy/deletion-requests")
async def list_deletion_requests() -> list[dict[str, object]]:
    not_implemented("List deletion requests")

@router.post("/privacy/deletion-requests/{request_id}/approve")
async def approve_deletion_request(request_id: int) -> dict[str, object]:
    del request_id
    not_implemented("Approve deletion request")
