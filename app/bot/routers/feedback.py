"""Feedback callback handlers for Telegram inline buttons."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from aiogram import Router

from app.logging import get_logger

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery

logger = get_logger(__name__)

router = Router(name="feedback")


@router.callback_query(lambda c: c.data and c.data.startswith("feedback:"))
async def handle_feedback(callback: CallbackQuery, **kwargs) -> None:
    """Process thumbs-up / thumbs-down callback data.

    Expected format: ``feedback:{answer_id}:{rating}``
    """
    container = kwargs.get("container")
    if container is None or not callback.data:
        await callback.answer("Service unavailable.")
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid feedback data.")
        return

    _, answer_id_str, rating = parts

    try:
        answer_id = uuid.UUID(answer_id_str)
    except ValueError:
        await callback.answer("Invalid answer ID.")
        return

    user_id = str(callback.from_user.id) if callback.from_user else None

    feedback_service = container.feedback_service
    await feedback_service.submit(
        answer_id=answer_id,
        rating=rating,
        user_id=user_id,
    )
    await callback.answer("Thanks for your feedback!")

    logger.info(
        "bot.feedback",
        answer_id=answer_id_str,
        rating=rating,
        user_id=user_id,
    )
