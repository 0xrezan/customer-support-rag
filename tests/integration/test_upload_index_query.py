"""Integration test — upload -> index -> query happy path.

Tests the full RAG pipeline with mocked infrastructure adapters.
Verifies that ingestion, embedding, indexing, and query flow work together.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.policies.chunking_policy import ChunkingConfig, ChunkingPolicy
from app.domain.services.citation_service import CitationService
from app.domain.services.query_service import QueryService
from app.domain.value_objects.answer_result import AnswerStatusEnum
from app.domain.value_objects.chunk_metadata import ChunkMetadata
from app.domain.value_objects.retrieval_result import RetrievalResult
from app.infrastructure.llm.base import LLMResponse


def _fake_embedding(dim: int = 8) -> list[float]:
    """Return a trivial embedding vector for testing."""
    return [0.1] * dim


def _make_retrieval_result(
    chunk_id: str,
    text: str,
    score: float,
    doc_name: str = "guide.pdf",
    page: int = 1,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        text=text,
        score=score,
        metadata=ChunkMetadata(
            chunk_id=chunk_id,
            document_id=uuid.uuid4(),
            document_name=doc_name,
            document_version=1,
            page=page,
            chunk_index=0,
            source_type="pdf",
            is_active=True,
        ),
    )


@pytest.mark.integration
class TestUploadIndexQuery:
    """Integration tests for the upload → index → query pipeline."""

    async def test_upload_creates_document(self) -> None:
        """Upload a file via UploadService, verify document and job are created."""
        from app.domain.services.upload_service import UploadService

        mock_doc = MagicMock()
        mock_doc.filename = "policy.pdf"
        mock_doc.version = 1
        mock_doc.status = "uploaded"

        doc_repo = AsyncMock()
        doc_repo.get_by_hash.return_value = None  # No existing document
        doc_repo.create.return_value = mock_doc

        job_repo = AsyncMock()
        job_repo.create_for_document = AsyncMock()

        service = UploadService(document_repo=doc_repo, job_repo=job_repo)
        doc, is_new = await service.register(
            file_bytes=b"fake pdf content",
            filename="policy.pdf",
            mime_type="application/pdf",
        )

        assert is_new is True
        assert isinstance(doc.id, uuid.UUID)
        doc_repo.create.assert_called_once()
        job_repo.create_for_document.assert_called_once()

    async def test_index_produces_chunks(self) -> None:
        """After ingestion, verify chunks are sent to the index."""
        from app.domain.services.ingestion_service import IngestionService
        from app.infrastructure.db.models import DocumentStatus

        doc_id = uuid.uuid4()
        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.filename = "readme.txt"
        mock_doc.version = 1
        mock_doc.mime_type = "text/plain"
        mock_doc.status = DocumentStatus.UPLOADED

        doc_repo = AsyncMock()
        # lock_for_processing is an async context manager yielding the document
        doc_repo.lock_for_processing = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_doc),
                __aexit__=AsyncMock(return_value=False),
            )
        )
        doc_repo.set_status = AsyncMock()
        doc_repo.set_chunk_counts = AsyncMock()
        doc_repo.activate_version = AsyncMock()

        job_repo = AsyncMock()

        embedding_client = AsyncMock()
        embedding_client.embed_batch.return_value = [_fake_embedding(), _fake_embedding()]

        chunk_index = MagicMock()
        chunk_index.add_chunks = MagicMock()

        settings = MagicMock()
        settings.chunk_size = 50
        settings.chunk_overlap = 10

        service = IngestionService(
            document_repo=doc_repo,
            job_repo=job_repo,
            embedding_client=embedding_client,
            chunk_index_repo=chunk_index,
            settings=settings,
        )
        # Patch the txt parser to return deterministic content
        service._txt_parser = MagicMock()
        service._txt_parser.parse.return_value = MagicMock(text="Hello world " * 20)
        service._chunker = ChunkingPolicy(
            ChunkingConfig(chunk_size=50, chunk_overlap=10, min_chunk_size=5)
        )

        await service.run(str(doc_id), file_bytes=b"Hello world " * 20)

        chunk_index.add_chunks.assert_called_once()
        call_args = chunk_index.add_chunks.call_args
        ids = call_args[0][0] if call_args[0] else call_args[1].get("ids", [])
        assert len(ids) >= 1
        assert mock_doc.status == DocumentStatus.INDEXED
        assert mock_doc.chunk_count_actual == len(ids)
        doc_repo.activate_version.assert_called_once_with(doc_id, 1)

    async def test_query_returns_answer(self) -> None:
        """Query with good retrieval results should produce an answered result."""
        chunk_index = MagicMock()
        chunk_index.query.return_value = [
            _make_retrieval_result("c1", "Our return policy is 30 days.", 0.85),
            _make_retrieval_result("c2", "Contact us at support@example.com.", 0.75),
        ]

        embedding_client = AsyncMock()
        embedding_client.embed.return_value = _fake_embedding()

        llm_client = AsyncMock()
        llm_client.generate.return_value = LLMResponse(
            text="Our return policy allows returns within 30 days.",
            model="gpt-4o-mini",
            provider="openai",
        )

        citation_service = CitationService()

        # Mock the chat repo — _persist() now uses raw INSERT via chat_repo._sf()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        chat_repo = AsyncMock()
        chat_repo._sf = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        redis = AsyncMock()

        settings = MagicMock()
        settings.retrieval_top_k = 5
        settings.retrieval_min_score = 0.3
        settings.retrieval_min_hit_count = 1
        settings.reranking_enabled = False
        settings.reranking_keyword_weight = 0.3
        settings.reranking_semantic_weight = 0.7
        settings.hybrid_retrieval_enabled = False
        settings.answer_cache_ttl_seconds = 300

        with (
            patch(
                "app.domain.services.query_service.cache_get",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.domain.services.query_service.cache_set",
                new_callable=AsyncMock,
            ),
        ):
            service = QueryService(
                chunk_index_repo=chunk_index,
                embedding_client=embedding_client,
                llm_client=llm_client,
                citation_service=citation_service,
                chat_repo=chat_repo,
                redis=redis,
                settings=settings,
            )
            # Patch _resolve_prompt to avoid filesystem dependency
            service._resolve_prompt = AsyncMock(  # type: ignore[method-assign]
                return_value=(
                    "Context:\n"
                    "{% for c in chunks %}{{ c.text }}\n{% endfor %}\n"
                    "Question: {{ question }}",
                    "You are a helpful assistant.",
                    "test_v1",
                )
            )

            result = await service.ask("What is your return policy?")

        assert result.status == AnswerStatusEnum.ANSWERED
        assert "30 days" in result.text
        assert len(result.citations) >= 1
        assert result.citations[0].document_name == "guide.pdf"
        llm_client.generate.assert_called_once()

    async def test_query_bypass_cache_skips_answer_cache(self) -> None:
        """Demo queries can force fresh generation without reading or writing answer cache."""
        chunk_index = MagicMock()
        chunk_index.query.return_value = [
            _make_retrieval_result("c1", "Delivery to Saratov takes 3-7 business days.", 0.85),
        ]

        embedding_client = AsyncMock()
        embedding_client.embed.return_value = _fake_embedding()

        llm_client = AsyncMock()
        llm_client.generate.return_value = LLMResponse(
            text="Delivery to Saratov takes 3-7 business days.",
            model="gpt-4o-mini",
            provider="openai",
        )

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        chat_repo = AsyncMock()
        chat_repo._sf = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        redis = AsyncMock()

        settings = MagicMock()
        settings.retrieval_top_k = 5
        settings.retrieval_min_score = 0.3
        settings.retrieval_min_hit_count = 1
        settings.reranking_enabled = False
        settings.reranking_keyword_weight = 0.3
        settings.reranking_semantic_weight = 0.7
        settings.hybrid_retrieval_enabled = False
        settings.answer_cache_ttl_seconds = 300

        with (
            patch(
                "app.domain.services.query_service.cache_get",
                new_callable=AsyncMock,
                return_value='{"status":"answered","text":"cached answer","citations":[]}',
            ) as cache_get_mock,
            patch(
                "app.domain.services.query_service.cache_set",
                new_callable=AsyncMock,
            ) as cache_set_mock,
        ):
            service = QueryService(
                chunk_index_repo=chunk_index,
                embedding_client=embedding_client,
                llm_client=llm_client,
                citation_service=CitationService(),
                chat_repo=chat_repo,
                redis=redis,
                settings=settings,
            )
            service._resolve_prompt = AsyncMock(  # type: ignore[method-assign]
                return_value=(
                    "{% for c in chunks %}{{ c.text }}{% endfor %}\n{{ question }}",
                    "You are a helpful assistant.",
                    "test_v1",
                )
            )

            result = await service.ask("Is delivery available in Saratov?", bypass_cache=True)

        assert result.status == AnswerStatusEnum.ANSWERED
        assert result.text == "Delivery to Saratov takes 3-7 business days."
        cache_get_mock.assert_not_awaited()
        cache_set_mock.assert_not_awaited()
        llm_client.generate.assert_called_once()

    async def test_ingestion_does_not_update_document_via_new_session_while_locked(
        self,
    ) -> None:
        """Ingestion must not self-block by updating a locked document row."""
        from app.domain.services.ingestion_service import IngestionService
        from app.infrastructure.db.models import DocumentStatus

        doc_id = uuid.uuid4()
        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.filename = "readme.txt"
        mock_doc.version = 1
        mock_doc.mime_type = "text/plain"
        mock_doc.status = DocumentStatus.UPLOADED

        class LockAwareDocumentRepo:
            def __init__(self) -> None:
                self.locked = False
                self.activate_version = AsyncMock()

            @asynccontextmanager
            async def lock_for_processing(self, _doc_id):
                self.locked = True
                try:
                    yield mock_doc
                finally:
                    self.locked = False

            async def set_status(self, *_args, **_kwargs) -> None:
                if self.locked:
                    raise AssertionError("set_status opened a new session while row is locked")

            async def set_chunk_counts(self, *_args, **_kwargs) -> None:
                if self.locked:
                    raise AssertionError(
                        "set_chunk_counts opened a new session while row is locked"
                    )

        doc_repo = LockAwareDocumentRepo()
        embedding_client = AsyncMock()
        embedding_client.embed_batch.return_value = [_fake_embedding()]

        chunk_index = MagicMock()
        chunk_index.add_chunks = MagicMock()

        settings = MagicMock()
        settings.chunk_size = 200
        settings.chunk_overlap = 20

        service = IngestionService(
            document_repo=doc_repo,
            job_repo=AsyncMock(),
            embedding_client=embedding_client,
            chunk_index_repo=chunk_index,
            settings=settings,
        )
        service._txt_parser = MagicMock()
        service._txt_parser.parse.return_value = MagicMock(text="Locked row safe ingestion. " * 10)
        service._chunker = ChunkingPolicy(
            ChunkingConfig(chunk_size=200, chunk_overlap=20, min_chunk_size=5)
        )

        await service.run(str(doc_id), file_bytes=b"Locked row safe ingestion. " * 10)

        assert mock_doc.status == DocumentStatus.INDEXED
        doc_repo.activate_version.assert_called_once_with(doc_id, 1)
