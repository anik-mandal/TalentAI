"""
shared/ui_theme.py
Centralized dark SaaS theme for TalentAI
"""

import streamlit as st

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0a0a0f;
    color: #e8e8f0;
}

#MainMenu, footer { visibility: hidden; }

/* Keep the sidebar toggle visible but hide the decorative header bar */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

.main .block-container {
    padding: 2rem 2rem;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    color: #ffffff !important;
}

/* Input fields */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background: #13131f !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div {
    background: #13131f !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}

/* Multiselect */
[data-testid="stMultiSelect"] > div {
    background: #13131f !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6c63ff, #a855f7) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(108, 99, 255, 0.4) !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: #13131f;
    border: 1px solid #2a2a3e;
    border-radius: 14px;
    padding: 1rem 1.2rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    background: #13131f;
    border-radius: 10px;
    border: 1px solid #2a2a3e;
    color: #e8e8f0;
    padding: 8px 16px;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Cards */
.portal-card {
    background: linear-gradient(145deg, #13131f, #1a1a2e);
    border: 1px solid #2a2a3e;
    border-radius: 16px;
    padding: 2.5rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
}

.portal-card:hover {
    border-color: #6c63ff;
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(108, 99, 255, 0.2);
}

.portal-card h2 {
    margin: 0.5rem 0 !important;
    font-size: 1.5rem !important;
}

.portal-card p {
    color: #7878a0;
    margin: 0;
    font-size: 0.95rem;
}

.portal-card .icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d0d15 !important;
    border-right: 1px solid #1a1a2e !important;
    min-width: 280px !important;
}

/* Sidebar collapse/expand button */
[data-testid="stSidebarCollapsedControl"] {
    color: #e8e8f0 !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    color: #e8e8f0;
}

/* Status badges */
.badge-shortlisted {
    background: #0d2b1a;
    color: #4ade80;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-rejected {
    background: #2b0d0d;
    color: #f87171;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-maybe {
    background: #2b2b0d;
    color: #facc15;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Dividers */
hr {
    border-color: #1a1a2e !important;
}

</style>
"""


def apply_theme():
    """Apply the centralized dark SaaS theme."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)
