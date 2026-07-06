"""Рекомендации по улучшению резюме на основе рынка."""

from __future__ import annotations


import streamlit as st


from db import get_session, init_db
from services.resume_advice_service import collect_market_requirements, generate_resume_advice
from ui.components import skill_badges
from ui.data import cached_profile_id, clear_data_cache
from ui.profile_filter import get_active_resume_profile_id, get_active_resume_profile_label


def _clear_stale_advice(profile_id: int) -> None:
    if st.session_state.get("resume_advice_profile_id") != profile_id:
        st.session_state.pop("resume_advice_result", None)
        st.session_state.run_resume_advice = False
    st.session_state.resume_advice_profile_id = profile_id


def render_resume_advice() -> None:
    st.header("📝 Усилить резюме")
    st.caption(
        "AI изучает вакансии вашего профиля и готовит **улучшенное резюме** под HeadHunter — "
        "с ключевыми словами рынка, формулой X–Y–Z и без выдуманных фактов."
    )

    profile_id = get_active_resume_profile_id() or cached_profile_id()
    if profile_id is None:
        st.warning("Сначала загрузите резюме на стартовом экране.")
        return

    _clear_stale_advice(profile_id)

    if st.button("Обновить резюме", help="Создать новый изолированный профиль"):
        from ui.workflow import start_resume_upload

        start_resume_upload()
        st.rerun()

    profile_label = get_active_resume_profile_label()

    init_db()
    session = get_session()
    try:
        market = collect_market_requirements(session, profile_id=profile_id)
    finally:
        session.close()

    if profile_label:
        st.caption(f"Профиль: **{profile_label}** · анализ по {market['vacancy_count']} вакансиям")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Вакансий", market["vacancy_count"])
    c2.metric("Топ-навыков", len(market["top_skills"]))
    c3.metric("Примеров вакансий", len(market.get("vacancy_samples", [])))
    sal = market.get("salary_stats") or {}
    if sal.get("median_rub"):
        c4.metric("Медиана ЗП", f"{sal['median_rub']:,} ₽".replace(",", " "))
    else:
        c4.metric("Требований", len(market.get("common_requirements", [])))

    with st.expander("Что требует рынок (из вашей БД вакансий)", expanded=False):
        if market.get("top_titles"):
            st.markdown("**Частые должности**")
            for t in market["top_titles"][:12]:
                st.caption(f"• {t}")
        if market["top_skills"]:
            st.markdown("**Частые навыки**")
            skill_badges(market["top_skills"][:20], kind="match")
        if market.get("common_requirements"):
            st.markdown("**Типичные требования (фрагменты)**")
            for line in market["common_requirements"][:15]:
                st.caption(f"• {line}")

    if market["vacancy_count"] < 5:
        st.info("Сначала соберите вакансии — «Сканировать рынок» в сайдбаре.")
        return

    if st.button("✨ Собрать улучшенное резюме", type="primary", use_container_width=True):
        st.session_state.run_resume_advice = True
        st.session_state.pop("resume_advice_result", None)

    if not st.session_state.get("run_resume_advice") and "resume_advice_result" not in st.session_state:
        st.info("Нажмите кнопку — AI проанализирует вакансии и выдаст готовое резюме для копирования.")
        return

    if st.session_state.get("run_resume_advice"):
        init_db()
        session = get_session()
        try:
            with st.spinner("Изучаем рынок и переписываем резюме (Yandex/Ollama)…"):
                advice = generate_resume_advice(session, profile_id, use_cache=False)
            st.session_state.resume_advice_result = advice
            st.session_state.resume_advice_profile_id = profile_id
            st.session_state.run_resume_advice = False
            clear_data_cache()
        except ValueError as exc:
            st.error(str(exc))
            st.session_state.run_resume_advice = False
            return
        finally:
            session.close()

    advice = st.session_state.get("resume_advice_result")
    if not advice:
        return

    if advice.get("profile_id") not in (None, profile_id):
        st.warning("Результат от другого профиля. Нажмите «Собрать улучшенное резюме» снова.")
        return

    if advice.get("candidate_name"):
        st.caption(f"Кандидат: **{advice['candidate_name']}**")

    fit = advice.get("overall_fit")
    if fit is not None:
        st.metric("Соответствие исходного резюме рынку", f"{fit}%")

    if advice.get("market_insight"):
        st.info(advice["market_insight"])

    if advice.get("experience_timeline_validation"):
        st.caption(f"Проверка стажа: {advice['experience_timeline_validation']}")

    merged = advice.get("merged_experience_blocks") or []
    if merged:
        with st.expander("Объединённые блоки раннего опыта", expanded=False):
            for block in merged:
                st.markdown(f"**{block.get('title', '—')}** · {block.get('period', '')}")
                if block.get("companies_merged"):
                    st.caption("Компании: " + ", ".join(block["companies_merged"]))

    improved = advice.get("improved_resume_markdown", "").strip()
    if improved:
        st.subheader("📋 Готовое резюме — скопируйте на hh.ru")
        st.text_area(
            "Улучшенное резюме",
            value=improved,
            height=480,
            key=f"improved_resume_copy_{profile_id}",
            label_visibility="collapsed",
        )
        st.caption("Проверьте каждый факт перед публикацией — AI не должен придумывать опыт.")

    if advice.get("summary"):
        st.subheader("Итог")
        st.write(advice["summary"])

    if advice.get("target_role"):
        st.caption(f"Целевая должность: **{advice['target_role']}**")

    keywords = advice.get("keywords_from_market") or []
    if keywords:
        st.subheader("Ключевые слова для поиска HH")
        skill_badges(keywords[:20], kind="match")

    classification = advice.get("experience_classification") or []
    if classification:
        with st.expander("Классификация опыта (релевантный / околорелевантный / убрать)", expanded=False):
            for item in classification:
                tag = item.get("type", "")
                emoji = {"relevant": "✅", "okolorelevant": "🔄", "irrelevant": "➖"}.get(tag, "•")
                st.markdown(
                    f"{emoji} **{item.get('item', '—')}** — {item.get('action', '')}: {item.get('reason', '')}"
                )

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Усилить в резюме")
        skill_badges(advice.get("skills_to_highlight", []), kind="match")
    with col_r:
        st.subheader("Пробелы vs рынок")
        for gap in advice.get("gaps", [])[:8]:
            st.caption(f"• {gap}")

    to_add = advice.get("skills_to_add_or_clarify") or advice.get("missing_skills") or []
    if to_add:
        st.subheader("Уточнить / добавить (если правда владеете)")
        skill_badges(to_add, kind="missing")

    improvements = advice.get("section_notes") or advice.get("resume_improvements") or []
    if improvements:
        st.subheader("Правки по разделам")
        for item in improvements:
            with st.container(border=True):
                st.markdown(f"**{item.get('section', 'Раздел')}**")
                if item.get("issue"):
                    st.caption(item["issue"])
                suggestion = item.get("suggestion") or item.get("changes")
                if suggestion:
                    st.write(suggestion)

    actions = advice.get("priority_actions", [])
    if actions:
        st.subheader("Следующие шаги")
        for i, action in enumerate(actions, 1):
            st.markdown(f"{i}. {action}")
