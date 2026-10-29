"""Offline quality evaluation for the RAG pipeline.

Indexes the sample knowledge base into an in-memory Chroma collection and runs a
fixed question set through two stages:

1. Retrieval: for each mode (dense, dense + rerank, hybrid BM25 + rerank), is the
   right document in the top-k, and do the retrieved chunks contain the fact the
   answer needs?
2. Answering: the real ``QueryService.ask`` path. Answerable questions are scored
   by required facts in the answer; unanswerable ones must be declined instead of
   invented.

Usage::

    OPENAI_API_KEY=... python -m evals.run_eval
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

import chromadb

from app.config import Settings
from app.domain.policies.chunking_policy import ChunkingConfig, ChunkingPolicy
from app.domain.policies.reranking_policy import RerankingConfig, RerankingPolicy
from app.domain.services.citation_service import CitationService
from app.domain.services.query_service import QueryService
from app.domain.value_objects.answer_result import AnswerStatusEnum
from app.domain.value_objects.chunk_metadata import ChunkMetadata
from app.infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingClient
from app.infrastructure.llm.openai_client import OpenAILLMClient
from app.infrastructure.parsers.text_parser import TextParser
from app.infrastructure.retrieval.bm25 import BM25Index
from app.infrastructure.vectorstore.chunk_index_repo import ChunkIndexRepository
from app.utils.ids import make_chunk_id

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "test_docs"
DATASET = Path(__file__).resolve().parent / "dataset.jsonl"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

# Phrases the answer prompt uses when the context does not cover the question.
DECLINE_MARKERS = (
    "could not find",
    "couldn't find",
    "does not have",
    "doesn't have",
    "not in the knowledge base",
    "no information",
    "не нашл",
    "нет информации",
    "нет данных",
    "нет сведений",
    "не содерж",
    "не указан",
)

JUDGE_PROMPT = """You grade a customer-support bot that must answer only from its knowledge base.
The question below is NOT covered by the knowledge base.

Question: {question}
Bot answer: {answer}

Did the bot avoid inventing a specific answer (it declined, said the information is
unavailable, or redirected to support)?
Reply with JSON: {{"declined": true}} or {{"declined": false}}."""


@dataclass
class Case:
    id: str
    question: str
    source: str | None = None
    expect: list[list[str]] = field(default_factory=list)
    unanswerable: bool = False


class _NullSession:
    async def execute(self, *_args, **_kwargs) -> None:
        return None

    async def commit(self) -> None:
        return None


class _NullChatRepo:
    """Answers are not persisted during evaluation."""

    @staticmethod
    @asynccontextmanager
    async def _sf():
        yield _NullSession()


def load_cases() -> list[Case]:
    lines = DATASET.read_text(encoding="utf-8").splitlines()
    return [Case(**json.loads(line)) for line in lines if line.strip()]


async def build_index(
    settings: Settings, embedder: OpenAIEmbeddingClient
) -> tuple[ChunkIndexRepository, BM25Index]:
    client = chromadb.EphemeralClient()
    index = ChunkIndexRepository(client, f"eval_{uuid.uuid4().hex[:8]}")
    chunker = ChunkingPolicy(
        ChunkingConfig(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    )
    parser = TextParser()

    for path in sorted(DOCS_DIR.glob("*.txt")):
        doc_id = uuid.uuid4()
        chunks = chunker.split_pages({1: parser.parse(path.read_bytes()).text})
        embeddings = await embedder.embed_batch([c.text for c in chunks])
        ids, metas = [], []
        for chunk in chunks:
            chunk_id = make_chunk_id(doc_id, 1, chunk.page, chunk.chunk_index)
            ids.append(chunk_id)
            metas.append(
                ChunkMetadata(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    document_name=path.name,
                    document_version=1,
                    page=chunk.page,
                    chunk_index=chunk.chunk_index,
                    source_type="text/plain",
                    is_active=True,
                ).to_dict()
            )
        index.add_chunks(ids, [c.text for c in chunks], embeddings, metas)

    bm25 = BM25Index()
    bm25.build(index.get_all_chunk_texts())
    return index, bm25


def retrieve(mode: str, question: str, embedding, service: QueryService) -> list:
    """Run QueryService retrieval for a single mode, without generation."""
    results = service._index.query(
        embedding, top_k=service._retrieval_policy.config.top_k, where={"is_active": True}
    )
    if mode == "hybrid" and results:
        results = service._hybrid_merge(question, results, embedding)
    if mode in ("rerank", "hybrid"):
        results = RerankingPolicy(RerankingConfig()).rerank(question, results)
    return results


def matches(answer: str, expect: list[list[str]]) -> bool:
    text = answer.lower()
    return all(any(alt.lower() in text for alt in group) for group in expect)


async def judge_declined(llm: OpenAILLMClient, question: str, answer: str) -> bool:
    lowered = answer.lower()
    if any(marker in lowered for marker in DECLINE_MARKERS):
        return True
    response = await llm.generate(JUDGE_PROMPT.format(question=question, answer=answer))
    found = re.search(r"\{.*\}", response.text, re.S)
    return bool(found and json.loads(found.group(0)).get("declined"))


def pct(values: list[bool]) -> float:
    return round(100 * sum(values) / len(values), 1) if values else 0.0


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hybrid", action="store_true", help="answer with hybrid retrieval on")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required")
    settings = Settings(
        _env_file=None,
        openai_api_key=api_key,
        hybrid_retrieval_enabled=args.hybrid,
        **(
            {"openai_chat_model": os.environ["OPENAI_CHAT_MODEL"]}
            if os.environ.get("OPENAI_CHAT_MODEL")
            else {}
        ),
    )
    embedder = OpenAIEmbeddingClient(
        api_key=api_key,
        model=settings.openai_embedding_model,
        dimensions=settings.openai_embedding_dimensions,
    )
    llm = OpenAILLMClient(
        api_key=api_key,
        model=settings.openai_chat_model,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature,
    )
    cases = load_cases()
    index, bm25 = await build_index(settings, embedder)
    service = QueryService(
        chunk_index_repo=index,
        embedding_client=embedder,
        llm_client=llm,
        citation_service=CitationService(),
        chat_repo=_NullChatRepo(),
        redis=None,
        settings=settings,
        bm25_index=bm25,
    )

    # Stage 1: retrieval only.
    answerable = [c for c in cases if not c.unanswerable]
    embeddings = {c.id: await embedder.embed(c.question) for c in answerable}
    retrieval: dict[str, dict[str, float]] = {}
    for mode in ("dense", "rerank", "hybrid"):
        hit1, hitk, recall, gated = [], [], [], []
        for case in answerable:
            results = retrieve(mode, case.question, embeddings[case.id], service)
            names = [r.metadata.document_name for r in results]
            hit1.append(bool(names) and names[0] == case.source)
            hitk.append(case.source in names)
            recall.append(matches(" ".join(r.text for r in results), case.expect))
            gated.append(any(r.score >= settings.retrieval_min_score for r in results))
        retrieval[mode] = {
            "doc_hit@1": pct(hit1),
            "doc_hit@k": pct(hitk),
            "fact_recall@k": pct(recall),
            "passes_gate": pct(gated),
        }

    # Stage 2: end-to-end answers through the production QueryService.
    # Hybrid merging only runs when settings.hybrid_retrieval_enabled is set.
    rows, latencies = [], []
    for case in cases:
        started = time.perf_counter()
        result = await service.ask(case.question, source="eval", bypass_cache=True)
        latencies.append((time.perf_counter() - started) * 1000)
        cited = sorted({c.document_name for c in result.citations})
        if case.unanswerable:
            ok = result.status == AnswerStatusEnum.INSUFFICIENT_CONTEXT or await judge_declined(
                llm, case.question, result.text
            )
        else:
            ok = result.status == AnswerStatusEnum.ANSWERED and matches(result.text, case.expect)
        rows.append(
            {
                "id": case.id,
                "unanswerable": case.unanswerable,
                "status": result.status.value,
                "ok": ok,
                "cited_expected_source": case.source in cited if case.source else None,
                "citations": cited,
                "answer": result.text,
            }
        )
        print(f"{'PASS' if ok else 'FAIL'}  {case.id:<22} {result.status.value}")

    answered_rows = [r for r in rows if not r["unanswerable"]]
    declined_rows = [r for r in rows if r["unanswerable"]]
    summary = {
        "model": settings.openai_chat_model,
        "embedding_model": settings.openai_embedding_model,
        "hybrid": args.hybrid,
        "cases": len(cases),
        "retrieval": retrieval,
        "answer_accuracy": pct([r["ok"] for r in answered_rows]),
        "citation_accuracy": pct([bool(r["cited_expected_source"]) for r in answered_rows]),
        "unanswerable_declined": pct([r["ok"] for r in declined_rows]),
        "latency_ms_p50": round(statistics.median(latencies)),
        "latency_ms_p95": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))]),
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    name = "latest-hybrid.json" if args.hybrid else "latest.json"
    (RESULTS_DIR / name).write_text(
        json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
