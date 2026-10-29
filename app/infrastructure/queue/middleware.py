"""Dramatiq middleware for retries, logging, and structured context."""

from __future__ import annotations

import dramatiq

from app.logging import get_logger, set_correlation_id

logger = get_logger(__name__)


class StructuredLoggingMiddleware(dramatiq.Middleware):
    """Inject correlation IDs and log task lifecycle events."""

    def before_process_message(
        self,
        broker: dramatiq.Broker,
        message: dramatiq.Message,
    ) -> None:
        cid = message.options.get("correlation_id", message.message_id)
        set_correlation_id(cid)
        logger.info(
            "task.start",
            actor=message.actor_name,
            message_id=message.message_id,
        )

    def after_process_message(
        self,
        broker: dramatiq.Broker,
        message: dramatiq.Message,
        *,
        result: object = None,
        exception: BaseException | None = None,
    ) -> None:
        if exception:
            logger.error(
                "task.failed",
                actor=message.actor_name,
                message_id=message.message_id,
                error=str(exception),
            )
        else:
            logger.info(
                "task.done",
                actor=message.actor_name,
                message_id=message.message_id,
            )
