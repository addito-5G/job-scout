"""Тесты fallback-цепочки AIRouter."""

from __future__ import annotations

from unittest.mock import MagicMock

from ai.ai_router import AIRouter


def test_provider_chain_ends_with_ollama_for_cloud_primary():
    router = AIRouter(MagicMock())
    chain = router._provider_chain("generate_cover_letter")
    assert chain[0] == "yandex"
    assert chain[-1] == "ollama"
