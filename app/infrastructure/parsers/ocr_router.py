"""OCR router — detect and route low-quality PDFs to needs_ocr / review state.

In Phase 1 this module only *detects* the need for OCR and flags the document.
Actual OCR execution is deferred to Phase 2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.logging import get_logger

if TYPE_CHECKING:
    from app.infrastructure.parsers.pdf_parser import PDFParseResult

logger = get_logger(__name__)


class OCRRouter:
    """Decide whether a parsed PDF needs OCR or manual review."""

    def needs_ocr(self, result: PDFParseResult) -> bool:
        """Return True if extraction quality is too low and OCR should be attempted."""
        if result.page_count == 0:
            return False
        return result.is_low_quality

    def route(self, result: PDFParseResult) -> str:
        """Return a target status string for the document.

        Returns:
            ``"ok"`` — extraction is acceptable, proceed with chunking.
            ``"needs_ocr"`` — extraction failed quality checks.
            ``"needs_review"`` — zero pages or completely empty.
        """
        if result.page_count == 0:
            logger.warning("ocr_router.empty_pdf")
            return "needs_review"

        if self.needs_ocr(result):
            logger.info("ocr_router.needs_ocr", total_chars=result.total_chars)
            return "needs_ocr"

        return "ok"
