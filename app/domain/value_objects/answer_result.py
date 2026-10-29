"""Final answer DTO with status and citations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid


class AnswerStatusEnum(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    ERROR = "error"


@dataclass(frozen=True)
class Citation:
    """A single source citation."""

    document_name: str
    page: int
    chunk_id: str = ""

    def display(self) -> str:
        return f"{self.document_name}, page {self.page}"


@dataclass
class AnswerResult:
    """Complete answer returned by the query service."""

    status: AnswerStatusEnum
    text: str = ""
    citations: list[Citation] = field(default_factory=list)
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    retrieval_scores: list[float] = field(default_factory=list)
    llm_provider: str = ""
    llm_model: str = ""
    prompt_version: str = ""
    latency_ms: int = 0
    answer_id: uuid.UUID | None = None
