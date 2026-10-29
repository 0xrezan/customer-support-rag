"""Common LLM interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardised response from any LLM provider."""

    text: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class BaseLLMClient(abc.ABC):
    """Abstract base for LLM provider adapters."""

    @abc.abstractmethod
    async def generate(self, prompt: str, *, system: str = "") -> LLMResponse:
        """Send a prompt and return the generated text."""
