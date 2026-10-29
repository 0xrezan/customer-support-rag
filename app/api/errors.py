"""HTTP error mapping and exception handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from app.logging import get_logger
from app.schemas.common import ErrorResponse

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

logger = get_logger(__name__)


class DomainError(Exception):
    """Base exception for domain-level errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentNotFoundError(DomainError):
    def __init__(self, doc_id: str) -> None:
        super().__init__(f"Document {doc_id} not found", status_code=404)


class InvalidTransitionError(DomainError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=409)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        logger.warning("api.domain_error", error=exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("api.unhandled_error")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="Internal server error").model_dump(),
        )
