#!/usr/bin/env python3
"""Сравнение fetcher-движков: requests vs Drission vs Camoufox."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass

from browser.fetcher import CamoufoxFetcher, DrissionFetcher, RequestsFetcher, create_fetcher
from parsers.hh_state import extract_state, find_vacancy_list

TEST_URL = "https://hh.ru/search/vacancy?text=product+manager&area=1"


@dataclass
class FetchReport:
    engine: str
    ok: bool
    elapsed_s: float
    html_bytes: int
    has_hh_state: bool
    vacancy_count: int
    error: str | None = None


def _probe(name: str, fetcher) -> FetchReport:
    t0 = time.perf_counter()
    error = None
    html = ""
    has_state = False
    count = 0
    try:
        html = fetcher.fetch(TEST_URL)
        state = extract_state(html)
        has_state = state is not None
        items = find_vacancy_list(state) if state else []
        count = len(items or [])
    except Exception as exc:
        error = str(exc)
    finally:
        try:
            fetcher.close()
        except Exception:
            pass
    elapsed = time.perf_counter() - t0
    return FetchReport(
        engine=name,
        ok=error is None and has_state and count > 0,
        elapsed_s=round(elapsed, 2),
        html_bytes=len(html.encode("utf-8")) if html else 0,
        has_hh_state=has_state,
        vacancy_count=count,
        error=error,
    )


def main() -> None:
    reports: list[FetchReport] = []

    reports.append(_probe("requests", RequestsFetcher()))

    try:
        reports.append(_probe("drission", DrissionFetcher(headless=True, delay_seconds=1.0)))
    except Exception as exc:
        reports.append(
            FetchReport("drission", False, 0, 0, False, 0, error=f"init failed: {exc}")
        )

    try:
        reports.append(_probe("camoufox", CamoufoxFetcher(headless=True, delay_seconds=1.0)))
    except Exception as exc:
        reports.append(
            FetchReport("camoufox", False, 0, 0, False, 0, error=f"init failed: {exc}")
        )

    auto_pick = "unknown"
    auto_report = None
    try:
        fetcher = create_fetcher(engine="auto", headless=True, delay_seconds=1.0)
        auto_pick = type(fetcher).__name__
        auto_report = _probe(f"auto→{auto_pick}", fetcher)
        reports.append(auto_report)
    except Exception as exc:
        reports.append(
            FetchReport(f"auto", False, 0, 0, False, 0, error=f"auto failed: {exc}")
        )

    print(json.dumps([asdict(r) for r in reports], ensure_ascii=False, indent=2))
    ok_engines = [r.engine for r in reports if r.ok]
    if not ok_engines:
        sys.exit(1)


if __name__ == "__main__":
    main()
