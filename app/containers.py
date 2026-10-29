"""Dependency wiring — builds repositories, adapters, and domain services."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from app.logging import get_logger

if TYPE_CHECKING:
    import chromadb  # type: ignore[import-untyped]
    import redis.asyncio as aioredis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.config import Settings
    from app.domain.services.citation_service import CitationService
    from app.domain.services.cleanup_service import CleanupService
    from app.domain.services.feedback_service import FeedbackService
    from app.domain.services.ingestion_service import IngestionService
    from app.domain.services.query_service import QueryService
    from app.domain.services.reconcile_service import ReconcileService
    from app.domain.services.report_service import ReportService
    from app.domain.services.upload_service import UploadService
    from app.infrastructure.cache.rate_limiter import RedisRateLimiter
    from app.infrastructure.db.repositories.admin_users import AdminUserRepository
    from app.infrastructure.db.repositories.chats import ChatRepository
    from app.infrastructure.db.repositories.documents import DocumentRepository
    from app.infrastructure.db.repositories.feedback import FeedbackRepository
    from app.infrastructure.db.repositories.ingestion_jobs import (
        IngestionJobRepository,
    )
    from app.infrastructure.db.repositories.knowledge_bases import (
        KnowledgeBaseRepository,
    )
    from app.infrastructure.db.repositories.prompt_versions import (
        PromptVersionRepository,
    )
    from app.infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingClient
    from app.infrastructure.llm.base import BaseLLMClient
    from app.infrastructure.retrieval.bm25 import BM25Index
    from app.infrastructure.vectorstore.chunk_index_repo import ChunkIndexRepository

logger = get_logger(__name__)
T = TypeVar("T")


def _require_initialized(value: T | None, name: str) -> T:
    if value is None:
        raise RuntimeError(f"{name} is not initialized; call init_resources() first")
    return value


class Container:
    """Poor-man's DI container.

    Holds references to all shared resources (DB session factory, Redis,
    Chroma client, adapters, and domain services).  Initialised once during
    ``lifespan`` and stored on ``app.state.container``.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Infrastructure handles — populated in init_resources()
        self.db_session_factory: async_sessionmaker[AsyncSession] | None = None
        self.redis: aioredis.Redis | None = None
        self.chroma_client: chromadb.ClientAPI | None = None  # type: ignore[type-arg]

        # Repositories
        self.document_repo: DocumentRepository | None = None
        self.job_repo: IngestionJobRepository | None = None
        self.chat_repo: ChatRepository | None = None
        self.feedback_repo: FeedbackRepository | None = None

        # Adapters
        self.embedding_client: OpenAIEmbeddingClient | None = None
        self.llm_client: BaseLLMClient | None = None
        self.chunk_index_repo: ChunkIndexRepository | None = None

        # Domain services
        self.upload_service: UploadService | None = None
        self.ingestion_service: IngestionService | None = None
        self.query_service: QueryService | None = None
        self.citation_service: CitationService | None = None
        self.feedback_service: FeedbackService | None = None
        self.reconcile_service: ReconcileService | None = None

        # BM25 hybrid retrieval
        self.bm25_index: BM25Index | None = None

        # Phase 2 additions
        self.prompt_repo: PromptVersionRepository | None = None
        self.kb_repo: KnowledgeBaseRepository | None = None
        self.admin_user_repo: AdminUserRepository | None = None
        self.rate_limiter: RedisRateLimiter | None = None
        self.report_service: ReportService | None = None
        self.cleanup_service: CleanupService | None = None

    # ── lifecycle ────────────────────────────────────────────

    async def init_resources(self) -> None:
        """Create DB engine, Redis pool, Chroma client, and wire services."""
        from app.infrastructure.cache.redis import create_redis_pool
        from app.infrastructure.db.session import create_session_factory
        from app.infrastructure.vectorstore.chroma_client import create_chroma_client

        # Database
        self.db_session_factory = create_session_factory(self.settings.database_url)
        logger.info("container.db.ready")

        # Redis
        self.redis = await create_redis_pool(self.settings.redis_url)
        logger.info("container.redis.ready")

        # ChromaDB
        self.chroma_client = create_chroma_client(
            host=self.settings.chroma_host,
            port=self.settings.chroma_port,
        )
        logger.info("container.chroma.ready")

        # Wire adapters and services
        self._wire_adapters()
        self._wire_services()
        logger.info("container.wired")

    async def close_resources(self) -> None:
        """Dispose DB engine, close Redis pool."""
        from app.infrastructure.db.session import dispose_engine

        if self.redis is not None:
            await self.redis.aclose()  # type: ignore[union-attr]
            logger.info("container.redis.closed")

        await dispose_engine()
        logger.info("container.db.closed")

    # ── internal wiring ─────────────────────────────────────

    def _wire_adapters(self) -> None:
        from app.infrastructure.db.repositories.chats import ChatRepository
        from app.infrastructure.db.repositories.documents import DocumentRepository
        from app.infrastructure.db.repositories.feedback import FeedbackRepository
        from app.infrastructure.db.repositories.ingestion_jobs import (
            IngestionJobRepository,
        )
        from app.infrastructure.embeddings.openai_embeddings import (
            OpenAIEmbeddingClient,
        )
        from app.infrastructure.vectorstore.chunk_index_repo import ChunkIndexRepository
        from app.infrastructure.vectorstore.collections import get_collection_name

        sf = _require_initialized(self.db_session_factory, "db_session_factory")
        redis = _require_initialized(self.redis, "redis")
        chroma_client = _require_initialized(self.chroma_client, "chroma_client")

        self.document_repo = DocumentRepository(sf)
        self.job_repo = IngestionJobRepository(sf)
        self.chat_repo = ChatRepository(sf)
        self.feedback_repo = FeedbackRepository(sf)

        # Phase 2 repositories
        from app.infrastructure.db.repositories.admin_users import AdminUserRepository
        from app.infrastructure.db.repositories.knowledge_bases import (
            KnowledgeBaseRepository,
        )
        from app.infrastructure.db.repositories.prompt_versions import (
            PromptVersionRepository,
        )

        self.prompt_repo = PromptVersionRepository(sf)
        self.kb_repo = KnowledgeBaseRepository(sf)
        self.admin_user_repo = AdminUserRepository(sf)

        # Phase 2 rate limiter
        from app.infrastructure.cache.rate_limiter import RedisRateLimiter

        self.rate_limiter = RedisRateLimiter(
            redis,
            window_seconds=self.settings.rate_limit_window_seconds,
            max_requests=self.settings.rate_limit_max_requests,
        )

        self.embedding_client = OpenAIEmbeddingClient(
            api_key=self.settings.openai_api_key.get_secret_value(),
            model=self.settings.openai_embedding_model,
            dimensions=self.settings.openai_embedding_dimensions,
        )

        collection_name = get_collection_name(self.settings.chroma_collection_prefix)
        self.chunk_index_repo = ChunkIndexRepository(
            client=chroma_client,
            collection_name=collection_name,
        )

        # BM25 hybrid retrieval index
        if self.settings.hybrid_retrieval_enabled:
            from app.infrastructure.retrieval.bm25 import BM25Index

            self.bm25_index = BM25Index()
            # Build from existing chunks if any
            try:
                all_chunks = self.chunk_index_repo.get_all_chunk_texts()  # type: ignore[union-attr]
                if all_chunks:
                    self.bm25_index.build(all_chunks)  # type: ignore[union-attr]
                    logger.info("container.bm25.built", chunk_count=len(all_chunks))
            except Exception:
                logger.warning("container.bm25.initial_build_failed")

        # LLM client — select provider
        if self.settings.llm_provider.value == "anthropic":
            from app.infrastructure.llm.anthropic_client import AnthropicLLMClient

            self.llm_client = AnthropicLLMClient(
                api_key=self.settings.anthropic_api_key.get_secret_value(),
                model=self.settings.anthropic_chat_model,
                max_tokens=self.settings.anthropic_max_tokens,
                temperature=self.settings.anthropic_temperature,
            )
        else:
            from app.infrastructure.llm.openai_client import OpenAILLMClient

            self.llm_client = OpenAILLMClient(
                api_key=self.settings.openai_api_key.get_secret_value(),
                model=self.settings.openai_chat_model,
                max_tokens=self.settings.openai_max_tokens,
                temperature=self.settings.openai_temperature,
            )

    def _wire_services(self) -> None:
        from app.domain.services.citation_service import CitationService
        from app.domain.services.feedback_service import FeedbackService
        from app.domain.services.ingestion_service import IngestionService
        from app.domain.services.query_service import QueryService
        from app.domain.services.reconcile_service import ReconcileService
        from app.domain.services.upload_service import UploadService

        # Local aliases — all guaranteed non-None after _wire_adapters()
        doc_repo = self.document_repo
        job_repo = self.job_repo
        embedding = self.embedding_client
        chunk_idx = self.chunk_index_repo
        chat_repo = self.chat_repo
        redis = self.redis
        fb_repo = self.feedback_repo
        sf = self.db_session_factory
        llm = self.llm_client
        doc_repo = _require_initialized(doc_repo, "document_repo")
        job_repo = _require_initialized(job_repo, "job_repo")
        embedding = _require_initialized(embedding, "embedding_client")
        chunk_idx = _require_initialized(chunk_idx, "chunk_index_repo")
        chat_repo = _require_initialized(chat_repo, "chat_repo")
        redis = _require_initialized(redis, "redis")
        fb_repo = _require_initialized(fb_repo, "feedback_repo")
        sf = _require_initialized(sf, "db_session_factory")
        llm = _require_initialized(llm, "llm_client")

        self.citation_service = CitationService()

        self.upload_service = UploadService(
            document_repo=doc_repo,
            job_repo=job_repo,
            settings=self.settings,
        )

        self.ingestion_service = IngestionService(
            document_repo=doc_repo,
            job_repo=job_repo,
            embedding_client=embedding,
            chunk_index_repo=chunk_idx,
            settings=self.settings,
            bm25_index=self.bm25_index,
        )

        self.query_service = QueryService(
            chunk_index_repo=chunk_idx,
            embedding_client=embedding,
            llm_client=llm,
            citation_service=self.citation_service,
            chat_repo=chat_repo,
            redis=redis,
            settings=self.settings,
            prompt_repo=self.prompt_repo,
            bm25_index=self.bm25_index,
        )

        self.feedback_service = FeedbackService(
            feedback_repo=fb_repo,
        )

        self.reconcile_service = ReconcileService(
            document_repo=doc_repo,
            chunk_index_repo=chunk_idx,
        )

        # Phase 2 services
        from app.domain.services.cleanup_service import CleanupService
        from app.domain.services.report_service import ReportService

        self.report_service = ReportService(sf)
        self.cleanup_service = CleanupService(
            sf,
            retention_days=self.settings.chat_retention_days,
        )
