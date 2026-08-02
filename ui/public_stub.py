"""Публичная заглушка для Streamlit Cloud / Redirect URI hh.ru."""

from __future__ import annotations

import streamlit as st

from ui.brand import PRODUCT_NAME, PRODUCT_TAGLINE


def render_public_stub(*, error: str | None = None) -> None:
    st.markdown(
        f"""
<div style="max-width:640px;margin:3rem auto;padding:0 1rem;font-family:system-ui,sans-serif">
  <div style="font-size:0.75rem;letter-spacing:0.12em;text-transform:uppercase;opacity:0.55;margin-bottom:0.5rem">
    Public demo
  </div>
  <h1 style="margin:0 0 0.5rem;font-size:2rem">{PRODUCT_NAME}</h1>
  <p style="opacity:0.75;margin:0 0 1.5rem">{PRODUCT_TAGLINE}</p>
  <p>
    Личный AI Career Copilot: резюме → поиск вакансий на hh.ru →
    Fit Score → сопроводительные и рекомендации.
  </p>
  <p style="opacity:0.8">
    Полный функционал работает локально (SQLite, Ollama и ключи AI).
    Этот публичный адрес нужен для регистрации приложения в
    <a href="https://dev.hh.ru/" target="_blank">API hh.ru</a>
    (Redirect URI).
  </p>
  <p>
    Репозиторий:
    <a href="https://github.com/addito-5G/job-scout" target="_blank">github.com/addito-5G/job-scout</a>
  </p>
</div>
""",
        unsafe_allow_html=True,
    )
    if error:
        with st.expander("Техническая заметка (для отладки)"):
            st.code(error[:2000])
