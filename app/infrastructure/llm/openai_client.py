"""OpenAI LLM implementation."""

from __future__ import annotations

import openai

from app.infrastructure.llm.base import BaseLLMClient, LLMResponse
from app.logging import get_logger

logger = get_logger(__name__)


class OpenAILLMClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    async def generate(self, prompt: str, *, system: str = "") -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_completion_tokens=self._max_tokens,
            temperature=self._temperature,
        )

        choice = response.choices[0]
        usage = response.usage

        logger.info(
            "llm.openai.generated",
            model=self._model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )

        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            provider="openai",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )
