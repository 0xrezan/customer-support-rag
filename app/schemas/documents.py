"""Pydantic document request / response schemas."""

from __future__ import annotations

import uuid  # noqa: TC003
from datetime import datetime  # noqa: TC003

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_hash: str
    file_size: int
    mime_type: str
    version: int
    is_active_version: bool
    status: str
    chunk_count_expected: int | None = None
    chunk_count_actual: int | None = None
    page_count: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    is_new: bool
    message: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


def document_to_response(doc: object) -> DocumentResponse:
    """Convert a Document ORM model to a DocumentResponse schema."""
    return DocumentResponse(
        id=doc.id,  # type: ignore[arg-type]
        filename=doc.filename,  # type: ignore[arg-type]
        content_hash=doc.content_hash,  # type: ignore[arg-type]
        file_size=doc.file_size,  # type: ignore[arg-type]
        mime_type=doc.mime_type,  # type: ignore[arg-type]
        version=doc.version,  # type: ignore[arg-type]
        is_active_version=doc.is_active_version,  # type: ignore[arg-type]
        status=doc.status.value if hasattr(doc.status, "value") else str(doc.status),  # type: ignore[arg-type]
        chunk_count_expected=doc.chunk_count_expected,  # type: ignore[arg-type]
        chunk_count_actual=doc.chunk_count_actual,  # type: ignore[arg-type]
        page_count=doc.page_count,  # type: ignore[arg-type]
        error_message=doc.error_message,  # type: ignore[arg-type]
        created_at=doc.created_at,  # type: ignore[arg-type]
        updated_at=doc.updated_at,  # type: ignore[arg-type]
    )
