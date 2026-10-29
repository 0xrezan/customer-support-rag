"""Add / query / delete chunk records in ChromaDB."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from app.domain.value_objects.chunk_metadata import ChunkMetadata
from app.domain.value_objects.retrieval_result import RetrievalResult
from app.infrastructure.vectorstore.collections import ensure_collection
from app.logging import get_logger

if TYPE_CHECKING:
    import chromadb

logger = get_logger(__name__)


class ChunkIndexRepository:
    """Thin adapter over a single Chroma collection."""

    def __init__(self, client: chromadb.HttpClient, collection_name: str) -> None:
        self._client = client
        self._collection_name = collection_name
        self._collection: chromadb.Collection | None = None

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._collection = ensure_collection(self._client, self._collection_name)
        return self._collection

    # ── write ────────────────────────────────────────────────

    def add_chunks(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert chunks into the collection."""
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("chunk_index.upserted", count=len(ids))

    # ── read ─────────────────────────────────────────────────

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Query the collection and return typed retrieval results."""
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        raw = self.collection.query(**kwargs)

        results: list[RetrievalResult] = []
        if not raw["ids"] or not raw["ids"][0]:
            return results

        for i, chunk_id in enumerate(raw["ids"][0]):
            distance = raw["distances"][0][i] if raw["distances"] else 1.0
            score = 1.0 - distance  # cosine distance -> similarity
            text = raw["documents"][0][i] if raw["documents"] else ""
            meta_raw = raw["metadatas"][0][i] if raw["metadatas"] else {}

            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                document_id=meta_raw.get("document_id", ""),
                document_name=meta_raw.get("document_name", ""),
                document_version=int(meta_raw.get("document_version", 0)),
                page=int(meta_raw.get("page", 0)),
                chunk_index=int(meta_raw.get("chunk_index", 0)),
                source_type=meta_raw.get("source_type", ""),
                is_active=bool(meta_raw.get("is_active", True)),
            )
            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=text,
                    score=score,
                    metadata=metadata,
                )
            )

        return results

    def get_by_ids(
        self,
        ids: list[str],
        query_embedding: list[float] | None = None,
    ) -> list[RetrievalResult]:
        """Fetch chunks by their IDs (for BM25 hybrid merge lookups).

        With ``query_embedding`` each result is scored by cosine similarity, the
        same scale ``query`` uses; otherwise the score is 0.
        """
        if not ids:
            return []
        include = ["documents", "metadatas"]
        if query_embedding is not None:
            include.append("embeddings")
        raw = self.collection.get(ids=ids, include=include)
        embeddings = raw.get("embeddings") if query_embedding is not None else None

        results: list[RetrievalResult] = []
        for i, chunk_id in enumerate(raw["ids"]):
            text = raw["documents"][i] if raw["documents"] else ""
            meta_raw = raw["metadatas"][i] if raw["metadatas"] else {}
            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                document_id=meta_raw.get("document_id", ""),
                document_name=meta_raw.get("document_name", ""),
                document_version=int(meta_raw.get("document_version", 0)),
                page=int(meta_raw.get("page", 0)),
                chunk_index=int(meta_raw.get("chunk_index", 0)),
                source_type=meta_raw.get("source_type", ""),
                is_active=bool(meta_raw.get("is_active", True)),
            )
            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=text,
                    score=(
                        _cosine(query_embedding, embeddings[i])
                        if query_embedding is not None and embeddings is not None
                        else 0.0
                    ),
                    metadata=metadata,
                )
            )
        return results

    def get_all_chunk_texts(self) -> list[tuple[str, str]]:
        """Return all (chunk_id, text) pairs for BM25 index building."""
        total = self.count()
        if total == 0:
            return []
        raw = self.collection.get(
            include=["documents"],
            limit=total,
        )
        return list(zip(raw["ids"], raw["documents"], strict=False))

    # ── delete ───────────────────────────────────────────────

    def delete_by_document_version(
        self,
        document_id: str,
        version: int,
    ) -> None:
        """Delete all chunks for a given document + version."""
        self.collection.delete(
            where={
                "$and": [
                    {"document_id": document_id},
                    {"document_version": version},
                ]
            }
        )
        logger.info(
            "chunk_index.deleted",
            document_id=document_id,
            version=version,
        )

    def delete_by_document(self, document_id: str) -> None:
        """Delete all chunks for a given document (all versions)."""
        self.collection.delete(where={"document_id": document_id})
        logger.info("chunk_index.deleted_all", document_id=document_id)

    def count(self) -> int:
        return self.collection.count()


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0
