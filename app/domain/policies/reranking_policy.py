"""Reranking stage after initial Chroma retrieval.

Uses a cross-encoder style scoring heuristic to re-order results.
In Phase 2 this is a lightweight keyword-overlap + score-weighted reranker.
Can be swapped for a model-based reranker (e.g. Cohere, bge-reranker) later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.logging import get_logger

if TYPE_CHECKING:
    from app.domain.value_objects.retrieval_result import RetrievalResult

logger = get_logger(__name__)


@dataclass
class RerankingConfig:
    """Tuneable reranking parameters."""

    enabled: bool = True
    keyword_weight: float = 0.3
    semantic_weight: float = 0.7
    top_n: int | None = None  # None = keep all, int = truncate after rerank


class RerankingPolicy:
    """Reranks retrieval results using a combined score of semantic similarity
    and keyword overlap with the original query.
    """

    def __init__(self, config: RerankingConfig | None = None) -> None:
        self._cfg = config or RerankingConfig()

    @property
    def config(self) -> RerankingConfig:
        return self._cfg

    def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Rerank results by combined semantic + keyword score."""
        if not self._cfg.enabled or not results:
            return results

        query_terms = self._tokenize(query)
        if not query_terms:
            return results

        scored: list[tuple[float, RetrievalResult]] = []
        for r in results:
            keyword_score = self._keyword_overlap(query_terms, r.text)
            combined = (
                self._cfg.semantic_weight * r.score + self._cfg.keyword_weight * keyword_score
            )
            scored.append((combined, r))

        scored.sort(key=lambda x: x[0], reverse=True)

        reranked = [r for _, r in scored]
        if self._cfg.top_n is not None:
            reranked = reranked[: self._cfg.top_n]

        logger.debug(
            "reranking.done",
            input_count=len(results),
            output_count=len(reranked),
        )
        return reranked

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Simple word-level tokenization."""
        return set(re.findall(r"\w{2,}", text.lower()))

    @staticmethod
    def _keyword_overlap(query_terms: set[str], chunk_text: str) -> float:
        """Fraction of query terms found in the chunk text."""
        if not query_terms:
            return 0.0
        chunk_terms = set(re.findall(r"\w{2,}", chunk_text.lower()))
        overlap = query_terms & chunk_terms
        return len(overlap) / len(query_terms)
