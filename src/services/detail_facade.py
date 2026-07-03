"""Application facade для страницы детали вакансии (UI → services, без прямого ORM)."""

from __future__ import annotations

from db.models import CandidateProfile, Vacancy
from db.repositories.vacancy_repo import get_vacancy_by_id
from services.cover_letter_service import generate_cover_letter, normalize_cover_letter
from services.match_service import deep_match_vacancy, fast_match_vacancy
from services.profile_service import get_latest_profile
from services.vacancy_service import MatchSelection, VacancyDetail, get_vacancy_detail
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
    return get_latest_profile(session)


def load_vacancy(session: Session, vacancy_id: int) -> Vacancy | None:
    return get_vacancy_by_id(session, vacancy_id)


def best_match(detail: VacancyDetail) -> MatchSelection:
    return MatchSelection.pick(detail.fast_match, detail.deep_match)


def run_fast_match(session: Session, profile: CandidateProfile, vacancy: Vacancy) -> dict:
    return fast_match_vacancy(session, profile, vacancy)


def run_deep_match(session: Session, profile: CandidateProfile, vacancy: Vacancy) -> dict:
    return deep_match_vacancy(session, profile, vacancy)


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
