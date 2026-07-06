"""Тесты парсера LinkedIn Jobs (guest, без авторизации)."""

from __future__ import annotations

from pathlib import Path

from parsers.linkedin_jobs import (
    build_search_url,
    extract_job_id,
    is_linkedin_job_url,
    parse_job_page,
    parse_search_fragment,
    vacancy_from_parsed,
)

FIXTURES = Path(__file__).parent / "fixtures" / "linkedin"


def test_is_linkedin_job_url():
    assert is_linkedin_job_url("https://www.linkedin.com/jobs/view/12345/")
    assert is_linkedin_job_url("https://www.linkedin.com/jobs/view/senior-pm-12345/")
    assert not is_linkedin_job_url("https://hh.ru/vacancy/1")


def test_extract_job_id():
    assert extract_job_id("https://www.linkedin.com/jobs/view/senior-pm-4242424242/") == "4242424242"


def test_build_search_url_guest_api():
    url = build_search_url(keywords="product manager", location="Russia", start=25)
    assert "seeMoreJobPostings/search" in url
    assert "keywords=product+manager" in url
    assert "start=25" in url


def test_parse_search_fragment():
    html = (FIXTURES / "search_fragment.html").read_text(encoding="utf-8")
    cards = parse_search_fragment(html)
    assert len(cards) == 1
    assert cards[0]["external_id"] == "4242424242"
    assert cards[0]["title"] == "Senior Product Manager"
    assert cards[0]["company"] == "KTS Group"


def test_parse_job_page_jsonld():
    html = (FIXTURES / "job_page.jsonld.html").read_text(encoding="utf-8")
    detail = parse_job_page(html, job_id="4242424242")
    assert detail is not None
    assert detail["title"] == "Senior Product Manager"
    assert detail["company"] == "KTS Group"
    assert detail["work_format"] == "remote"
    assert "Discovery" in detail["description_full"]


def test_vacancy_from_parsed_merges_detail():
    card = {"external_id": "1", "title": "PM", "company": "X", "location": "Moscow", "url": "https://li/1"}
    detail = {"description_full": "Long text", "work_format": "remote"}
    fields = vacancy_from_parsed(card, detail)
    assert fields["source"] == "linkedin"
    assert fields["description_full"] == "Long text"
    assert fields["work_format"] == "remote"
