"""Time helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=UTC)


def ms_since(start: datetime) -> int:
    """Milliseconds elapsed since *start*."""
    delta = utc_now() - start
    return int(delta.total_seconds() * 1000)
