"""Разбор HH-Lux-InitialState из HTML страниц hh.ru."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

logger = logging.getLogger(__name__)

_STATE_MARKER = 'id="HH-Lux-InitialState"'


def extract_state(html: str) -> dict | None:
    """Parse embedded HH Lux state. Returns None if missing or invalid JSON."""
    start = html.find(_STATE_MARKER)
    if start < 0:
        return None
    gt = html.find(">", start)
    if gt < 0:
        return None
    end = html.find("</template>", gt)
    if end < 0:
        match = re.search(
            r'id="HH-Lux-InitialState"[^>]*>(\{.*?\})</template>',
            html[start:],
            re.DOTALL,
        )
        if not match:
            return None
        raw = match.group(1)
    else:
        raw = html[gt + 1 : end].strip()
    if not raw.startswith("{"):
        return None
    try:
        data = json.loads(unescape(raw))
    except json.JSONDecodeError as exc:
        logger.warning("HH-Lux-InitialState JSON broken: %s", exc)
        return None
    return data if isinstance(data, dict) else None


def find_vacancy_list(obj: Any) -> list[dict] | None:
    if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
        if obj[0].get("vacancyId") and obj[0].get("name"):
            return obj
    if isinstance(obj, dict):
        for value in obj.values():
            found = find_vacancy_list(value)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_vacancy_list(value)
            if found:
                return found
    return None


def find_vacancy_view(obj: Any) -> dict | None:
    if isinstance(obj, dict):
        if "vacancyView" in obj and isinstance(obj["vacancyView"], dict):
            return obj["vacancyView"]
        for value in obj.values():
            found = find_vacancy_view(value)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_vacancy_view(value)
            if found:
                return found
    return None


def parse_published(raw: Any) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, dict):
        if raw.get("$"):
            try:
                return datetime.fromisoformat(raw["$"].replace("Z", "+00:00"))
            except ValueError:
                pass
        if raw.get("@timestamp"):
            try:
                return datetime.fromtimestamp(int(raw["@timestamp"]), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                pass
    return None


def format_salary(compensation: dict | None) -> str:
    if not compensation:
        return ""
    if compensation.get("noCompensation"):
        return "не указана"
    parts = []
    if compensation.get("from"):
        parts.append(f"от {compensation['from']:,}".replace(",", " "))
    if compensation.get("to"):
        parts.append(f"до {compensation['to']:,}".replace(",", " "))
    currency = compensation.get("currencyCode", "RUR")
    gross = "gross" if compensation.get("gross") else "net"
    if parts:
        return f"{' '.join(parts)} {currency} ({gross})"
    return ""


def parse_compensation(compensation: dict | None) -> tuple[int | None, int | None, str, bool | None]:
    if not compensation or compensation.get("noCompensation"):
        return None, None, "", None
    salary_from = compensation.get("from")
    salary_to = compensation.get("to")
    currency = compensation.get("currencyCode", "RUR") or "RUR"
    gross = compensation.get("gross")
    return (
        int(salary_from) if salary_from is not None else None,
        int(salary_to) if salary_to is not None else None,
        currency,
        bool(gross) if gross is not None else None,
    )


def _strip_html(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_skills(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        skills: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                name = item.get("name") or item.get("title")
                if name:
                    skills.append(unescape(str(name)).strip())
            elif item:
                skills.append(unescape(str(item)).strip())
        return skills
    return []


def _label_from_dict(data: dict) -> str:
    for key in ("name", "title", "text", "label"):
        val = data.get(key)
        if val:
            return unescape(str(val)).strip()
    for key in ("id", "@type"):
        val = data.get(key)
        if val:
            return str(val).strip()
    return ""


def _join_labels(raw: Any) -> str:
    if not raw:
        return ""
    if isinstance(raw, str):
        return unescape(raw).strip()
    if isinstance(raw, list):
        parts = [_label_from_dict(x) if isinstance(x, dict) else _join_labels(x) for x in raw]
        return ", ".join(p for p in parts if p)
    if isinstance(raw, dict):
        return _label_from_dict(raw)
    return str(raw).strip()


def parse_vacancy_detail(state: dict) -> dict[str, Any]:
    """Полные данные со страницы вакансии."""
    vv = find_vacancy_view(state)
    if not vv:
        return {}

    compensation = vv.get("compensation")
    salary_min, salary_max, currency, gross = parse_compensation(compensation)
    skills = _parse_skills(vv.get("keySkills") or vv.get("confirmableKeySkills"))

    description_html = vv.get("description") or ""
    description_text = _strip_html(description_html)

    area = unescape((vv.get("area") or {}).get("name") or "")
    company = unescape((vv.get("company") or {}).get("name") or "")

    return {
        "title": unescape(vv.get("name") or "").strip(),
        "company": company,
        "location": area,
        "salary": format_salary(compensation),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": currency,
        "salary_gross": gross,
        "skills": skills,
        "employment": _join_labels(vv.get("employmentForm") or vv.get("employment")),
        "work_schedule": _join_labels(
            vv.get("workFormats") or vv.get("workScheduleByDays") or vv.get("workingHours")
        ),
        "experience": _join_labels(vv.get("workExperience")),
        "full_description": description_text,
        "published_at": parse_published(vv.get("publicationDate")),
    }


def parse_search_item(item: dict) -> dict[str, Any]:
    """Краткие данные из выдачи поиска."""
    compensation = item.get("compensation")
    salary_min, salary_max, currency, gross = parse_compensation(compensation)
    skills = _parse_skills(item.get("keySkills"))

    return {
        "external_id": str(item["vacancyId"]),
        "title": unescape(item.get("name", "").strip()),
        "company": unescape((item.get("company") or {}).get("name") or ""),
        "location": unescape((item.get("area") or {}).get("name") or ""),
        "salary": format_salary(compensation),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": currency,
        "salary_gross": gross,
        "skills": skills,
        "employment": _join_labels(item.get("employment")),
        "work_schedule": _join_labels(item.get("workSchedule") or item.get("workFormats")),
        "experience": _join_labels(item.get("workExperience")),
        "published_at": parse_published(item.get("publicationTime")),
        "url": f"https://hh.ru/vacancy/{item['vacancyId']}",
    }
