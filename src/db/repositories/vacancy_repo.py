from __future__ import annotations

import json
import logging
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

logger = logging.getLogger(__name__)


def _json_dump(data) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def upsert_vacancy(
    session: Session,
    v: VacancyDTO,
    *,
    profile_id: int,
    search_settings_id: int | None = None,
    profile_role: str | None = None,
) -> tuple[int, str]:
    """Вернуть (vacancy_id, outcome): new | skipped | meta_updated."""
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
        select(Vacancy).where(
            Vacancy.profile_id == profile_id,
            Vacancy.source == source,
            Vacancy.external_id == external_id,
        )
    ).scalar_one_or_none()

    incoming_active = getattr(v, "is_active", True)
    if v.user_status == "archived":
        incoming_active = False

    if existing:
        meta_changed = False
        if v.salary_min is not None and existing.salary_from != v.salary_min:
            existing.salary_from = v.salary_min
            meta_changed = True
        if v.salary_max is not None and existing.salary_to != v.salary_max:
            existing.salary_to = v.salary_max
            meta_changed = True
        if v.salary and existing.salary_text != v.salary:
            existing.salary_text = v.salary
            meta_changed = True
        if existing.is_active != incoming_active:
            existing.is_active = incoming_active
            existing.status = "active" if incoming_active else "inactive"
            meta_changed = True
        if meta_changed:
            existing.updated_at = utc_now()
            session.commit()
            return existing.id, "meta_updated"
        return existing.id, "skipped"

    fields = {
        "profile_id": profile_id,
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
        "is_active": incoming_active,
        "published_at": published,
        "enriched_at": enriched or (utc_now() if desc_full else None),
        "updated_at": utc_now(),
    }
    if search_settings_id is not None:
        fields["search_settings_id"] = search_settings_id
    if profile_role is not None:
        fields["profile_role"] = profile_role

    row = Vacancy(source=source, external_id=external_id, scraped_at=utc_now(), **fields)
    session.add(row)

    try:
        session.flush()
        sync_vacancy_skills(session, row.id, v.skills)
        sync_vacancy_tags(session, row.id, tags)
        session.commit()
        session.refresh(row)
        return row.id, "new"
    except IntegrityError:
        session.rollback()
        existing = _find_existing_vacancy(
            session,
            profile_id=profile_id,
            source=source,
            external_id=external_id,
            external_url=external_url,
        )
        if existing:
            return existing.id, "skipped"
        # Should be rare after schema migration; never surface raw IntegrityError to UI.
        logger.warning(
            "vacancy upsert conflict unresolved profile=%s source=%s id=%s url=%s",
            profile_id,
            source,
            external_id,
            external_url,
        )
        return 0, "skipped"


def _find_existing_vacancy(
    session: Session,
    *,
    profile_id: int,
    source: str,
    external_id: str,
    external_url: str,
) -> Vacancy | None:
    existing = session.execute(
        select(Vacancy).where(
            Vacancy.profile_id == profile_id,
            Vacancy.source == source,
            Vacancy.external_id == external_id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    existing = session.execute(
        select(Vacancy).where(
            Vacancy.profile_id == profile_id,
            Vacancy.external_url == external_url,
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    # Legacy global unique(source, external_id) / unique(url) rows without matching profile lookup.
    existing = session.execute(
        select(Vacancy).where(
            Vacancy.source == source,
            Vacancy.external_id == external_id,
        )
    ).scalar_one_or_none()
    if existing and existing.profile_id == profile_id:
        return existing
    existing = session.execute(
        select(Vacancy).where(Vacancy.external_url == external_url)
    ).scalar_one_or_none()
    if existing and existing.profile_id == profile_id:
        return existing
    return None


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


def count_new_vacancies(session: Session, days: int, *, profile_id: int | None = None) -> int:
    """Вакансии, опубликованные или собранные за последние N дней."""
    since = utc_now() - timedelta(days=days)
    query = (
        select(func.count())
        .select_from(Vacancy)
        .where(or_(Vacancy.published_at >= since, Vacancy.scraped_at >= since))
    )
    if profile_id is not None:
        query = query.where(Vacancy.profile_id == profile_id)
    return session.execute(query).scalar_one()


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


def list_for_enrichment(session: Session, limit: int = 50) -> list[Vacancy]:
    return list(
        session.execute(
            select(Vacancy)
            .where(
                or_(Vacancy.description_full.is_(None), Vacancy.description_full == ""),
                Vacancy.is_active.is_(True),
            )
            .order_by(Vacancy.published_at.desc().nullslast(), Vacancy.updated_at.desc())
            .limit(limit)
        ).scalars()
    )


def list_for_matching(
    session: Session,
    profile_id: int,
    *,
    match_level: str = "fit",
    limit: int = 50,
    priority_vacancy_ids: list[int] | None = None,
) -> list[Vacancy]:
    matched_ids = select(VacancyMatch.vacancy_id).where(
        VacancyMatch.profile_id == profile_id,
        VacancyMatch.match_level == match_level,
    )
    base_filters = (
        Vacancy.profile_id == profile_id,
        Vacancy.is_active.is_(True),
        Vacancy.user_status != "hidden",
        not_(Vacancy.id.in_(matched_ids)),
    )

    vacancies: list[Vacancy] = []
    seen: set[int] = set()

    if priority_vacancy_ids:
        priority_rows = list(
            session.execute(
                select(Vacancy).where(
                    Vacancy.id.in_(priority_vacancy_ids),
                    *base_filters,
                )
            ).scalars()
        )
        by_id = {row.id: row for row in priority_rows}
        for vacancy_id in priority_vacancy_ids:
            row = by_id.get(vacancy_id)
            if row is None or row.id in seen:
                continue
            vacancies.append(row)
            seen.add(row.id)
            if len(vacancies) >= limit:
                return vacancies

    remaining = limit - len(vacancies)
    if remaining <= 0:
        return vacancies

    extra_query = (
        select(Vacancy)
        .where(*base_filters)
        .order_by(Vacancy.published_at.desc().nullslast(), Vacancy.updated_at.desc())
        .limit(remaining)
    )
    if seen:
        extra_query = extra_query.where(not_(Vacancy.id.in_(seen)))

    vacancies.extend(session.execute(extra_query).scalars())
    return vacancies


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
    upsert_vacancy(session, dto, profile_id=row.profile_id)
    return get_vacancy_by_id(session, vacancy.id) or vacancy
