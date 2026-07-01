from __future__ import annotations

from adapters.base import HabrRssAdapter, ManualUrlAdapter
from adapters.geekjob_parser import GeekjobParserAdapter
from adapters.habr_parser import HabrParserAdapter
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
            engine=browser_cfg.get("engine", "auto"),
            headless=browser_cfg.get("headless", True),
            delay_seconds=float(browser_cfg.get("delay_seconds", 2)),
        )

    if manual_url:
        adapters.append(ManualUrlAdapter(manual_url, manual_title, manual_company))
        return adapters

    habr_html = sources_cfg.get("habr_parser", {})
    if habr_html.get("enabled"):
        adapters.append(
            HabrParserAdapter(
                queries=habr_html.get("queries"),
                pages_per_query=int(habr_html.get("pages_per_query", 2)),
                delay_seconds=float(habr_html.get("delay_seconds", 2)),
                fetcher=fetcher,
            )
        )
    elif sources_cfg.get("habr_rss", {}).get("enabled"):
        habr = sources_cfg["habr_rss"]
        adapters.append(HabrRssAdapter(habr["url"]))

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

    gj = sources_cfg.get("geekjob_parser", {})
    if gj.get("enabled"):
        adapters.append(
            GeekjobParserAdapter(
                queries=gj.get("queries"),
                pages_per_query=int(gj.get("pages_per_query", 2)),
                delay_seconds=float(gj.get("delay_seconds", 2)),
                fetcher=fetcher,
            )
        )

    return adapters
