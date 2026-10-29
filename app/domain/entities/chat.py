"""Chat question / answer entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import datetime


class AnswerStatus(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    ERROR = "error"


@dataclass
class QuestionEntity:
    """A user question."""

    id: uuid.UUID
    question_text: str
    question_hash: str = ""
    source: str = "web"
    user_id: str | None = None
    created_at: datetime | None = None


@dataclass
class AnswerEntity:
    """An answer produced by the RAG pipeline."""

    id: uuid.UUID
    question_id: uuid.UUID
    answer_text: str = ""
    status: AnswerStatus = AnswerStatus.ANSWERED
    llm_provider: str = "openai"
    llm_model: str = ""
    prompt_version: str = "answer_v1"
    retrieval_scores: list[float] = field(default_factory=list)
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    citations: list[dict[str, str]] = field(default_factory=list)
    latency_ms: int | None = None
    created_at: datetime | None = None
