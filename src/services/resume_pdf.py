"""Извлечение текста резюме из PDF (без OCR — только текстовый слой)."""

from __future__ import annotations

from pathlib import Path


class ResumePdfError(ValueError):
    """PDF не удалось прочитать или в нём нет текста."""


def extract_text_from_pdf(data: bytes) -> str:
    """Достать текст из PDF. Пустой/скан → ResumePdfError."""
    if not data:
        raise ResumePdfError("Файл PDF пустой.")

    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise ResumePdfError(
            "Для PDF нужен пакет pymupdf. Установите: pip install pymupdf"
        ) from exc

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ResumePdfError(f"Не удалось открыть PDF: {exc}") from exc

    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text") or "")
        text = "\n".join(parts)
    finally:
        doc.close()

    text = _normalize_resume_text(text)
    if len(text) < 40:
        raise ResumePdfError(
            "В PDF почти нет текста (возможно скан или картинка). "
            "Вставьте текст резюме вручную или загрузите PDF с текстовым слоем."
        )
    return text


def extract_text_from_pdf_path(path: str | Path) -> str:
    return extract_text_from_pdf(Path(path).read_bytes())


def load_resume_file_bytes(data: bytes, filename: str) -> tuple[str, str]:
    """Вернуть (text, safe_filename) для PDF или UTF-8 текста."""
    name = Path(filename or "resume.pdf").name
    suffix = Path(name).suffix.lower()

    if suffix == ".pdf" or data[:4] == b"%PDF":
        if not name.lower().endswith(".pdf"):
            name = f"{name}.pdf"
        return extract_text_from_pdf(data), name

    try:
        text = data.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ResumePdfError(
            "Поддерживаются PDF или текстовые файлы UTF-8. Этот файл не распознан."
        ) from exc

    text = _normalize_resume_text(text)
    if len(text) < 40:
        raise ResumePdfError("В файле слишком мало текста для разбора резюме.")
    if suffix not in {".txt", ".md"}:
        name = f"{Path(name).stem}.txt"
    return text, name


def _normalize_resume_text(text: str) -> str:
    lines = [line.rstrip() for line in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    collapsed: list[str] = []
    blank = 0
    for line in lines:
        if not line.strip():
            blank += 1
            if blank <= 1:
                collapsed.append("")
            continue
        blank = 0
        collapsed.append(line)
    return "\n".join(collapsed).strip()
