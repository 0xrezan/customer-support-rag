"""Retrieved chunk + score value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.value_objects.chunk_metadata import ChunkMetadata


@dataclass(frozen=True)
class RetrievalResult:
    """A single chunk returned by the vector store query."""

    chunk_id: str
    text: str
    score: float
    metadata: ChunkMetadata

    @property
    def document_name(self) -> str:
        return self.metadata.document_name

    @property
    def page(self) -> int:
        return self.metadata.page
