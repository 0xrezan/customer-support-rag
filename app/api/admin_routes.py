"""Admin endpoints — document upload, status, reindex, delete."""

from __future__ import annotations

import uuid  # noqa: TC003 - FastAPI resolves path param types at runtime

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status

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
from app.schemas.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
    document_to_response,
)
from app.security.admin_auth import require_admin_token

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_token)])


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    upload_service=Depends(get_upload_service),
    settings=Depends(get_settings),
) -> ResponseEnvelope[DocumentUploadResponse]:
    """Upload a document for ingestion."""
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

    return ResponseEnvelope(
        data=DocumentUploadResponse(
            document=document_to_response(doc),
            is_new=is_new,
            message="Document registered and ingestion enqueued"
            if is_new
            else "Duplicate document",
        )
    )


@router.get("/documents")
async def list_documents(
    document_repo=Depends(get_document_repo),
) -> ResponseEnvelope[DocumentListResponse]:
    """List all documents."""
    docs = await document_repo.list_all()
    items = [document_to_response(d) for d in docs]
    return ResponseEnvelope(data=DocumentListResponse(documents=items, total=len(items)))


@router.get("/documents/{doc_id}")
async def get_document_status(
    doc_id: uuid.UUID,
    document_repo=Depends(get_document_repo),
) -> ResponseEnvelope[DocumentResponse]:
    """Get a document's current status."""
    doc = await document_repo.get_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return ResponseEnvelope(data=document_to_response(doc))


@router.post("/documents/{doc_id}/reindex")
async def reindex_document(
    doc_id: uuid.UUID,
    document_repo=Depends(get_document_repo),
    upload_service=Depends(get_upload_service),
) -> ResponseEnvelope[dict]:
    """Trigger re-indexing of a document."""
    doc = await document_repo.get_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    from app.infrastructure.queue.tasks import reindex_document_task

    reindex_document_task.send(str(doc_id))
    return ResponseEnvelope(data={"message": "Reindex enqueued", "document_id": str(doc_id)})


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    hard: bool = False,
    document_repo=Depends(get_document_repo),
    request: Request = None,  # type: ignore[assignment]
) -> ResponseEnvelope[dict]:
    """Delete a document. Use ``?hard=true`` for permanent removal.

    Soft delete (default): enqueues a background task that marks the document
    deleted and removes its chunks from the vector store.

    Hard delete: removes vector-store chunks inline, then permanently deletes
    the database row.  Does **not** enqueue a background task (BUG-5 fix:
    the row would already be gone by the time the task runs).
    """
    doc = await document_repo.get_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if hard:
        # Clean up vector-store entries inline, then hard-delete the row.
        try:
            container = request.app.state.container
            container.chunk_index_repo.delete_by_document(str(doc_id))
        except Exception:
            logger.exception("admin.hard_delete.chroma_cleanup_failed", doc_id=str(doc_id))
        await document_repo.hard_delete(doc_id)
        return ResponseEnvelope(
            data={"message": "Hard delete executed", "document_id": str(doc_id)}
        )

    from app.infrastructure.queue.tasks import delete_document_task

    delete_document_task.send(str(doc_id))
    return ResponseEnvelope(data={"message": "Soft delete enqueued", "document_id": str(doc_id)})
