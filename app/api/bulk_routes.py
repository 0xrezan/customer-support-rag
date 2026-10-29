"""Bulk upload and reindex endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.deps import get_document_repo, get_upload_service
from app.api.uploads import read_upload_file
from app.config import get_settings
from app.domain.services.upload_validation import (
    InvalidUploadFilenameError,
    UnsupportedUploadTypeError,
    UploadTooLargeError,
    UploadValidationError,
)
from app.logging import get_logger
from app.schemas.common import ResponseEnvelope
from app.security.admin_auth import require_admin_token

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin/bulk",
    dependencies=[Depends(require_admin_token)],
)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload(
    files: list[UploadFile],
    upload_service=Depends(get_upload_service),
    settings=Depends(get_settings),
) -> ResponseEnvelope[dict]:
    """Upload multiple documents at once."""
    results: list[dict] = []

    for file in files:
        try:
            upload = await read_upload_file(
                file,
                max_size_bytes=settings.max_upload_size_bytes,
                allowed_extensions=set(settings.allowed_upload_extensions),
                allowed_mime_types=set(settings.allowed_upload_mime_types),
            )
        except InvalidUploadFilenameError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except UploadTooLargeError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except UnsupportedUploadTypeError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except UploadValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        doc, is_new = await upload_service.register(
            upload.file_bytes,
            upload.filename,
            upload.mime_type,
        )
        if is_new:
            upload_service.enqueue_ingestion(doc.id)

        results.append(
            {
                "filename": upload.filename,
                "document_id": str(doc.id),
                "is_new": is_new,
                "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
            }
        )

    logger.info("bulk.upload", count=len(results))
    return ResponseEnvelope(
        data={
            "uploaded": len(results),
            "documents": results,
        }
    )


@router.post("/reindex")
async def bulk_reindex(
    document_repo=Depends(get_document_repo),
) -> ResponseEnvelope[dict]:
    """Trigger re-indexing of all active documents."""
    from app.infrastructure.queue.tasks import reindex_document_task

    docs = await document_repo.list_active()
    enqueued = 0
    for doc in docs:
        reindex_document_task.send(str(doc.id))
        enqueued += 1

    logger.info("bulk.reindex", count=enqueued)
    return ResponseEnvelope(
        data={
            "message": f"Reindex enqueued for {enqueued} documents",
            "count": enqueued,
        }
    )
