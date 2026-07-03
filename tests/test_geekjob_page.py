"""Golden fixtures для Geekjob parser."""

from __future__ import annotations

from parsers.geekjob_page import build_search_url, parse_search_page


def test_build_search_url_first_page():
    url = build_search_url("product manager")
    assert url.startswith("https://geekjob.ru/vacancies?")
    assert "product+manager" in url or "product%20manager" in url


def test_build_search_url_pagination():
    url = build_search_url("pm", page=2)
    assert "page=2" in url


def test_parse_search_page_extracts_vacancy_links():
    slug = "a" * 24
    html = f'<a href="/vacancy/{slug}" class="title">Backend PM</a>'
    rows = parse_search_page(html)
    assert len(rows) == 1
    assert rows[0]["external_id"] == slug
    assert rows[0]["title"] == "Backend PM"
