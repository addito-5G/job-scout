"""Golden fixtures для HH state parser."""

from __future__ import annotations

from parsers.hh_state import find_vacancy_list, format_salary, parse_search_item


HH_SEARCH_ITEM = {
    "vacancyId": 12345,
    "name": "Product Manager",
    "company": {"name": "Acme"},
    "area": {"name": "Москва"},
    "compensation": {
        "from": 200000,
        "to": 300000,
        "currencyCode": "RUR",
        "gross": True,
    },
    "keySkills": [{"name": "Roadmap"}, {"name": "SQL"}],
    "employment": {"@type": "FULL"},
    "publicationTime": {"$": "2024-01-15T10:00:00+03:00"},
}

HH_NESTED_STATE = {
    "page": {
        "vacancies": [
            {"vacancyId": 1, "name": "PM One"},
            {"vacancyId": 2, "name": "PM Two"},
        ]
    }
}


def test_parse_search_item_maps_core_fields():
    parsed = parse_search_item(HH_SEARCH_ITEM)
    assert parsed["external_id"] == "12345"
    assert parsed["title"] == "Product Manager"
    assert parsed["company"] == "Acme"
    assert "Roadmap" in parsed["skills"]
    assert parsed["salary_min"] == 200000


def test_format_salary_range():
    text = format_salary({"from": 100000, "to": 150000, "currencyCode": "RUR"})
    assert "100" in text and "150" in text


def test_find_vacancy_list_nested():
    found = find_vacancy_list(HH_NESTED_STATE)
    assert found is not None
    assert len(found) == 2
    assert found[0]["vacancyId"] == 1
