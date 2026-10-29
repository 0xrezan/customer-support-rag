"""Integration test — version switching and no mixed-version retrieval.

Tests reindex behaviour using mocked infrastructure adapters.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.policies.chunking_policy import ChunkingConfig, ChunkingPolicy
from app.infrastructure.db.models import DocumentStatus


def _fake_embedding(dim: int = 8) -> list[float]:
    return [0.1] * dim


@pytest.mark.integration
class TestReindexVersioning:
    async def test_reindex_bumps_version(self) -> None:
        """Re-index a document and verify version is incremented via activate_version."""
        from app.domain.services.ingestion_service import IngestionService

        doc_id = uuid.uuid4()
        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.filename = "policy.txt"
        mock_doc.version = 2  # Simulates a v2 re-index
        mock_doc.mime_type = "text/plain"
        mock_doc.status = DocumentStatus.INDEXED  # Already indexed — reindex=True needed

        doc_repo = AsyncMock()
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
        embedding_client.embed_batch.return_value = [_fake_embedding()]

        chunk_index = MagicMock()
        chunk_index.add_chunks = MagicMock()

        settings = MagicMock()
        settings.chunk_size = 200
        settings.chunk_overlap = 20

        service = IngestionService(
            document_repo=doc_repo,
            job_repo=job_repo,
            embedding_client=embedding_client,
            chunk_index_repo=chunk_index,
            settings=settings,
        )
        service._txt_parser = MagicMock()
        service._txt_parser.parse.return_value = MagicMock(text="Updated policy text.")
        service._chunker = ChunkingPolicy(
            ChunkingConfig(chunk_size=200, chunk_overlap=20, min_chunk_size=5)
        )

        await service.run(str(doc_id), reindex=True, file_bytes=b"Updated policy text.")

        # activate_version should be called with version=2
        doc_repo.activate_version.assert_called_once_with(doc_id, 2)
        assert mock_doc.status == DocumentStatus.INDEXED

    async def test_no_mixed_version_retrieval(self) -> None:
        """During reindex, only chunks with is_active=True are retrieved.

        This verifies the query service passes ``where={\"is_active\": True}``
        so old-version chunks are excluded.
        """
        from unittest.mock import patch

        from app.domain.services.citation_service import CitationService
        from app.domain.services.query_service import QueryService
        from app.domain.value_objects.answer_result import AnswerStatusEnum
        from app.domain.value_objects.chunk_metadata import ChunkMetadata
        from app.domain.value_objects.retrieval_result import RetrievalResult
        from app.infrastructure.llm.base import LLMResponse

        # Only active chunks are returned — no v1 mixed in
        active_chunk = RetrievalResult(
            chunk_id="doc1-v2-p1-c0",
            text="Active version 2 content.",
            score=0.9,
            metadata=ChunkMetadata(
                chunk_id="doc1-v2-p1-c0",
                document_id=uuid.uuid4(),
                document_name="policy.txt",
                document_version=2,
                page=1,
                chunk_index=0,
                source_type="text/plain",
                is_active=True,
            ),
        )

        chunk_index = MagicMock()
        chunk_index.query.return_value = [active_chunk]

        embedding_client = AsyncMock()
        embedding_client.embed.return_value = _fake_embedding()

        llm_client = AsyncMock()
        llm_client.generate.return_value = LLMResponse(
            text="Version 2 answer.",
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
                citation_service=CitationService(),
                chat_repo=chat_repo,
                redis=AsyncMock(),
                settings=settings,
            )
            service._resolve_prompt = AsyncMock(  # type: ignore[method-assign]
                return_value=(
                    "{% for c in chunks %}{{ c.text }}{% endfor %}\n{{ question }}",
                    "You are a helpful assistant.",
                    "test_v1",
                )
            )

            result = await service.ask("What is the policy?")

        assert result.status == AnswerStatusEnum.ANSWERED
        # Verify chunk_index.query was called with is_active filter
        chunk_index.query.assert_called_once()
        call_kwargs = chunk_index.query.call_args
        where_filter = (
            call_kwargs[1].get("where") or call_kwargs[0][2]
            if len(call_kwargs[0]) > 2
            else call_kwargs[1].get("where")
        )
        assert where_filter == {"is_active": True}
