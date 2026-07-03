from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy import func, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from db.entities import (
    extract_tags_from_text,
    map_work_format,
    normalize_title,
    sync_vacancy_skills,
    sync_vacancy_tags,
    upsert_company,
    upsert_location,
)
from db.models import Company, Skill, Vacancy, VacancyMatch, VacancySkill, VacancyTag
from db.normalize import normalize_source, normalize_work_format, normalize_experience, parse_datetime
from models import Vacancy as VacancyDTO
from time_utils import utc_now


def _json_dump(data) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def upsert_vacancy(
    session: Session,
    v: VacancyDTO,
    *,
    search_settings_id: int | None = None,
    profile_role: str | None = None,
) -> tuple[int, bool]:
    source = normalize_source(v.source)
    external_id = v.external_id
    external_url = v.url or f"{source}:{external_id}"

    company = upsert_company(
        session,
        source=source,
        name=v.company,
        external_id=v.company_external_id,
        logo_url=v.company_logo_url,
    )
    location = upsert_location(
        session,
        source=source,
        name=v.location,
        external_id=v.location_external_id,
    )

    work_format = map_work_format(v.work_schedule, v.location, v.work_format)
    desc_short = v.description_short or v.description or ""
    desc_full = v.description_full or v.full_description or desc_short
    published = parse_datetime(v.published_at.isoformat() if v.published_at else None)
    enriched = parse_datetime(v.enriched_at.isoformat() if v.enriched_at else None)

    tags = list(v.tags)
    tags.extend(extract_tags_from_text(f"{v.title} {desc_full}"))

    existing = session.execute(
        select(Vacancy).where(Vacancy.source == source, Vacancy.external_id == external_id)
    ).scalar_one_or_none()
    if existing is None and external_url:
        existing = session.execute(
            select(Vacancy).where(Vacancy.external_url == external_url)
        ).scalar_one_or_none()

    fields = {
        "external_url": external_url,
        "title": v.title,
        "title_normalized": normalize_title(v.title),
        "company_id": company.id if company else None,
        "description_short": desc_short or None,
        "description_full": desc_full or None,
        "description_raw": _json_dump(v.description_raw),
        "salary_from": v.salary_min,
        "salary_to": v.salary_max,
        "salary_currency": v.salary_currency or "RUR",
        "salary_gross": bool(v.salary_gross) if v.salary_gross is not None else False,
        "salary_text": v.salary or None,
        "work_format": work_format,
        "work_format_raw": v.work_schedule or None,
        "schedule": v.work_schedule or None,
        "employment": v.employment or None,
        "location_id": location.id if location else None,
        "location_text": v.location or None,
        "experience_required": normalize_experience(v.experience) or None,
        "user_status": v.user_status or "new",
        "status": "active",
        "is_active": True,
        "published_at": published,
        "enriched_at": enriched,
        "rule_score": v.score or 0,
        "rule_score_reasons": "; ".join(v.score_reasons) if v.score_reasons else None,
        "updated_at": utc_now(),
    }
    if search_settings_id is not None:
        fields["search_settings_id"] = search_settings_id
    if profile_role is not None:
        fields["profile_role"] = profile_role

    is_new = existing is None
    if existing:
        if existing.source != source:
            existing.source = source
        if existing.external_id != external_id:
            existing.external_id = external_id
        for key, value in fields.items():
            setattr(existing, key, value)
        if desc_full:
            existing.enriched_at = enriched or utc_now()
        row = existing
    else:
        row = Vacancy(source=source, external_id=external_id, scraped_at=utc_now(), **fields)
        session.add(row)

    try:
        session.flush()
        sync_vacancy_skills(session, row.id, v.skills)
        sync_vacancy_tags(session, row.id, tags)
        session.commit()
        session.refresh(row)
        return row.id, is_new
    except IntegrityError:
        session.rollback()
        by_url = session.execute(
            select(Vacancy).where(Vacancy.external_url == external_url)
        ).scalar_one_or_none()
        if not by_url:
            raise
        for key, value in fields.items():
            setattr(by_url, key, value)
        by_url.source = source
        by_url.external_id = external_id
        if desc_full:
            by_url.enriched_at = enriched or utc_now()
        session.flush()
        sync_vacancy_skills(session, by_url.id, v.skills)
        sync_vacancy_tags(session, by_url.id, tags)
        session.commit()
        session.refresh(by_url)
        return by_url.id, False


def get_vacancy_by_id(session: Session, vacancy_id: int) -> Vacancy | None:
    return session.execute(
        select(Vacancy)
        .options(
            joinedload(Vacancy.company_rel),
            joinedload(Vacancy.location_rel),
            joinedload(Vacancy.vacancy_skills).joinedload(VacancySkill.skill),
            joinedload(Vacancy.tags),
        )
        .where(Vacancy.id == vacancy_id)
    ).unique().scalar_one_or_none()


def count_vacancies(session: Session) -> int:
    return session.execute(select(func.count()).select_from(Vacancy)).scalar_one()


def count_new_vacancies(session: Session, days: int) -> int:
    """Вакансии, опубликованные или собранные за последние N дней."""
    since = utc_now() - timedelta(days=days)
    return session.execute(
        select(func.count())
        .select_from(Vacancy)
        .where(or_(Vacancy.published_at >= since, Vacancy.scraped_at >= since))
    ).scalar_one()


def get_vacancy_skills(session: Session, vacancy_id: int) -> list[str]:
    rows = session.execute(
        select(Skill.name)
        .join(VacancySkill, VacancySkill.skill_id == Skill.id)
        .where(VacancySkill.vacancy_id == vacancy_id)
        .order_by(Skill.name)
    ).all()
    return [r[0] for r in rows]


def get_vacancy_tags(session: Session, vacancy_id: int) -> list[tuple[str, str | None]]:
    rows = session.execute(
        select(VacancyTag.tag, VacancyTag.tag_type).where(VacancyTag.vacancy_id == vacancy_id)
    ).all()
    return [(r[0], r[1]) for r in rows]


def list_for_enrichment(session: Session, limit: int = 50, min_score: int = 0) -> list[Vacancy]:
    return list(
        session.execute(
            select(Vacancy)
            .where(
                or_(Vacancy.description_full.is_(None), Vacancy.description_full == ""),
                Vacancy.rule_score >= min_score,
                Vacancy.is_active.is_(True),
            )
            .order_by(Vacancy.rule_score.desc(), Vacancy.updated_at.desc())
            .limit(limit)
        ).scalars()
    )


def list_for_matching(
    session: Session,
    profile_id: int,
    *,
    match_level: str = "fast",
    limit: int = 50,
    min_score: int = 0,
) -> list[Vacancy]:
    matched_ids = select(VacancyMatch.vacancy_id).where(
        VacancyMatch.profile_id == profile_id,
        VacancyMatch.match_level == match_level,
    )
    return list(
        session.execute(
            select(Vacancy)
            .where(
                Vacancy.rule_score >= min_score,
                Vacancy.is_active.is_(True),
                Vacancy.user_status != "hidden",
                not_(Vacancy.id.in_(matched_ids)),
            )
            .order_by(Vacancy.rule_score.desc(), Vacancy.published_at.desc())
            .limit(limit)
        ).scalars()
    )


def apply_enrichment(session: Session, vacancy: Vacancy, detail: dict) -> Vacancy:
    dto = VacancyDTO(
        source=vacancy.source,
        external_id=vacancy.external_id,
        title=detail.get("title") or vacancy.title,
        company=detail.get("company") or (vacancy.company_rel.name if vacancy.company_rel else ""),
        url=vacancy.external_url,
        description=vacancy.description_short or "",
        description_short=vacancy.description_short or "",
        description_full=detail.get("description_full") or detail.get("full_description") or vacancy.description_full or "",
        skills=detail.get("skills") or [],
        salary=detail.get("salary") or vacancy.salary_text or "",
        location=detail.get("location") or vacancy.location_text or "",
        salary_min=detail.get("salary_min") if detail.get("salary_min") is not None else vacancy.salary_from,
        salary_max=detail.get("salary_max") if detail.get("salary_max") is not None else vacancy.salary_to,
        salary_currency=detail.get("salary_currency") or vacancy.salary_currency,
        employment=detail.get("employment") or vacancy.employment or "",
        work_schedule=detail.get("work_schedule") or vacancy.schedule or "",
        work_format=detail.get("work_format") or vacancy.work_format,
        experience=detail.get("experience") or vacancy.experience_required or "",
        user_status=vacancy.user_status,
        enriched_at=utc_now(),
    )
    upsert_vacancy(session, dto)
    return get_vacancy_by_id(session, vacancy.id) or vacancy
