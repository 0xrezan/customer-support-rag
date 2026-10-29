"""Structlog configuration and correlation-ID helpers."""

from __future__ import annotations

import contextvars
import logging
import sys
import uuid
from typing import Any

import structlog

# Context variable holding the current request / correlation ID.
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


def set_correlation_id(cid: str | None = None) -> str:
    """Set (or generate) a correlation ID for the current async context."""
    value = cid or uuid.uuid4().hex[:16]
    correlation_id_ctx.set(value)
    return value


def get_correlation_id() -> str:
    return correlation_id_ctx.get("")


def _add_correlation_id(
    logger: Any,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    cid = correlation_id_ctx.get("")
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog + stdlib logging for the whole application."""

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_correlation_id,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level.upper())

    # Silence noisy third-party loggers
    for name in ("uvicorn.access", "httpx", "httpcore", "chromadb"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
