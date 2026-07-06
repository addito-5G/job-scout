"""Парсинг публичных вакансий LinkedIn (без авторизации)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from urllib.parse import urlencode

GUEST_SEARCH_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOBS_PER_PAGE = 25

JOB_ID_RE = re.compile(r"urn:li:jobPosting:(\d+)")
LINKEDIN_JOB_URL_RE = re.compile(
    r"linkedin\.com/jobs/view/(?:[^/?#]+-)?(\d+)",
    re.IGNORECASE,
)


def is_linkedin_job_url(url: str) -> bool:
    return bool(url and LINKEDIN_JOB_URL_RE.search(url))


def extract_job_id(url: str) -> str | None:
    match = LINKEDIN_JOB_URL_RE.search(url or "")
    return match.group(1) if match else None


def build_search_url(
    *,
    keywords: str,
    location: str = "Russia",
    start: int = 0,
    f_TPR: str = "r604800",
    sort_by: str = "DD",
    remote_only: bool = False,
) -> str:
    params: dict[str, str | int] = {
        "keywords": keywords,
        "location": location,
        "start": start,
        "f_TPR": f_TPR,
        "sortBy": sort_by,
    }
    if remote_only:
        params["f_WT"] = 2
    return f"{GUEST_SEARCH_API}?{urlencode(params)}"


def canonical_job_url(job_id: str) -> str:
    return f"https://www.linkedin.com/jobs/view/{job_id}/"


def _strip_html(text: str) -> str:
    text = unescape(text or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _parse_iso_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _work_format_from_jsonld(data: dict) -> str | None:
    loc_type = (data.get("jobLocationType") or "").upper()
    if loc_type == "TELECOMMUTE":
        return "remote"
    return None


def _location_from_jsonld(data: dict) -> str:
    locations = data.get("jobLocation")
    if isinstance(locations, list):
        locations = locations[0] if locations else {}
    if not isinstance(locations, dict):
        return ""
    address = locations.get("address") or {}
    if not isinstance(address, dict):
        return _strip_html(str(address))
    parts = [
        address.get("addressLocality"),
        address.get("addressRegion"),
        address.get("addressCountry"),
    ]
    return ", ".join(p for p in parts if p)


def _description_from_jsonld(data: dict, html: str) -> str:
    desc = data.get("description") or ""
    if desc and "<" in desc:
        return _strip_html(desc)
    if desc:
        return desc.strip()
    markup = re.search(
        r'class="[^"]*show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if markup:
        return _strip_html(markup.group(1))
    return ""


def _load_jsonld(html: str) -> dict | None:
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    return item
        elif isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return None


def parse_search_fragment(html: str) -> list[dict]:
    """Карточки из HTML-фрагмента guest API seeMoreJobPostings."""
    if not html or not html.strip():
        return []

    results: list[dict] = []
    seen: set[str] = set()

    for job_id in JOB_ID_RE.findall(html):
        if job_id in seen:
            continue
        seen.add(job_id)

        window = ""
        idx = html.find(f"urn:li:jobPosting:{job_id}")
        if idx >= 0:
            window = html[max(0, idx - 400) : idx + 2500]

        title = ""
        title_match = re.search(
            r'class="[^"]*base-search-card__title[^"]*"[^>]*>\s*([^<]+)',
            window,
            re.IGNORECASE,
        )
        if title_match:
            title = _strip_html(title_match.group(1))

        company = ""
        company_match = re.search(
            r'class="[^"]*hidden-nested-link[^"]*"[^>]*>\s*([^<]+)',
            window,
            re.IGNORECASE,
        )
        if company_match:
            company = _strip_html(company_match.group(1))

        location = ""
        loc_match = re.search(
            r'class="[^"]*job-search-card__location[^"]*"[^>]*>\s*([^<]+)',
            window,
            re.IGNORECASE,
        )
        if loc_match:
            location = _strip_html(loc_match.group(1))

        url = canonical_job_url(job_id)
        href_match = re.search(rf'href="([^"]+/jobs/view/[^"]*{job_id}[^"]*)"', window)
        if href_match:
            href = href_match.group(1)
            url = href if href.startswith("http") else f"https://www.linkedin.com{href}"

        results.append(
            {
                "external_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": url,
            }
        )

    return results


def parse_job_page(html: str, *, job_id: str | None = None) -> dict | None:
    data = _load_jsonld(html)
    if not data:
        return None

    org = data.get("hiringOrganization") or {}
    if isinstance(org, list):
        org = org[0] if org else {}
    company = org.get("name") if isinstance(org, dict) else ""

    identifier = data.get("identifier") or {}
    ext_id = job_id
    if isinstance(identifier, dict):
        ext_id = ext_id or str(identifier.get("value") or "")
    if not ext_id:
        ext_id = extract_job_id(data.get("url") or "") or ""

    title = (data.get("title") or "").strip()
    description = _description_from_jsonld(data, html)
    location = _location_from_jsonld(data)
    work_format = _work_format_from_jsonld(data)
    published_at = _parse_iso_date(data.get("datePosted"))

    employment = ""
    emp_type = data.get("employmentType")
    if isinstance(emp_type, list):
        employment = ", ".join(str(x) for x in emp_type)
    elif emp_type:
        employment = str(emp_type)

    return {
        "external_id": ext_id or "",
        "title": title,
        "company": company,
        "url": canonical_job_url(ext_id) if ext_id else (data.get("url") or ""),
        "description_full": description,
        "location": location,
        "work_format": work_format,
        "employment": employment,
        "published_at": published_at,
        "experience": "",
    }


def vacancy_from_parsed(card: dict, detail: dict | None = None) -> dict:
    """Собрать поля для models.Vacancy."""
    merged = {**card, **(detail or {})}
    desc_short = " | ".join(
        p for p in [merged.get("title"), merged.get("company"), merged.get("location")] if p
    )
    return {
        "source": "linkedin",
        "external_id": merged["external_id"],
        "title": merged.get("title") or "Вакансия LinkedIn",
        "company": merged.get("company") or "",
        "url": merged.get("url") or canonical_job_url(merged["external_id"]),
        "description_short": desc_short,
        "description_full": merged.get("description_full") or "",
        "location": merged.get("location") or "",
        "published_at": merged.get("published_at"),
        "work_format": merged.get("work_format"),
        "employment": merged.get("employment") or "",
        "experience": merged.get("experience") or "",
    }
