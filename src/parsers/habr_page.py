from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape

from parsers.json_embed import extract_json_array_items, extract_json_object


def _strip_html(text: str) -> str:
    text = unescape(text or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _parse_habr_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00").split("+")[0])
    except ValueError:
        return None


def parse_search_page(html: str) -> list[dict]:
    items = extract_json_array_items(html)
    results = []
    for item in items:
        vid = item["id"]
        results.append({
            "external_id": vid,
            "title": item.get("title") or "",
            "url": f"https://career.habr.com{item['href']}",
        })
    return results


def parse_vacancy_page(html: str) -> dict | None:
    data = extract_json_object(html, "vacancy")
    if not data:
        return None

    company = data.get("company") or {}
    salary = data.get("salary") or {}
    skills = [s.get("title") for s in (data.get("skills") or []) if s.get("title")]
    locations = [loc.get("title") for loc in (data.get("locations") or []) if loc.get("title")]
    if not locations and data.get("location"):
        locations = [data["location"].get("title", "")]

    salary_from = salary.get("from")
    salary_to = salary.get("to")
    currency = salary.get("currency") or "RUR"
    salary_text = salary.get("formatted") or ""
    if not salary_text and (salary_from or salary_to):
        parts = []
        if salary_from:
            parts.append(f"от {salary_from:,}".replace(",", " "))
        if salary_to:
            parts.append(f"до {salary_to:,}".replace(",", " "))
        salary_text = f"{' '.join(parts)} {currency}".strip()

    remote = bool(data.get("remoteWork"))
    work_format = "remote" if remote else None

    desc_el = re.search(
        r'class="[^"]*vacancy-description[^"]*"[^>]*>(.*?)</div>',
        html,
        re.DOTALL,
    )
    full_description = _strip_html(desc_el.group(1)) if desc_el else ""

    pub = data.get("publishedDate") or {}
    published = _parse_habr_date(pub.get("date"))

    return {
        "external_id": str(data.get("id", "")),
        "title": data.get("title") or "",
        "company": company.get("title") or "",
        "url": f"https://career.habr.com{data.get('href', '')}",
        "salary": salary_text,
        "salary_min": int(salary_from) if salary_from else None,
        "salary_max": int(salary_to) if salary_to else None,
        "salary_currency": currency,
        "location": ", ".join(locations) if locations else "",
        "work_format": work_format,
        "work_schedule": "remote" if remote else "",
        "employment": data.get("employment") or "",
        "experience": (data.get("salaryQualification") or {}).get("title") or "",
        "skills": skills,
        "full_description": full_description,
        "published_at": published,
    }


def parse_vacancy_json_ld(html: str) -> dict | None:
  """Fallback: некоторые страницы содержат JSON-LD."""
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
  return {
      "title": data.get("title") or "",
      "company": org.get("name") or "",
      "full_description": _strip_html(data.get("description") or ""),
      "published_at": _parse_habr_date(data.get("datePosted")),
  }
