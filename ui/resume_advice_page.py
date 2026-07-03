"""Рекомендации по улучшению резюме на основе рынка."""

from __future__ import annotations


import streamlit as st


from db import get_session, init_db
from services.resume_advice_service import collect_market_requirements, generate_resume_advice
from ui.components import skill_badges
from ui.data import cached_profile_id, clear_data_cache
from ui.profile_filter import get_selected_profile_label, get_selected_profile_role


def render_resume_advice() -> None:
    st.header("📝 Рекомендации к резюме")
    st.caption(
        "Сравнение вашего резюме с типичными требованиями из собранных вакансий. "
        "Анализ запускается вручную."
    )

    profile_id = cached_profile_id()
    if profile_id is None:
        st.warning("Сначала загрузите резюме на стартовом экране.")
        return

    if st.button("Обновить резюме", help="Загрузить другой файл и пересобрать профиль поиска"):
        from ui.workflow import reset_to_input

        reset_to_input()
        st.session_state.workflow_stage = "input"
        st.rerun()

    profile_role = get_selected_profile_role()
    profile_label = get_selected_profile_label()

    init_db()
    session = get_session()
    try:
        market = collect_market_requirements(session, profile_role=profile_role)
    finally:
        session.close()

    if profile_label:
        st.caption(f"Анализ рынка для профиля: **{profile_label}**")

    c1, c2, c3 = st.columns(3)
    c1.metric("Вакансий в базе", market["vacancy_count"])
    c2.metric("Топ-навыков", len(market["top_skills"]))
    c3.metric("Сниппетов требований", len(market["sample_requirement_snippets"]))

    with st.expander("Что требует рынок (из вакансий)", expanded=False):
        if market["top_skills"]:
            st.markdown("**Частые навыки**")
            skill_badges(market["top_skills"][:20], kind="match")
        if market["experience_distribution"]:
            st.markdown("**Опыт**")
            for exp, cnt in market["experience_distribution"].items():
                st.caption(f"• {exp}: {cnt} вакансий")
        if market["work_format_distribution"]:
            st.markdown("**Формат работы**")
            for fmt, cnt in market["work_format_distribution"].items():
                st.caption(f"• {fmt}: {cnt}")

    if market["vacancy_count"] < 5:
        st.info("Сначала соберите вакансии — «Обновить сейчас» в сайдбаре или дождитесь автообновления.")
        return

    if st.button("🔍 Получить рекомендации", type="primary", use_container_width=False):
        st.session_state.run_resume_advice = True

    if not st.session_state.get("run_resume_advice") and "resume_advice_result" not in st.session_state:
        st.info("Нажмите кнопку выше — AI сравнит резюме с требованиями рынка.")
        return

    if st.session_state.get("run_resume_advice"):
        init_db()
        session = get_session()
        try:
            with st.spinner("Анализируем резюме и рынок (Groq/Ollama)..."):
                advice = generate_resume_advice(
                    session, profile_id, profile_role=profile_role
                )
            st.session_state.resume_advice_result = advice
            st.session_state.run_resume_advice = False
        except ValueError as exc:
            st.error(str(exc))
            st.session_state.run_resume_advice = False
            return
        finally:
            session.close()

    advice = st.session_state.get("resume_advice_result")
    if not advice:
        return

    fit = advice.get("overall_fit")
    if fit is not None:
        st.metric("Соответствие рынку", f"{fit}%")

    if advice.get("summary"):
        st.subheader("Итог")
        st.write(advice["summary"])

    if advice.get("target_role_alignment"):
        st.info(advice["target_role_alignment"])

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Добавить / усилить")
        skill_badges(advice.get("skills_to_highlight", []), kind="match")
        st.markdown("**Чего не хватает на рынке**")
        skill_badges(advice.get("missing_skills", []), kind="missing")
    with col_r:
        st.subheader("Опыт")
        for item in advice.get("missing_experience", [])[:8]:
            st.caption(f"• {item}")

    improvements = advice.get("resume_improvements", [])
    if improvements:
        st.subheader("Правки по разделам")
        for item in improvements:
            with st.container(border=True):
                st.markdown(f"**{item.get('section', 'Раздел')}**")
                if item.get("issue"):
                    st.caption(item["issue"])
                if item.get("suggestion"):
                    st.write(item["suggestion"])

    actions = advice.get("priority_actions", [])
    if actions:
        st.subheader("Приоритетные шаги")
        for i, action in enumerate(actions, 1):
            st.markdown(f"{i}. {action}")
