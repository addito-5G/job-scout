"""Smoke-тесты реестра промптов AI."""

from __future__ import annotations

from ai.task_prompts import TASK_PROMPT_BUILDERS, build_task_prompt


def test_task_registry_has_cover_letter():
    assert "generate_cover_letter" in TASK_PROMPT_BUILDERS


def test_build_task_prompt_custom_payload():
    prompt, system = build_task_prompt("custom", {"prompt": "hello", "system": "sys"})
    assert prompt == "hello"
    assert system == "sys"
