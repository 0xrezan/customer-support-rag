"""Deterministic ID builders for chunks and document versions."""

from __future__ import annotations

import uuid


def make_chunk_id(
    document_id: uuid.UUID,
    version: int,
    page: int,
    chunk_index: int,
) -> str:
    """Build a deterministic chunk ID.

    Format: ``{document_id}:{version}:{page}:{chunk_index}``
    This ensures that the same chunk always gets the same ID, making
    ingestion idempotent.
    """
    return f"{document_id}:{version}:{page}:{chunk_index}"


def make_version_id(document_id: uuid.UUID, version: int) -> str:
    """Build a deterministic version identifier for metadata filtering."""
    return f"{document_id}:v{version}"


def deterministic_uuid(seed: str) -> str:
    """Produce a UUID-5 from a seed string (useful for Chroma IDs)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
