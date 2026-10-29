"""Pydantic feedback schemas."""

from __future__ import annotations

import uuid  # noqa: TC003

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    answer_id: uuid.UUID
    rating: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    comment: str | None = None
    user_id: str | None = None


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    answer_id: uuid.UUID
    rating: str
    message: str = "Feedback recorded"
