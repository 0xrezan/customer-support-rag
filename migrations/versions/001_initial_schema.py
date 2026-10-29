"""Initial schema — all Phase 1 and Phase 2 tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-04-05

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Enums ────────────────────────────────────────────────
    document_status = postgresql.ENUM(
        "uploaded",
        "parsing",
        "indexing",
        "indexed",
        "needs_ocr",
        "needs_review",
        "failed_parse",
        "failed_index",
        "deleted",
        name="document_status",
        create_type=False,
    )
    document_status.create(op.get_bind(), checkfirst=True)

    job_status = postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "retrying",
        name="job_status",
        create_type=False,
    )
    job_status.create(op.get_bind(), checkfirst=True)

    answer_status = postgresql.ENUM(
        "answered",
        "insufficient_context",
        "error",
        name="answer_status",
        create_type=False,
    )
    answer_status.create(op.get_bind(), checkfirst=True)

    feedback_rating = postgresql.ENUM(
        "thumbs_up",
        "thumbs_down",
        name="feedback_rating",
        create_type=False,
    )
    feedback_rating.create(op.get_bind(), checkfirst=True)

    admin_role = postgresql.ENUM(
        "super_admin",
        "admin",
        "operator",
        "viewer",
        name="admin_role",
        create_type=False,
    )
    admin_role.create(op.get_bind(), checkfirst=True)

    # ── Phase 1 tables ───────────────────────────────────────

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column("file_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "mime_type",
            sa.String(128),
            nullable=False,
            server_default="application/octet-stream",
        ),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active_version", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "status",
            document_status,
            nullable=False,
            server_default="uploaded",
        ),
        sa.Column("chunk_count_expected", sa.Integer, nullable=True),
        sa.Column("chunk_count_actual", sa.Integer, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("content_hash", "version", name="uq_document_hash_version"),
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            job_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "chat_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("question_hash", sa.String(64), nullable=False, server_default="", index=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="web"),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "chat_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer_text", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "status",
            answer_status,
            nullable=False,
            server_default="answered",
        ),
        sa.Column("llm_provider", sa.String(32), nullable=False, server_default="openai"),
        sa.Column("llm_model", sa.String(64), nullable=False, server_default=""),
        sa.Column("prompt_version", sa.String(32), nullable=False, server_default="answer_v1"),
        sa.Column("retrieval_scores", postgresql.JSONB, nullable=True),
        sa.Column("retrieved_chunk_ids", postgresql.JSONB, nullable=True),
        sa.Column("citations", postgresql.JSONB, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "feedback_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "answer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_answers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", feedback_rating, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Phase 2 tables ───────────────────────────────────────

    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, index=True),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("template_text", sa.Text, nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(128), nullable=False, unique=True),
        sa.Column("email", sa.String(256), nullable=False, server_default=""),
        sa.Column("telegram_id", sa.Integer, nullable=True),
        sa.Column(
            "role",
            admin_role,
            nullable=False,
            server_default="operator",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("api_token_hash", sa.String(128), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("admin_users")
    op.drop_table("knowledge_bases")
    op.drop_table("prompt_versions")
    op.drop_table("feedback_events")
    op.drop_table("chat_answers")
    op.drop_table("chat_questions")
    op.drop_table("ingestion_jobs")
    op.drop_table("documents")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS admin_role")
    op.execute("DROP TYPE IF EXISTS feedback_rating")
    op.execute("DROP TYPE IF EXISTS answer_status")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS document_status")
