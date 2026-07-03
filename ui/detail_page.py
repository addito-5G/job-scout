"""Детальная карточка вакансии."""

from __future__ import annotations


import streamlit as st


from ai.ai_router import AIRouterError
from db import session_scope
from services.detail_facade import (
    best_match,
    generate_letter,
    load_detail,
    load_profile,
    load_vacancy,
    normalize_letter,
    run_deep_match,
    run_fast_match,
)
from services.vacancy_status_service import set_vacancy_status
from ui.components import format_salary, match_score_badge, skill_badges, work_format_label
from ui.constants import recommendation_label
from ui.data import cached_profile_id, clear_data_cache
from ui.navigation import source_label


def _render_match_analysis(
    session,
    profile,
    vacancy_id: int,
    detail,
) -> None:
    st.markdown(
        f'<div class="nm-section-label">AI Match</div>',
        unsafe_allow_html=True,
    )

    match, level = best_match(detail)
    vacancy_orm = load_vacancy(session, vacancy_id)

    if not match and profile and vacancy_orm:
        if st.button("🤖 Запустить анализ соответствия", type="primary", key=f"run_match_{vacancy_id}"):
            try:
                with st.spinner("AI сравнивает резюме с вакансией…"):
                    run_fast_match(session, profile, vacancy_orm)
                clear_data_cache()
                st.rerun()
            except Exception as exc:
                st.warning(f"Анализ недоступен: {exc}")
        st.caption("Сравнение резюме с требованиями вакансии — навыки, пробелы, рекомендация.")
        return

    if not match:
        st.info("Загрузите резюме, чтобы получить AI-анализ соответствия.")
        return

    score = match.get("match_score")
    rec_label = recommendation_label(match.get("recommendation"))
    level_label = "глубокий" if level == "deep" else "быстрый"

    st.markdown(
        f'<div class="nm-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem">'
        f'<div><span class="nm-badge">{level_label} анализ</span> '
        f'<span class="nm-badge">{rec_label}</span></div>'
        f"{match_score_badge(score)}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    summary = match.get("deep_analysis") or match.get("match_summary") or ""
    if summary:
        st.markdown(summary)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Совпадает**")
        matched = match.get("matched_skills") or []
        if matched:
            skill_badges(matched, kind="match")
        else:
            st.caption("—")
    with c2:
        st.markdown("**Не хватает**")
        missing = match.get("missing_skills") or []
        if missing:
            skill_badges(missing, kind="missing")
        else:
            st.caption("—")

    strengths = match.get("strengths") or []
    risks = match.get("risks") or []
    if strengths:
        st.markdown("**Сильные стороны для этой роли**")
        skill_badges(strengths, kind="match")
    if risks:
        st.markdown("**Риски**")
        skill_badges(risks, kind="missing")

    if level == "fast" and profile and vacancy_orm:
        if st.button("🔬 Углубить анализ (Groq)", key=f"deep_match_{vacancy_id}"):
            try:
                with st.spinner("Глубокий анализ…"):
                    run_deep_match(session, profile, vacancy_orm)
                clear_data_cache()
                st.rerun()
            except Exception as exc:
                st.warning(str(exc))


def render_detail(vacancy_id: int) -> None:
    profile_id = cached_profile_id()

    with session_scope() as session:
        profile = load_profile(session, profile_id)
        detail = load_detail(session, vacancy_id, profile_id)
        if not detail:
            st.error("Вакансия не найдена")
            return

        if st.button("← К списку"):
            st.query_params.clear()
            st.session_state.view = "opportunities"
            st.rerun()

        st.header(detail.title)
        st.caption(
            f"{detail.company or '—'} · {source_label(detail.source)} · "
            f"{work_format_label(detail.work_format)} · {format_salary(detail)}"
        )

        link_col, score_col = st.columns([2, 1])
        with link_col:
            st.link_button("🔗 Открыть на площадке", detail.url, use_container_width=True)
        with score_col:
            match, _ = best_match(detail)
            if match:
                st.markdown(match_score_badge(match.get("match_score")), unsafe_allow_html=True)

        _render_match_analysis(session, profile, vacancy_id, detail)

        st.subheader("📄 Описание")
        body = detail.full_description or detail.description or "Описание отсутствует"
        st.markdown(body[:14000])

        if detail.skills:
            st.subheader("Навыки вакансии")
            skill_badges(detail.skills, kind="match")

        st.subheader("✉️ Сопроводительное письмо")
        st.caption("По структурному шаблону · YandexGPT")

        letter_state_key = f"cover_letter_{vacancy_id}"
        if letter_state_key not in st.session_state:
            saved = detail.cover_letter or ""
            if saved and profile:
                saved = normalize_letter(saved, profile)
            st.session_state[letter_state_key] = saved

        if profile:
            if st.button(
                "✨ Сгенерировать сопроводительное письмо",
                type="primary",
                key=f"generate_letter_{vacancy_id}",
            ):
                vacancy_orm = load_vacancy(session, vacancy_id)
                if vacancy_orm:
                    try:
                        with st.spinner("YandexGPT пишет письмо…"):
                            letter = generate_letter(
                                session, profile, vacancy_orm, use_cache=False
                            )
                        st.session_state[letter_state_key] = letter
                        clear_data_cache()
                        st.toast("Письмо сохранено", icon="✅")
                        st.rerun()
                    except AIRouterError as exc:
                        st.warning(f"AI недоступен: {exc}")
                    except Exception as exc:
                        st.warning(f"Ошибка: {exc}")

            st.text_area("Текст", height=300, key=letter_state_key)
        else:
            st.info("Загрузите резюме для генерации письма.")

        st.subheader("Действия")
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("✅ Откликнулся", use_container_width=True):
                set_vacancy_status(vacancy_id, "applied")
                clear_data_cache()
                st.success("Статус: applied")
        with a2:
            if st.button("⭐ В избранное", use_container_width=True):
                set_vacancy_status(vacancy_id, "favorite")
                clear_data_cache()
                st.success("В избранном")
        with a3:
            if st.button("🙈 Скрыть", use_container_width=True):
                set_vacancy_status(vacancy_id, "hidden")
                clear_data_cache()
                st.session_state.view = "opportunities"
                st.rerun()
