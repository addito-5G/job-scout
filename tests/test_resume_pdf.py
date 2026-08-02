"""Тесты извлечения текста из PDF резюме."""

from __future__ import annotations

import pytest

from services.resume_pdf import ResumePdfError, extract_text_from_pdf, load_resume_file_bytes


def _make_pdf_bytes(text: str) -> bytes:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


def test_extract_text_from_pdf_reads_text_layer():
    payload = _make_pdf_bytes(
        "Andrey Nakimov\nProduct Manager\nSkills: Python, SQL, Roadmaps, Stakeholder management"
    )
    text = extract_text_from_pdf(payload)
    assert "Product Manager" in text
    assert "Python" in text


def test_extract_text_from_empty_pdf_raises():
    payload = _make_pdf_bytes("")
    with pytest.raises(ResumePdfError, match="почти нет текста"):
        extract_text_from_pdf(payload)


def test_load_resume_file_bytes_pdf_and_text():
    pdf = _make_pdf_bytes(
        "Ivan Ivanov\nBackend Engineer\nExperience with Django, PostgreSQL and Redis systems"
    )
    text, name = load_resume_file_bytes(pdf, "cv.pdf")
    assert name.endswith(".pdf")
    assert "Backend Engineer" in text

    plain, plain_name = load_resume_file_bytes(
        b"Anna Petrova\nData Analyst\nSQL, Tableau, A/B testing, Python analytics stack",
        "cv.txt",
    )
    assert plain_name.endswith(".txt")
    assert "Data Analyst" in plain
