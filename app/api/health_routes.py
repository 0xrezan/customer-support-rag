"""Liveness, readiness, and dependency health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health")


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Kubernetes-style liveness probe."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness(request: Request) -> JSONResponse:
    """Readiness probe — checks DB, Redis, Chroma connectivity."""
    container = request.app.state.container
    checks: dict[str, str] = {}

    # Redis
    try:
        await container.redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    # Chroma
    try:
        container.chroma_client.heartbeat()
        checks["chroma"] = "ok"
    except Exception:
        checks["chroma"] = "error"

    # Database (basic connectivity)
    try:
        async with container.db_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503
    return JSONResponse(
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
        status_code=status_code,
    )
