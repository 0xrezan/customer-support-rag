"""User chat handlers — accept questions and call QueryService."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot.presenters.answer_formatter import format_answer_for_telegram
from app.logging import get_logger

logger = get_logger(__name__)

router = Router(name="user_chat")


def _feedback_keyboard(answer_id: str) -> InlineKeyboardMarkup:
    """Build an inline keyboard with thumbs-up / thumbs-down buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f44d",
                    callback_data=f"feedback:{answer_id}:thumbs_up",
                ),
                InlineKeyboardButton(
                    text="\U0001f44e",
                    callback_data=f"feedback:{answer_id}:thumbs_down",
                ),
            ]
        ]
    )


@router.message()
async def handle_question(message: Message, **kwargs) -> None:
    """Handle any text message as a user question."""
    if not message.text:
        return

    container = kwargs.get("container")
    if container is None:
        await message.answer("Service unavailable. Please try again later.")
        return

    query_service = container.query_service
    user_id = str(message.from_user.id) if message.from_user else None

    result = await query_service.ask(
        message.text,
        source="telegram",
        user_id=user_id,
    )

    formatted = format_answer_for_telegram(result)

    # Attach feedback buttons when we have a persisted answer_id
    reply_markup = None
    if result.answer_id is not None:
        reply_markup = _feedback_keyboard(str(result.answer_id))

    await message.answer(formatted, reply_markup=reply_markup)

    logger.info(
        "bot.question",
        user_id=user_id,
        status=result.status.value,
        latency_ms=result.latency_ms,
    )
