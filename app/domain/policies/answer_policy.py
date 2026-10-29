"""Answer policy — decides whether to call the LLM or return insufficient context."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.value_objects.answer_result import AnswerResult, AnswerStatusEnum

if TYPE_CHECKING:
    from app.domain.policies.retrieval_policy import RetrievalPolicy
    from app.domain.value_objects.retrieval_result import RetrievalResult

_INSUFFICIENT_CONTEXT_MSG = (
    "Our Arch Tech knowledge base does not have enough precise information "
    "to answer this question yet. We can help with what is already covered "
    "in the knowledge base: product categories, delivery, payments, returns, "
    "warranty, and support requests."
)


class AnswerPolicy:
    """Gate between retrieval and generation.

    If retrieval is weak, returns an ``insufficient_context`` result
    without calling the LLM at all.
    """

    def __init__(self, retrieval_policy: RetrievalPolicy) -> None:
        self._retrieval_policy = retrieval_policy

    def evaluate(
        self,
        results: list[RetrievalResult],
    ) -> tuple[bool, list[RetrievalResult]]:
        """Return (should_generate, valid_results).

        ``should_generate`` is True when retrieval passes the gate.
        """
        valid = self._retrieval_policy.filter_results(results)
        should_generate = self._retrieval_policy.is_sufficient(valid)
        return should_generate, valid

    @staticmethod
    def insufficient_context_result() -> AnswerResult:
        return AnswerResult(
            status=AnswerStatusEnum.INSUFFICIENT_CONTEXT,
            text=_INSUFFICIENT_CONTEXT_MSG,
        )

    @staticmethod
    def error_result(error_msg: str = "") -> AnswerResult:
        return AnswerResult(
            status=AnswerStatusEnum.ERROR,
            text=f"An error occurred while generating the answer. {error_msg}".strip(),
        )
