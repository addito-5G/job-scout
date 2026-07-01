from __future__ import annotations

import re
from datetime import datetime

SOURCE_ALIASES = {
    "hh_parser": "hh",
    "hh_api": "hh",
    "habr_rss": "habr",
    "habr_parser": "habr",
    "geekjob_parser": "geekjob",
}


EXPERIENCE_ALIASES: dict[str, str] = {
    "noexperience": "Без опыта",
    "no_experience": "Без опыта",
    "lessthan1": "Менее 1 года",
    "less_than_1": "Менее 1 года",
    "between1and3": "От 1 до 3 лет",
    "between1and3years": "От 1 до 3 лет",
    "between3and6": "От 3 до 6 лет",
    "between3and6years": "От 3 до 6 лет",
    "morethan6": "Более 6 лет",
    "more_than_6": "Более 6 лет",
}

WORK_FORMAT_LABELS: dict[str, str] = {
    "remote": "Удалённо",
    "office": "Офис",
    "hybrid": "Гибрид",
}


def normalize_source(source: str) -> str:
    return SOURCE_ALIASES.get(source, source)


def normalize_experience(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    mapped = EXPERIENCE_ALIASES.get(text.lower().replace("-", "").replace("_", ""))
    if mapped:
        return mapped
    mapped = EXPERIENCE_ALIASES.get(text.lower())
    return mapped or text


def experience_label(value: str | None) -> str:
    return normalize_experience(value) or "не указан"


def work_format_label(value: str | None) -> str:
    if not value:
        return "не указан"
    return WORK_FORMAT_LABELS.get(value, value)


def normalize_work_format(work_schedule: str | None, location: str | None = None) -> str | None:
    text = " ".join(filter(None, [work_schedule or "", location or ""])).lower()
    if not text:
        return None
    if any(k in text for k in ("remote", "удал", "удалён", "удален")):
        return "remote"
    if any(k in text for k in ("hybrid", "гибрид")):
        return "hybrid"
    if any(k in text for k in ("office", "офис", "on_site", "onsite")):
        return "office"
    return None


def parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00").split("+")[0])
    except ValueError:
        return None


def extract_external_id_from_url(url: str, source: str) -> str | None:
    if source in ("hh", "hh_parser"):
        m = re.search(r"/vacancy/(\d+)", url)
        return m.group(1) if m else None
    return None
