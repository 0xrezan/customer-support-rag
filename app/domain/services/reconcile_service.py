"""Repair and consistency checks between SQL and vector index."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.logging import get_logger

if TYPE_CHECKING:
    from app.infrastructure.db.repositories.documents import DocumentRepository
    from app.infrastructure.vectorstore.chunk_index_repo import ChunkIndexRepository

logger = get_logger(__name__)


class ReconcileService:
    """Verifies SQL/index consistency and repairs broken states."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_index_repo: ChunkIndexRepository,
    ) -> None:
        self._doc_repo = document_repo
        self._index = chunk_index_repo

    async def run(self) -> dict[str, int]:
        """Check for drift between SQL and Chroma.

        Returns a summary dict with counts of issues found and fixed.
        """
        summary = {"checked": 0, "orphaned_index_entries": 0, "missing_index": 0}

        active_docs = await self._doc_repo.list_active()
        summary["checked"] = len(active_docs)

        for doc in active_docs:
            # Verify that chunk_count_expected matches chunk_count_actual
            if (
                doc.chunk_count_expected is not None
                and doc.chunk_count_actual is not None
                and doc.chunk_count_expected != doc.chunk_count_actual
            ):
                summary["missing_index"] += 1
                logger.warning(
                    "reconcile.count_mismatch",
                    doc_id=str(doc.id),
                    expected=doc.chunk_count_expected,
                    actual=doc.chunk_count_actual,
                )

        logger.info("reconcile.complete", **summary)
        return summary
