"""Feedback submit endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_feedback_service
from app.logging import get_logger
from app.schemas.common import ResponseEnvelope
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/feedback")


@router.post("/submit")
async def submit_feedback(
    body: FeedbackRequest,
    feedback_service=Depends(get_feedback_service),
) -> ResponseEnvelope[FeedbackResponse]:
    """Submit thumbs-up / thumbs-down feedback on an answer."""
    event = await feedback_service.submit(
        answer_id=body.answer_id,
        rating=body.rating,
        comment=body.comment,
        user_id=body.user_id,
    )
    return ResponseEnvelope(
        data=FeedbackResponse(
            id=event.id,
            answer_id=event.answer_id,
            rating=event.rating.value if hasattr(event.rating, "value") else str(event.rating),
        )
    )
