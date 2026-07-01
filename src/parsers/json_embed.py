from __future__ import annotations

import json
import re


def extract_json_object(html: str, key: str) -> dict | None:
    marker = f'"{key}":'
    idx = html.find(marker)
    if idx < 0:
        return None
    start = idx + len(marker)
    while start < len(html) and html[start] in " \n\r\t":
        start += 1
    if start >= len(html) or html[start] != "{":
        return None
    depth = 0
    for i in range(start, min(len(html), start + 500_000)):
        ch = html[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def extract_json_array_items(html: str, object_key: str = "id", href_prefix: str = "/vacancies/") -> list[dict]:
    """Извлекает объекты вакансий из встроенного JSON на странице поиска Habr."""
    results: list[dict] = []
    pattern = re.compile(
        rf'\{{"id":(\d+),"href":"({re.escape(href_prefix)}\d+)"(?:,"title":"((?:\\.|[^"\\])*)")?',
        re.DOTALL,
    )
    for m in pattern.finditer(html):
        vid, href, title = m.group(1), m.group(2), m.group(3) or ""
        title = title.encode("utf-8").decode("unicode_escape") if "\\" in title else title
        results.append({"id": vid, "href": href, "title": title})

    seen: set[str] = set()
    unique: list[dict] = []
    for item in results:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique
