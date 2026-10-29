"""Content and question hashing utilities."""

from __future__ import annotations

import hashlib

from app.utils.text_normalization import normalize_text


def content_hash(data: bytes) -> str:
    """Return a SHA-256 hex digest for raw file bytes (document dedup)."""
    return hashlib.sha256(data).hexdigest()


def question_hash(text: str) -> str:
    """Return a SHA-256 hex digest for a normalised question string (cache / dedup)."""
    normalised = normalize_text(text)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()
