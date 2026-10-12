"""Visual shell: global CSS injection plus the hero / section headings."""

from __future__ import annotations

import streamlit as st

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #0f172a;
    --muted: #64748b;
    --line: rgba(15, 23, 42, 0.08);
    --card: #ffffff;
    --accent: #4f46e5;
    --accent-soft: rgba(79, 70, 229, 0.10);
    --radius: 18px;
    --shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 12px 32px -16px rgba(16, 24, 40, 0.22);
}

html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.stApp {
    background:
        radial-gradient(1200px 480px at 100% -10%, rgba(79, 70, 229, 0.10), transparent 60%),
        radial-gradient(900px 420px at -10% 10%, rgba(14, 165, 233, 0.08), transparent 55%),
        #f6f7fb;
}

.block-container { max-width: 1080px; padding-top: 2.4rem; padding-bottom: 4rem; }

h1, h2, h3, h4 { letter-spacing: -0.02em; color: var(--ink); font-weight: 700; }
h1 { font-weight: 800; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid var(--line);
}
[data-testid="stSidebarNav"] a { border-radius: 12px; }

/* Metric cards */
[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 18px 20px;
    box-shadow: var(--shadow);
    transition: transform .15s ease, box-shadow .15s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); }
[data-testid="stMetricLabel"] p {
    text-transform: uppercase;
    letter-spacing: .07em;
    font-size: .70rem !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] { font-size: 1.85rem; font-weight: 700; letter-spacing: -0.02em; }

/* Section hero */
.tech-hero { margin: 0 0 1rem 0; }
.tech-hero h2 { margin: 0; font-size: 1.6rem; }
.tech-hero p { margin: .2rem 0 0; color: var(--muted); font-size: .92rem; }

.section-label {
    display: inline-flex; align-items: center; gap: .5rem;
    text-transform: uppercase; letter-spacing: .09em; font-size: .70rem;
    font-weight: 700; color: var(--accent);
    background: var(--accent-soft);
    padding: .32rem .6rem; border-radius: 999px;
    margin: 0 0 .5rem 0;
}

/* Expanders as cards */
[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03) !important;
    overflow: hidden;
    background: var(--card);
    margin-bottom: .5rem;
}
[data-testid="stExpander"] summary { font-weight: 600; padding: .75rem 1rem; }
[data-testid="stExpander"] summary:hover { background: #f8fafc; }

/* Tabs: transparent, underline for the active one */
.stTabs [data-baseweb="tab-list"] {
    gap: 1.4rem;
    background: transparent;
    border-bottom: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
    height: auto;
    padding: .5rem .15rem;
    background: transparent !important;
    border-radius: 0;
    font-weight: 600;
    color: var(--muted);
    border-bottom: 2px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { background: transparent !important; color: var(--ink); }
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab"] > div { background: transparent !important; }

/* Tables */
[data-testid="stTable"] table, [data-testid="stDataFrame"] {
    border-radius: 14px; overflow: hidden; border: 1px solid var(--line);
}
[data-testid="stTable"] thead th {
    background: #f8fafc !important; text-transform: uppercase;
    letter-spacing: .05em; font-size: .68rem; color: var(--muted) !important;
}
[data-testid="stTable"] tbody tr:hover { background: #f8fafc; }

/* Code */
pre, [data-testid="stCode"] pre {
    border-radius: 12px !important;
    border: 1px solid var(--line) !important;
    background: #0f172a0a !important;
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
    border-radius: 12px !important; font-weight: 600 !important;
    border: 1px solid var(--line) !important;
    transition: transform .12s ease, box-shadow .12s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
.stButton > button[kind="primary"] { background: var(--accent) !important; border-color: var(--accent) !important; }

/* Alerts */
[data-testid="stAlert"] { border-radius: 14px; }

hr { border-color: var(--line); }

/* Timeline */
.tl-stage {
    display: flex; justify-content: space-between; align-items: center;
    margin: 1.1rem 0 .4rem; font-weight: 700; color: var(--ink);
    padding-bottom: .35rem; border-bottom: 1px solid var(--line);
}
.tl-note { color: var(--muted); font-size: .85rem; margin: .1rem 0 .35rem 1.5rem; font-style: italic; }
.tl-time {
    text-align: right; color: var(--muted); font-weight: 600;
    font-variant-numeric: tabular-nums; padding-top: .62rem; font-size: .85rem;
}

/* Inline token badge */
.badge {
    display: inline-block; padding: .12rem .5rem; border-radius: 999px;
    background: #eef1f7; color: var(--muted); font-size: .72rem; font-weight: 600;
}
</style>
"""


def inject_style() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"<div class='tech-hero'><h2>{title}</h2>" + (f"<p>{subtitle}</p>" if subtitle else "") + "</div>",
        unsafe_allow_html=True,
    )


def section(label: str) -> None:
    st.markdown(f"<div class='section-label'>{label}</div>", unsafe_allow_html=True)
