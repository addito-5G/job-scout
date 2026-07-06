"""Краткая AI-справка о компании-работодателе."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ai import AIRouter
from db.models import Company


def ensure_company_brief(
    session: Session,
    company: Company | None,
    *,
    vacancy_snippet: str = "",
    source: str = "",
) -> str | None:
    if not company or company.ai_brief:
        return company.ai_brief if company else None

    snippet = (vacancy_snippet or company.description or company.name or "")[:1200]
    router = AIRouter(session)
    try:
        result = router.route(
            "company_brief",
            {
                "company_name": company.name,
                "source": source,
                "vacancy_snippet": snippet,
            },
            parse_json=True,
        )
        brief = ""
        if result.parsed:
            brief = str(result.parsed.get("brief", "")).strip()
        if not brief:
            brief = (result.content or "").strip()[:200]
        brief = brief[:200]
        if brief:
            company.ai_brief = brief
            session.commit()
        return brief or None
    except Exception:
        return None
