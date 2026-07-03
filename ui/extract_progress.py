"""Прогресс извлечения ключей из резюме."""

from __future__ import annotations


import streamlit as st


from db import get_session, init_db
from services.extract_service import extract_search_keys
from ui.data import clear_data_cache
from ui.keyword_editor import apply_draft_to_lists
from ui.workflow import go_to


def run_extract_with_progress() -> None:
    content = st.session_state.get("pending_resume_content", "")
    filename = st.session_state.get("pending_resume_filename", "resume.md")

    st.markdown("## Извлекаем ключи из резюме")
    st.info("AI анализирует резюме и подбирает запросы для HeadHunter, Habr и Geekjob.")

    if not content.strip():
        st.error("Текст резюме пустой. Вернитесь на шаг 1.")
        st.session_state.extract_running = False
        go_to("input")
        if st.button("← Назад к резюме"):
            st.rerun()
        return

    progress_bar = st.progress(0.0, text="Подготовка...")
    status = st.empty()

    def on_progress(value: float, message: str) -> None:
        value = min(max(value, 0.0), 1.0)
        progress_bar.progress(value, text=message)
        status.markdown(f"**{message}**")

    try:
        init_db()
        session = get_session()
        profile_title = "профиль"
        try:
            profile, draft = extract_search_keys(
                session, content, filename=filename, progress=on_progress
            )
            profile_title = profile.title or profile.full_name or "профиль"
            st.session_state.search_draft = draft
            st.session_state.processed_resume_id = f"{filename}:{len(content)}"
            apply_draft_to_lists(draft)
            st.session_state.keys_extracted = True
            clear_data_cache()
        finally:
            session.close()

        progress_bar.progress(1.0, text="Готово")
        st.success(f"Ключи извлечены для: **{profile_title}**")
        go_to("keywords")
        st.session_state.extract_running = False
        st.session_state.pop("pending_resume_content", None)
        st.session_state.pop("pending_resume_filename", None)
        st.rerun()
    except Exception as exc:
        progress_bar.empty()
        st.error(f"Не удалось извлечь ключи: {exc}")
        st.caption("Проверьте, что Ollama запущена: `ollama serve`")
        st.session_state.extract_running = False
        go_to("input")
        if st.button("← Попробовать снова"):
            st.rerun()
