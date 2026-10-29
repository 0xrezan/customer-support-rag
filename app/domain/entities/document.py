"""Document aggregate with status and version."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import datetime


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    INDEXING = "indexing"
    INDEXED = "indexed"
    NEEDS_OCR = "needs_ocr"
    NEEDS_REVIEW = "needs_review"
    FAILED_PARSE = "failed_parse"
    FAILED_INDEX = "failed_index"
    DELETED = "deleted"


# Allowed status transitions (current -> set of valid next statuses)
_TRANSITIONS: dict[DocumentStatus, set[DocumentStatus]] = {
    DocumentStatus.UPLOADED: {DocumentStatus.PARSING, DocumentStatus.DELETED},
    DocumentStatus.PARSING: {
        DocumentStatus.INDEXING,
        DocumentStatus.NEEDS_OCR,
        DocumentStatus.NEEDS_REVIEW,
        DocumentStatus.FAILED_PARSE,
    },
    DocumentStatus.INDEXING: {
        DocumentStatus.INDEXED,
        DocumentStatus.FAILED_INDEX,
    },
    DocumentStatus.INDEXED: {
        DocumentStatus.PARSING,  # re-index
        DocumentStatus.DELETED,
    },
    DocumentStatus.NEEDS_OCR: {DocumentStatus.PARSING, DocumentStatus.DELETED},
    DocumentStatus.NEEDS_REVIEW: {DocumentStatus.PARSING, DocumentStatus.DELETED},
    DocumentStatus.FAILED_PARSE: {DocumentStatus.PARSING, DocumentStatus.DELETED},
    DocumentStatus.FAILED_INDEX: {DocumentStatus.PARSING, DocumentStatus.DELETED},
    DocumentStatus.DELETED: set(),
}


@dataclass
class DocumentEntity:
    """Domain-level document representation."""

    id: uuid.UUID
    filename: str
    content_hash: str
    file_size: int = 0
    mime_type: str = "application/octet-stream"
    version: int = 1
    is_active_version: bool = False
    status: DocumentStatus = DocumentStatus.UPLOADED
    chunk_count_expected: int | None = None
    chunk_count_actual: int | None = None
    page_count: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ── invariants ──────────────────────────────────────────

    def can_transition_to(self, target: DocumentStatus) -> bool:
        return target in _TRANSITIONS.get(self.status, set())

    def transition_to(self, target: DocumentStatus) -> None:
        if not self.can_transition_to(target):
            msg = f"Invalid transition: {self.status} -> {target}"
            raise ValueError(msg)
        self.status = target

    @property
    def is_terminal(self) -> bool:
        return self.status == DocumentStatus.DELETED

    @property
    def needs_reprocessing(self) -> bool:
        return self.status in {
            DocumentStatus.NEEDS_OCR,
            DocumentStatus.NEEDS_REVIEW,
            DocumentStatus.FAILED_PARSE,
            DocumentStatus.FAILED_INDEX,
        }
