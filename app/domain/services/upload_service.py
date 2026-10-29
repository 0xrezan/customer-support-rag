"""Register files, compute hash, deduplicate, create document row, enqueue ingestion."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from app.domain.services.upload_validation import validate_upload
from app.infrastructure.db.models import Document, DocumentStatus
from app.logging import get_logger
from app.utils.hashing import content_hash

if TYPE_CHECKING:
    from app.config import Settings
    from app.infrastructure.db.repositories.documents import DocumentRepository
    from app.infrastructure.db.repositories.ingestion_jobs import (
        IngestionJobRepository,
    )

logger = get_logger(__name__)


class UploadService:
    """Handles document registration and deduplication."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        job_repo: IngestionJobRepository,
        settings: Settings | None = None,
    ) -> None:
        self._doc_repo = document_repo
        self._job_repo = job_repo
        self._upload_dir = Path(settings.upload_dir if settings else "uploads")
        self._max_upload_size_bytes = (
            settings.max_upload_size_bytes if settings else 50 * 1024 * 1024
        )
        self._allowed_upload_extensions = (
            set(settings.allowed_upload_extensions)
            if settings
            else {".pdf", ".txt", ".md", ".markdown"}
        )
        self._allowed_upload_mime_types = (
            set(settings.allowed_upload_mime_types)
            if settings
            else {
                "application/pdf",
                "application/octet-stream",
                "text/markdown",
                "text/plain",
            }
        )
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    async def register(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str = "application/octet-stream",
    ) -> tuple[Document, bool]:
        """Register a document.

        Returns:
            (document, is_new) — if the document already exists with the
            same content hash, the existing row is returned and ``is_new``
            is False.
        """
        validated = validate_upload(
            file_bytes=file_bytes,
            filename=filename,
            mime_type=mime_type,
            max_size_bytes=self._max_upload_size_bytes,
            allowed_extensions=self._allowed_upload_extensions,
            allowed_mime_types=self._allowed_upload_mime_types,
        )
        file_bytes = validated.file_bytes
        filename = validated.filename
        mime_type = validated.mime_type

        file_hash = content_hash(file_bytes)
        existing = await self._doc_repo.get_by_hash(file_hash)
        if existing and existing.status not in (
            DocumentStatus.DELETED,
            DocumentStatus.FAILED_PARSE,
            DocumentStatus.FAILED_INDEX,
        ):
            logger.info(
                "upload.deduplicated",
                filename=filename,
                content_hash=file_hash,
                existing_id=str(existing.id),
            )
            return existing, False

        version = (existing.version + 1) if existing else 1

        doc_id = uuid.uuid4()
        doc = Document(
            filename=filename,
            content_hash=file_hash,
            file_size=len(file_bytes),
            mime_type=mime_type,
            version=version,
            status=DocumentStatus.UPLOADED,
        )
        doc.id = doc_id  # set explicitly — MappedAsDataclass init=False won't auto-generate
        doc = await self._doc_repo.create(doc)
        # Restore id after session detach (MappedAsDataclass loses it)
        doc.id = doc_id

        # Save file to disk so the worker can read it later
        file_path = self._upload_dir / str(doc_id)
        file_path.write_bytes(file_bytes)

        # Create an ingestion job via raw INSERT to bypass MappedAsDataclass issues
        await self._job_repo.create_for_document(doc_id)

        logger.info(
            "upload.registered",
            doc_id=str(doc_id),
            filename=filename,
            version=version,
        )
        return doc, True

    def enqueue_ingestion(self, document_id: uuid.UUID) -> None:
        """Enqueue the background ingestion task."""
        from app.infrastructure.queue.tasks import ingest_document_task

        ingest_document_task.send(str(document_id))
        logger.info("upload.enqueued", doc_id=str(document_id))
