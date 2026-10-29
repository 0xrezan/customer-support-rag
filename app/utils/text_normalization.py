"""Text cleanup utilities used before hashing, chunking, and embedding."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Canonical text cleanup.

    1. Unicode NFC normalisation
    2. Collapse multiple whitespace / newlines into single spaces
    3. Strip leading / trailing whitespace
    4. Lowercase
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text.lower()


def clean_extracted_text(text: str) -> str:
    """Clean text coming from PDF/doc extraction.

    Preserves paragraph structure (double newlines) while collapsing
    extraneous whitespace within paragraphs.
    """
    text = unicodedata.normalize("NFC", text)
    # Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of 3+ newlines to double newline (paragraph separator)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Within paragraphs, collapse horizontal whitespace
    lines = text.split("\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    return "\n".join(lines).strip()
