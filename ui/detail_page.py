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
from services.cover_letter_service import _normalize_letter, generate_cover_letter
from services.match_service import deep_match_vacancy, fast_match_vacancy
from services.profile_service import get_latest_profile
from services.vacancy_service import (
    get_vacancy_detail,
    pick_best_match,
    update_vacancy_status,
)
from ui.components import format_salary, match_score_badge, skill_badges, work_format_label
from ui.data import cached_profile_id, clear_data_cache
from ui.navigation import source_label

_REC_LABELS = {
    "apply": "✅ Откликаться",
    "skip": "⏭ Пропустить",
    "improve_resume": "📝 Усилить резюме",
    "consider": "🤔 Рассмотреть",
}


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

    match, level = pick_best_match(detail.fast_match, detail.deep_match)
    vacancy_orm = get_vacancy_by_id(session, vacancy_id)

    if not match and profile and vacancy_orm:
        if st.button("🤖 Запустить анализ соответствия", type="primary", key=f"run_match_{vacancy_id}"):
            try:
                with st.spinner("AI сравнивает резюме с вакансией…"):
                    fast_match_vacancy(session, profile, vacancy_orm)
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
    rec = match.get("recommendation") or ""
    rec_label = _REC_LABELS.get(rec, rec or "—")
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
                    deep_match_vacancy(session, profile, vacancy_orm)
                clear_data_cache()
                st.rerun()
            except Exception as exc:
                st.warning(str(exc))


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
        match, _ = pick_best_match(detail.fast_match, detail.deep_match)
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
            saved = _normalize_letter(saved, profile)
        st.session_state[letter_state_key] = saved

    if profile:
        if st.button(
            "✨ Сгенерировать сопроводительное письмо",
            type="primary",
            key=f"generate_letter_{vacancy_id}",
        ):
            vacancy_orm = get_vacancy_by_id(session, vacancy_id)
            if vacancy_orm:
                try:
                    with st.spinner("YandexGPT пишет письмо…"):
                        letter = generate_cover_letter(
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
            st.session_state.view = "opportunities"
            st.rerun()

    session.close()
