"""Parse, chunk, embed, index orchestration."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.domain.policies.chunking_policy import ChunkingConfig, ChunkingPolicy
from app.domain.value_objects.chunk_metadata import ChunkMetadata
from app.infrastructure.db.models import Document, DocumentStatus
from app.infrastructure.parsers.markdown_parser import MarkdownParser
from app.infrastructure.parsers.ocr_pipeline import OCRPipeline
from app.infrastructure.parsers.ocr_router import OCRRouter
from app.infrastructure.parsers.pdf_parser import PDFParser
from app.infrastructure.parsers.text_parser import TextParser
from app.logging import get_logger
from app.utils.ids import make_chunk_id

if TYPE_CHECKING:
    from app.config import Settings
    from app.infrastructure.db.repositories.documents import DocumentRepository
    from app.infrastructure.db.repositories.ingestion_jobs import (
        IngestionJobRepository,
    )
    from app.infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingClient
    from app.infrastructure.retrieval.bm25 import BM25Index
    from app.infrastructure.vectorstore.chunk_index_repo import ChunkIndexRepository

logger = get_logger(__name__)


class IngestionService:
    """Orchestrates the full document ingestion pipeline."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        job_repo: IngestionJobRepository,
        embedding_client: OpenAIEmbeddingClient,
        chunk_index_repo: ChunkIndexRepository,
        settings: Settings,
        bm25_index: BM25Index | None = None,
    ) -> None:
        self._doc_repo = document_repo
        self._job_repo = job_repo
        self._embedding = embedding_client
        self._index = chunk_index_repo
        self._settings = settings
        self._bm25_index = bm25_index

        self._pdf_parser = PDFParser()
        self._md_parser = MarkdownParser()
        self._txt_parser = TextParser()
        self._ocr_router = OCRRouter()
        self._ocr_pipeline = OCRPipeline()
        self._chunker = ChunkingPolicy(
            ChunkingConfig(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
        )

    async def run(
        self,
        document_id: str,
        *,
        reindex: bool = False,
        file_bytes: bytes | None = None,
    ) -> None:
        """Execute the full pipeline for a single document.

        Uses ``lock_for_processing`` so the ``SELECT … FOR UPDATE`` row lock
        is held for the entire duration of ingestion, preventing concurrent
        processing of the same document (BUG-4 fix).
        """
        doc_uuid = uuid.UUID(document_id)
        activation: tuple[uuid.UUID, int] | None = None
        failed_status: tuple[uuid.UUID, DocumentStatus, str] | None = None

        try:
            async with self._doc_repo.lock_for_processing(doc_uuid) as doc:
                if doc is None:
                    logger.error("ingestion.document_not_found", document_id=document_id)
                    return

                if doc.status == DocumentStatus.INDEXED and not reindex:
                    logger.info("ingestion.already_indexed", document_id=document_id)
                    return

                try:
                    should_activate = await self._run_pipeline(
                        doc,
                        document_id,
                        file_bytes=file_bytes,
                    )
                    if should_activate:
                        activation = (doc.id, doc.version)
                except Exception as exc:
                    failed_status = (
                        doc.id,
                        DocumentStatus.FAILED_INDEX,
                        str(exc),
                    )
                    logger.exception("ingestion.failed", document_id=document_id)
                    raise
        except Exception:
            if failed_status is not None:
                failed_doc_id, status, error_message = failed_status
                await self._doc_repo.set_status(
                    failed_doc_id,
                    status,
                    error_message=error_message,
                )
            raise

        if activation is not None:
            await self._doc_repo.activate_version(*activation)

    async def _run_pipeline(
        self,
        doc: Document,
        document_id: str,
        *,
        file_bytes: bytes | None = None,
    ) -> bool:
        """Inner pipeline logic, called under the row lock."""
        doc_uuid = doc.id

        # 0. Load file from disk if not provided
        if not file_bytes:
            from pathlib import Path

            file_path = Path(self._settings.upload_dir) / str(doc_uuid)
            if file_path.exists():
                file_bytes = file_path.read_bytes()
            else:
                logger.error(
                    "ingestion.file_not_found",
                    document_id=document_id,
                    path=str(file_path),
                )
                doc.status = DocumentStatus.FAILED_PARSE
                doc.error_message = f"File not found: {file_path}"
                return False

        # 1. Parse
        doc.status = DocumentStatus.PARSING
        doc.error_message = None
        pages = self._parse(doc.filename, doc.mime_type, file_bytes)
        if pages is None:
            doc.status = DocumentStatus.FAILED_PARSE
            doc.error_message = "Unable to parse document"
            return False

        # 2. Chunk
        doc.status = DocumentStatus.INDEXING
        chunks = self._chunker.split_pages(pages)
        if not chunks:
            doc.status = DocumentStatus.FAILED_PARSE
            doc.error_message = "No chunks produced"
            return False

        # 3. Embed
        texts = [c.text for c in chunks]
        embeddings = await self._embedding.embed_batch(texts)

        # 4. Build metadata and index
        ids: list[str] = []
        documents: list[str] = []
        metas: list[dict] = []
        for _i, chunk in enumerate(chunks):
            chunk_id = make_chunk_id(doc.id, doc.version, chunk.page, chunk.chunk_index)
            meta = ChunkMetadata(
                chunk_id=chunk_id,
                document_id=doc.id,
                document_name=doc.filename,
                document_version=doc.version,
                page=chunk.page,
                chunk_index=chunk.chunk_index,
                source_type=doc.mime_type,
                is_active=True,
            )
            ids.append(chunk_id)
            documents.append(chunk.text)
            metas.append(meta.to_dict())

        self._index.add_chunks(ids, documents, embeddings, metas)

        # 4b. Rebuild BM25 index if hybrid retrieval is enabled
        if self._bm25_index is not None:
            self._rebuild_bm25()

        # 5. Update document
        doc.chunk_count_expected = len(chunks)
        doc.chunk_count_actual = len(ids)
        doc.status = DocumentStatus.INDEXED

        logger.info(
            "ingestion.complete",
            document_id=document_id,
            chunks=len(chunks),
        )
        return True

    def _parse(
        self,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> dict[int, str] | None:
        """Route file to the appropriate parser, return {page_num: text}."""
        ext = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""

        if ext == "pdf" or mime_type == "application/pdf":
            result = self._pdf_parser.parse(file_bytes)
            route = self._ocr_router.route(result)
            if route == "ok":
                return {p.page_number: p.text for p in result.pages}

            # Attempt OCR for low-quality / scanned PDFs
            if route == "needs_ocr":
                logger.info("ingestion.ocr_attempt", filename=filename)
                ocr_result = self._ocr_pipeline.process(file_bytes)
                if ocr_result.success and ocr_result.pages:
                    return {p.page_number: p.text for p in ocr_result.pages}
                logger.warning("ingestion.ocr_failed", filename=filename)

            # needs_review or OCR failed
            logger.info("ingestion.ocr_route", route=route, filename=filename)
            return None

        if ext == "md":
            sections = self._md_parser.parse(file_bytes.decode("utf-8", errors="replace"))
            return {s.section_index: s.text for s in sections}

        if ext == "txt" or mime_type.startswith("text/"):
            parsed = self._txt_parser.parse(file_bytes)
            return {1: parsed.text}

        logger.warning("ingestion.unsupported_type", ext=ext, mime_type=mime_type)
        return None

    def _rebuild_bm25(self) -> None:
        """Rebuild the in-memory BM25 index from all indexed chunks."""
        try:
            all_chunks = self._index.get_all_chunk_texts()
            if all_chunks:
                self._bm25_index.build(all_chunks)  # type: ignore[union-attr]
                logger.info("ingestion.bm25_rebuilt", chunk_count=len(all_chunks))
            else:
                logger.debug("ingestion.bm25_skip_empty")
        except Exception:
            logger.exception("ingestion.bm25_rebuild_failed")
