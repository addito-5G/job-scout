"""Golden fixtures для чистых парсеров (без сети)."""

from __future__ import annotations

from parsers.json_embed import extract_json_array_items, extract_json_object


def test_extract_json_object_from_embedded_state():
    html = '<script>window.state = {"vacancy": {"id": 42, "title": "PM"}}</script>'
    data = extract_json_object(html, "vacancy")
    assert data == {"id": 42, "title": "PM"}


def test_extract_json_object_returns_none_when_missing():
    assert extract_json_object("<html></html>", "vacancy") is None


def test_extract_json_array_items_habr_style():
    html = (
        '{"id":101,"href":"/vacancies/101","title":"Product Manager"},'
        '{"id":102,"href":"/vacancies/102","title":"Analyst"}'
    )
    items = extract_json_array_items(html)
    assert len(items) == 2
    assert items[0]["id"] == "101"
    assert items[0]["title"] == "Product Manager"
