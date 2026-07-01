from __future__ import annotations

import hashlib
import json
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db.models import Company, Location, Skill, VacancySkill, VacancyTag
from db.normalize import normalize_work_format


def _slug_id(source: str, name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (name or "unknown").lower()).strip("-") or "unknown"
    return hashlib.md5(f"{source}:{base}".encode()).hexdigest()[:16]


def normalize_title(title: str) -> str:
    t = (title or "").strip()
    t = re.sub(r"\s+", " ", t)
    return t


def normalize_skill_name(name: str) -> str:
    return (name or "").strip()


def upsert_company(
    session: Session,
    *,
    source: str,
    name: str,
    external_id: str | None = None,
    logo_url: str | None = None,
) -> Company | None:
    if not name:
        return None
    ext = external_id or _slug_id(source, name)
    row = session.execute(
        select(Company).where(Company.source == source, Company.external_id == ext)
    ).scalar_one_or_none()
    if row:
        row.name = name
        if logo_url:
            row.logo_url = logo_url
        return row
    row = Company(source=source, external_id=ext, name=name, logo_url=logo_url)
    session.add(row)
    session.flush()
    return row


def upsert_location(
    session: Session,
    *,
    source: str,
    name: str,
    external_id: str | None = None,
) -> Location | None:
    if not name:
        return None
    ext = external_id
    if ext:
        row = session.execute(
            select(Location).where(Location.source == source, Location.external_id == ext)
        ).scalar_one_or_none()
    else:
        row = session.execute(
            select(Location).where(Location.name == name, Location.source == source)
        ).scalar_one_or_none()
    if row:
        row.name = name
        if not row.city:
            row.city = name.split(",")[0].strip()
        return row
    city = name.split(",")[0].strip()
    row = Location(source=source, external_id=ext, name=name, city=city, name_full=name)
    session.add(row)
    session.flush()
    return row


def upsert_skill(session: Session, name: str) -> Skill | None:
    clean = normalize_skill_name(name)
    if not clean:
        return None
    norm = clean.lower()
    row = session.execute(select(Skill).where(Skill.name == clean)).scalar_one_or_none()
    if not row:
        row = session.execute(select(Skill).where(Skill.name_normalized == norm)).scalar_one_or_none()
    if row:
        row.popularity = (row.popularity or 0) + 1
        return row
    row = Skill(name=clean, name_normalized=norm)
    session.add(row)
    session.flush()
    return row


def sync_vacancy_skills(session: Session, vacancy_id: int, skills: list[str]) -> None:
    session.execute(delete(VacancySkill).where(VacancySkill.vacancy_id == vacancy_id))
    for skill_name in skills:
        skill = upsert_skill(session, skill_name)
        if skill:
            session.add(VacancySkill(vacancy_id=vacancy_id, skill_id=skill.id))


def sync_vacancy_tags(session: Session, vacancy_id: int, tags: list[tuple[str, str]]) -> None:
    session.execute(delete(VacancyTag).where(VacancyTag.vacancy_id == vacancy_id))
    seen: set[tuple[str, str]] = set()
    for tag, tag_type in tags:
        key = (tag.strip(), tag_type or "other")
        if not key[0] or key in seen:
            continue
        seen.add(key)
        session.add(VacancyTag(vacancy_id=vacancy_id, tag=key[0], tag_type=key[1]))


def extract_tags_from_text(text: str) -> list[tuple[str, str]]:
    text_l = (text or "").lower()
    mapping = {
        "b2b": "industry",
        "saas": "product_type",
        "fintech": "industry",
        "e-commerce": "industry",
        "ecommerce": "industry",
        "маркетплейс": "industry",
        "marketplace": "industry",
        "remote": "work_format",
        "удалённо": "work_format",
        "hybrid": "work_format",
    }
    found = []
    for kw, ttype in mapping.items():
        if kw in text_l:
            found.append((kw.upper() if len(kw) <= 4 else kw.title(), ttype))
    return found


def map_work_format(schedule: str, location: str, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    return normalize_work_format(schedule, location)
