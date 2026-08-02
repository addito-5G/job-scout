"""Стартовый экран: загрузка PDF или вставка резюме."""

from __future__ import annotations

import streamlit as st

from services.resume_pdf import ResumePdfError, load_resume_file_bytes
from ui.workflow import go_to


def _resolve_resume_content() -> tuple[str | None, str, bytes | None, str | None]:
    """Прочитать резюме из session_state.

    Returns:
        text, filename, source_bytes (для PDF), error_message
    """
    mode = st.session_state.get("resume_input_mode", "file")
    if mode == "file":
        uploaded = st.session_state.get("onboard_file")
        if uploaded is not None:
            try:
                data = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
                name = uploaded.name or "resume.pdf"
                text, safe_name = load_resume_file_bytes(data, name)
                source = data if safe_name.lower().endswith(".pdf") else None
                return text, safe_name, source, None
            except ResumePdfError as exc:
                return None, uploaded.name or "resume.pdf", None, str(exc)
            except Exception as exc:
                return None, uploaded.name or "resume.pdf", None, f"Не удалось прочитать файл: {exc}"
        return None, "resume.pdf", None, None

    pasted = (st.session_state.get("resume_paste") or "").strip()
    if pasted:
        return pasted, "pasted_resume.txt", None, None

    return None, "resume.pdf", None, None


def render_onboarding() -> None:
    st.markdown("## Job Scout")
    st.markdown(
        "Загрузите резюме **PDF** или вставьте текстом — система создаст изолированный профиль "
        "с отдельной базой вакансий. Парсинг площадок запустится только после вашего подтверждения."
    )

    st.text_input(
        "Название профиля резюме",
        placeholder="Например: Менеджер по продажам, PM B2B, Backend Python",
        key="profile_display_name",
        help="По этому имени вы будете переключаться между несколькими резюме.",
    )

    mode = st.radio(
        "Как передать резюме",
        options=["file", "text"],
        format_func=lambda x: "📎 Загрузить PDF" if x == "file" else "📝 Вставить текст",
        horizontal=True,
        key="resume_input_mode",
    )

    if mode == "file":
        st.file_uploader(
            "Выберите PDF резюме",
            type=["pdf"],
            key="onboard_file",
            help="Нужен PDF с текстовым слоем (не скан-картинка).",
        )
        uploaded = st.session_state.get("onboard_file")
        if uploaded is not None:
            st.success(f"Файл: **{uploaded.name}** ({max(uploaded.size // 1024, 1)} KB)")
    else:
        st.text_area(
            "Текст резюме",
            height=320,
            placeholder="ФИО\nДолжность\nОпыт работы...",
            key="resume_paste",
        )
        pasted = (st.session_state.get("resume_paste") or "").strip()
        if pasted:
            st.caption(f"✓ {len(pasted)} символов — можно извлекать ключи")

    content, filename, source_bytes, read_error = _resolve_resume_content()
    if read_error:
        st.warning(read_error)
    elif content and mode == "file":
        st.caption(f"✓ Извлечено {len(content)} символов текста из PDF")

    st.divider()

    if st.button("🔑 Извлечь ключи для поиска", type="primary", use_container_width=True):
        content, filename, source_bytes, read_error = _resolve_resume_content()
        display_name = (st.session_state.get("profile_display_name") or "").strip()
        if read_error:
            st.error(read_error)
            return
        if not content:
            st.error("Сначала загрузите PDF резюме или вставьте текст.")
            return
        if not display_name:
            st.error("Укажите название профиля резюме.")
            return
        st.session_state.pending_resume_content = content
        st.session_state.pending_resume_filename = filename
        st.session_state.pending_resume_bytes = source_bytes
        st.session_state.pending_profile_display_name = display_name
        st.session_state.extract_running = True
        go_to("extracting")
        st.rerun()
    elif not content and not read_error:
        st.caption("Загрузите PDF или вставьте текст, затем нажмите кнопку выше.")
