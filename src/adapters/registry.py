from __future__ import annotations

from adapters.base import ManualUrlAdapter
from adapters.hh_parser import HhParserAdapter
from browser.fetcher import PageFetcher, create_fetcher


def build_adapters(
    sources_cfg: dict,
    browser_cfg: dict,
    *,
    db_queries: list[dict] | None = None,
    manual_url: str | None = None,
    manual_title: str = "",
    manual_company: str = "",
) -> list:
    adapters = []
    fetcher: PageFetcher | None = None

    if browser_cfg.get("use_for_scan") or browser_cfg.get("engine") == "drission":
        fetcher = create_fetcher(
            engine=browser_cfg.get("engine", "requests"),
            headless=browser_cfg.get("headless", True),
            delay_seconds=float(browser_cfg.get("delay_seconds", 2)),
        )

    if manual_url:
        adapters.append(ManualUrlAdapter(manual_url, manual_title, manual_company))
        return adapters

    hh = sources_cfg.get("hh_parser", {})
    if hh.get("enabled"):
        queries = db_queries or hh.get("queries", [])
        adapters.append(
            HhParserAdapter(
                queries=queries,
                pages_per_query=int(hh.get("pages_per_query", 2)),
                delay_seconds=float(hh.get("delay_seconds", 2)),
                fetcher=fetcher,
            )
        )

    return adapters
