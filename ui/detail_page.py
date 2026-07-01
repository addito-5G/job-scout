"""Детальная карточка вакансии."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ai.ai_router import AIRouterError
from db import get_session, init_db
from db.repositories.vacancy_repo import get_vacancy_by_id
from services.cover_letter_service import generate_cover_letter
from services.match_service import deep_match_vacancy
from services.profile_service import get_latest_profile
from services.vacancy_service import get_vacancy_detail, update_vacancy_status
from ui.components import format_salary, match_score_badge, skill_badges, work_format_label
from ui.data import cached_profile_id, clear_data_cache
from ui.navigation import source_label


def render_detail(vacancy_id: int) -> None:
    init_db()
    session = get_session()
    profile_id = cached_profile_id()
    profile = get_latest_profile(session) if profile_id else None

    detail = get_vacancy_detail(session, vacancy_id, profile_id)
    if not detail:
        st.error("Вакансия не найдена")
        session.close()
        return

    if st.button("← К списку"):
        st.query_params.clear()
        st.session_state.view = "vacancies"
        st.rerun()

    st.header(detail.title)
    st.caption(
        f"{detail.company or '—'} · {source_label(detail.source)} · "
        f"{work_format_label(detail.work_format)} · {format_salary(detail)}"
    )

    link_col, score_col = st.columns([2, 1])
    with link_col:
        st.link_button("🔗 Открыть вакансию на площадке", detail.url, use_container_width=True)
    with score_col:
        if detail.fast_match or detail.deep_match:
            ms = (detail.deep_match or detail.fast_match or {}).get("match_score")
            st.markdown(match_score_badge(ms), unsafe_allow_html=True)

    st.subheader("📄 Описание")
    body = detail.full_description or detail.description or "Описание отсутствует"
    st.markdown(body[:14000])

    if detail.skills:
        st.subheader("Навыки")
        skill_badges(detail.skills, kind="match")

    st.subheader("✉️ Сопроводительное письмо")
    st.caption("По правилам Анастасии Бурмистровой · YandexGPT")

    letter_text = detail.cover_letter or ""
    if letter_text:
        st.text_area("Текст", letter_text, height=300, key="letter_saved")

    if profile:
        if st.button("✨ Сгенерировать сопроводительное письмо", type="primary"):
            vacancy_orm = get_vacancy_by_id(session, vacancy_id)
            if vacancy_orm:
                try:
                    with st.spinner("YandexGPT пишет письмо..."):
                        letter = generate_cover_letter(session, profile, vacancy_orm)
                    st.text_area("Результат", letter, height=300, key="letter_generated")
                    clear_data_cache()
                    st.toast("Письмо сохранено", icon="✅")
                except AIRouterError as exc:
                    st.warning(f"AI недоступен: {exc}")
                except Exception as exc:
                    st.warning(f"Ошибка: {exc}")
    else:
        st.info("Загрузите резюме для генерации письма.")

    with st.expander("🤖 AI-анализ соответствия"):
        deep = detail.deep_match
        if not deep and profile:
            vacancy_orm = get_vacancy_by_id(session, vacancy_id)
            if vacancy_orm and st.button("Запустить глубокий анализ"):
                try:
                    with st.spinner("Groq анализирует..."):
                        deep_match_vacancy(session, profile, vacancy_orm)
                    clear_data_cache()
                    st.rerun()
                except Exception as exc:
                    st.warning(str(exc))
        elif deep:
            if deep.get("match_summary"):
                st.write(deep["match_summary"])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Совпадает**")
                skill_badges(deep.get("matched_skills", []), kind="match")
            with c2:
                st.markdown("**Не хватает**")
                skill_badges(deep.get("missing_skills", []), kind="missing")

    st.subheader("Действия")
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("✅ Откликнулся", use_container_width=True):
            update_vacancy_status(session, vacancy_id, "applied")
            clear_data_cache()
            st.success("Статус: applied")
    with a2:
        if st.button("⭐ В избранное", use_container_width=True):
            update_vacancy_status(session, vacancy_id, "favorite")
            clear_data_cache()
            st.success("В избранном")
    with a3:
        if st.button("🙈 Скрыть", use_container_width=True):
            update_vacancy_status(session, vacancy_id, "hidden")
            clear_data_cache()
            st.session_state.view = "vacancies"
            st.rerun()

    session.close()
