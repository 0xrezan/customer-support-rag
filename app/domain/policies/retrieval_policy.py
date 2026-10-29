"""Retrieval policy — thresholds and acceptance rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.value_objects.retrieval_result import RetrievalResult


@dataclass
class RetrievalConfig:
    """Tuneable retrieval parameters."""

    top_k: int = 5
    min_score: float = 0.25
    min_hit_count: int = 1


class RetrievalPolicy:
    """Decides whether retrieval results are good enough to proceed with generation."""

    def __init__(self, config: RetrievalConfig | None = None) -> None:
        self._cfg = config or RetrievalConfig()

    @property
    def config(self) -> RetrievalConfig:
        return self._cfg

    def filter_results(
        self,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Return only chunks meeting the minimum score threshold."""
        return [r for r in results if r.score >= self._cfg.min_score]

    def is_sufficient(self, valid_results: list[RetrievalResult]) -> bool:
        """Return True if enough valid chunks passed the filter."""
        return len(valid_results) >= self._cfg.min_hit_count
