"""PhytoGraph Research Atlas — presentation-layer redesign for Anti-AMR GraphRAG.

Works with the existing database.py, ranking.py, graphrag.py,
ollama_engine.py, groq_engine.py and evaluation/answerability_detector.py.
No data or backend scientific logic is modified here.
"""

from __future__ import annotations

from html import escape as html_escape
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from database import _secret, get_driver
from evaluation.answerability_detector import detect_answerability
from graph_visualization import (
    build_full_graph_html,
    build_graph_html,
    get_compound_options,
    get_graph_relationship_type_counts,
    get_graph_relationship_types,
)
from graphrag import answer_question
from groq_engine import generate_groq_answer
from ollama_engine import generate_local_answer
from ranking import load_rankings


load_dotenv()
DATABASE = _secret("NEO4J_DATABASE", "neo4j")

st.set_page_config(
    page_title="PhytoGraph | Anti-AMR Research Atlas",
    page_icon=":material/biotech:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "PhytoGraph is an exploratory Anti-AMR knowledge-graph research prototype."},
)


# -----------------------------------------------------------------------------
# Original, locally defined SVG icons. No emoji or external icon-image service.
# -----------------------------------------------------------------------------
SVG = {
    "mark": '''<svg viewBox="0 0 48 48" fill="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="46" height="46" rx="14" fill="#285C49"/><path d="M15 31c7-1 13-8 15-17 3 10-2 21-12 22" stroke="#E9F5E9" stroke-width="2.3" stroke-linecap="round"/><path d="M15 31c-2-8 0-15 12-18 2 9-1 16-12 18Z" stroke="#D5EBCF" stroke-width="2" stroke-linejoin="round"/><path d="M15 31 27 17" stroke="#D5EBCF" stroke-width="1.4" stroke-linecap="round"/><circle cx="33" cy="32" r="4" fill="#D8B47E"/><circle cx="34" cy="19" r="2.5" fill="#B5D8C7"/><path d="M30 25 33 29" stroke="#D8B47E" stroke-width="1.6"/></svg>''',
    "leaf": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 4C11 4 4 8 4 15a5 5 0 0 0 5 5c7 0 11-7 11-16Z"/><path d="M4 20c2-5 6-8 11-11"/></svg>''',
    "flask": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v7l-5.8 9.2A2 2 0 0 0 5.9 22h12.2a2 2 0 0 0 1.7-2.8L14 10V3"/><path d="M7 16h10"/></svg>''',
    "target": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>''',
    "network": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="5" cy="6" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="12" cy="19" r="2"/><circle cx="19" cy="16" r="2"/><path d="M7 6.2 17 5.3M6.3 7.8 10.8 17.4M17.5 6.7 13.1 17M17.8 14.2 18.8 7"/></svg>''',
    "activity": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18h18M5 14l5-5 4 3 6-7"/><path d="M16 5h4v4"/></svg>''',
    "shield": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 2 8 4v6c0 5-3.3 8.4-8 10-4.7-1.6-8-5-8-10V6l8-4Z"/><path d="m8.5 12 2.5 2.5 4.5-5"/></svg>''',
    "book": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 6c-2.5-2-5.5-2-9-1v14c3.5-1 6.5-1 9 1 2.5-2 5.5-2 9-1V5c-3.5-1-6.5-1-9 1Z"/><path d="M12 6v14"/></svg>''',
    "spark": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 2 2.1 7.9L22 12l-7.9 2.1L12 22l-2.1-7.9L2 12l7.9-2.1L12 2Z"/></svg>''',
}


STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght,SOFT,WONK@9..144,500,40,0&display=swap');
:root { --ink:#203A30; --forest:#285C49; --forestdeep:#173F31; --muted:#6D8175;
        --cream:#F7F8F3; --line:#E0E8DE; --gold:#D8AF73; --card:#FFFFFF; }
html,body,[data-testid="stApp"], [data-testid="stMain"] { font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; color:var(--ink); }
[data-testid="stAppViewContainer"] { background: #F7F8F3; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1380px; padding-top: 1.35rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #EDF3EB; border-right:1px solid #DCE7DB; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.68rem; }
[data-testid="stSidebar"] .stButton > button { justify-content:flex-start; width:100%; min-height:42px;
  border:1px solid transparent; background:transparent; color:#4D6758; box-shadow:none;
  font-weight:600; border-radius:11px; padding:0.55rem 0.9rem; }
[data-testid="stSidebar"] .stButton > button:hover { background:#E0EADF; color:#1F523D; border-color:#D2E1D0; }
[data-testid="stSidebar"] .stButton > button[kind="primary"] { background:#D9E7D9; border-color:#C4D9C6; color:#1D513B; }
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover { background:#D2E3D1; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:#285C49; color:white; border-color:#285C49; box-shadow: 0 4px 14px rgba(40,92,73,.13); }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover { background:#1C4937; border-color:#1C4937; color:white; }
.stButton > button, .stFormSubmitButton > button { border-radius:10px; font-weight:600; min-height:42px; }
[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; border:1px solid #E0E8DE; }
[data-testid="stMetric"] { padding:.3rem .2rem; }
[data-testid="stMetricValue"] { color:var(--forestdeep); font-weight:700; letter-spacing:-.04em; }
[data-testid="stExpander"] { border-color:#E2E8DF; border-radius:12px; background:#FFF; }
[data-testid="stAlert"] { border-radius:12px; }
[data-testid="stForm"] { background:#fff; border:1px solid #DFE8DE; border-radius:18px; padding:1rem 1.25rem; }
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input { border-radius:10px; }
h1,h2,h3 { color:#1F3F32; letter-spacing:-.028em; }
hr { border-color:#E0E8DE !important; }
.ph-brand { display:flex; align-items:center; gap:13px; padding:16px 3px 20px; }
.ph-brand-mark { width:52px; height:52px; flex-shrink:0; }
.ph-brand-name { color:#193D2D; font-weight:800; letter-spacing:-.055em; font-size:27px; line-height:1.08; }
.ph-brand-caption { color:#567864; font-weight:700; font-size:11px; letter-spacing:.035em; line-height:1.35; margin-top:6px; }
@media (max-width: 480px) {
  .ph-brand-name { font-size:25px; }
  .ph-brand-caption { font-size:10.5px; }
}
.ph-side-label { color:#7A9081; font-size:10px; letter-spacing:.16em; font-weight:700; margin:1.2rem 4px .38rem; }
.ph-side-stat { display:flex; align-items:center; justify-content:space-between; margin:.25rem 4px; font-size:12px; color:#617867; }
.ph-side-stat strong { color:#2D543F; font-weight:700; }
.ph-status { display:flex; align-items:center; gap:8px; padding:12px 13px; background:#FAFCF8; border:1px solid #DDE8DB; border-radius:12px; color:#315E48; font-size:12px; font-weight:650; }
.ph-dot { width:8px; height:8px; border-radius:50%; display:inline-block; background:#54A680; box-shadow:0 0 0 3px #DDF2E4; }
.ph-dot.offline { background:#C97777; box-shadow:0 0 0 3px #F6E5E2; }
.ph-sidebar-note { font-size:11px; color:#789082; line-height:1.58; padding:7px 3px; }
.ph-eyebrow { color:#5C8C70; text-transform:uppercase; font-size:10px; letter-spacing:.18em; font-weight:750; }
.ph-topline { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:4px 0 17px; }
.ph-topmeta { color:#839386; font-size:11px; font-weight:600; letter-spacing:.055em; }
.ph-hero { background:linear-gradient(118deg,#EBF3E6 0%,#E6F0E7 53%,#E2EEE6 100%); border:1px solid #DAE6D9;
  border-radius:23px; display:grid; grid-template-columns:1.22fr .78fr; align-items:center; overflow:hidden; min-height:296px; position:relative; }
.ph-hero-copy { padding:38px 14px 37px 39px; position:relative; z-index:2; }
.ph-hero h1 { font-family:'Fraunces',Georgia,serif; font-weight:500; font-size:clamp(32px,4.05vw,55px); line-height:1.12; letter-spacing:-.048em; color:#1C4835; margin:13px 0 14px; }
.ph-hero p { color:#537261; font-size:14px; line-height:1.75; max-width:510px; margin:0; }
.ph-art { height:294px; min-width:0; display:flex; align-items:center; justify-content:center; overflow:hidden; }
.ph-art svg { width:100%; height:100%; min-width:290px; }
.ph-chipline { display:flex; gap:10px; flex-wrap:wrap; margin-top:20px; }
.ph-chip { border:1px solid #BFD5C0; color:#396750; background:#F3F8F0; padding:6px 10px; border-radius:99px; font-size:10px; letter-spacing:.015em; font-weight:650; }
.ph-section { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin:29px 0 14px; }
.ph-section h2 { font-family:'Fraunces',Georgia,serif; font-size:26px; font-weight:500; letter-spacing:-.035em; margin:3px 0 6px; color:#214332; }
.ph-section p { color:#738679; font-size:13px; line-height:1.6; margin:0; max-width:760px; }
.ph-section-meta { border:1px solid #DBE5DB; border-radius:100px; color:#60796B; font-size:10px; padding:8px 12px; white-space:nowrap; background:#fff; }
.ph-kpis { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:21px 0 5px; }
.ph-kpi { background:#fff; border:1px solid #E1E8E0; border-radius:17px; padding:18px 19px 17px; min-height:136px; box-shadow:0 3px 15px rgba(35,74,45,.024); }
.ph-kpi-top { display:flex; align-items:center; justify-content:space-between; }
.ph-kpi-icon { width:36px; height:36px; border-radius:11px; background:#EDF5EE; display:flex; align-items:center; justify-content:center; color:#508468; }
.ph-kpi-icon svg { width:19px; height:19px; }
.ph-kpi-index { color:#B3C0B7; font-size:10px; font-weight:700; letter-spacing:.1em; }
.ph-kpi-number { color:#244C39; font-size:30px; font-weight:730; letter-spacing:-.055em; margin:12px 0 1px; }
.ph-kpi-label { color:#7A8B7F; font-size:11px; font-weight:550; }
.ph-strip { display:flex; gap:18px; flex-wrap:wrap; padding:14px 19px; border:1px solid #E0E8DE; border-radius:13px; margin:14px 0 11px; background:#FDFEFB; }
.ph-strip-item { display:flex; gap:7px; align-items:center; font-size:11px; color:#758A7B; }
.ph-strip-item b { color:#315A43; font-weight:750; }
.ph-panel { background:#fff; border:1px solid #E1E9E0; border-radius:16px; padding:23px; }
.ph-panel h3 { font-size:15px; font-weight:750; margin:0 0 8px; letter-spacing:-.02em; }
.ph-panel p { font-size:12px; line-height:1.7; color:#708378; margin:0; }
.ph-steps { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:13px; }
.ph-step { position:relative; background:#fff; border:1px solid #E1E9E0; border-radius:16px; padding:20px 18px; min-height:160px; }
.ph-step-no { color:#A7B7AC; font-size:11px; letter-spacing:.11em; font-weight:700; }
.ph-step-ico { color:#477D62; margin:14px 0 9px; width:23px; height:23px; }
.ph-step-ico svg { width:23px; height:23px; }
.ph-step-title { font-size:14px; font-weight:750; color:#234634; margin-bottom:6px; }
.ph-step-text { color:#78877C; line-height:1.6; font-size:11px; }
.ph-page-intro { border-bottom:1px solid #E0E8DF; padding:8px 0 22px; margin-bottom:20px; }
.ph-page-intro h1 { font-family:'Fraunces',Georgia,serif; font-size:clamp(30px,3.4vw,42px); font-weight:500; letter-spacing:-.047em; margin:10px 0 10px; line-height:1.2; }
.ph-page-intro p { max-width:820px; font-size:14px; color:#718478; line-height:1.73; margin:0; }
.ph-card-heading { font-size:15px; font-weight:750; color:#284837; margin:5px 0 12px; }
.ph-profile { padding:20px; border-radius:16px; border:1px solid #DCE7DA; background:linear-gradient(145deg,#F0F6EE,#FFF); }
.ph-profile small { display:block; color:#628572; font-weight:700; letter-spacing:.15em; font-size:10px; text-transform:uppercase; }
.ph-profile h3 { font-family:'Fraunces',Georgia,serif; font-size:28px; font-weight:500; color:#224733; margin:8px 0; }
.ph-profile-meta { color:#6B8374; font-size:12px; margin-bottom:14px; }
.ph-big-score { font-size:36px; font-weight:750; letter-spacing:-.05em; color:#2B6148; line-height:1.1; }
.ph-score-label { font-size:11px; color:#7B9182; margin-top:4px; }
.ph-score-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; margin:14px 0; }
.ph-score-part { background:#F5F9F3; border:1px solid #DEEADD; padding:13px 11px; border-radius:12px; min-width:0; }
.ph-score-points { font-size:21px; font-weight:750; color:#285C49; line-height:1.2; }
.ph-score-name { margin-top:6px; font-size:11px; color:#557363; line-height:1.45; font-weight:600; }
@media (max-width:950px) { .ph-score-grid { grid-template-columns:repeat(3,minmax(0,1fr)); } }
@media (max-width:550px) { .ph-score-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.ph-disclaimer { border-left:3px solid #CFA46B; background:#FFFDF7; border-radius:0 11px 11px 0; padding:12px 14px; color:#806D4D; font-size:12px; line-height:1.65; margin:15px 0 8px; }
.ph-legend { display:flex; gap:17px; align-items:center; flex-wrap:wrap; font-size:11px; color:#667C6E; padding:10px 0 3px; }
.ph-legend-item { display:inline-flex; align-items:center; gap:6px; }
.ph-legend-dot { height:9px; width:9px; border-radius:50%; display:inline-block; }
.ph-answer-head { display:flex; gap:11px; align-items:center; margin:5px 0 13px; }
.ph-answer-icon { height:37px; width:37px; border-radius:12px; color:#366A50; background:#E8F3E9; display:flex; align-items:center; justify-content:center; }
.ph-answer-icon svg { height:20px; width:20px; }
.ph-answer-copy strong { display:block; font-size:13px; color:#2E5943; }
.ph-answer-copy span { display:block; font-size:11px; color:#7C9182; }
.ph-footer { margin:38px 0 3px; padding:18px 0; display:flex; gap:16px; align-items:center; justify-content:space-between; border-top:1px solid #DFE8DC; color:#8A9D90; font-size:10px; }
@media(max-width:1000px) { .ph-hero { grid-template-columns:1fr .6fr; } .ph-kpis { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media(max-width:700px) { .ph-hero { grid-template-columns:1fr; } .ph-hero-copy { padding:25px 24px 5px; } .ph-hero h1 { font-size:34px; } .ph-art { height:175px; } .ph-art svg { max-height:225px; } .ph-kpis,.ph-steps { grid-template-columns:repeat(2,minmax(0,1fr)); } .ph-section-meta { display:none; } .ph-footer { flex-direction:column; align-items:start; } }
@media(max-width:460px) { .ph-steps { grid-template-columns:1fr; } .ph-kpi { padding:14px; } .ph-kpi-number { font-size:25px; } }
</style>
"""


def show_html(markup: str) -> None:
    """Render static first-party HTML (dynamic values must be escaped)."""
    st.html(markup)


def escape(value: object) -> str:
    return html_escape(str(value), quote=True)


def icon(name: str) -> str:
    return SVG[name]


def section_head(kicker: str, title: str, subtitle: str = "", meta: str = "") -> None:
    right = f'<span class="ph-section-meta">{escape(meta)}</span>' if meta else ""
    show_html(
        f'<div class="ph-section"><div><span class="ph-eyebrow">{escape(kicker)}</span>'
        f'<h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div>{right}</div>'
    )


def page_intro(kicker: str, title: str, subtitle: str) -> None:
    show_html(
        f'<div class="ph-page-intro"><span class="ph-eyebrow">{escape(kicker)}</span>'
        f'<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>'
    )


def metric_tile(index: int, title: str, value: str, symbol: str) -> str:
    return (
        f'<div class="ph-kpi"><div class="ph-kpi-top"><div class="ph-kpi-icon">{icon(symbol)}</div>'
        f'<span class="ph-kpi-index">{index:02d}</span></div>'
        f'<div class="ph-kpi-number">{escape(value)}</div>'
        f'<div class="ph-kpi-label">{escape(title)}</div></div>'
    )


def caution(text: str) -> None:
    show_html(f'<div class="ph-disclaimer">{escape(text)}</div>')


def show_scoring_guide() -> None:
    """Explain what the evidence fields and legacy score can safely establish."""
    with st.expander("How to interpret this evidence explorer", expanded=False):
        st.markdown(
            "**This page describes the evidence fields stored in the current CSV export.** "
            "It does not calculate a score from those fields at runtime."
        )
        st.markdown(
            """
            **What the repository documents**

            The project README describes these intended maximum weight allocations:

            | Evidence dimension | Documented maximum |
            |---|---:|
            | Pathogen-study evidence grade | 30 points |
            | Molecular-target evidence grade | 25 points |
            | Resistance-specificity information | 20 points |
            | Distinct research-source breadth | 15 points |
            | Pathogen-record breadth | 10 points |
            | **Total** | **100 points** |

            **Important implementation limitation:** the current `ranking.py` only loads
            `data/V3_EVIDENCE_PRIORITIZATION_137.csv`. The repository does not include
            an executable scoring-generation procedure showing how the component fields
            are normalized, converted into points, and combined to produce
            `V3_Heuristic_Score`. Therefore, the stored numerical score cannot currently
            be independently reproduced from this application code.
            """
        )
        st.warning(
            "Treat the stored score and rank as legacy, precomputed exploratory fields. "
            "This page does not use them to filter or sort candidates. Do not interpret "
            "them as antimicrobial potency, probability of treatment success, binding "
            "confidence, safety, or clinical effectiveness."
        )
        st.markdown(
            "**How to read the evidence fields:** "
            "`Activity_Grade` and `Target_Grade` are internal values in the supplied "
            "export; they are not percentages. `Specificity_Proxy` is a proxy field, "
            "not a percentage of resistance or effectiveness. Publication counts are "
            "provisional deduplicated estimates and may need manual verification. "
            "A zero caution-flag count does not establish safety or complete verification."
        )
        st.caption(
            "The current export contains 137 mapped compound profiles. The remaining "
            "288 of the 425 registered compounds have no profile in this export; "
            "they are not thereby classified as inactive."
        )

@st.cache_data(ttl=180)
def get_rankings() -> pd.DataFrame:
    df = load_rankings()
    df = df.loc[:, ~df.columns.str.endswith(".1")].copy()
    if "Caution_Flags" in df.columns:
        df["Caution_Flags"] = df["Caution_Flags"].fillna("")
    df = df.rename(columns={"V3_Heuristic_Score": "Evidence_Priority_Score"})
    df["Evidence_Priority_Score"] = pd.to_numeric(df["Evidence_Priority_Score"], errors="coerce")
    return df.sort_values("Evidence_Priority_Score", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=120)
def get_graph_statistics() -> dict:
    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            totals = session.run(
                "MATCH (n) WITH count(n) AS nodes "
                "OPTIONAL MATCH ()-[r]->() "
                "RETURN nodes, count(r) AS relationships"
            ).single()
            label_rows = session.run(
                "MATCH (n) UNWIND labels(n) AS label "
                "RETURN label, count(*) AS total"
            ).data()
    stats = {"nodes": totals["nodes"], "relationships": totals["relationships"]}
    stats.update({row["label"]: row["total"] for row in label_rows})
    return stats


@st.cache_data(ttl=180)
def cached_graph_relationship_counts() -> dict[str, int]:
    return get_graph_relationship_type_counts()


@st.cache_data(ttl=180)
def cached_compound_options() -> list[dict[str, str]]:
    return get_compound_options()


rankings = get_rankings()
try:
    graph_stats = get_graph_statistics()
    database_online = True
except Exception:
    graph_stats = None
    database_online = False


# -----------------------------------------------------------------------------
# Sidebar and navigation — custom layout, real Streamlit controls.
# -----------------------------------------------------------------------------

show_html(STYLE)

PAGES = (
    ("Overview", "overview"),
    ("Evidence Coverage Explorer", "rankings"),
    ("Knowledge Graph", "graph"),
    ("AI Research Assistant", "assistant"),
    ("About the Research", "about"),
)
if "current_page" not in st.session_state:
    st.session_state.current_page = "overview"

with st.sidebar:
    show_html(
        f'<div class="ph-brand"><div class="ph-brand-mark">{icon("mark")}</div>'
        '<div><div class="ph-brand-name">PhytoGraph</div>'
        '<div class="ph-brand-caption">Research atlas / Anti-AMR</div></div></div>'
    )
    show_html('<div class="ph-side-label">DISCOVER</div>')
    for label, page_key in PAGES:
        if st.button(
            label,
            key=f"nav_{page_key}",
            type="primary" if st.session_state.current_page == page_key else "secondary",
            width="stretch",
        ):
            st.session_state.current_page = page_key
            st.rerun()

    show_html('<div class="ph-side-label">DATASET SNAPSHOT</div>')
    for label, n in (
        ("Medicinal plants", (graph_stats or {}).get("Plant", 100)),
        ("Phytochemicals", (graph_stats or {}).get("Compound", 425)),
        ("Pathogen records", (graph_stats or {}).get("Pathogen", 24)),
        ("Molecular targets", (graph_stats or {}).get("Target", 49)),
    ):
        show_html(f'<div class="ph-side-stat"><span>{escape(label)}</span><strong>{int(n):,}</strong></div>')

    show_html('<div class="ph-side-label">INFRASTRUCTURE</div>')
    if database_online:
        show_html('<div class="ph-status"><span class="ph-dot"></span>Neo4j database connected</div>')
    else:
        show_html('<div class="ph-status"><span class="ph-dot offline"></span>Neo4j connection unavailable</div>')
    show_html(
        '<div class="ph-sidebar-note">AuraDB-ready knowledge graph and Groq-supported evidence retrieval. '
        'Results are exploratory and are not evidence of clinical efficacy.</div>'
    )

show_html(
    '<div class="ph-topline"><span class="ph-eyebrow">PHYTOCHEMICAL DISCOVERY / KNOWLEDGE GRAPH</span>'
    '<span class="ph-topmeta">RESEARCH PROTOTYPE</span></div>'
)


# -----------------------------------------------------------------------------
# Page: overview
# -----------------------------------------------------------------------------

HERO_ART = """
<svg viewBox="0 0 470 320" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Botanical leaves and molecular network illustration" role="img">
<defs><linearGradient id="leafgrad" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#6EA88A"/><stop offset="1" stop-color="#2A614D"/></linearGradient>
<linearGradient id="leaflight" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#BBDCC2"/><stop offset="1" stop-color="#75B194"/></linearGradient></defs>
<circle cx="298" cy="161" r="125" stroke="#BDD5C5" stroke-width="1" stroke-dasharray="3 7"/><circle cx="298" cy="161" r="89" stroke="#C8DCCB" stroke-width="1.1"/><circle cx="298" cy="161" r="51" stroke="#B6D2BC" stroke-width="1" stroke-dasharray="3 6"/>
<path d="M224 292C226 232 250 201 290 155" stroke="#397658" stroke-width="4" stroke-linecap="round"/>
<path d="M273 176C227 151 205 109 223 63c47 7 78 49 50 113Z" fill="url(#leafgrad)"/><path d="M273 176c-7-49-22-72-45-98" stroke="#CDE6D1" stroke-width="2"/>
<path d="M256 204C292 155 343 137 377 153c-20 57-77 86-121 51Z" fill="url(#leaflight)"/><path d="M256 204c40-20 68-31 106-42" stroke="#E6F6E7" stroke-width="2"/>
<path d="M240 252C205 230 178 188 190 146c46 5 70 58 50 106Z" fill="#80B89A"/><path d="M240 252c-4-28-15-53-39-86" stroke="#E7F6E7" stroke-width="1.8"/>
<path d="M293 150 359 83 425 126M293 150 357 236 418 202M359 83 357 236M224 92 293 150" stroke="#88B6A5" stroke-width="1.7" stroke-dasharray="3 6"/>
<circle cx="359" cy="83" r="12" fill="#FFF7E8" stroke="#CEA46B" stroke-width="3"/><circle cx="425" cy="126" r="9" fill="#E6F0F9" stroke="#729DB9" stroke-width="2.6"/><circle cx="357" cy="236" r="11" fill="#F9E9E8" stroke="#C68186" stroke-width="3"/><circle cx="418" cy="202" r="7" fill="#E6F0F9" stroke="#729DB9" stroke-width="2"/><circle cx="224" cy="92" r="6" fill="#D2E7D7" stroke="#72A78A" stroke-width="2"/>
<circle cx="293" cy="150" r="13" fill="#FFFFFF" stroke="#D5AE78" stroke-width="3"/><circle cx="293" cy="150" r="4" fill="#D5AE78"/><circle cx="359" cy="83" r="4" fill="#D2AB77"/>
<path d="M146 292h264" stroke="#B9D2BD" stroke-width="1"/><text x="151" y="308" font-size="10" fill="#779681" font-family="sans-serif" letter-spacing="2">BOTANICAL  /  MOLECULAR  /  EVIDENCE</text>
</svg>
"""


def show_overview() -> None:
    show_html(
        '<div class="ph-hero"><div class="ph-hero-copy">'
        '<span class="ph-eyebrow">BOTANICAL INTELLIGENCE MEETS SCIENTIFIC EVIDENCE</span>'
        '<h1>Nature holds possibilities.<br>Evidence reveals connections.</h1>'
        '<p>Discover phytochemicals from traditional medicinal plants, trace their reported molecular '
        'relationships, and explore antimicrobial research in one connected workspace.</p>'
        '<div class="ph-chipline"><span class="ph-chip">Evidence-first discovery</span>'
        '<span class="ph-chip">Knowledge graph</span><span class="ph-chip">AI-assisted research</span></div>'
        f'</div><div class="ph-art">{HERO_ART}</div></div>'
    )
    c1, c2, _ = st.columns([1.1, 1.2, 3.4], gap="small")
    with c1:
        if st.button("Explore compounds", type="primary", width="stretch", key="overview_compounds"):
            st.session_state.current_page = "rankings"
            st.rerun()
    with c2:
        if st.button("Open knowledge graph", width="stretch", key="overview_graph"):
            st.session_state.current_page = "graph"
            st.rerun()

    stats = graph_stats or {}
    show_html(
        '<div class="ph-kpis">'
        + metric_tile(1, "Medicinal plants", f'{stats.get("Plant", 100):,}', "leaf")
        + metric_tile(2, "Phytochemical compounds", f'{stats.get("Compound", 425):,}', "flask")
        + metric_tile(3, "Pathogen / resistance records", f'{stats.get("Pathogen", 24):,}', "network")
        + metric_tile(4, "Molecular targets", f'{stats.get("Target", 49):,}', "target")
        + '</div>'
        + '<div class="ph-strip">'
        + f'<span class="ph-strip-item"><b>{stats.get("nodes", "—")}</b> total graph nodes</span>'
        + f'<span class="ph-strip-item"><b>{stats.get("relationships", "—")}</b> graph relationships</span>'
        + f'<span class="ph-strip-item"><b>{len(rankings)}</b> evidence-ranked compounds</span>'
        + '<span class="ph-strip-item"><b>0–100</b> evidence priority index</span>'
        + '</div>'
    )

    section_head("RESEARCH WORKFLOW", "One connected discovery journey", "From traditional medicine to a traceable scientific evidence record.")
    steps = [
        ("01", "leaf", "Explore botanicals", "Begin with medicinal plant records and their curated phytochemical associations."),
        ("02", "network", "Inspect connections", "Navigate compound relationships with pathogen records and molecular targets."),
        ("03", "spark", "Interrogate the evidence", "Ask GraphRAG questions and inspect the retrieved publications and limitations."),
    ]
    show_html('<div class="ph-steps">' + ''.join(
        f'<div class="ph-step"><div class="ph-step-no">{n} / DISCOVERY</div>'
        f'<div class="ph-step-ico">{icon(ic)}</div><div class="ph-step-title">{escape(title)}</div>'
        f'<div class="ph-step-text">{escape(desc)}</div></div>'
        for n, ic, title, desc in steps
    ) + '</div>')

    section_head("CANDIDATE LANDSCAPE", "Prioritized research candidates", "Evidence priority scores summarize mapped research evidence; they do not measure clinical effectiveness.", meta="TOP 12 / 137 SCORED")
    if not rankings.empty:
        ranked = rankings.head(12).set_index("Compound")["Evidence_Priority_Score"].rename("Evidence priority score")
        st.bar_chart(ranked, horizontal=True, color="#5E9175", height=370)
    caution("These rankings are an exploratory guide for further research, not a measure of antibacterial potency, safety or clinical effectiveness.")


# -----------------------------------------------------------------------------
# Page: compound explorer
# -----------------------------------------------------------------------------


def show_rankings() -> None:
    page_intro(
        "DISCOVERY / 01", "Evidence Coverage Explorer",
        "Explore the recorded antimicrobial and molecular-target evidence associated with mapped phytochemicals. Compare evidence coverage and traceability fields rather than relying on an unexplained numerical score."
    )

    if rankings.empty:
        st.warning("The evidence-prioritization export contains no compound profiles.")
        return

    coverage = rankings.get(
        "Evidence_Coverage", pd.Series(index=rankings.index, dtype="object")
    ).fillna("Not recorded")
    both_count = int((coverage == "Both evidence types").sum())
    pathogen_only_count = int((coverage == "Pathogen evidence only").sum())
    target_only_count = int((coverage == "Target evidence only").sum())

    show_html(
        '<div class="ph-kpis">'
        + metric_tile(1, "Mapped evidence profiles", str(len(rankings)), "flask")
        + metric_tile(2, "Both evidence types", str(both_count), "network")
        + metric_tile(3, "Graph nodes", str((graph_stats or {}).get("nodes", "—")), "network")
        + metric_tile(4, "Protein targets", str((graph_stats or {}).get("Target", 49)), "target")
        + '</div>'
    )
    st.caption(
        f"Evidence coverage in this export: {both_count} with both pathogen and target evidence, "
        f"{pathogen_only_count} with pathogen evidence only, and "
        f"{target_only_count} with target evidence only."
    )

    section_head(
        "EVIDENCE DIRECTORY",
        "Browse mapped compound profiles",
        "Search profiles and compare their recorded evidence grades, source coverage, pathogen records, target connections and caution flags."
    )
    show_scoring_guide()

    a, b, c = st.columns([2.2, 1.5, 1.5], gap="medium")
    with a:
        text_filter = st.text_input(
            "Search compound",
            placeholder="Search by compound name or ID",
            key="compound_search",
        )
    coverage_values = [
        value for value in (
            "Both evidence types",
            "Pathogen evidence only",
            "Target evidence only",
        )
        if value in set(coverage.astype(str))
    ]
    with b:
        coverage_filter = st.selectbox(
            "Evidence coverage",
            options=["All profiles"] + coverage_values,
            key="evidence_coverage_filter",
        )
    with c:
        sort_label = st.selectbox(
            "Sort profiles by",
            options=[
                "Most estimated sources",
                "Most pathogen records",
                "Most target connections",
                "Most evidence cautions",
                "Compound name (A–Z)",
            ],
            key="evidence_profile_sort",
        )

    filtered = rankings.copy()
    if text_filter.strip():
        query = text_filter.strip()
        mask = filtered["Compound"].astype(str).str.contains(
            query, case=False, na=False, regex=False
        )
        if "Compound_ID" in filtered.columns:
            mask = mask | filtered["Compound_ID"].astype(str).str.contains(
                query, case=False, na=False, regex=False
            )
        filtered = filtered[mask]

    if coverage_filter != "All profiles":
        filtered = filtered[
            filtered["Evidence_Coverage"].fillna("Not recorded") == coverage_filter
        ]

    sort_columns = {
        "Most estimated sources": "Unique_Publications_Provisional",
        "Most pathogen records": "Unique_Pathogen_Records",
        "Most target connections": "Target_Links",
        "Most evidence cautions": "Caution_Flags_Count",
        "Compound name (A–Z)": "Compound",
    }
    sort_column = sort_columns[sort_label]
    if sort_column in filtered.columns:
        filtered = filtered.sort_values(
            sort_column,
            ascending=(sort_label == "Compound name (A–Z)"),
            na_position="last",
        )

    if filtered.empty:
        st.info("No compound profiles match the current search and evidence-coverage filter.")
        return

    count_options = [n for n in (10, 20, 50, 100) if n < len(filtered)]
    count_options.append(len(filtered))
    count = st.selectbox(
        "Show profiles",
        options=count_options,
        index=min(1, len(count_options) - 1),
        key="evidence_profile_count",
    )

    display_columns = [
        "Compound_ID",
        "Compound",
        "Evidence_Coverage",
        "Activity_Grade",
        "Target_Grade",
        "Specificity_Proxy",
        "Unique_Publications_Provisional",
        "Pathogen_Publications",
        "Target_Publications",
        "Unique_Pathogen_Records",
        "Pathogen_Links",
        "Target_Links",
        "Synergy_Relationships",
        "Caution_Flags_Count",
    ]
    available_columns = [column for column in display_columns if column in filtered.columns]
    st.dataframe(
        filtered[available_columns].head(count),
        hide_index=True,
        width="stretch",
        height=425,
        column_config={
            "Compound_ID": st.column_config.TextColumn("Compound ID", width="small"),
            "Compound": st.column_config.TextColumn("Phytochemical", width="medium"),
            "Evidence_Coverage": st.column_config.TextColumn(
                "Recorded evidence coverage",
                help="Whether the export records pathogen-side evidence, target-side evidence, or both.",
            ),
            "Activity_Grade": st.column_config.NumberColumn(
                "Antimicrobial evidence grade",
                format="%.3f",
                help="Internal value from the supplied export; not a bacterial-killing percentage.",
            ),
            "Target_Grade": st.column_config.NumberColumn(
                "Target evidence grade",
                format="%.3f",
                help="Internal value from the supplied export; not a probability of physical binding.",
            ),
            "Specificity_Proxy": st.column_config.NumberColumn(
                "Resistance-specificity proxy",
                format="%.2f",
                help="Proxy field supplied in the export. Its exact construction is not reproducible from the current repository code.",
            ),
            "Unique_Publications_Provisional": st.column_config.NumberColumn(
                "Estimated distinct sources",
                format="%d",
                help="Provisional deduplicated publication estimate; verify source identity before treating as definitive.",
            ),
            "Pathogen_Publications": st.column_config.NumberColumn("Pathogen publications", format="%d"),
            "Target_Publications": st.column_config.NumberColumn("Target publications", format="%d"),
            "Unique_Pathogen_Records": st.column_config.NumberColumn("Pathogen records", format="%d"),
            "Pathogen_Links": st.column_config.NumberColumn("Pathogen links", format="%d"),
            "Target_Links": st.column_config.NumberColumn("Target connections", format="%d"),
            "Synergy_Relationships": st.column_config.NumberColumn(
                "Synergy links",
                format="%d",
                help="Recorded graph relationships; not necessarily independent publications.",
            ),
            "Caution_Flags_Count": st.column_config.NumberColumn(
                "Evidence cautions",
                format="%d",
                help="Recorded caution flags. Zero does not mean proven safe or fully verified.",
            ),
        },
    )
    st.caption(
        f"Showing {min(len(filtered), count)} of {len(filtered)} matching profiles. "
        "This export covers 137 of the 425 registered compounds; compounds absent from "
        "the export are unscored here, not classified as inactive."
    )

    section_head(
        "DEEPER INSPECTION",
        "Compound evidence profile",
        "Review the evidence fields and recorded limitations for one selected compound."
    )
    names = filtered["Compound"].dropna().astype(str).unique().tolist()
    if not names:
        st.info("No compound names are available in the filtered profiles.")
        return
    name = st.selectbox(
        "Select a compound profile",
        options=names,
        key="profile_name",
    )
    data = filtered.loc[filtered["Compound"].astype(str) == name].iloc[0]

    left, right = st.columns([1.0, 1.45], gap="large")
    with left:
        coverage_label = str(data.get("Evidence_Coverage") or "Not recorded")
        compound_id = str(data.get("Compound_ID") or "")
        show_html(
            f'<div class="ph-profile"><small>PHYTOCHEMICAL / {escape(compound_id)}</small>'
            f'<h3>{escape(name)}</h3>'
            f'<div class="ph-profile-meta">{escape(coverage_label)} · recorded research profile</div>'
            '</div>'
        )
        st.markdown("**Recorded interpretation**")
        interpretation = data.get("Interpretation")
        st.write(
            str(interpretation)
            if pd.notna(interpretation) and str(interpretation).strip()
            else "No interpretation is recorded in this export."
        )
        with st.expander("Legacy precomputed score (not used for filtering or sorting)", expanded=False):
            score = data.get("Evidence_Priority_Score")
            rank = data.get("Rank_Among_137_Mapped")
            if pd.notna(score):
                st.metric("Stored V3 heuristic score", f"{float(score):.2f}")
            else:
                st.write("No precomputed score is recorded.")
            if pd.notna(rank):
                st.caption(f"Stored export rank: {int(rank)} of 137.")
            st.warning(
                "This value is loaded from the CSV. The current repository does not contain "
                "the executable calculation needed to reproduce how its component fields "
                "combine into this number. It is retained for traceability only."
            )

    with right:
        m1, m2, m3, m4 = st.columns(4)
        def display_count(field: str) -> int:
            value = pd.to_numeric(pd.Series([data.get(field)]), errors="coerce").iloc[0]
            return int(value) if pd.notna(value) else 0

        m1.metric(
            "Est. sources",
            display_count("Unique_Publications_Provisional"),
            help="Provisional deduplicated estimate; verify publication identity.",
        )
        m2.metric("Pathogen records", display_count("Unique_Pathogen_Records"))
        m3.metric("Target connections", display_count("Target_Links"))
        m4.metric("Evidence cautions", display_count("Caution_Flags_Count"))

        details = [
            (
                "Evidence coverage", "Evidence_Coverage",
                "Indicates which evidence categories are represented in this export; it does not rate evidence quality."
            ),
            (
                "Antimicrobial evidence grade", "Activity_Grade",
                "Internal pathogen-side grade from the CSV. It is not a percentage of bacterial killing."
            ),
            (
                "Target evidence grade", "Target_Grade",
                "Internal target-side grade from the CSV. It is not proof of physical binding."
            ),
            (
                "Resistance-specificity proxy", "Specificity_Proxy",
                "A proxy field supplied in the CSV. Its exact construction is not documented in the current executable code."
            ),
            (
                "Pathogen publications", "Pathogen_Publications",
                "Publication count attributed to pathogen-side evidence in the export; source deduplication is provisional."
            ),
            (
                "Target publications", "Target_Publications",
                "Publication count attributed to target-side evidence in the export; source deduplication is provisional."
            ),
            (
                "Pathogen links", "Pathogen_Links",
                "Number of pathogen relationship entries recorded for this compound."
            ),
            (
                "Synergy relationships", "Synergy_Relationships",
                "Number of synergy relationship entries recorded for this compound; not necessarily independent publications."
            ),
            (
                "Recorded evidence cautions", "Caution_Flags",
                "Warning flags recorded in the export. No recorded flag does not establish safety or complete verification."
            ),
        ]
        with st.expander("Inspect evidence fields and their meaning", expanded=True):
            for label, field, meaning in details:
                value = data.get(field, None)
                shown = (
                    str(value)
                    if value is not None and pd.notna(value) and str(value).strip()
                    else "None recorded"
                )
                st.markdown(f"**{label}:** {shown}")
                st.caption(meaning)

    caution(
        "This explorer compares the contents and coverage of the supplied evidence records. "
        "Record counts and internal grades are not clinical outcomes. Mapped relationships "
        "do not independently establish antimicrobial potency, safety, physical binding, "
        "or clinical benefit."
    )

# -----------------------------------------------------------------------------
# Page: graph exploration
# -----------------------------------------------------------------------------


def show_graph() -> None:
    page_intro(
        "KNOWLEDGE GRAPH", "Knowledge Graph Explorer",
        "Explore the complete Anti-AMR knowledge graph or search for one phytochemical to inspect its connected plants, targets and pathogen records."
    )
    show_html(
        '<div class="ph-legend">'
        '<span class="ph-legend-item"><i class="ph-legend-dot" style="background:#5C9A77"></i>Medicinal plants</span>'
        '<span class="ph-legend-item"><i class="ph-legend-dot" style="background:#D3A45F"></i>Compounds</span>'
        '<span class="ph-legend-item"><i class="ph-legend-dot" style="background:#6E93BE"></i>Molecular targets</span>'
        '<span class="ph-legend-item"><i class="ph-legend-dot" style="background:#C98289"></i>Pathogen records</span>'
        '</div>'
    )

    if st.session_state.get("graph_view_mode") == "Compound-Centred Network":
        st.session_state["graph_view_mode"] = "Search by Compound"

    graph_mode = st.radio(
        "Choose graph view",
        options=["Full Knowledge Graph", "Search by Compound"],
        horizontal=True,
        key="graph_view_mode",
    )

    if graph_mode == "Full Knowledge Graph":
        st.markdown(
            "View the connected dataset across all four entity categories. "
            "The filters let you focus on selected entity and relationship types."
        )
        st.caption(
            "The full graph is visually dense. Reset the filters to restore all four entity types "
            "and all recorded relationship types. Node positions and edge lengths are visual layout only."
        )

        if not database_online:
            st.error("Neo4j is unavailable. Check the configured AuraDB connection and retry.")
            return

        try:
            relationship_counts = cached_graph_relationship_counts()
            relationship_options = list(relationship_counts)
            if not relationship_options:
                relationship_options = get_graph_relationship_types()
        except Exception as exc:
            st.error(
                "Could not load relationship-type filters from Neo4j: "
                f"{type(exc).__name__}"
            )
            return

        node_options = ["Plant", "Compound", "Target", "Pathogen"]
        node_display = {
            "Plant": "Medicinal plants",
            "Compound": "Phytochemical compounds",
            "Target": "Molecular targets",
            "Pathogen": "Pathogen / resistance records",
        }
        relationship_display = {
            "CONTAINS_COMPOUND": "Plant → compound: occurrence / contains",
            "INTERACTS_WITH_TARGET": "Compound → target: molecular-target evidence",
            "ACTS_AGAINST_PATHOGEN": "Compound → pathogen: antimicrobial evidence",
            "ASSOCIATED_WITH_TARGET": "Pathogen → target: resistance-associated target",
        }

        reset_col, helper_col = st.columns([1, 3], gap="small")
        with reset_col:
            if st.button("Reset all graph filters", key="reset_full_graph_filters"):
                for key in (
                    "full_graph_node_types",
                    "full_graph_relationship_types",
                    "full_graph_html",
                    "full_graph_signature",
                    "full_graph_loaded",
                ):
                    st.session_state.pop(key, None)
                st.rerun()
        with helper_col:
            st.caption(
                "Default view: all entity types and all relationship types. "
                "Each relationship label below also shows its database record count."
            )

        left, right = st.columns(2, gap="medium")
        with left:
            selected_node_types = st.multiselect(
                "Entity types to display",
                options=node_options,
                default=node_options,
                format_func=lambda value: node_display[value],
                key="full_graph_node_types",
            )
        with right:
            selected_relationship_types = st.multiselect(
                "Relationship types to display",
                options=relationship_options,
                default=relationship_options,
                format_func=lambda value: (
                    f"{relationship_display.get(value, value.replace('_', ' ').title())} "
                    f"({relationship_counts.get(value, 0):,})"
                ),
                key="full_graph_relationship_types",
            )

        c1, c2 = st.columns([1, 1.5], gap="medium")
        with c1:
            max_relationships = st.selectbox(
                "Maximum relationships to load",
                options=[1000, 2500, 5000, 10000],
                index=3,
                format_func=lambda value: f"{value:,}",
                key="full_graph_max_relationships",
                help="Choose 10,000 to include the current 4,299-relationship dataset without truncation.",
            )
        with c2:
            show_edge_labels = st.checkbox(
                "Show labels on every connection",
                value=False,
                key="full_graph_edge_labels",
                help="This can clutter the complete graph. Hover over a connection to inspect its evidence details.",
            )

        if selected_node_types:
            st.caption(
                "Relationship direction and endpoint types: Plant → Compound; "
                "Compound → Target; Compound → Pathogen; Pathogen → Target. "
                "A connection appears only when both of its endpoint categories are selected."
            )

        load_full_graph = st.button(
            "Load Full Knowledge Graph",
            type="primary",
            width="stretch",
            key="load_full_graph",
        )

        full_signature = (
            tuple(selected_node_types),
            tuple(selected_relationship_types),
            int(max_relationships),
            bool(show_edge_labels),
        )

        if load_full_graph:
            if not selected_node_types:
                st.warning("Select at least one entity type.")
            elif not selected_relationship_types:
                st.warning("Select at least one relationship type.")
            else:
                try:
                    with st.spinner("Retrieving graph entities and relationships from Neo4j..."):
                        html = build_full_graph_html(
                            node_types=selected_node_types,
                            relationship_types=selected_relationship_types,
                            max_relationships=max_relationships,
                            show_edge_labels=show_edge_labels,
                        )
                    if html is None:
                        st.warning("No graph records matched the selected filters.")
                        st.session_state.pop("full_graph_html", None)
                        st.session_state.pop("full_graph_signature", None)
                    else:
                        st.session_state["full_graph_html"] = html
                        st.session_state["full_graph_signature"] = full_signature
                        st.session_state["full_graph_loaded"] = True
                except Exception as exc:
                    st.error(
                        "Full knowledge graph could not be generated: "
                        f"{type(exc).__name__}. Check the terminal for details."
                    )

        if st.session_state.get("full_graph_html"):
            if st.session_state.get("full_graph_signature") != full_signature:
                st.info("Your filters have changed. Select **Load Full Knowledge Graph** to update the visualization.")
            else:
                section_head(
                    "NETWORK CANVAS",
                    "Full Knowledge Graph",
                    "Search for a node in the graph using the FIND A NODE box inside the canvas. Hover over edges for their recorded evidence.",
                    meta="FULL GRAPH" if len(selected_node_types) == 4 else "FILTERED GRAPH",
                )
                st.components.v1.html(
                    st.session_state["full_graph_html"],
                    height=790,
                    scrolling=False,
                )
                if (
                    len(selected_node_types) == 4
                    and set(selected_relationship_types) == set(relationship_options)
                    and graph_stats
                ):
                    st.caption(
                        f"Complete dataset view: {graph_stats.get('nodes', '—'):,} nodes "
                        f"and {graph_stats.get('relationships', '—'):,} relationships, "
                        "subject to the selected relationship limit."
                    )
                else:
                    st.caption(
                        "Filtered graph view. Only selected entity and relationship types are displayed."
                    )
        else:
            show_html(
                '<div class="ph-panel" style="min-height:150px;display:flex;align-items:center;gap:18px;margin-top:20px">'
                f'<div class="ph-kpi-icon" style="width:50px;height:50px;flex-shrink:0">{icon("network")}</div>'
                '<div><h3>Explore the complete knowledge graph</h3>'
                '<p>Keep all filters selected and click Load Full Knowledge Graph to inspect the complete network.</p></div></div>'
            )

        caution(
            "The full graph shows recorded Neo4j relationships. Arrows follow the stored relationship direction. "
            "Node positions and edge lengths do not represent biological distance, interaction strength, confidence "
            "or evidence grade."
        )
        return

    # Search by Compound: all registered compounds, including compounds outside the scored subset.
    st.markdown(
        "Search the full compound registry (not just the 137 compounds with ranking scores), "
        "then load the selected compound's directly connected network."
    )
    if not database_online:
        st.error("Neo4j is unavailable. Check the configured AuraDB connection and retry.")
        return

    try:
        compound_records = cached_compound_options()
    except Exception as exc:
        st.error(f"Could not load the compound directory from Neo4j: {type(exc).__name__}")
        return

    if not compound_records:
        st.info("No registered compounds were returned by Neo4j.")
        return

    search_text = st.text_input(
        "Search by compound name or ID",
        placeholder="For example: Baicalein, Quercetin, Curcumin or CMP011",
        key="graph_compound_search_text",
    )
    search_lower = search_text.strip().casefold()
    filtered_compounds = [
        item for item in compound_records
        if not search_lower
        or search_lower in item["compound_name"].casefold()
        or search_lower in item["compound_id"].casefold()
    ]

    st.caption(
        f"{len(filtered_compounds):,} matching compounds out of {len(compound_records):,} registered in the graph."
    )
    if not filtered_compounds:
        st.warning("No compound matches that search. Try another name or compound ID.")
        return

    compound_labels = [
        f'{item["compound_name"]}  ·  {item["compound_id"]}'
        for item in filtered_compounds
    ]
    label_to_record = dict(zip(compound_labels, filtered_compounds))
    if st.session_state.get("graph_compound_choice") not in label_to_record:
        st.session_state.pop("graph_compound_choice", None)

    a, b = st.columns([2.2, 1.0], vertical_alignment="bottom", gap="medium")
    with a:
        selected_label = st.selectbox(
            "Choose a compound",
            options=compound_labels,
            key="graph_compound_choice",
        )
    with b:
        max_plants = st.slider(
            "Plant display limit",
            min_value=5,
            max_value=40,
            value=15,
            step=5,
            key="graph_max_plants",
        )

    selected_record = label_to_record[selected_label]
    selected_name = selected_record["compound_name"]
    selected_id = selected_record["compound_id"]
    requested = st.button(
        "Explore connections",
        type="primary",
        width="stretch",
        key="graph_explore",
    )

    compound_signature = (str(selected_id), int(max_plants))
    if requested:
        try:
            with st.spinner("Building the selected compound's evidence-linked network..."):
                html = build_graph_html(selected_id, max_plants=max_plants)
            if html is None:
                st.warning("No matching compound or graph record was found.")
                st.session_state.pop("compound_graph_html", None)
                st.session_state.pop("compound_graph_signature", None)
            else:
                st.session_state["compound_graph_html"] = html
                st.session_state["compound_graph_signature"] = compound_signature
        except Exception as exc:
            st.error(
                "Compound network visualization could not be generated: "
                f"{type(exc).__name__}. Check the terminal for details."
            )

    if st.session_state.get("compound_graph_html"):
        if st.session_state.get("compound_graph_signature") != compound_signature:
            st.info("Your selected compound or plant limit has changed. Select **Explore connections** to update the network.")
        else:
            section_head(
                "NETWORK CANVAS",
                selected_name,
                "The selected phytochemical and its directly connected plants, targets and pathogen records. Hover over each connection for the recorded evidence.",
                meta="COMPOUND NETWORK",
            )
            st.components.v1.html(
                st.session_state["compound_graph_html"],
                height=635,
                scrolling=False,
            )
            st.caption(
                "This is a compound-centred network, not the complete graph. "
                "Only direct relationships of the selected compound are shown."
            )
    else:
        show_html(
            '<div class="ph-panel" style="min-height:150px;display:flex;align-items:center;gap:18px;margin-top:25px">'
            f'<div class="ph-kpi-icon" style="width:50px;height:50px;flex-shrink:0">{icon("network")}</div>'
            '<div><h3>Search for a compound to build its network</h3>'
            '<p>Search all registered compounds by name or ID, select one, then choose Explore connections.</p></div></div>'
        )

    caution(
        "Relationship labels summarize records in the knowledge graph; they do not independently verify primary "
        "literature, prove physical binding, or demonstrate clinical effectiveness. Edge lengths and node positions "
        "are visualization choices, not measures of biological activity."
    )

# -----------------------------------------------------------------------------
# Page: AI Research Assistant — backend unchanged and safety screening retained.
# -----------------------------------------------------------------------------

EXAMPLES = (
    "What experimental evidence links Kaempferol to OXA-48?",
    "What evidence supports Isoliquiritin?",
    "What evidence supports Eugenol?",
    "Which compounds interact with NDM-1?",
    "Which phytochemicals interact with OXA-48?",
)


def show_assistant() -> None:
    page_intro(
        "DISCOVERY / 03", "Evidence Research Assistant",
        "Ask questions about recorded compound, pathogen and target relationships. The assistant retrieves Neo4j evidence before composing an explanation."
    )
    section_head("START WITH A QUESTION", "Suggested investigations", "Use a sample question or write a research question of your own.")
    x, y = st.columns(2, gap="small")
    for idx, text in enumerate(EXAMPLES):
        with (x if idx % 2 == 0 else y):
            if st.button(text, key=f"sample_{idx}", width="stretch"):
                st.session_state["ai_question"] = text
                st.rerun()

    with st.form("graphrag_form", clear_on_submit=False, border=True):
        question = st.text_area(
            "Your research question",
            key="ai_question",
            height=108,
            placeholder="For example: What experimental evidence links Kaempferol to OXA-48?",
        )
        provider = st.selectbox(
            "Explanation mode",
            options=["Groq (hosted AI)", "Evidence only", "Gemma on DGX (local only)"],
            key="rag_provider",
            help="Groq is hosted. Evidence-only does not use an LLM. DGX Gemma requires a locally configured and authorized connection.",
        )
        submitted = st.form_submit_button("Generate evidence-grounded answer", type="primary", width="stretch")

    if submitted:
        if not question.strip():
            st.warning("Enter a research question to continue.")
        elif not database_online:
            st.error("The Neo4j database is currently unavailable. Check the AuraDB connection and retry.")
        else:
            try:
                with st.spinner("Retrieving and assessing Neo4j evidence..."):
                    retrieval_answer, evidence = answer_question(question)
                    evidence = list(evidence or [])
                    classification, reason = detect_answerability(question, evidence)
                    if classification == "INSUFFICIENT":
                        answer = (
                            "The retrieved knowledge-graph records do not establish the requested claim. "
                            + reason
                            + " Review the available evidence; no clinical or numerical result should be inferred from unrelated measurements."
                        )
                        mode = "insufficient_evidence"
                    elif classification == "REVIEW_REQUIRED":
                        answer = (
                            "The retrieved evidence requires further review before answering this question. "
                            + reason + " Inspect the linked sources below."
                        )
                        mode = "review_required"
                    elif provider == "Groq (hosted AI)" and evidence:
                        answer, mode = generate_groq_answer(question, evidence, retrieval_answer)
                    elif provider == "Gemma on DGX (local only)" and evidence:
                        answer, mode = generate_local_answer(question, evidence, retrieval_answer)
                    else:
                        answer, mode = retrieval_answer, "evidence_only"
                st.session_state["rag_output"] = {
                    "question": question,
                    "answer": answer,
                    "evidence": evidence,
                    "classification": classification,
                    "reason": reason,
                    "mode": mode,
                    "provider": provider,
                }
            except Exception as exc:
                st.error(f"Research request failed: {type(exc).__name__}. Check the terminal for details.")

    result = st.session_state.get("rag_output")
    if not result:
        show_html(
            '<div class="ph-panel" style="margin-top:22px;display:flex;gap:15px;align-items:center">'
            f'<div class="ph-answer-icon" style="flex-shrink:0">{icon("spark")}</div>'
            '<div><h3>Built for traceable scientific questions</h3>'
            '<p>Generated answers are screened for unsupported claim types and accompanied by the underlying graph records.</p>'
            '</div></div>'
        )
        return

    section_head("RESEARCH OUTPUT", "Your evidence-grounded answer", "Read the interpretation alongside its original evidence records.")
    # Describe what actually produced the answer, not the mode chosen in the form.
    # In particular, unanswered clinical/binding questions never call Groq.
    mode = result.get("mode")
    answer_display = {
        "graph_lookup": (
            "Direct knowledge graph result", "Neo4j lookup · No LLM used", "network"
        ),
        "groq": (
            "GraphRAG research interpretation", "Groq (hosted AI) · Evidence-linked records", "spark"
        ),
        "gemma": (
            "GraphRAG research interpretation", "Gemma · Evidence-linked records", "spark"
        ),
        "insufficient_evidence": (
            "Evidence assessment", "Insufficient evidence · No LLM used", "shield"
        ),
        "review_required": (
            "Evidence review required", "Manual verification needed · No LLM used", "shield"
        ),
        "evidence_only": (
            "Evidence-only graph summary", "Neo4j retrieval · No LLM used", "network"
        ),
        "groq_unavailable": (
            "Evidence-only fallback", "Groq answer not accepted · Neo4j retrieval", "book"
        ),
        "gemma_unavailable": (
            "Evidence-only fallback", "Gemma answer not accepted · Neo4j retrieval", "book"
        ),
    }
    answer_title, answer_subtitle, answer_icon = answer_display.get(
        mode, ("Evidence retrieval summary", "Neo4j evidence records", "network")
    )
    show_html(
        f'<div class="ph-answer-head"><div class="ph-answer-icon">{icon(answer_icon)}</div>'
        f'<div class="ph-answer-copy"><strong>{escape(answer_title)}</strong>'
        f'<span>{escape(answer_subtitle)}</span></div></div>'
    )
    with st.container(border=True):
        st.markdown(result["answer"])

    classification = result.get("classification", "NOT_CHECKED")
    st.markdown(f"**Answerability screening:** `{classification}`")
    st.caption(
        str(result.get("reason") or "")
        + " Rule-based screening is provisional and does not verify every scientific claim."
    )

    mode = result.get("mode")
    if mode == "groq":
        st.success("Explanation generated by Groq using retrieved Neo4j evidence.", icon=None)
    elif mode == "groq_unavailable":
        st.warning("Groq was unavailable or its output failed basic evidence checks. Showing the Neo4j retrieval summary.", icon=None)
    elif mode == "gemma":
        st.success("Explanation generated by the configured Gemma backend.", icon=None)
    elif mode == "insufficient_evidence":
        st.warning("Insufficient evidence for the requested claim; no LLM was called.", icon=None)
    elif mode == "review_required":
        st.warning("Manual literature review required; no LLM was called.", icon=None)
    elif mode == "graph_lookup":
        st.info("Direct Neo4j answer: compound names and citations were retrieved from graph records. No LLM was required.", icon=None)
    elif mode == "evidence_only":
        st.info("Showing the Neo4j evidence-only result; no LLM was called.", icon=None)
    else:
        st.info("Showing the available evidence retrieval result.", icon=None)

    evidence = result.get("evidence") or []
    section_head("TRACEABILITY", "Supporting evidence", "Citation IDs refer to graph records, not necessarily different publications.", meta=f"{len(evidence)} {'RECORD' if len(evidence) == 1 else 'RECORDS'}")
    if not evidence:
        st.warning("No supporting evidence records were retrieved.")
    for idx, item in enumerate(evidence, start=1):
        compound = item.get("compound") or "Compound"
        entity = item.get("entity") or "Unknown entity"
        with st.expander(f"[E{idx}] {compound}  →  {entity}", expanded=(len(evidence) == 1)):
            for label, field in (
                ("Relationship", "relationship"),
                ("Evidence type", "evidence_type"),
                ("Activity", "activity"),
                ("Evidence category", "category"),
                ("Scientific finding", "finding"),
                ("Graph link ID", "link_id"),
            ):
                st.markdown(f"**{label}**")
                st.write(item.get(field) or "Not recorded")
            src = item.get("source")
            if isinstance(src, str) and src.startswith(("https://", "http://")):
                st.link_button("Open scientific source", url=src)
            else:
                st.caption("No source URL recorded for this relationship.")
    caution("AI explanations may contain unsupported inferences. Source links and retrieval records must be checked before claiming experimental verification or clinical relevance.")


# -----------------------------------------------------------------------------
# Page: methodology / research caveats
# -----------------------------------------------------------------------------


def show_about() -> None:
    page_intro(
        "DOCUMENTATION / METHODS", "About the Research",
        "An AI-assisted knowledge graph for exploring research associations among medicinal plants, phytochemicals, antimicrobial-resistant pathogens and molecular targets."
    )
    section_head("ARCHITECTURE", "How the research platform works", "An evidence-oriented pipeline with separate data, retrieval, prioritization and explanation layers.")
    show_html(
        '<div class="ph-steps">'
        f'<div class="ph-step"><div class="ph-step-no">01 / STRUCTURE</div><div class="ph-step-ico">{icon("network")}</div><div class="ph-step-title">Neo4j knowledge graph</div><div class="ph-step-text">Entities and relationships with recorded evidence fields and source identifiers.</div></div>'
        f'<div class="ph-step"><div class="ph-step-no">02 / PRIORITIZE</div><div class="ph-step-ico">{icon("activity")}</div><div class="ph-step-title">Evidence-priority scoring</div><div class="ph-step-text">An exploratory research index for 137 scored compounds, based on mapped evidence categories and record breadth.</div></div>'
        f'<div class="ph-step"><div class="ph-step-no">03 / EXPLAIN</div><div class="ph-step-ico">{icon("spark")}</div><div class="ph-step-title">Evidence-grounded GraphRAG</div><div class="ph-step-text">Question-specific Neo4j retrieval, answerability screening and optional LLM interpretation.</div></div>'
        '</div>'
    )
    show_scoring_guide()
    section_head("INTERPRETATION", "What this system can — and cannot — establish", "Scientific caution is a design requirement, not a footnote.")
    a, b = st.columns(2, gap="medium")
    with a:
        show_html(
            f'<div class="ph-panel">{icon("shield")}<h3 style="margin-top:12px">Designed to support</h3>'
            '<p>Literature-oriented candidate exploration, evidence traceability, identification of graph-linked targets, '
            'and generation of hypothesis-level research questions.</p></div>'
        )
    with b:
        show_html(
            f'<div class="ph-panel">{icon("book")}<h3 style="margin-top:12px">Not a clinical prediction tool</h3>'
            '<p>Links and heuristic scores do not prove physical target binding, in vivo activity, '
            'antimicrobial efficacy in patients, safety or regulatory suitability.</p></div>'
        )
    st.markdown("#### Data interpretation notes")
    st.markdown(
        "The database includes plant–compound occurrence links, compound–target and compound–pathogen evidence records, "
        "and pathogen–target associations. Their sources and evidence strengths vary. Literature records and systematic "
        "matching do not constitute independent validation of every individual claim."
    )
    st.markdown("#### Computational stack")
    st.markdown("**Streamlit** interface · **Neo4j AuraDB** graph storage · **Groq** optional hosted explanations · **PyVis** interactive network · **Evidence Priority Score (exploratory research index)**")
    caution("The prototype is intended for academic research and demonstration, not clinical or therapeutic decision-making.")


PAGE_HANDLERS = {
    "overview": show_overview,
    "rankings": show_rankings,
    "graph": show_graph,
    "assistant": show_assistant,
    "about": show_about,
}
PAGE_HANDLERS.get(st.session_state.current_page, show_overview)()

show_html(
    '<div class="ph-footer"><span>PHYTOGRAPH RESEARCH ATLAS &nbsp; / &nbsp; ANTI-AMR PHYTOCHEMICAL DISCOVERY</span>'
    '<span>Neo4j · Evidence Priority Scores · AI-assisted Research</span></div>'
)
