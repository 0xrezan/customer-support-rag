"""Telegram-friendly answer and citation formatting."""

from __future__ import annotations

from app.domain.value_objects.answer_result import AnswerResult, AnswerStatusEnum


def format_answer_for_telegram(result: AnswerResult) -> str:
    """Render an AnswerResult as HTML text suitable for Telegram."""
    if result.status == AnswerStatusEnum.ERROR:
        return "An error occurred while processing your question. Please try again later."

    if result.status == AnswerStatusEnum.INSUFFICIENT_CONTEXT:
        return (
            "I couldn't find enough information in the knowledge base "
            "to answer your question. Please try rephrasing, or contact "
            "a human support agent."
        )

    parts: list[str] = [result.text]

    if result.citations:
        parts.append("")
        parts.append("<b>Sources:</b>")
        seen: set[str] = set()
        for c in result.citations:
            display = c.display()
            if display not in seen:
                seen.add(display)
                parts.append(f"  - {display}")

    return "\n".join(parts)
