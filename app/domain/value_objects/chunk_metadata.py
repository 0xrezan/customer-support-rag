"""Chunk metadata value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid


@dataclass(frozen=True)
class ChunkMetadata:
    """Immutable metadata attached to every text chunk."""

    chunk_id: str
    document_id: uuid.UUID
    document_name: str
    document_version: int
    page: int
    chunk_index: int
    source_type: str = "pdf"
    is_active: bool = True
    knowledge_base_id: uuid.UUID | None = None

    def to_dict(self) -> dict[str, str | int | bool]:
        """Serialise for Chroma metadata storage."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": str(self.document_id),
            "document_name": self.document_name,
            "document_version": self.document_version,
            "page": self.page,
            "chunk_index": self.chunk_index,
            "source_type": self.source_type,
            "is_active": self.is_active,
            "knowledge_base_id": str(self.knowledge_base_id) if self.knowledge_base_id else "",
        }
