"""Редактор ключей: компактные теги с удалением и добавлением."""

from __future__ import annotations

import html

import streamlit as st

_CHIP_STYLES = {
    "title": ("#1e3a5f", "#dbeafe", "#3b82f6"),
    "include": ("#14532d", "#dcfce7", "#22c55e"),
    "exclude": ("#450a0a", "#fee2e2", "#ef4444"),
}

_CSS_INJECTED = False


def inject_keyword_styles() -> None:
    global _CSS_INJECTED
    if _CSS_INJECTED:
        return
    st.markdown(
        """
        <style>
        .kw-block {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }
        .kw-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #f0f3f6;
            margin: 0 0 4px 0;
        }
        .kw-hint {
            font-size: 0.88rem;
            color: #9da7b3 !important;
            margin: 0 0 12px 0;
        }
        .kw-chip {
            display: block;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.92rem;
            line-height: 1.35;
            word-break: break-word;
        }
        .kw-empty {
            color: #8b949e;
            font-size: 0.88rem;
            margin: 0 0 10px 0;
        }
        div[data-testid="column"] button[kind="secondary"] {
            min-height: 2rem;
            padding: 0 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    _CSS_INJECTED = True


def _chip_html(text: str, kind: str) -> str:
    bg, fg, accent = _CHIP_STYLES.get(kind, _CHIP_STYLES["include"])
    safe = html.escape(text)
    return (
        f'<div class="kw-chip" style="background:{bg};color:{fg};'
        f'border-left:3px solid {accent};">{safe}</div>'
    )


def sync_keyword_lists(draft: dict, *, sync_id: str, force: bool = False) -> int:
    if force or st.session_state.get("force_kw_reload") or st.session_state.get("kw_sync_id") != sync_id:
        st.session_state.kw_desired_titles = list(draft.get("desired_titles") or [])
        st.session_state.kw_keywords_include = list(draft.get("keywords_include") or [])
        st.session_state.kw_keywords_exclude = list(draft.get("keywords_exclude") or [])
        st.session_state.kw_sync_id = sync_id
        st.session_state.kw_rev = int(st.session_state.get("kw_rev", 0)) + 1
        st.session_state.force_kw_reload = False
    return int(st.session_state.kw_rev)


def apply_draft_to_lists(draft: dict) -> None:
    st.session_state.kw_desired_titles = list(draft.get("desired_titles") or [])
    st.session_state.kw_keywords_include = list(draft.get("keywords_include") or [])
    st.session_state.kw_keywords_exclude = list(draft.get("keywords_exclude") or [])
    st.session_state.kw_rev = int(st.session_state.get("kw_rev", 0)) + 1


def _remove_at(state_key: str, index: int) -> None:
    items: list[str] = st.session_state[state_key]
    if 0 <= index < len(items):
        items.pop(index)
        st.session_state.kw_rev = int(st.session_state.get("kw_rev", 0)) + 1


def _add_item(state_key: str, value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    items: list[str] = st.session_state.setdefault(state_key, [])
    if value.lower() in {x.lower() for x in items}:
        return False
    items.append(value)
    st.session_state.kw_rev = int(st.session_state.get("kw_rev", 0)) + 1
    return True


def render_keyword_editor(
    label: str,
    state_key: str,
    *,
    kind: str = "include",
    hint: str = "",
    rev: int = 0,
) -> list[str]:
    inject_keyword_styles()

    with st.container(border=True):
        st.markdown(f'<p class="kw-title">{html.escape(label)}</p>', unsafe_allow_html=True)
        if hint:
            st.markdown(f'<p class="kw-hint">{html.escape(hint)}</p>', unsafe_allow_html=True)

        items: list[str] = st.session_state.setdefault(state_key, [])

        if not items:
            st.markdown('<p class="kw-empty">Пока пусто — добавьте ключ ниже</p>', unsafe_allow_html=True)
        else:
            for i, item in enumerate(items):
                left, right = st.columns([12, 1], gap="small", vertical_alignment="center")
                with left:
                    st.markdown(_chip_html(item, kind), unsafe_allow_html=True)
                with right:
                    if st.button("✕", key=f"del_{state_key}_{rev}_{i}", help="Удалить", type="secondary"):
                        _remove_at(state_key, i)
                        st.rerun()

        input_key = f"add_{state_key}_{rev}"
        btn_key = f"btn_add_{state_key}_{rev}"
        inp, btn = st.columns([5, 1], gap="small", vertical_alignment="bottom")
        with inp:
            new_val = st.text_input(
                "new_keyword",
                key=input_key,
                label_visibility="collapsed",
                placeholder="Добавить ключ…",
            )
        with btn:
            if st.button("➕", key=btn_key, help="Добавить", use_container_width=True, type="primary"):
                if _add_item(state_key, new_val):
                    if input_key in st.session_state:
                        del st.session_state[input_key]
                    st.rerun()
                elif new_val.strip():
                    st.toast("Уже есть в списке", icon="⚠️")

    return list(st.session_state.get(state_key, []))
