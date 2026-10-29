"""Application settings loaded from environment variables via pydantic-settings."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Settings(BaseSettings):
    """Central configuration — every value comes from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────
    app_name: str = "customer-support-bot"
    app_env: Environment = Environment.DEVELOPMENT
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = "INFO"

    # ── FastAPI ─────────────────────────────────────────────
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    # ── Admin Auth ──────────────────────────────────────────
    admin_api_token: SecretStr = SecretStr("changeme-admin-token-here")
    admin_telegram_ids: list[int] = Field(default_factory=list)

    # ── PostgreSQL ──────────────────────────────────────────
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "bot"
    postgres_password: SecretStr = SecretStr("bot_secret")
    postgres_db: str = "support_bot"
    database_url: str = "postgresql+asyncpg://bot:bot_secret@postgres:5432/support_bot"

    # ── Redis ───────────────────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = "redis://redis:6379/0"

    # ── ChromaDB ────────────────────────────────────────────
    chroma_host: str = "chroma"
    chroma_port: int = 8100
    chroma_collection_prefix: str = "kb"

    # ── Telegram ────────────────────────────────────────────
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_webhook_enabled: bool = False
    telegram_webhook_url: str = ""
    telegram_webhook_secret: SecretStr = SecretStr("")

    # ── OpenAI ──────────────────────────────────────────────
    openai_api_key: SecretStr = SecretStr("")
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536
    openai_chat_model: str = "gpt-5.4-mini"
    openai_max_tokens: int = 1024
    openai_temperature: float = 0.1

    # ── Anthropic ───────────────────────────────────────────
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_chat_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 1024
    anthropic_temperature: float = 0.1

    # ── LLM Provider ────────────────────────────────────────
    llm_provider: LLMProvider = LLMProvider.OPENAI

    # ── RAG Settings ────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.25
    retrieval_min_hit_count: int = 1

    # ── Cache ───────────────────────────────────────────────
    answer_cache_ttl_seconds: int = 300

    # ── Dramatiq ────────────────────────────────────────────
    dramatiq_broker_url: str = "redis://redis:6379/1"

    # ── Phase 2: Reranking ──────────────────────────────────
    reranking_enabled: bool = True
    reranking_keyword_weight: float = 0.3
    reranking_semantic_weight: float = 0.7

    # ── Phase 2: Hybrid Retrieval ───────────────────────────
    hybrid_retrieval_enabled: bool = False
    hybrid_dense_weight: float = 0.7
    hybrid_bm25_weight: float = 0.3

    # ── Phase 2: Rate Limiting ──────────────────────────────
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 20

    # ── Phase 2: Chat Cleanup ───────────────────────────────
    chat_retention_days: int = 90

    # ── File Storage ─────────────────────────────────────────
    upload_dir: str = "uploads"
    max_upload_size_bytes: int = 50 * 1024 * 1024
    allowed_upload_extensions: set[str] = Field(
        default_factory=lambda: {".pdf", ".txt", ".md", ".markdown"}
    )
    allowed_upload_mime_types: set[str] = Field(
        default_factory=lambda: {
            "application/pdf",
            "application/octet-stream",
            "text/markdown",
            "text/plain",
        }
    )

    # ── Derived helpers ─────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings (parsed once from .env)."""
    return Settings()
