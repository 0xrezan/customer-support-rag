"""PDF text extraction via pypdf with extraction-quality heuristics."""

from __future__ import annotations

from dataclasses import dataclass

from pypdf import PdfReader

from app.logging import get_logger
from app.utils.text_normalization import clean_extracted_text

logger = get_logger(__name__)

# If average characters per page falls below this threshold the PDF is
# considered low quality (likely a scan).
_MIN_AVG_CHARS_PER_PAGE = 50


@dataclass
class ParsedPage:
    """Result for a single page."""

    page_number: int
    text: str
    char_count: int


@dataclass
class PDFParseResult:
    """Aggregated parse result for a whole PDF."""

    pages: list[ParsedPage]
    page_count: int
    total_chars: int
    is_low_quality: bool


class PDFParser:
    """Extracts text from a PDF byte stream page by page."""

    def parse(self, file_bytes: bytes) -> PDFParseResult:
        """Parse a PDF and return page-level results with quality assessment."""
        import io

        reader = PdfReader(io.BytesIO(file_bytes))
        pages: list[ParsedPage] = []

        for idx, page in enumerate(reader.pages):
            raw = page.extract_text() or ""
            cleaned = clean_extracted_text(raw)
            pages.append(
                ParsedPage(
                    page_number=idx + 1,
                    text=cleaned,
                    char_count=len(cleaned),
                )
            )

        total_chars = sum(p.char_count for p in pages)
        page_count = len(pages)
        avg_chars = total_chars / page_count if page_count else 0
        is_low_quality = avg_chars < _MIN_AVG_CHARS_PER_PAGE

        if is_low_quality:
            logger.warning(
                "pdf.low_quality",
                page_count=page_count,
                avg_chars=avg_chars,
            )

        return PDFParseResult(
            pages=pages,
            page_count=page_count,
            total_chars=total_chars,
            is_low_quality=is_low_quality,
        )
