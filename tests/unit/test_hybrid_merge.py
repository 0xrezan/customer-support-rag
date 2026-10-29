"""Hybrid retrieval must keep similarity scores so the answer gate still works."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.domain.policies.retrieval_policy import RetrievalConfig, RetrievalPolicy
from app.domain.services.query_service import QueryService
from app.domain.value_objects.chunk_metadata import ChunkMetadata
from app.domain.value_objects.retrieval_result import RetrievalResult
from app.infrastructure.retrieval.bm25 import BM25Score


def _result(chunk_id: str, score: float) -> RetrievalResult:
    meta = ChunkMetadata(
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        document_name="kb.txt",
        document_version=1,
        page=1,
        chunk_index=0,
        source_type="text/plain",
        is_active=True,
    )
    return RetrievalResult(chunk_id=chunk_id, text=chunk_id, score=score, metadata=meta)


class _Index:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], list[float] | None]] = []

    def get_by_ids(self, ids, query_embedding=None):
        self.calls.append((ids, query_embedding))
        return [_result(cid, 0.42) for cid in ids]


class _BM25:
    def query(self, _text, top_k=10):
        return [BM25Score(chunk_id="keyword-only", score=7.0), BM25Score(chunk_id="a", score=3.0)]


def _service(index: _Index) -> QueryService:
    service = QueryService.__new__(QueryService)
    service._index = index
    service._bm25_index = _BM25()
    service._settings = SimpleNamespace(hybrid_dense_weight=0.7, hybrid_bm25_weight=0.3)
    service._retrieval_policy = RetrievalPolicy(RetrievalConfig(top_k=5, min_score=0.25))
    return service


def test_hybrid_merge_keeps_similarity_scores_for_the_answer_gate() -> None:
    index = _Index()
    dense = [_result("a", 0.61), _result("b", 0.33)]

    merged = _service(index)._hybrid_merge("question", dense, [0.1, 0.2])

    scores = {r.chunk_id: r.score for r in merged}
    assert scores == {"a": 0.61, "b": 0.33, "keyword-only": 0.42}
    # "a" is ranked first by both retrievers, so fusion puts it on top.
    assert merged[0].chunk_id == "a"
    # Similarity for BM25-only chunks is computed against the same query embedding.
    assert index.calls == [(["keyword-only"], [0.1, 0.2])]
    assert RetrievalPolicy(RetrievalConfig(min_score=0.25)).filter_results(merged) == merged
