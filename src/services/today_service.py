"""Daily briefing — «What should I do today to get hired?»"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Vacancy, VacancyMatch
from db.repositories.scan_repo import get_last_scan_run
from services.dashboard_service import get_metrics
from services.profile_filter_service import vacancy_profile_scope
from services.vacancy_service import VacancyFilters, list_vacancies


def _scope(profile_id: int | None) -> list:
    cond = [Vacancy.is_active.is_(True), Vacancy.user_status != "hidden"]
    scope = vacancy_profile_scope(profile_id)
    if scope is not None:
        cond.append(scope)
    return cond


def _greeting_name(full_name: str | None) -> str:
    if not full_name:
        return "друг"
    return full_name.strip().split()[0]


def _count_excellent_matches(session: Session, profile_id: int) -> int:
    fit = VacancyMatch.__table__.alias("fit_today")
    legacy = VacancyMatch.__table__.alias("legacy_today")
    cond = _scope(profile_id)
    score_expr = func.coalesce(fit.c.match_score, legacy.c.match_score)
    q = (
        select(func.count())
        .select_from(Vacancy)
        .outerjoin(
            fit,
            (fit.c.vacancy_id == Vacancy.id)
            & (fit.c.profile_id == profile_id)
            & (fit.c.match_level == "fit"),
        )
        .outerjoin(
            legacy,
            (legacy.c.vacancy_id == Vacancy.id)
            & (legacy.c.profile_id == profile_id)
            & (legacy.c.match_level.in_(("deep", "fast"))),
        )
        .where(*cond, score_expr >= 72)
    )
    return int(session.execute(q).scalar_one())


def _top_opportunity(session: Session, profile_id: int) -> dict | None:
    items, _ = list_vacancies(
        session,
        profile_id,
        VacancyFilters(min_match_score=70, page=1, per_page=1),
    )
    if not items:
        return None
    top = items[0]
    if top.status == "applied":
        items2, _ = list_vacancies(
            session,
            profile_id,
            VacancyFilters(min_match_score=60, page=1, per_page=5),
        )
        for item in items2:
            if item.status not in ("applied", "hidden"):
                top = item
                break
        else:
            return None
    return {
        "id": top.id,
        "title": top.title,
        "company": top.company,
        "match_score": top.match_score,
        "recommendation": top.recommendation,
    }


def _application_counts(session: Session, profile_id: int | None) -> dict[str, int]:
    cond = _scope(profile_id)
    rows = session.execute(
        select(Vacancy.user_status, func.count()).where(*cond).group_by(Vacancy.user_status)
    ).all()
    return {row[0] or "new": int(row[1]) for row in rows}


def build_today_briefing(
    session: Session,
    profile_id: int | None,
    *,
    full_name: str | None = None,
) -> dict:
    metrics = get_metrics(session, profile_id)
    last_scan = get_last_scan_run(session)
    new_since_scan = int(last_scan.new_added or 0) if last_scan else metrics.get("new_7d", 0)

    excellent = _count_excellent_matches(session, profile_id) if profile_id else 0
    top = _top_opportunity(session, profile_id) if profile_id else None
    apps = _application_counts(session, profile_id)

    applied = apps.get("applied", 0)
    favorites = apps.get("favorite", 0)
    pipeline = applied + favorites

    insights: list[dict[str, str]] = []

    if new_since_scan:
        insights.append({
            "text": f"{new_since_scan} новых возможностей с последнего сканирования рынка",
            "action": "opportunities",
        })
    if excellent:
        insights.append({
            "text": f"{excellent} отличных совпадений (match ≥ 90%) — стоит откликнуться сегодня",
            "action": "opportunities",
        })
    if top and top.get("match_score"):
        insights.append({
            "text": f"Лучший кандидат на отклик: {top['title'][:60]} ({top['match_score']}%)",
            "action": "detail",
            "vacancy_id": str(top["id"]),
        })
    avg = metrics.get("avg_match_score")
    if avg is not None:
        insights.append({
            "text": f"Средний match по рынку — {avg}%. Усильте резюме, чтобы поднять до 85%+",
            "action": "resume",
        })
    if metrics.get("median_salary"):
        sal = f"{metrics['median_salary']:,}".replace(",", " ")
        insights.append({
            "text": f"Медианная зарплата в выборке — {sal} ₽",
            "action": "insights",
        })
    if applied and applied >= 3:
        insights.append({
            "text": f"{applied} откликов в работе — проверьте статусы и follow-up",
            "action": "applications",
        })
    if not insights:
        insights.append({
            "text": "Запустите сканирование рынка, чтобы получить персональные рекомендации",
            "action": "scan",
        })

    return {
        "greeting_name": _greeting_name(full_name),
        "new_opportunities": new_since_scan,
        "excellent_matches": excellent,
        "top_opportunity": top,
        "avg_match": avg,
        "median_salary": metrics.get("median_salary"),
        "total_opportunities": metrics.get("total", 0),
        "applications_applied": applied,
        "applications_favorites": favorites,
        "pipeline_count": pipeline,
        "insights": insights[:6],
    }
