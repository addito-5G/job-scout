"""Тесты параметров поиска hh_parser."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.hh_parser import HhParserAdapter


def test_search_params_include_week_period():
    adapter = HhParserAdapter(queries=[{"text": "Python"}])
    params = adapter._search_params({"text": "Python", "area": 2})
    assert params["search_period"] == 7
    assert params["order_by"] == "publication_time"
    assert params["area"] == 2


def test_search_params_omit_period_when_disabled():
    adapter = HhParserAdapter(queries=[], search_period=0)
    params = adapter._search_params({"text": "Python"})
    assert "search_period" not in params


def test_within_period_filters_old_vacancies():
    adapter = HhParserAdapter(queries=[])
    now = datetime.now(timezone.utc)
    assert adapter._within_period(now - timedelta(days=3), 7) is True
    assert adapter._within_period(now - timedelta(days=10), 7) is False
    assert adapter._within_period(None, 7) is False
    assert adapter._within_period(None, 0) is True


def test_fetch_records_page_errors():
    adapter = HhParserAdapter(queries=[{"text": "x"}], pages_per_query=1, delay_seconds=0)

    def boom(_params, _page):
        raise RuntimeError("boom")

    adapter._fetch_page = boom  # type: ignore[method-assign]
    assert list(adapter.fetch()) == []
    assert adapter.errors
    assert "boom" in adapter.errors[0]
