"""Plain-text parser — TXT parsing and normalisation."""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.text_normalization import clean_extracted_text


@dataclass
class TextParseResult:
    text: str
    char_count: int


class TextParser:
    """Parse a plain-text file (UTF-8)."""

    def parse(self, file_bytes: bytes) -> TextParseResult:
        raw = file_bytes.decode("utf-8", errors="replace")
        cleaned = clean_extracted_text(raw)
        return TextParseResult(text=cleaned, char_count=len(cleaned))
