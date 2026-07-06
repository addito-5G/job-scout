"""Запись вакансий: upsert, статус, cover letter."""

from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import SearchSettings
from db.repositories.vacancy_repo import get_vacancy_by_id, upsert_vacancy
from models import Vacancy as VacancyDTO
from services.company_brief_service import ensure_company_brief
from services.profile_filter_service import infer_role_from_settings
from time_utils import utc_now


def upsert_scored_vacancy(
    session: Session,
    vacancy: VacancyDTO,
    *,
    profile_id: int,
    search_settings_id: int | None = None,
) -> tuple[int, str]:
    profile_role: str | None = None
    if search_settings_id is not None:
        settings = session.get(SearchSettings, search_settings_id)
        if settings:
            profile_role = infer_role_from_settings(settings)

    vacancy_id, outcome = upsert_vacancy(
        session,
        vacancy,
        profile_id=profile_id,
        search_settings_id=search_settings_id,
        profile_role=profile_role,
    )

    if outcome == "new":
        row = get_vacancy_by_id(session, vacancy_id)
        if row and row.company_rel:
            snippet = row.description_full or row.description_short or vacancy.description or ""
            ensure_company_brief(
                session,
                row.company_rel,
                vacancy_snippet=snippet,
                source=row.source,
            )

    return vacancy_id, outcome


def update_vacancy_status(session: Session, vacancy_id: int, status: str) -> bool:
    v = get_vacancy_by_id(session, vacancy_id)
    if not v:
        return False
    v.user_status = status
    v.updated_at = utc_now()
    session.commit()
    return True


def save_vacancy_cover_letter(session: Session, vacancy_id: int, letter: str) -> bool:
    v = get_vacancy_by_id(session, vacancy_id)
    if not v:
        return False
    if v.matches:
        for m in v.matches:
            if m.match_level in ("fit", "deep", "fast"):
                m.cover_letter_draft = letter
    session.commit()
    return True
