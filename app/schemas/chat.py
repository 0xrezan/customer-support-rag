"""Pydantic chat schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    source: str = "web"
    user_id: str | None = None
    bypass_cache: bool = False


class CitationSchema(BaseModel):
    document_name: str
    page: int
    chunk_id: str = ""


class AskResponse(BaseModel):
    status: str
    answer: str
    citations: list[CitationSchema] = []
    llm_provider: str = ""
    llm_model: str = ""
    latency_ms: int = 0
