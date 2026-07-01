"""Список вакансий по выбранной площадке."""

from __future__ import annotations

import math

import streamlit as st

from ui.components import format_salary, match_score_badge, work_format_label
from ui.data import cached_profile_id, cached_vacancy_list
from ui.navigation import source_label
from ui.profile_filter import get_selected_profile_role

PER_PAGE = 30


def _init_state() -> None:
    st.session_state.setdefault("vac_page", 1)


def render_vacancies(source: str) -> None:
    _init_state()
    profile_id = cached_profile_id()
    profile_role = get_selected_profile_role()

    st.header(source_label(source))

    search = st.text_input("Поиск по названию / компании", key=f"search_{source}")
    min_match = st.slider("Мин. AI match, %", 0, 100, 0, step=5, key=f"match_{source}")

    items, total = cached_vacancy_list(
        profile_id,
        source,
        min_match,
        search.strip(),
        st.session_state.vac_page,
        profile_role,
    )

    total_pages = max(1, math.ceil(total / PER_PAGE))
    st.caption(f"Найдено: **{total}** · Страница {st.session_state.vac_page} из {total_pages}")

    if profile_id is None:
        st.warning("Загрузите резюме (.md) в сайдбаре для AI-матчинга")

    if not items:
        st.info("Нет вакансий на этой площадке. Запустите «Обновить вакансии» в сайдбаре.")
        return

    for item in items:
        with st.container(border=True):
            cols = st.columns([5, 2, 1])
            with cols[0]:
                st.markdown(f"**{item['title']}**")
                st.caption(f"{item['company'] or '—'} · {work_format_label(item['work_format'])}")
                st.caption(format_salary(type("O", (), item)()))
                if item.get("tags"):
                    st.caption("🏷 " + ", ".join(item["tags"][:5]))
            with cols[1]:
                st.markdown(match_score_badge(item["match_score"]), unsafe_allow_html=True)
                if item["recommendation"]:
                    st.caption(f"AI: {item['recommendation']}")
            with cols[2]:
                if st.button("Подробно", key=f"detail_{item['id']}", use_container_width=True):
                    st.session_state.view = "detail"
                    st.session_state.selected_vacancy_id = item["id"]
                    st.query_params["vacancy_id"] = str(item["id"])
                    st.rerun()

    nav1, _, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.session_state.vac_page > 1 and st.button("← Назад", key=f"back_{source}"):
            st.session_state.vac_page -= 1
            st.rerun()
    with nav3:
        if st.session_state.vac_page < total_pages and st.button("Вперёд →", key=f"fwd_{source}"):
            st.session_state.vac_page += 1
            st.rerun()
