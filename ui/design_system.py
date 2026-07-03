"""Design tokens and global styles — Linear / Notion inspired."""

from __future__ import annotations

import streamlit as st

from ui.brand import PRODUCT_NAME, PRODUCT_TAGLINE

# --- Tokens ---
COLORS = {
    "bg": "#0a0a0b",
    "surface": "#141416",
    "surface_raised": "#1c1c1f",
    "border": "#2a2a2e",
    "text": "#ededed",
    "text_muted": "#8b8b93",
    "text_subtle": "#5c5c66",
    "accent": "#5e6ad2",
    "accent_hover": "#7078e0",
    "success": "#3ecf8e",
    "warning": "#f5a623",
    "danger": "#e5484d",
    "info": "#52a9ff",
}

TYPOGRAPHY = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
"""

GLOBAL_CSS = f"""
{TYPOGRAPHY}
:root {{
  --nm-bg: {COLORS["bg"]};
  --nm-surface: {COLORS["surface"]};
  --nm-border: {COLORS["border"]};
  --nm-text: {COLORS["text"]};
  --nm-muted: {COLORS["text_muted"]};
  --nm-accent: {COLORS["accent"]};
}}

html, body, [class*="css"] {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

.stApp {{
  background: {COLORS["bg"]} !important;
  color: {COLORS["text"]};
}}

[data-testid="stSidebar"] {{
  background: {COLORS["surface"]} !important;
  border-right: 1px solid {COLORS["border"]};
}}

[data-testid="stSidebar"] .stMarkdown h1 {{
  font-size: 1.15rem !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
}}

.block-container {{
  padding-top: 1.5rem !important;
  max-width: 1100px !important;
}}

/* Nav buttons */
[data-testid="stSidebar"] .stButton > button {{
  border-radius: 8px !important;
  border: 1px solid transparent !important;
  font-weight: 500 !important;
  transition: all 0.15s ease !important;
}}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: {COLORS["accent"]} !important;
  color: white !important;
}}

[data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
  background: transparent !important;
  color: {COLORS["text_muted"]} !important;
}}

[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
  background: {COLORS["surface_raised"]} !important;
  color: {COLORS["text"]} !important;
}}

/* Cards */
.nm-card {{
  background: {COLORS["surface"]};
  border: 1px solid {COLORS["border"]};
  border-radius: 12px;
  padding: 1.25rem 1.35rem;
  margin-bottom: 0.75rem;
  transition: border-color 0.15s ease;
}}

.nm-card:hover {{
  border-color: #3a3a42;
}}

.nm-card-hero {{
  background: linear-gradient(135deg, {COLORS["surface_raised"]} 0%, {COLORS["surface"]} 100%);
  border: 1px solid {COLORS["border"]};
  border-radius: 16px;
  padding: 1.75rem 2rem;
  margin-bottom: 1.5rem;
}}

.nm-eyebrow {{
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: {COLORS["text_subtle"]};
  margin-bottom: 0.35rem;
}}

.nm-title {{
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.2;
  margin: 0 0 0.5rem 0;
  color: {COLORS["text"]};
}}

.nm-subtitle {{
  font-size: 0.95rem;
  color: {COLORS["text_muted"]};
  line-height: 1.5;
  margin: 0;
}}

.nm-insight {{
  display: flex;
  gap: 0.65rem;
  align-items: flex-start;
  padding: 0.65rem 0;
  border-bottom: 1px solid {COLORS["border"]};
  font-size: 0.9rem;
  color: {COLORS["text"]};
}}

.nm-insight:last-child {{ border-bottom: none; }}

.nm-dot {{
  width: 6px; height: 6px;
  border-radius: 50%;
  background: {COLORS["accent"]};
  margin-top: 0.45rem;
  flex-shrink: 0;
}}

.nm-match-lg {{
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1;
}}

.nm-match-excellent {{ color: {COLORS["success"]}; }}
.nm-match-good {{ color: {COLORS["accent"]}; }}
.nm-match-ok {{ color: {COLORS["warning"]}; }}
.nm-match-low {{ color: {COLORS["danger"]}; }}

.nm-badge {{
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  background: {COLORS["surface_raised"]};
  color: {COLORS["text_muted"]};
  border: 1px solid {COLORS["border"]};
}}

.nm-cta-primary {{
  display: inline-block;
  background: {COLORS["accent"]};
  color: white !important;
  padding: 0.65rem 1.25rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none !important;
}}

.nm-section-label {{
  font-size: 0.8rem;
  font-weight: 600;
  color: {COLORS["text_subtle"]};
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 1.5rem 0 0.75rem 0;
}}

/* Hide Streamlit chrome noise */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{
  background: transparent !important;
}}
"""


def inject_design_system() -> None:
    st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    st.sidebar.markdown(
        f'<div style="margin-bottom:0.25rem">'
        f'<span style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em">{PRODUCT_NAME}</span>'
        f'</div>'
        f'<div style="font-size:0.75rem;color:{COLORS["text_subtle"]};margin-bottom:1rem">'
        f"{PRODUCT_TAGLINE}</div>",
        unsafe_allow_html=True,
    )
