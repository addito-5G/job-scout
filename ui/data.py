"""Кэшированные вызовы сервисов для Streamlit."""

from __future__ import annotations



import streamlit as st

from db import session_scope
from db.repositories.scan_repo import get_last_scan_run
from services.dashboard_service import (
    experience_distribution,
    get_metrics,
    match_score_buckets,
    source_distribution,
    top_companies,
    top_skills,
    vacancy_timeline,
    work_format_distribution,
)
from services.profile_service import get_active_profile
from services.schedule_service import format_dt_msk, load_schedule, next_scan_label
from services.vacancy_service import VacancyFilters, count_vacancies_by_source, list_companies, list_vacancies


@st.cache_data(ttl=30, show_spinner=False)
def cached_last_scan() -> dict | None:
    with session_scope() as session:
        run = get_last_scan_run(session)
        if not run:
            return None
        return {
            "finished_at": format_dt_msk(run.finished_at or run.started_at),
            "total_found": int(run.total_found or 0),
            "new_added": int(run.new_added or 0),
            "status": run.status,
        }


@st.cache_data(ttl=30, show_spinner=False)
def cached_schedule_summary() -> dict:
    schedule = load_schedule()
    return {
        "enabled": bool(schedule.get("enabled", True)),
        "scan_time": str(schedule.get("scan_time", "09:00")),
        "next_run": next_scan_label(),
    }


@st.cache_data(ttl=60, show_spinner=False)
def cached_profile_id() -> int | None:
    """Активный профиль: session_state (сайдбар) приоритетнее БД-кэша."""
    from ui.profile_filter import get_active_resume_profile_id

    session_id = get_active_resume_profile_id()
    if session_id is not None:
        return int(session_id)
    with session_scope() as session:
        profile = get_active_profile(session)
        return profile.id if profile else None


@st.cache_data(ttl=60, show_spinner=False)
def cached_source_counts(profile_id: int | None) -> dict[str, int]:
    with session_scope() as session:
        return count_vacancies_by_source(session, profile_id=profile_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_vacancy_list(
    profile_id: int | None,
    source: str,
    min_match_score: int,
    search: str,
    page: int,
) -> tuple[list[dict], int]:
    return cached_opportunity_list(profile_id, source or None, min_match_score, search, page, status=None)


@st.cache_data(ttl=60, show_spinner=False)
def cached_company_list(
    profile_id: int | None,
    source: str | None,
    min_match_score: int,
    search: str,
    page: int,
    status: str | None = None,
) -> tuple[list[dict], int]:
    with session_scope() as session:
        filters = VacancyFilters(
            source=source,
            min_match_score=min_match_score,
            search=search or None,
            page=page,
            per_page=20,
            user_status=status,
            hide_hidden=status != "hidden",
        )
        items, total = list_companies(session, profile_id, filters)
        return [
            {
                "id": c.id,
                "name": c.name,
                "ai_brief": c.ai_brief,
                "website": c.website,
                "vacancy_count": c.vacancy_count,
                "best_match_score": c.best_match_score,
                "sources": c.sources,
            }
            for c in items
        ], total


@st.cache_data(ttl=60, show_spinner=False)
def cached_company_detail(company_id: int, profile_id: int | None) -> dict | None:
    from services.vacancy_service import get_company_detail

    with session_scope() as session:
        detail = get_company_detail(session, company_id, profile_id, ensure_brief=True)
        if not detail:
            return None
        return {
            "id": detail.id,
            "name": detail.name,
            "ai_brief": detail.ai_brief,
            "website": detail.website,
            "description": detail.description,
            "vacancy_count": detail.vacancy_count,
            "best_match_score": detail.best_match_score,
        }


@st.cache_data(ttl=60, show_spinner=False)
def cached_opportunity_list(
    profile_id: int | None,
    source: str | None,
    min_match_score: int,
    search: str,
    page: int,
    status: str | None = None,
    company_id: int | None = None,
) -> tuple[list[dict], int]:
    with session_scope() as session:
        filters = VacancyFilters(
            source=source,
            min_match_score=min_match_score,
            search=search or None,
            page=page,
            per_page=20,
            user_status=status,
            hide_hidden=status != "hidden",
            company_id=company_id,
        )
        items, total = list_vacancies(session, profile_id, filters)
        return [
            {
                "id": i.id,
                "title": i.title,
                "company": i.company,
                "salary": i.salary,
                "salary_min": i.salary_min,
                "salary_max": i.salary_max,
                "work_format": i.work_format,
                "location": i.location,
                "match_score": i.match_score,
                "recommendation": i.recommendation,
                "status": i.status,
                "url": i.url,
                "score": i.score,
                "tags": i.tags,
                "source": i.source,
            }
            for i in items
        ], total


@st.cache_data(ttl=120, show_spinner=False)
def cached_dashboard_metrics(profile_id: int | None) -> dict:
    with session_scope() as session:
        return get_metrics(session, profile_id)


@st.cache_data(ttl=120, show_spinner=False)
def cached_work_format_chart(profile_id: int | None) -> list[tuple[str, int]]:
    with session_scope() as session:
        return work_format_distribution(session, profile_id=profile_id)


@st.cache_data(ttl=120, show_spinner=False)
def cached_source_chart(profile_id: int | None) -> list[tuple[str, int]]:
    with session_scope() as session:
        return source_distribution(session, profile_id=profile_id)


@st.cache_data(ttl=120, show_spinner=False)
def cached_top_companies(limit: int, profile_id: int | None) -> list[tuple[str, int]]:
    with session_scope() as session:
        return top_companies(session, limit=limit, profile_id=profile_id)


@st.cache_data(ttl=120, show_spinner=False)
def cached_experience_chart(profile_id: int | None) -> list[tuple[str, int]]:
    with session_scope() as session:
        return experience_distribution(session, profile_id=profile_id)


@st.cache_data(ttl=120, show_spinner=False)
def cached_match_buckets(profile_id: int | None) -> dict[str, int]:
    with session_scope() as session:
        return match_score_buckets(session, profile_id)


@st.cache_data(ttl=120, show_spinner=False)
def cached_top_skills(limit: int, profile_id: int | None) -> list[tuple[str, int]]:
    with session_scope() as session:
        return top_skills(session, limit=limit, profile_id=profile_id)


@st.cache_data(ttl=120, show_spinner=False)
def cached_timeline(days: int, profile_id: int | None) -> list[tuple[str, int]]:
    with session_scope() as session:
        return vacancy_timeline(session, days=days, profile_id=profile_id)


def clear_data_cache() -> None:
    st.cache_data.clear()
