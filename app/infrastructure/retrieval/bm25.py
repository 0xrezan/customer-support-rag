"""Lightweight BM25 implementation for hybrid retrieval (dense + keyword).

This module provides an in-memory BM25 index that can be built from
chunk texts and used alongside dense vector search for hybrid scoring.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class BM25Document:
    """A single document in the BM25 index."""

    chunk_id: str
    terms: list[str]
    term_freqs: Counter = field(init=False)

    def __post_init__(self) -> None:
        self.term_freqs = Counter(self.terms)


@dataclass
class BM25Score:
    """BM25 score for a chunk."""

    chunk_id: str
    score: float


class BM25Index:
    """Okapi BM25 scoring over a corpus of text chunks.

    Parameters:
        k1: Term frequency saturation parameter (default 1.5).
        b:  Length normalisation parameter (default 0.75).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._docs: list[BM25Document] = []
        self._avgdl: float = 0.0
        self._df: Counter = Counter()  # document frequency per term
        self._n: int = 0

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Simple lowercase word tokenization (2+ char tokens)."""
        return re.findall(r"\w{2,}", text.lower())

    def build(self, chunks: list[tuple[str, str]]) -> None:
        """Build the index from (chunk_id, text) pairs."""
        self._docs = []
        self._df = Counter()
        total_len = 0

        for chunk_id, text in chunks:
            terms = self.tokenize(text)
            doc = BM25Document(chunk_id=chunk_id, terms=terms)
            self._docs.append(doc)
            total_len += len(terms)
            # Count unique terms per document for DF
            for term in set(terms):
                self._df[term] += 1

        self._n = len(self._docs)
        self._avgdl = total_len / self._n if self._n else 1.0

    def query(self, query_text: str, top_k: int = 10) -> list[BM25Score]:
        """Score all documents against a query and return top-k."""
        query_terms = self.tokenize(query_text)
        if not query_terms or not self._docs:
            return []

        scores: list[BM25Score] = []
        for doc in self._docs:
            score = self._score_document(query_terms, doc)
            if score > 0:
                scores.append(BM25Score(chunk_id=doc.chunk_id, score=score))

        scores.sort(key=lambda s: s.score, reverse=True)
        return scores[:top_k]

    def _score_document(self, query_terms: list[str], doc: BM25Document) -> float:
        """Compute BM25 score for a single document."""
        score = 0.0
        dl = len(doc.terms)

        for term in query_terms:
            tf = doc.term_freqs.get(term, 0)
            if tf == 0:
                continue
            df = self._df.get(term, 0)
            idf = math.log((self._n - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (self._k1 + 1)
            denominator = tf + self._k1 * (1 - self._b + self._b * dl / self._avgdl)
            score += idf * numerator / denominator

        return score


@dataclass
class HybridConfig:
    """Configuration for hybrid dense + BM25 retrieval."""

    enabled: bool = True
    dense_weight: float = 0.7
    bm25_weight: float = 0.3
    bm25_top_k: int = 20


def hybrid_merge(
    dense_results: list[tuple[str, float]],
    bm25_results: list[BM25Score],
    config: HybridConfig,
) -> list[tuple[str, float]]:
    """Merge dense and BM25 scores using Reciprocal Rank Fusion (RRF).

    Returns a list of (chunk_id, combined_score) sorted descending.
    """
    rrf_k = 60  # standard RRF constant

    scores: dict[str, float] = {}

    # Dense contribution
    for rank, (chunk_id, _score) in enumerate(dense_results):
        rrf_score = config.dense_weight / (rrf_k + rank + 1)
        scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_score

    # BM25 contribution
    for rank, bm25 in enumerate(bm25_results):
        rrf_score = config.bm25_weight / (rrf_k + rank + 1)
        scores[bm25.chunk_id] = scores.get(bm25.chunk_id, 0.0) + rrf_score

    merged = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return merged
