from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from hr_aiaas.api.errors import not_implemented

router = APIRouter(prefix="/documents", tags=["documents and ingestion"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF or DOCX CV")],
    candidate_public_id: Annotated[str | None, Form()] = None,
) -> dict[str, object]:
    del file, candidate_public_id
    not_implemented("CV upload")

@router.get("/{public_id}")
async def get_document(public_id: str) -> dict[str, object]:
    del public_id
    not_implemented("Get document metadata")

@router.get("/{public_id}/download", response_class=FileResponse)
async def download_document(public_id: str) -> FileResponse:
    del public_id
    not_implemented("Document download")

@router.get("/{public_id}/versions")
async def list_document_versions(public_id: str) -> list[dict[str, object]]:
    del public_id
    not_implemented("List document versions")

@router.post("/{public_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_document(public_id: str) -> dict[str, object]:
    del public_id
    not_implemented("Reprocess document")

@router.get("/ingestion-jobs/{job_public_id}")
async def get_ingestion_job(job_public_id: str) -> dict[str, object]:
    del job_public_id
    not_implemented("Ingestion job status")

@router.post("/ingestion-jobs/{job_public_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_ingestion_job(job_public_id: str) -> dict[str, object]:
    del job_public_id
    not_implemented("Cancel ingestion job")
