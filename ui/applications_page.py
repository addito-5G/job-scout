"""Applications pipeline — job search CRM."""

from __future__ import annotations

import streamlit as st

from ui.components import format_salary, match_score_class, work_format_label
from ui.data import cached_opportunity_list, cached_profile_id
from ui.design_system import COLORS
from ui.profile_filter import get_active_resume_profile_label

PIPELINE = [
    ("favorite", "⭐ Сохранено", "Готовы к отклику"),
    ("applied", "✉ Откликнулись", "Ждём ответа"),
    ("new", "🆕 Новые", "Ещё не обработаны"),
]


def render_applications() -> None:
    profile_id = cached_profile_id()

    st.markdown(
        '<div class="nm-eyebrow">Отклики</div>'
        '<div class="nm-title" style="font-size:1.35rem">Ваши заявки</div>'
        '<p class="nm-subtitle">Отслеживайте воронку: от сохранения до оффера</p>',
        unsafe_allow_html=True,
    )

    for status, label, hint in PIPELINE:
        items, total = cached_opportunity_list(
            profile_id,
            None,
            0,
            "",
            1,
            status=status if status != "new" else None,
        )
        if status == "new":
            items = [i for i in items if i.get("status", "new") == "new"][:10]
            total = len(items)

        with st.expander(f"{label} ({total})", expanded=status == "favorite"):
            st.caption(hint)
            if not items:
                st.caption("Пусто")
                continue
            for item in items[:8]:
                mc = match_score_class(item.get("match_score"))
                st.markdown(
                    f'<div class="nm-card" style="padding:0.85rem 1rem">'
                    f'<div style="display:flex;justify-content:space-between">'
                    f'<div><strong>{item["title"]}</strong><br>'
                    f'<span style="color:{COLORS["text_muted"]};font-size:0.8rem">'
                    f'{item.get("company") or "—"} · {work_format_label(item.get("work_format"))}'
                    f"</span></div>"
                    f'<span class="{mc}" style="font-weight:700">{item.get("match_score") or "—"}%</span>'
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                if st.button("Открыть", key=f"app_open_{status}_{item['id']}"):
                    st.session_state.view = "detail"
                    st.session_state.selected_vacancy_id = item["id"]
                    st.query_params["vacancy_id"] = str(item["id"])
                    st.rerun()
