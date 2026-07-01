from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from urllib.parse import urlencode


SEARCH_URL = "https://geekjob.ru/vacancies"


def _strip_html(text: str) -> str:
    text = unescape(text or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.split("T")[0])
    except ValueError:
        return None


def parse_search_page(html: str) -> list[dict]:
    titles_by_slug: dict[str, str] = {}
    for slug, title in re.findall(
        r'href="/vacancy/([a-f0-9]{24})"[^>]*class="title"[^>]*>([^<]+)</a>',
        html,
    ):
        titles_by_slug.setdefault(slug, unescape(title).strip())

    links = re.findall(r'href="(/vacancy/[a-f0-9]{24})"', html)
    seen: set[str] = set()
    results = []
    for href in links:
        slug = href.split("/")[-1]
        if slug in seen:
            continue
        seen.add(slug)
        results.append({
            "external_id": slug,
            "url": f"https://geekjob.ru{href}",
            "title": titles_by_slug.get(slug, ""),
        })
    return results


def parse_vacancy_page(html: str, url: str = "") -> dict | None:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    if data.get("@type") != "JobPosting":
        return None

    org = data.get("hiringOrganization") or {}
    identifier = (data.get("identifier") or {}).get("value") or ""
    ext_id = url.rstrip("/").split("/")[-1] if url else identifier

    salary = data.get("baseSalary") or {}
    value = salary.get("value") or {}
    salary_min = value.get("minValue") or value.get("value")
    salary_max = value.get("maxValue")
    currency = (salary.get("currency") or value.get("unitText") or "RUR")

    employment = data.get("employmentType") or ""
    work_format = None
    desc_text = _strip_html(data.get("description") or "").lower()
    if "удал" in desc_text or "remote" in desc_text:
        work_format = "remote"

    job_location = data.get("jobLocation") or {}
    if isinstance(job_location, list):
        job_location = job_location[0] if job_location else {}
    address = job_location.get("address") or {}
    location = address.get("addressLocality") or address.get("addressRegion") or ""

    skills_raw = data.get("skills")
    skills: list[str] = []
    if isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    elif isinstance(skills_raw, list):
        skills = [str(s) for s in skills_raw]

    salary_parts = []
    if salary_min:
        salary_parts.append(f"от {int(salary_min):,}".replace(",", " "))
    if salary_max:
        salary_parts.append(f"до {int(salary_max):,}".replace(",", " "))
    salary_text = f"{' '.join(salary_parts)} {currency}".strip() if salary_parts else ""

    return {
        "external_id": ext_id,
        "title": data.get("title") or "",
        "company": org.get("name") or "",
        "url": url or data.get("url") or "",
        "salary": salary_text,
        "salary_min": int(salary_min) if salary_min else None,
        "salary_max": int(salary_max) if salary_max else None,
        "salary_currency": str(currency),
        "location": location,
        "work_format": work_format,
        "employment": employment,
        "skills": skills,
        "full_description": _strip_html(data.get("description") or ""),
        "published_at": _parse_date(data.get("datePosted")),
    }


def build_search_url(query: str, page: int = 1) -> str:
    params = {"q": query}
    if page > 1:
        params["page"] = page
    return f"{SEARCH_URL}?{urlencode(params)}"
