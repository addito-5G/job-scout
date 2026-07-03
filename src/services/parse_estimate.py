"""Оценка длительности парсинга."""

from __future__ import annotations

from config_loader import load_sources


def estimate_parse_seconds() -> int:
    raw = load_sources()
    browser = raw.get("browser", {})
    delay = float(browser.get("delay_seconds", 2))
    sources_cfg = raw.get("sources", {})
    total = 45.0

    for cfg in sources_cfg.values():
        if not cfg.get("enabled", True):
            continue
        pages = int(cfg.get("pages_per_query", 1))
        queries = cfg.get("queries") or []
        q_count = max(len(queries), 1)
        total += pages * q_count * (delay + 10)

    if browser.get("use_for_scan"):
        total += 480

    return int(max(total, 120))
