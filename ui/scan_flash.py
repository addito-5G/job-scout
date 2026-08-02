"""Flash messages for scan results that survive st.rerun()."""

from __future__ import annotations

import streamlit as st

_FLASH_KEY = "scan_flash"


def store_scan_flash(
    *,
    scraped: int,
    new_count: int,
    matched: int,
    errors: list[str] | None = None,
) -> None:
    st.session_state[_FLASH_KEY] = {
        "scraped": int(scraped),
        "new_count": int(new_count),
        "matched": int(matched),
        "errors": list(errors or []),
    }


def render_scan_flash() -> None:
    flash = st.session_state.pop(_FLASH_KEY, None)
    if not flash:
        return

    scraped = int(flash.get("scraped") or 0)
    new_count = int(flash.get("new_count") or 0)
    matched = int(flash.get("matched") or 0)
    errors = list(flash.get("errors") or [])
    err_n = len(errors)

    summary = f"Скан: scraped={scraped}, новых={new_count}, матчинг={matched}"
    if err_n:
        summary += f", ошибок={err_n}"

    if scraped == 0 and errors:
        st.error(
            f"{summary}\n\nПричины:\n\n- " + "\n- ".join(e[:300] for e in errors[:5])
        )
    elif scraped == 0:
        st.warning(f"{summary}. Проверьте ключи поиска и период.")
    else:
        st.success(
            f"{summary}. Откройте «Возможности» или карточку вакансии."
        )
        if errors:
            st.warning(
                "Частичные ошибки (скан всё же что-то сохранил):\n\n- "
                + "\n- ".join(e[:300] for e in errors[:5])
            )
