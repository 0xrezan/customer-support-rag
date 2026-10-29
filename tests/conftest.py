"""Shared test fixtures."""

from __future__ import annotations

import uuid

import pytest

from app.domain.policies.chunking_policy import ChunkingConfig, ChunkingPolicy
from app.domain.policies.retrieval_policy import RetrievalConfig, RetrievalPolicy
from app.domain.value_objects.chunk_metadata import ChunkMetadata
from app.domain.value_objects.retrieval_result import RetrievalResult


@pytest.fixture()
def chunking_policy() -> ChunkingPolicy:
    return ChunkingPolicy(ChunkingConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=10))


@pytest.fixture()
def retrieval_policy() -> RetrievalPolicy:
    return RetrievalPolicy(RetrievalConfig(top_k=5, min_score=0.3, min_hit_count=1))


@pytest.fixture()
def sample_retrieval_results() -> list[RetrievalResult]:
    doc_id = uuid.uuid4()
    return [
        RetrievalResult(
            chunk_id=f"chunk_{i}",
            text=f"Sample text for chunk {i}",
            score=0.9 - (i * 0.1),
            metadata=ChunkMetadata(
                chunk_id=f"chunk_{i}",
                document_id=doc_id,
                document_name="test_doc.pdf",
                document_version=1,
                page=i + 1,
                chunk_index=i,
                source_type="pdf",
                is_active=True,
            ),
        )
        for i in range(5)
    ]
