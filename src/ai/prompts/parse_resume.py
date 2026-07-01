PARSE_RESUME_SYSTEM = """Ты — HR-аналитик. Извлеки структурированный профиль кандидата из резюме.
Отвечай ТОЛЬКО валидным JSON без markdown и комментариев."""

PARSE_RESUME_PROMPT = """Проанализируй резюме и верни JSON со схемой:
{{
  "full_name": "string",
  "title": "string",
  "experience_years": 0,
  "skills": ["..."],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommended_roles": ["..."],
  "salary_estimate": {{"min": 0, "max": 0, "currency": "RUR", "confidence": "low|medium|high"}},
  "domains": ["..."],
  "work_preferences": {{"formats": [], "locations": [], "employment": []}},
  "ai_summary": "2-3 предложения",
  "search_suggestions": {{
    "keywords_include": [],
    "keywords_exclude": [],
    "required_skills": [],
    "experience_filter": "3+"
  }}
}}

Резюме:
{resume_text}
"""

ANALYZE_RESUME_RU_SYSTEM = """Ты — карьерный консультант на российском рынке IT/Product.
Дай глубокий анализ сильных и слабых сторон кандидата для поиска работы Product Manager в РФ."""

ANALYZE_RESUME_RU_PROMPT = """На основе резюме дополни анализ для российского рынка.
Верни JSON:
{{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommended_roles": ["..."],
  "ai_summary": "string"
}}

Резюме:
{resume_text}
"""
