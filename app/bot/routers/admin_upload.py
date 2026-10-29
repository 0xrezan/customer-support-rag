"""Admin document upload handlers for Telegram."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot, Router
from aiogram.filters import Command

from app.logging import get_logger

if TYPE_CHECKING:
    from aiogram.types import Message

logger = get_logger(__name__)

router = Router(name="admin_upload")


@router.message(Command("upload"))
async def handle_upload(message: Message, bot: Bot, **kwargs) -> None:
    """Accept a document from an allowlisted admin."""
    container = kwargs["container"]

    if not message.document:
        await message.answer("Please attach a file with the /upload command.")
        return

    file = await bot.get_file(message.document.file_id)
    if not file.file_path:
        await message.answer("Could not retrieve file.")
        return

    file_bytes = await bot.download_file(file.file_path)
    if file_bytes is None:
        await message.answer("Could not download file.")
        return

    data = file_bytes.read()
    filename = message.document.file_name or "unknown"
    mime = message.document.mime_type or "application/octet-stream"

    upload_service = container.upload_service
    doc, is_new = await upload_service.register(data, filename, mime)

    if is_new:
        upload_service.enqueue_ingestion(doc.id)
        await message.answer(
            f"Document <b>{filename}</b> registered (v{doc.version}). Ingestion started."
        )
    else:
        await message.answer(
            f"Document <b>{filename}</b> already exists (v{doc.version}, status: {doc.status})."
        )

    logger.info(
        "bot.upload",
        user_id=message.from_user.id if message.from_user else None,
        filename=filename,
        is_new=is_new,
    )
