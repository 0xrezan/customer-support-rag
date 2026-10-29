"""OCR execution pipeline — extract text from scanned/image PDFs.

Phase 2 implementation uses a pluggable OCR backend interface.
Default implementation shells out to Tesseract via pytesseract if available,
otherwise falls back to a no-op that marks the document as needs_review.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass

from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OCRPageResult:
    """OCR result for a single page."""

    page_number: int
    text: str
    confidence: float  # 0.0 - 1.0


@dataclass
class OCRResult:
    """Aggregated OCR result for a document."""

    pages: list[OCRPageResult]
    total_chars: int
    avg_confidence: float
    success: bool


class OCRBackend(abc.ABC):
    """Abstract OCR backend interface."""

    @abc.abstractmethod
    def ocr_pdf_bytes(self, file_bytes: bytes) -> OCRResult:
        """Run OCR on a PDF and return page-level results."""


class TesseractOCRBackend(OCRBackend):
    """Tesseract-based OCR via pytesseract + pdf2image."""

    def ocr_pdf_bytes(self, file_bytes: bytes) -> OCRResult:
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
        except ImportError:
            logger.warning("ocr.tesseract_not_installed")
            return OCRResult(pages=[], total_chars=0, avg_confidence=0.0, success=False)

        try:
            images = convert_from_bytes(file_bytes)
            pages: list[OCRPageResult] = []

            for idx, image in enumerate(images):
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                text_parts = []
                confidences = []
                for i, word in enumerate(data["text"]):
                    if word.strip():
                        text_parts.append(word)
                        conf = int(data["conf"][i])
                        if conf > 0:
                            confidences.append(conf / 100.0)

                text = " ".join(text_parts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                pages.append(
                    OCRPageResult(
                        page_number=idx + 1,
                        text=text,
                        confidence=avg_conf,
                    )
                )

            total_chars = sum(len(p.text) for p in pages)
            all_conf = [p.confidence for p in pages if p.confidence > 0]
            avg_confidence = sum(all_conf) / len(all_conf) if all_conf else 0.0

            logger.info("ocr.tesseract.complete", pages=len(pages), total_chars=total_chars)
            return OCRResult(
                pages=pages,
                total_chars=total_chars,
                avg_confidence=avg_confidence,
                success=True,
            )
        except Exception:
            logger.exception("ocr.tesseract.failed")
            return OCRResult(pages=[], total_chars=0, avg_confidence=0.0, success=False)


class NoOpOCRBackend(OCRBackend):
    """Fallback that always returns failure — document stays in needs_review."""

    def ocr_pdf_bytes(self, file_bytes: bytes) -> OCRResult:
        logger.info("ocr.noop_backend")
        return OCRResult(pages=[], total_chars=0, avg_confidence=0.0, success=False)


class OCRPipeline:
    """Orchestrates OCR execution with backend selection."""

    def __init__(self, backend: OCRBackend | None = None) -> None:
        if backend is not None:
            self._backend = backend
        else:
            # Auto-detect best available backend
            try:
                import pytesseract  # noqa: F401

                self._backend = TesseractOCRBackend()
            except ImportError:
                self._backend = NoOpOCRBackend()

    def process(self, file_bytes: bytes) -> OCRResult:
        """Run OCR on a PDF file."""
        return self._backend.ocr_pdf_bytes(file_bytes)
