"""Counters and latency metrics (lightweight, log-based in Phase 1)."""

from __future__ import annotations

from app.logging import get_logger

logger = get_logger(__name__)


def record_query_latency(latency_ms: int, *, status: str) -> None:
    """Log query latency for external aggregation."""
    logger.info("metric.query_latency", latency_ms=latency_ms, status=status)


def record_ingestion_duration(duration_ms: int, *, document_id: str) -> None:
    """Log ingestion duration."""
    logger.info("metric.ingestion_duration", duration_ms=duration_ms, document_id=document_id)


def increment_feedback(rating: str) -> None:
    """Log feedback event for aggregation."""
    logger.info("metric.feedback", rating=rating)
