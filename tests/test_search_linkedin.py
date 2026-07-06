"""Тесты LinkedIn-запросов из настроек поиска."""

from __future__ import annotations

from services.search_service import (
    _region_to_linkedin_location,
    settings_to_linkedin_queries_from_data,
)


def test_region_to_linkedin_location_moscow():
    assert _region_to_linkedin_location(["Москва"]) == "Russia"


def test_linkedin_queries_use_location_and_remote():
    queries = settings_to_linkedin_queries_from_data(
        {
            "desired_titles": ["Product Manager"],
            "keywords_include": [],
            "work_formats": ["remote"],
            "linkedin_location": "Moscow",
        }
    )
    assert len(queries) == 1
    assert queries[0]["keywords"] == "Product Manager"
    assert queries[0]["location"] == "Moscow"
    assert queries[0]["remote_only"] is True


def test_linkedin_queries_fallback_region():
    queries = settings_to_linkedin_queries_from_data(
        {
            "desired_titles": ["PM"],
            "regions": ["Москва"],
            "work_formats": [],
        }
    )
    assert queries[0]["location"] == "Russia"
