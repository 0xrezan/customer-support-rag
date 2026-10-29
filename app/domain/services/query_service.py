"""Retrieve, judge, generate, and log answers."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

from app.domain.policies.answer_policy import AnswerPolicy
from app.domain.policies.reranking_policy import RerankingConfig, RerankingPolicy
from app.domain.policies.retrieval_policy import RetrievalConfig, RetrievalPolicy
from app.domain.value_objects.answer_result import AnswerResult, AnswerStatusEnum, Citation
from app.infrastructure.cache.redis import cache_get, cache_set
from app.infrastructure.db.models import AnswerStatus, ChatAnswer, ChatQuestion
from app.infrastructure.telemetry.metrics import record_query_latency
from app.logging import get_logger
from app.utils.hashing import question_hash
from app.utils.time import ms_since, utc_now

if TYPE_CHECKING:
    import redis.asyncio as aioredis

    from app.config import Settings
    from app.domain.services.citation_service import CitationService
    from app.domain.value_objects.retrieval_result import RetrievalResult
    from app.infrastructure.db.repositories.chats import ChatRepository
    from app.infrastructure.db.repositories.prompt_versions import (
        PromptVersionRepository,
    )
    from app.infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingClient
    from app.infrastructure.llm.base import BaseLLMClient
    from app.infrastructure.retrieval.bm25 import BM25Index
    from app.infrastructure.vectorstore.chunk_index_repo import ChunkIndexRepository

logger = get_logger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_PROMPTS_DIR)),
    autoescape=True,
)


class QueryService:
    """End-to-end question answering with retrieval gating."""

    def __init__(
        self,
        chunk_index_repo: ChunkIndexRepository,
        embedding_client: OpenAIEmbeddingClient,
        llm_client: BaseLLMClient,
        citation_service: CitationService,
        chat_repo: ChatRepository,
        redis: aioredis.Redis,
        settings: Settings,
        prompt_repo: PromptVersionRepository | None = None,
        bm25_index: BM25Index | None = None,
    ) -> None:
        self._index = chunk_index_repo
        self._embedding = embedding_client
        self._llm = llm_client
        self._citations = citation_service
        self._chat_repo = chat_repo
        self._redis = redis
        self._settings = settings
        self._prompt_repo = prompt_repo
        self._bm25_index = bm25_index

        self._retrieval_policy = RetrievalPolicy(
            RetrievalConfig(
                top_k=settings.retrieval_top_k,
                min_score=settings.retrieval_min_score,
                min_hit_count=settings.retrieval_min_hit_count,
            )
        )
        self._answer_policy = AnswerPolicy(self._retrieval_policy)
        self._reranker = RerankingPolicy(
            RerankingConfig(
                enabled=settings.reranking_enabled,
                keyword_weight=settings.reranking_keyword_weight,
                semantic_weight=settings.reranking_semantic_weight,
            )
        )

    async def ask(
        self,
        question_text: str,
        *,
        source: str = "web",
        user_id: str | None = None,
        bypass_cache: bool = False,
    ) -> AnswerResult:
        """Process a user question through the full RAG pipeline."""
        start = utc_now()
        q_hash = question_hash(question_text)

        # 1. Check cache
        cache_key = f"answer:{q_hash}"
        if bypass_cache:
            logger.info("query.cache_bypass", question_hash=q_hash)
        else:
            cached = await cache_get(self._redis, cache_key)
            if cached:
                logger.info("query.cache_hit", question_hash=q_hash)
                data = json.loads(cached)
                data["status"] = AnswerStatusEnum(data["status"])
                data["citations"] = [Citation(**c) for c in data.get("citations", [])]
                return AnswerResult(**data)

        # 2. Embed the question
        query_embedding = await self._embedding.embed(question_text)

        # 3. Retrieve (dense)
        raw_results = self._index.query(
            query_embedding,
            top_k=self._retrieval_policy.config.top_k,
            where={"is_active": True},
        )

        # 3a. Hybrid merge with BM25 if enabled
        if (
            self._settings.hybrid_retrieval_enabled
            and self._bm25_index is not None
            and raw_results
        ):
            raw_results = self._hybrid_merge(question_text, raw_results, query_embedding)

        # 3b. Rerank if enabled
        if self._reranker.config.enabled and raw_results:
            raw_results = self._reranker.rerank(question_text, raw_results)
            logger.debug("query.reranked", count=len(raw_results))

        # 4. Evaluate retrieval
        should_generate, valid_results = self._answer_policy.evaluate(raw_results)

        if not should_generate:
            result = self._answer_policy.insufficient_context_result()
            result.latency_ms = ms_since(start)
            record_query_latency(result.latency_ms, status=result.status.value)
            await self._persist(question_text, q_hash, source, user_id, result)
            return result

        # 5. Generate answer
        try:
            # Try SQL prompt registry first, fall back to Jinja2 file
            template_text, system, prompt_version = await self._resolve_prompt()
            prompt = jinja2.Template(template_text).render(
                question=question_text,
                chunks=[
                    {
                        "document_name": r.metadata.document_name,
                        "page": r.metadata.page,
                        "text": r.text,
                    }
                    for r in valid_results
                ],
            )

            llm_response = await self._llm.generate(prompt, system=system)

            citations = self._citations.build(valid_results)

            result = AnswerResult(
                status=AnswerStatusEnum.ANSWERED,
                text=llm_response.text,
                citations=citations,
                retrieved_chunk_ids=[r.chunk_id for r in valid_results],
                retrieval_scores=[r.score for r in valid_results],
                llm_provider=llm_response.provider,
                llm_model=llm_response.model,
                prompt_version=prompt_version,
                latency_ms=ms_since(start),
            )

        except Exception as exc:
            logger.exception("query.generation_failed")
            result = self._answer_policy.error_result(str(exc))
            result.latency_ms = ms_since(start)
            record_query_latency(result.latency_ms, status=result.status.value)
            await self._persist(question_text, q_hash, source, user_id, result)
            return result

        record_query_latency(result.latency_ms, status=result.status.value)

        # 6. Cache and persist
        if not bypass_cache:
            await cache_set(
                self._redis,
                cache_key,
                json.dumps(
                    {
                        "status": result.status.value,
                        "text": result.text,
                        "citations": [
                            {
                                "document_name": c.document_name,
                                "page": c.page,
                                "chunk_id": c.chunk_id,
                            }
                            for c in result.citations
                        ],
                        "llm_provider": result.llm_provider,
                        "llm_model": result.llm_model,
                        "prompt_version": result.prompt_version,
                        "latency_ms": result.latency_ms,
                    }
                ),
                ttl_seconds=self._settings.answer_cache_ttl_seconds,
            )
        await self._persist(question_text, q_hash, source, user_id, result)

        return result

    async def _persist(
        self,
        question_text: str,
        q_hash: str,
        source: str,
        user_id: str | None,
        result: AnswerResult,
    ) -> None:
        """Store question and answer in SQL for observability.

        Uses raw INSERT to bypass MappedAsDataclass id-generation quirks
        (see BUG-1: question_id was None when using ORM dataclass __init__).
        Sets ``result.answer_id`` so callers (e.g. Telegram feedback buttons)
        can reference the persisted answer.
        """
        try:
            from sqlalchemy import insert

            question_id = uuid.uuid4()
            answer_id = uuid.uuid4()

            async with self._chat_repo._sf() as session:
                await session.execute(
                    insert(ChatQuestion.__table__).values(
                        id=question_id,
                        question_text=question_text,
                        question_hash=q_hash,
                        source=source,
                        user_id=user_id,
                    )
                )
                await session.execute(
                    insert(ChatAnswer.__table__).values(
                        id=answer_id,
                        question_id=question_id,
                        answer_text=result.text,
                        status=AnswerStatus(result.status.value).value,
                        llm_provider=result.llm_provider or "openai",
                        llm_model=result.llm_model or "",
                        prompt_version=result.prompt_version or "answer_v1",
                        retrieval_scores=result.retrieval_scores,
                        retrieved_chunk_ids=result.retrieved_chunk_ids,
                        citations=[
                            {
                                "document_name": c.document_name,
                                "page": c.page,
                                "chunk_id": c.chunk_id,
                            }
                            for c in result.citations
                        ],
                        latency_ms=result.latency_ms,
                    )
                )
                await session.commit()

            result.answer_id = answer_id
            logger.debug(
                "query.persisted",
                question_id=str(question_id),
                answer_id=str(answer_id),
            )
        except Exception:
            logger.exception("query.persist_failed")

    def _hybrid_merge(
        self,
        question_text: str,
        dense_results: list,
        query_embedding: list[float],
    ) -> list:
        """Merge dense retrieval results with BM25 using RRF.

        RRF decides the order only. Each result keeps its cosine similarity as
        ``score`` so the answer policy's ``min_score`` gate still means the same
        thing; RRF values (~0.01) would otherwise fail the gate every time.
        """
        from app.infrastructure.retrieval.bm25 import HybridConfig, hybrid_merge

        config = HybridConfig(
            enabled=True,
            dense_weight=self._settings.hybrid_dense_weight,
            bm25_weight=self._settings.hybrid_bm25_weight,
        )

        bm25_results = self._bm25_index.query(  # type: ignore[union-attr]
            question_text,
            top_k=config.bm25_top_k,
        )

        if not bm25_results:
            return dense_results

        dense_tuples = [(r.chunk_id, r.score) for r in dense_results]
        merged = hybrid_merge(dense_tuples, bm25_results, config)

        # Build lookup of dense results by chunk_id
        dense_map: dict[str, RetrievalResult] = {r.chunk_id: r for r in dense_results}

        # Find BM25-only chunk IDs not in dense results
        bm25_only_ids = [cid for cid, _ in merged if cid not in dense_map]
        if bm25_only_ids:
            bm25_only_results = self._index.get_by_ids(
                bm25_only_ids, query_embedding=query_embedding
            )
            for r in bm25_only_results:
                dense_map[r.chunk_id] = r

        # Reconstruct results in fused order, keeping similarity scores
        final: list[RetrievalResult] = [
            dense_map[chunk_id] for chunk_id, _rrf in merged if chunk_id in dense_map
        ]

        top_k = self._retrieval_policy.config.top_k
        logger.debug("query.hybrid_merged", total=len(final), top_k=top_k)
        return final[:top_k]

    async def _resolve_prompt(self) -> tuple[str, str, str]:
        """Load prompt template: try SQL registry, fall back to Jinja2 file.

        Returns (template_text, system_prompt, prompt_version_name).
        """
        # Try SQL prompt registry
        if self._prompt_repo is not None:
            try:
                active = await self._prompt_repo.get_active("answer")
                if active is not None:
                    logger.debug("query.prompt_from_sql", version=active.version)
                    return active.template_text, active.system_prompt, active.version
            except Exception:
                logger.warning("query.prompt_registry_failed_falling_back")

        # Fallback to Jinja2 file — read raw source so jinja2.Template() works
        source = _jinja_env.loader.get_source(_jinja_env, "answer_v1.jinja2")[0]  # type: ignore[union-attr]
        system = (
            "You answer on behalf of Arch Tech customer support. "
            "Speak on behalf of the company: we, our team, our Arch Tech knowledge base. "
            "Use only facts from the knowledge base and do not invent unsupported products, "
            "policies, prices, dates, contacts, or instructions."
        )
        return source, system, "answer_v1"
