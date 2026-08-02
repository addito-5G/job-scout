"""Реестр построителей промптов для AIRouter (без изменения текстов)."""

from __future__ import annotations

import json
from typing import Any, Callable

PromptBuilder = Callable[[dict[str, Any]], tuple[str, str | None]]


def _build_parse_resume(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.parse_resume import PARSE_RESUME_PROMPT, PARSE_RESUME_SYSTEM

    return (
        PARSE_RESUME_PROMPT.format(resume_text=payload.get("resume_text", "")),
        PARSE_RESUME_SYSTEM,
    )


def _build_analyze_resume_ru(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.parse_resume import ANALYZE_RESUME_RU_PROMPT, ANALYZE_RESUME_RU_SYSTEM

    return (
        ANALYZE_RESUME_RU_PROMPT.format(resume_text=payload.get("resume_text", "")),
        ANALYZE_RESUME_RU_SYSTEM,
    )


def _build_suggest_filters(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.suggest_filters import SUGGEST_FILTERS_PROMPT, SUGGEST_FILTERS_SYSTEM

    return (
        SUGGEST_FILTERS_PROMPT.format(profile_json=payload.get("profile_json", "{}")),
        SUGGEST_FILTERS_SYSTEM,
    )


def _build_cover_letter(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.cover_letter import (
        COVER_LETTER_EXAMPLE,
        COVER_LETTER_SYSTEM,
        ROLE_SKILL_GUIDANCE,
        TARGET_ROLE_LABELS,
        apply_channel_guidance,
        format_cover_letter_prompt,
    )

    target_role = payload.get("target_role", "general")
    profile_data = json.loads(payload.get("profile_json", "{}"))
    vacancy_data = json.loads(payload.get("vacancy_json", "{}"))
    vacancy_source = str(vacancy_data.get("source") or "hh")
    channel = payload.get("apply_channel", "same")
    return (
        format_cover_letter_prompt(
            example=COVER_LETTER_EXAMPLE,
            target_role_label=TARGET_ROLE_LABELS.get(target_role, TARGET_ROLE_LABELS["general"]),
            role_guidance=ROLE_SKILL_GUIDANCE.get(target_role, ROLE_SKILL_GUIDANCE["general"]),
            apply_channel_guidance=apply_channel_guidance(vacancy_source, apply_channel=channel),
            candidate_role_title=profile_data.get("role_title", "специалист"),
            profile_json=payload.get("profile_json", "{}"),
            vacancy_json=payload.get("vacancy_json", "{}"),
            match_context_json=payload.get("match_context_json", "{}"),
        ),
        COVER_LETTER_SYSTEM,
    )


def _build_company_brief(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.company_brief import COMPANY_BRIEF_PROMPT, COMPANY_BRIEF_SYSTEM

    return (
        COMPANY_BRIEF_PROMPT.format(
            company_name=payload.get("company_name", ""),
            source=payload.get("source", ""),
            vacancy_snippet=payload.get("vacancy_snippet", ""),
        ),
        COMPANY_BRIEF_SYSTEM,
    )


def _build_improve_resume(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.improve_resume import IMPROVE_RESUME_PROMPT, IMPROVE_RESUME_SYSTEM

    return (
        IMPROVE_RESUME_PROMPT.format(
            resume_text=payload.get("resume_text", ""),
            profile_json=payload.get("profile_json", "{}"),
            market_requirements_json=payload.get("market_requirements_json", "{}"),
            vacancy_count=payload.get("vacancy_count", 0),
            target_role=payload.get("target_role", "специалист"),
            total_experience_years=payload.get("total_experience_years", "не указан"),
            candidate_full_name=payload.get("candidate_full_name", "не указано"),
            profile_id=payload.get("profile_id", 0),
            profile_label=payload.get("profile_label", ""),
        ),
        IMPROVE_RESUME_SYSTEM,
    )


def _build_vacancy_fit_advice(payload: dict[str, Any]) -> tuple[str, str | None]:
    from ai.prompts.vacancy_fit_advice import VACANCY_FIT_ADVICE_PROMPT, VACANCY_FIT_ADVICE_SYSTEM

    return (
        VACANCY_FIT_ADVICE_PROMPT.format(
            candidate_name=payload.get("candidate_name", "Кандидат"),
            target_role=payload.get("target_role", "специалист"),
            resume_excerpt=payload.get("resume_excerpt", ""),
            profile_json=payload.get("profile_json", "{}"),
            vacancy_json=payload.get("vacancy_json", "{}"),
            fit_context_json=payload.get("fit_context_json", "{}"),
        ),
        VACANCY_FIT_ADVICE_SYSTEM,
    )


TASK_PROMPT_BUILDERS: dict[str, PromptBuilder] = {
    "parse_resume": _build_parse_resume,
    "analyze_resume_ru": _build_analyze_resume_ru,
    "suggest_filters": _build_suggest_filters,
    "generate_cover_letter": _build_cover_letter,
    "improve_resume": _build_improve_resume,
    "vacancy_fit_advice": _build_vacancy_fit_advice,
    "company_brief": _build_company_brief,
}


def build_task_prompt(task_type: str, payload: dict[str, Any]) -> tuple[str, str | None]:
    builder = TASK_PROMPT_BUILDERS.get(task_type)
    if builder:
        return builder(payload)
    if "prompt" in payload:
        return payload["prompt"], payload.get("system")
    raise ValueError(f"Неизвестный payload для задачи {task_type}")
