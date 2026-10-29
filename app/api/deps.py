"""FastAPI dependency providers — exposes typed services from the container."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request, status

if TYPE_CHECKING:
    from app.containers import Container
    from app.domain.services.feedback_service import FeedbackService
    from app.domain.services.query_service import QueryService
    from app.domain.services.reconcile_service import ReconcileService
    from app.domain.services.upload_service import UploadService
    from app.infrastructure.db.repositories.documents import DocumentRepository


def get_container(request: Request) -> Container:
    """Return the DI container from app state."""
    return request.app.state.container


def _require(service: object | None, name: str) -> object:
    """Raise 503 if a service is not initialised."""
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{name} is not available — the server is still starting up",
        )
    return service


def get_upload_service(request: Request) -> UploadService:
    svc = get_container(request).upload_service
    return _require(svc, "UploadService")  # type: ignore[return-value]


def get_query_service(request: Request) -> QueryService:
    svc = get_container(request).query_service
    return _require(svc, "QueryService")  # type: ignore[return-value]


def get_feedback_service(request: Request) -> FeedbackService:
    svc = get_container(request).feedback_service
    return _require(svc, "FeedbackService")  # type: ignore[return-value]


def get_document_repo(request: Request) -> DocumentRepository:
    repo = get_container(request).document_repo
    return _require(repo, "DocumentRepository")  # type: ignore[return-value]


def get_reconcile_service(request: Request) -> ReconcileService:
    svc = get_container(request).reconcile_service
    return _require(svc, "ReconcileService")  # type: ignore[return-value]
