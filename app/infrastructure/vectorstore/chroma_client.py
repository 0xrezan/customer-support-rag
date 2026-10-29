"""ChromaDB client initialisation."""

from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.logging import get_logger

logger = get_logger(__name__)

_NOOP_TELEMETRY = "app.infrastructure.vectorstore.chroma_telemetry.NoopProductTelemetryClient"


def create_chroma_client(
    host: str = "chroma",
    port: int = 8100,
) -> chromadb.HttpClient:
    """Return a persistent HTTP Chroma client."""
    client = chromadb.HttpClient(
        host=host,
        port=port,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            chroma_product_telemetry_impl=_NOOP_TELEMETRY,
            chroma_telemetry_impl=_NOOP_TELEMETRY,
        ),
    )
    logger.info("chroma.client_created", host=host, port=port)
    return client
