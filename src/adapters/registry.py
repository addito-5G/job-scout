from __future__ import annotations

from adapters.base import HabrRssAdapter, ManualUrlAdapter
from adapters.geekjob_parser import GeekjobParserAdapter
from adapters.habr_parser import HabrParserAdapter
from adapters.hh_parser import HhParserAdapter
from adapters.linkedin_parser import LinkedinJobUrlAdapter, LinkedinParserAdapter
from browser.fetcher import PageFetcher, create_fetcher
from parsers.linkedin_jobs import is_linkedin_job_url


def build_adapters(
    sources_cfg: dict,
    browser_cfg: dict,
    *,
    db_queries: list[dict] | None = None,
    linkedin_queries: list[dict] | None = None,
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
        if is_linkedin_job_url(manual_url):
            adapters.append(LinkedinJobUrlAdapter(manual_url, fetcher=fetcher))
        else:
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

    li = sources_cfg.get("linkedin_parser", {})
    if li.get("enabled"):
        queries = linkedin_queries or li.get("queries", [])
        adapters.append(
            LinkedinParserAdapter(
                queries=queries,
                pages_per_query=int(li.get("pages_per_query", 2)),
                delay_seconds=float(li.get("delay_seconds", 3)),
                fetcher=fetcher,
                location=str(li.get("location", "Russia")),
                f_TPR=str(li.get("f_TPR", "r604800")),
                remote_only=bool(li.get("remote_only", False)),
            )
        )

    return adapters
