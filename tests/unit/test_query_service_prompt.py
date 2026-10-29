"""Query prompt contract tests."""

from __future__ import annotations

import pytest

from app.domain.services.query_service import QueryService


@pytest.mark.asyncio
async def test_fallback_prompt_speaks_as_arch_tech_support_in_english() -> None:
    service = QueryService.__new__(QueryService)
    service._prompt_repo = None

    template, system, version = await service._resolve_prompt()

    assert version == "answer_v1"
    normalized_system = system.lower()
    assert "Arch Tech customer support" in system
    assert "speak on behalf of the company" in normalized_system
    assert "use only facts from the knowledge base" in normalized_system
    assert "our arch tech knowledge base" in template.lower()
    assert "предоставленном контексте" not in template.lower()
    assert "provided context" not in template.lower()
    assert "службы поддержки" not in system
    assert "говоришь" not in system
