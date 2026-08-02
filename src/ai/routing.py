from __future__ import annotations

"""Маршрутизация AI-задач по провайдерам."""

# primary provider per task; fallback chain handled in ai_router
TASK_ROUTING: dict[str, str] = {
    "parse_resume": "ollama",
    "extract_skills": "ollama",
    "extract_skills_ru": "yandex",
    "categorize_vacancy": "ollama",
    "improve_resume": "yandex",
    "generate_cover_letter": "yandex",
    "vacancy_fit_advice": "groq",
    "suggest_filters": "ollama",
    "company_brief": "yandex",
}

FALLBACK_CHAIN: dict[str, list[str]] = {
    "ollama": ["yandex", "groq"],
    "yandex": ["groq", "ollama"],
    "groq": ["yandex", "ollama"],
}

# TTL in days per task type
CACHE_TTL_DAYS: dict[str, int] = {
    "parse_resume": 7,
    "analyze_resume_ru": 7,
    "extract_skills": 30,
    "extract_skills_ru": 30,
    "improve_resume": 7,
    "vacancy_fit_advice": 14,
    "company_brief": 30,
    "default": 30,
}
