"""Детальная карточка вакансии."""

from __future__ import annotations


import streamlit as st


from ai.ai_router import AIRouterError
from db import session_scope
from services.detail_facade import (
    best_match,
    generate_letter,
    generate_outreach,
    load_detail,
    load_profile,
    load_vacancy,
    normalize_letter,
    people_search_url,
    refresh_fit_match,
)
from services.vacancy_status_service import set_vacancy_status
from ui.components import format_salary, match_score_badge, skill_badges, work_format_label
from ai.prompts.linkedin_outreach import CONTACT_ROLE_UI_LABELS
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
        '<div class="nm-section-label">Соответствие резюме</div>',
        unsafe_allow_html=True,
    )

    match = best_match(detail)
    vacancy_orm = load_vacancy(session, vacancy_id)

    if not match and profile and vacancy_orm:
        auto_key = f"auto_match_attempted_{vacancy_id}"
        if not st.session_state.get(auto_key):
            st.session_state[auto_key] = True
            try:
                with st.spinner("Считаем соответствие резюме…"):
                    refresh_fit_match(session, profile, vacancy_orm)
                clear_data_cache()
                st.rerun()
            except Exception as exc:
                st.warning(f"Не удалось посчитать соответствие: {exc}")
        else:
            st.caption("Соответствие ещё не рассчитано. Запустите «Сканировать рынок» в сайдбаре.")
        return

    if not match:
        st.info("Загрузите резюме, чтобы увидеть соответствие вакансии.")
        return

    score = match.get("match_score")
    rec_label = recommendation_label(match.get("recommendation"))

    st.markdown(
        f'<div class="nm-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem">'
        f'<div><span class="nm-badge">fit score</span> '
        f'<span class="nm-badge">{rec_label}</span></div>'
        f"{match_score_badge(score)}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    summary = match.get("match_summary") or ""
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

    gaps = match.get("gaps_to_improve") or []
    if gaps:
        st.markdown("**Что усилить для лучшего соответствия**")
        for gap in gaps:
            st.caption(f"• {gap}")

    strengths = match.get("strengths") or []
    risks = match.get("risks") or []
    if strengths:
        st.markdown("**Сильные стороны для этой роли**")
        skill_badges(strengths, kind="match")
    if risks:
        st.markdown("**Риски**")
        skill_badges(risks, kind="missing")

    if profile and vacancy_orm:
        if st.button("🔄 Пересчитать соответствие", key=f"refresh_fit_{vacancy_id}"):
            try:
                refresh_fit_match(session, profile, vacancy_orm)
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
            match = best_match(detail)
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

        if detail.source == "linkedin":
            st.subheader("💬 Мягкий вход в LinkedIn")
            st.caption(
                "Черновик сообщения для connection note или первого DM. "
                "Отправляете вручную — аккаунт не затрагивается."
            )

            outreach_key = f"linkedin_outreach_{vacancy_id}"
            role_key = f"linkedin_outreach_role_{vacancy_id}"
            if outreach_key not in st.session_state:
                st.session_state[outreach_key] = ""

            contact_role = st.selectbox(
                "Кому пишем",
                options=list(CONTACT_ROLE_UI_LABELS.keys()),
                format_func=lambda x: CONTACT_ROLE_UI_LABELS.get(x, x),
                key=role_key,
            )

            vacancy_orm = load_vacancy(session, vacancy_id)
            if profile and vacancy_orm:
                search_url = people_search_url(vacancy_orm, contact_role=contact_role)
                col_gen, col_search = st.columns(2)
                with col_gen:
                    if st.button(
                        "✨ Сгенерировать сообщение",
                        type="secondary",
                        key=f"generate_outreach_{vacancy_id}",
                    ):
                        try:
                            with st.spinner("YandexGPT готовит мягкий вход…"):
                                msg = generate_outreach(
                                    session,
                                    profile,
                                    vacancy_orm,
                                    contact_role=contact_role,
                                    use_cache=False,
                                )
                            st.session_state[outreach_key] = msg
                            st.toast("Черновик готов", icon="✅")
                            st.rerun()
                        except AIRouterError as exc:
                            st.warning(f"AI недоступен: {exc}")
                        except Exception as exc:
                            st.warning(f"Ошибка: {exc}")
                with col_search:
                    st.link_button("🔍 Найти контакт на LinkedIn", search_url, use_container_width=True)

                st.text_area("Сообщение (скопируйте и отправьте сами)", height=180, key=outreach_key)
                msg_len = len(st.session_state.get(outreach_key, "") or "")
                if msg_len:
                    hint = "в норме" if 280 <= msg_len <= 550 else ("коротковато" if msg_len < 280 else "длинновато")
                    st.caption(f"{msg_len} символов · {hint} (цель 280–550)")

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
