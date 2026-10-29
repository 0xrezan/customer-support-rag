"""Collection naming and creation helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.logging import get_logger

if TYPE_CHECKING:
    import chromadb

logger = get_logger(__name__)

_DEFAULT_PREFIX = "kb"


def get_collection_name(prefix: str = _DEFAULT_PREFIX) -> str:
    """Return the canonical collection name for the main knowledge base."""
    return f"{prefix}_chunks"


def ensure_collection(
    client: chromadb.HttpClient,
    name: str,
) -> chromadb.Collection:
    """Get or create a Chroma collection."""
    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info("chroma.collection_ready", name=name)
    return collection
