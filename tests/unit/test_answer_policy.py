"""Answer / fallback policy tests."""

from __future__ import annotations

import uuid

from app.domain.policies.answer_policy import AnswerPolicy
from app.domain.policies.retrieval_policy import RetrievalConfig, RetrievalPolicy
from app.domain.value_objects.answer_result import AnswerStatusEnum
from app.domain.value_objects.chunk_metadata import ChunkMetadata
from app.domain.value_objects.retrieval_result import RetrievalResult


def _make_result(score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id="c1",
        text="text",
        score=score,
        metadata=ChunkMetadata(
            chunk_id="c1",
            document_id=uuid.uuid4(),
            document_name="doc.pdf",
            document_version=1,
            page=1,
            chunk_index=0,
        ),
    )


class TestAnswerPolicy:
    def test_sufficient_retrieval_allows_generation(self) -> None:
        policy = AnswerPolicy(RetrievalPolicy(RetrievalConfig(min_score=0.3, min_hit_count=1)))
        results = [_make_result(0.8), _make_result(0.5)]
        should_generate, valid = policy.evaluate(results)
        assert should_generate is True
        assert len(valid) == 2

    def test_all_below_threshold_blocks_generation(self) -> None:
        policy = AnswerPolicy(RetrievalPolicy(RetrievalConfig(min_score=0.5, min_hit_count=1)))
        results = [_make_result(0.2), _make_result(0.3)]
        should_generate, valid = policy.evaluate(results)
        assert should_generate is False
        assert len(valid) == 0

    def test_insufficient_hit_count_blocks_generation(self) -> None:
        policy = AnswerPolicy(RetrievalPolicy(RetrievalConfig(min_score=0.3, min_hit_count=3)))
        results = [_make_result(0.8), _make_result(0.5)]
        should_generate, _valid = policy.evaluate(results)
        assert should_generate is False

    def test_insufficient_context_result(self) -> None:
        result = AnswerPolicy.insufficient_context_result()
        assert result.status == AnswerStatusEnum.INSUFFICIENT_CONTEXT
        assert result.text != ""
        assert "our arch tech knowledge base" in result.text.lower()
        assert "Arch Tech" in result.text
        assert "нашей базе знаний" not in result.text
        assert "human agent" not in result.text.lower()

    def test_error_result(self) -> None:
        result = AnswerPolicy.error_result("timeout")
        assert result.status == AnswerStatusEnum.ERROR
        assert "timeout" in result.text

    def test_empty_results_blocks_generation(self) -> None:
        policy = AnswerPolicy(RetrievalPolicy(RetrievalConfig(min_score=0.1, min_hit_count=1)))
        should_generate, _valid = policy.evaluate([])
        assert should_generate is False
