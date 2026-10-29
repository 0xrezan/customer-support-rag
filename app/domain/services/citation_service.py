"""Build and deduplicate source citations from retrieved chunk metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.value_objects.answer_result import Citation

if TYPE_CHECKING:
    from app.domain.value_objects.retrieval_result import RetrievalResult


class CitationService:
    """Builds first-class citation objects from chunk metadata — no LLM parsing."""

    def build(self, results: list[RetrievalResult]) -> list[Citation]:
        """Return deduplicated citations from retrieval results."""
        seen: set[tuple[str, int]] = set()
        citations: list[Citation] = []

        for r in results:
            key = (r.metadata.document_name, r.metadata.page)
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                Citation(
                    document_name=r.metadata.document_name,
                    page=r.metadata.page,
                    chunk_id=r.chunk_id,
                )
            )

        return citations
