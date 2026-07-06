"""Тесты генерации ссылки поиска людей LinkedIn."""

from __future__ import annotations

from services.linkedin_outreach_service import linkedin_people_search_url


def test_linkedin_people_search_url_encodes_query():
    url = linkedin_people_search_url(
        company="KTS",
        vacancy_title="Product Manager",
        contact_role="recruiter",
    )
    assert url.startswith("https://www.linkedin.com/search/results/people/")
    assert "KTS" in url
