"""Application facade для страницы детали вакансии (UI → services, без прямого ORM)."""

from __future__ import annotations

from db.models import CandidateProfile, Vacancy
from db.repositories.vacancy_repo import get_vacancy_by_id
from services.cover_letter_service import generate_cover_letter, normalize_cover_letter
from services.linkedin_outreach_service import generate_linkedin_outreach, linkedin_people_search_url
from services.match_service import compute_fit_match
from services.vacancy_fit_advice_service import generate_vacancy_fit_advice
from services.vacancy_service import VacancyDetail, get_vacancy_detail
from sqlalchemy.orm import Session


def load_detail(
    session: Session,
    vacancy_id: int,
    profile_id: int | None,
) -> VacancyDetail | None:
    return get_vacancy_detail(session, vacancy_id, profile_id)


def load_profile(session: Session, profile_id: int | None) -> CandidateProfile | None:
    if not profile_id:
        return None
    return session.get(CandidateProfile, profile_id)


def load_vacancy(session: Session, vacancy_id: int) -> Vacancy | None:
    return get_vacancy_by_id(session, vacancy_id)


def best_match(detail: VacancyDetail) -> dict | None:
    return detail.fit_match


def refresh_fit_match(session: Session, profile: CandidateProfile, vacancy: Vacancy) -> dict:
    return compute_fit_match(session, profile, vacancy)


def generate_fit_advice(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    *,
    use_cache: bool = False,
) -> dict:
    return generate_vacancy_fit_advice(session, profile, vacancy, use_cache=use_cache)


def generate_letter(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    *,
    use_cache: bool = False,
) -> str:
    return generate_cover_letter(session, profile, vacancy, use_cache=use_cache)


def normalize_letter(letter: str, profile: CandidateProfile) -> str:
    return normalize_cover_letter(letter, profile)


def generate_outreach(
    session: Session,
    profile: CandidateProfile,
    vacancy: Vacancy,
    *,
    contact_role: str = "recruiter",
    use_cache: bool = False,
) -> str:
    return generate_linkedin_outreach(
        session,
        profile,
        vacancy,
        contact_role=contact_role,
        use_cache=use_cache,
    )


def people_search_url(vacancy: Vacancy, *, contact_role: str = "recruiter") -> str:
    company = vacancy.company_rel.name if vacancy.company_rel else ""
    return linkedin_people_search_url(
        company=company,
        vacancy_title=vacancy.title,
        contact_role=contact_role,
    )
