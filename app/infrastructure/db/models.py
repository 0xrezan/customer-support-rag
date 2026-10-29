"""SQLAlchemy ORM models for all Phase-1 tables."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime  # noqa: TC003

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

# ── Enums ────────────────────────────────────────────────────


class DocumentStatus(enum.StrEnum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    INDEXING = "indexing"
    INDEXED = "indexed"
    NEEDS_OCR = "needs_ocr"
    NEEDS_REVIEW = "needs_review"
    FAILED_PARSE = "failed_parse"
    FAILED_INDEX = "failed_index"
    DELETED = "deleted"


class JobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class AnswerStatus(enum.StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    ERROR = "error"


class FeedbackRating(enum.StrEnum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


# ── Models ───────────────────────────────────────────────────


class Document(Base):
    """A registered document in the knowledge base."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("content_hash", "version", name="uq_document_hash_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid.uuid4,
        init=False,
    )
    filename: Mapped[str] = mapped_column(String(512))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active_version: Mapped[bool] = mapped_column(default=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus, name="document_status", values_callable=lambda e: [x.value for x in e]
        ),
        default=DocumentStatus.UPLOADED,
    )
    chunk_count_expected: Mapped[int | None] = mapped_column(Integer, default=None)
    chunk_count_actual: Mapped[int | None] = mapped_column(Integer, default=None)
    page_count: Mapped[int | None] = mapped_column(Integer, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        init=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )

    # Relationships
    ingestion_jobs: Mapped[list[IngestionJob]] = relationship(
        back_populates="document",
        default_factory=list,
        init=False,
    )


class IngestionJob(Base):
    """Background ingestion job tied to a document."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid.uuid4,
        init=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", values_callable=lambda e: [x.value for x in e]),
        default=JobStatus.PENDING,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        init=False,
    )

    document: Mapped[Document] = relationship(
        back_populates="ingestion_jobs",
        default=None,
        init=False,
    )


class ChatQuestion(Base):
    """A user question submitted via web or Telegram."""

    __tablename__ = "chat_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid.uuid4,
        init=False,
    )
    question_text: Mapped[str] = mapped_column(Text)
    question_hash: Mapped[str] = mapped_column(String(64), index=True, default="")
    source: Mapped[str] = mapped_column(String(32), default="web")
    user_id: Mapped[str | None] = mapped_column(String(128), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        init=False,
    )

    answer: Mapped[ChatAnswer | None] = relationship(
        back_populates="question",
        default=None,
        init=False,
    )


class ChatAnswer(Base):
    """An answer generated for a chat question."""

    __tablename__ = "chat_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid.uuid4,
        init=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_questions.id", ondelete="CASCADE"),
    )
    answer_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[AnswerStatus] = mapped_column(
        Enum(AnswerStatus, name="answer_status", values_callable=lambda e: [x.value for x in e]),
        default=AnswerStatus.ANSWERED,
    )
    llm_provider: Mapped[str] = mapped_column(String(32), default="openai")
    llm_model: Mapped[str] = mapped_column(String(64), default="")
    prompt_version: Mapped[str] = mapped_column(String(32), default="answer_v1")
    retrieval_scores: Mapped[list | dict | None] = mapped_column(JSONB, default=None)
    retrieved_chunk_ids: Mapped[list | None] = mapped_column(JSONB, default=None)
    citations: Mapped[list | None] = mapped_column(JSONB, default=None)
    latency_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        init=False,
    )

    question: Mapped[ChatQuestion] = relationship(
        back_populates="answer",
        default=None,
        init=False,
    )
    feedback_events: Mapped[list[FeedbackEvent]] = relationship(
        back_populates="answer",
        default_factory=list,
        init=False,
    )


class FeedbackEvent(Base):
    """Thumbs-up / thumbs-down feedback on an answer."""

    __tablename__ = "feedback_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid.uuid4,
        init=False,
    )
    answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_answers.id", ondelete="CASCADE"),
    )
    rating: Mapped[FeedbackRating] = mapped_column(
        Enum(
            FeedbackRating, name="feedback_rating", values_callable=lambda e: [x.value for x in e]
        ),
    )
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    user_id: Mapped[str | None] = mapped_column(String(128), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        init=False,
    )

    answer: Mapped[ChatAnswer] = relationship(
        back_populates="feedback_events",
        default=None,
        init=False,
    )
