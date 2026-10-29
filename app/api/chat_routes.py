"""Web chat endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_query_service
from app.logging import get_logger
from app.schemas.chat import AskRequest, AskResponse, CitationSchema
from app.schemas.common import ResponseEnvelope

logger = get_logger(__name__)

router = APIRouter(prefix="/chat")


async def _rate_limit_check(request: Request) -> None:
    """Enforce per-IP rate limiting on public chat endpoints."""
    container = request.app.state.container
    if container.rate_limiter is None:
        return
    client_ip = request.client.host if request.client else "unknown"
    key = f"chat:rate:{client_ip}"
    allowed: bool = await container.rate_limiter.is_allowed(key)
    if not allowed:
        logger.warning("chat.rate_limited", client_ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )


@router.post("/ask", dependencies=[Depends(_rate_limit_check)])
async def ask_question(
    body: AskRequest,
    query_service=Depends(get_query_service),
) -> ResponseEnvelope[AskResponse]:
    """Submit a question and receive an AI-generated answer."""
    result = await query_service.ask(
        body.question,
        source=body.source,
        user_id=body.user_id,
        bypass_cache=body.bypass_cache,
    )
    return ResponseEnvelope(
        data=AskResponse(
            status=result.status.value,
            answer=result.text,
            citations=[
                CitationSchema(
                    document_name=c.document_name,
                    page=c.page,
                    chunk_id=c.chunk_id,
                )
                for c in result.citations
            ],
            llm_provider=result.llm_provider,
            llm_model=result.llm_model,
            latency_ms=result.latency_ms,
        )
    )
