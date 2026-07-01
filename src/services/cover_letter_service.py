from __future__ import annotations

from sqlalchemy.orm import Session

from ai import AIRouter
from ai.ai_router import AIRouterError
from db.models import CandidateProfile, Vacancy
from db.repositories.match_repo import get_match, upsert_match
from services.match_service import profile_to_json, vacancy_to_json


def generate_cover_letter(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    *,
    save: bool = True,
) -> str:
    router = AIRouter(session)
    payload = {
        "profile_id": profile.id,
        "vacancy_id": vacancy.id,
        "profile_json": profile_to_json(profile),
        "vacancy_json": vacancy_to_json(session, vacancy),
    }
    result = router.route("generate_cover_letter", payload, parse_json=False, use_cache=True)
    letter = (result.content or "").strip()
    if not letter:
        raise AIRouterError("Пустой ответ от AI")
    if save:
        existing = get_match(session, vacancy.id, profile.id, "deep")
        if existing:
            existing.cover_letter_draft = letter
            session.commit()
        else:
            upsert_match(
                session,
                vacancy.id,
                profile.id,
                "deep",
                {"match_score": 0, "match_summary": "", "recommendation": "consider", "deep_analysis": ""},
            )
            row = get_match(session, vacancy.id, profile.id, "deep")
            if row:
                row.cover_letter_draft = letter
                session.commit()
    return letter
