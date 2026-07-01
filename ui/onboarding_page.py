"""Стартовый экран: загрузка или вставка резюме."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ui.workflow import go_to


def _resolve_resume_content() -> tuple[str | None, str]:
    """Прочитать резюме из session_state (файл или текст)."""
    uploaded = st.session_state.get("onboard_file")
    if uploaded is not None:
        try:
            data = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
            text = data.decode("utf-8").strip()
            if text:
                return text, uploaded.name or "resume.md"
        except Exception:
            pass

    pasted = (st.session_state.get("resume_paste") or "").strip()
    if pasted:
        return pasted, "pasted_resume.md"

    return None, "resume.md"


def render_onboarding() -> None:
    st.markdown("## Job Scout")
    st.markdown(
        "Загрузите резюме **или вставьте текстом** — система извлечёт ключи для поиска вакансий. "
        "Парсинг площадок запустится только после вашего подтверждения."
    )

    mode = st.radio(
        "Как передать резюме",
        options=["text", "file"],
        format_func=lambda x: "📝 Вставить текст" if x == "text" else "📎 Загрузить файл .md",
        horizontal=True,
        key="resume_input_mode",
    )

    if mode == "file":
        st.file_uploader(
            "Выберите файл",
            type=["md", "txt"],
            key="onboard_file",
        )
        uploaded = st.session_state.get("onboard_file")
        if uploaded is not None:
            st.success(f"Файл: **{uploaded.name}** ({uploaded.size // 1024} KB)")
    else:
        st.text_area(
            "Текст резюме",
            height=320,
            placeholder="ФИО\nДолжность\nОпыт работы...\n\nПоддерживается обычный текст или Markdown.",
            key="resume_paste",
        )
        pasted = (st.session_state.get("resume_paste") or "").strip()
        if pasted:
            st.caption(f"✓ {len(pasted)} символов — можно извлекать ключи")

    content, filename = _resolve_resume_content()

    st.divider()

    if st.button("🔑 Извлечь ключи для поиска", type="primary", use_container_width=True):
        content, filename = _resolve_resume_content()
        if not content:
            st.error("Сначала вставьте текст резюме или загрузите файл.")
            return
        st.session_state.pending_resume_content = content
        st.session_state.pending_resume_filename = filename
        st.session_state.extract_running = True
        go_to("extracting")
        st.rerun()
    elif not content:
        st.caption("Вставьте текст или загрузите файл, затем нажмите кнопку выше.")
