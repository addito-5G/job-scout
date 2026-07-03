"""Golden fixtures для Habr Career parser."""

from __future__ import annotations

from parsers.habr_page import parse_search_page


def test_parse_search_page_from_embedded_json():
    html = (
        '{"id":9001,"href":"/vacancies/9001","title":"Product Manager"},'
        '{"id":9002,"href":"/vacancies/9002","title":"Product Analyst"}'
    )
    rows = parse_search_page(html)
    assert len(rows) == 2
    assert rows[0]["external_id"] == "9001"
    assert rows[0]["title"] == "Product Manager"
    assert rows[0]["url"] == "https://career.habr.com/vacancies/9001"
