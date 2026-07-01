FAST_MATCH_SYSTEM = """Ты — карьерный ассистент. Оцени соответствие вакансии профилю кандидата.
Отвечай ТОЛЬКО валидным JSON без markdown."""

FAST_MATCH_PROMPT = """Оцени соответствие вакансии профилю кандидата (0-100).

Профиль:
{profile_json}

Вакансия:
{vacancy_json}

Верни JSON:
{{
  "match_score": 0,
  "match_summary": "1-2 предложения почему подходит/нет",
  "matched_skills": ["..."],
  "missing_skills": ["..."],
  "recommendation": "apply|skip|improve_resume"
}}
"""

DEEP_MATCH_SYSTEM = """Ты — senior карьерный консультант. Дай глубокий анализ соответствия кандидата вакансии.
Отвечай ТОЛЬКО валидным JSON без markdown."""

DEEP_MATCH_PROMPT = """Глубокий анализ соответствия.

Профиль:
{profile_json}

Вакансия:
{vacancy_json}

Верни JSON:
{{
  "match_score": 0,
  "match_summary": "краткое резюме",
  "matched_skills": ["..."],
  "missing_skills": ["..."],
  "strengths": ["сильные стороны кандидата для этой роли"],
  "risks": ["потенциальные риски/слабые места"],
  "recommendation": "apply|skip|improve_resume",
  "deep_analysis": "развёрнутый анализ 3-5 предложений"
}}
"""
