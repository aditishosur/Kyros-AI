import streamlit as st


PLOT_BG = "#0b1726"
PANEL = "#101d2d"
PANEL_2 = "#142338"
TEXT = "#eef6ff"
MUTED = "#8fa4b9"
CYAN = "#62d3ff"
BLUE = "#86a8cf"
PINK = "#c38eb4"
ROSE = "#e1c8d7"
RED = "#ff6b7a"
ORANGE = "#f7b267"
GREEN = "#6ee7a8"


def apply_theme() -> None:
    st.set_page_config(page_title="PulseOps", page_icon="PulseOps", layout="wide", initial_sidebar_state="expanded")
    st.markdown(
        """
        <style>
        :root {
            --bg: #081320;
            --panel: #101d2d;
            --panel2: #142338;
            --line: rgba(134,168,207,.24);
            --text: #eef6ff;
            --muted: #8fa4b9;
            --cyan: #62d3ff;
            --pink: #c38eb4;
            --rose: #e1c8d7;
            --red: #ff6b7a;
            --orange: #f7b267;
            --green: #6ee7a8;
        }
        .stApp {
            background:
                radial-gradient(circle at 16% 8%, rgba(195,142,180,.18), transparent 26%),
                radial-gradient(circle at 78% 0%, rgba(98,211,255,.12), transparent 25%),
                linear-gradient(180deg, #081320 0%, #0b1726 55%, #08111d 100%);
            color: var(--text);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #091522 0%, #0c1724 100%);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * { color: var(--text); }
        .block-container { padding: 1.4rem 2.1rem 3rem; max-width: 1520px; }
        h1, h2, h3 { letter-spacing: 0; color: var(--text); }
        h1 { font-size: 2.35rem; margin-bottom: .3rem; }
        h2 { font-size: 1.35rem; margin-top: 1.2rem; }
        h3 { font-size: 1.05rem; }
        p, label, span { color: inherit; }
        .muted { color: var(--muted); }
        .brand {
            padding: 1rem .75rem 1.25rem;
            border-bottom: 1px solid var(--line);
            margin-bottom: .9rem;
        }
        .brand .name {
            font-size: 1.24rem;
            font-weight: 800;
            letter-spacing: .08em;
        }
        .brand .tag { color: var(--muted); font-size: .82rem; margin-top: .12rem; }
        .side-status {
            margin-top: 2.2rem;
            padding: .9rem;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(16,29,45,.72);
            font-size: .82rem;
        }
        .panel {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(20,35,56,.94), rgba(12,24,39,.94));
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 16px 48px rgba(0,0,0,.28);
        }
        .hero {
            min-height: 560px;
            display: grid;
            grid-template-columns: minmax(0, 1.04fr) minmax(360px, .96fr);
            gap: 2rem;
            align-items: center;
            padding: 2rem 0 1rem;
        }
        .hero-title {
            font-size: clamp(3rem, 5vw, 5.8rem);
            line-height: .92;
            font-weight: 900;
            color: var(--text);
            margin: .2rem 0 .9rem;
        }
        .eyebrow {
            color: var(--cyan);
            text-transform: uppercase;
            letter-spacing: .14em;
            font-size: .78rem;
            font-weight: 800;
        }
        .hero-copy { color: #bbcada; font-size: 1.08rem; max-width: 720px; line-height: 1.65; }
        .flow-card {
            border-radius: 8px;
            border: 1px solid rgba(225,200,215,.28);
            padding: 1rem;
            background: linear-gradient(180deg, rgba(195,142,180,.16), rgba(20,35,56,.72));
            box-shadow: 0 24px 70px rgba(0,0,0,.38);
        }
        .flow-node {
            margin: .72rem 0;
            padding: .86rem 1rem;
            border-radius: 999px;
            border: 1px solid rgba(134,168,207,.32);
            background: linear-gradient(90deg, rgba(8,19,32,.95), rgba(134,168,207,.20));
            display: flex;
            justify-content: space-between;
            align-items: center;
            min-height: 54px;
        }
        .flow-node strong { color: var(--text); }
        .flow-node span { color: var(--muted); font-size: .78rem; }
        .kpi, .feature-card, .attention-card, .metric-card {
            border: 1px solid var(--line);
            background: rgba(16,29,45,.88);
            border-radius: 8px;
            padding: 1rem;
            min-height: 112px;
        }
        .kpi .label, .metric-card .label { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
        .kpi .value { font-size: 1.75rem; font-weight: 800; margin: .25rem 0; color: var(--text); }
        .kpi .trend { color: var(--cyan); font-size: .84rem; }
        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: .22rem .58rem;
            font-size: .72rem;
            font-weight: 800;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .badge-healthy { color: var(--green); border-color: rgba(110,231,168,.35); background: rgba(110,231,168,.08); }
        .badge-degraded { color: var(--orange); border-color: rgba(247,178,103,.35); background: rgba(247,178,103,.08); }
        .badge-critical { color: var(--red); border-color: rgba(255,107,122,.38); background: rgba(255,107,122,.09); }
        .risk-score {
            height: 12px;
            border-radius: 999px;
            background: #0a1421;
            overflow: hidden;
            border: 1px solid var(--line);
        }
        .risk-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--green), var(--orange), var(--red)); }
        .chain {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: .7rem;
            align-items: stretch;
        }
        .chain-node {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .9rem;
            background: linear-gradient(180deg, rgba(20,35,56,.95), rgba(8,19,32,.95));
            min-height: 128px;
        }
        .chain-node .num { font-size: 1.55rem; font-weight: 900; color: var(--cyan); margin-top: .4rem; }
        .sim-grid {
            display: grid;
            grid-template-columns: minmax(300px, .82fr) minmax(460px, 1.18fr);
            gap: 1rem;
            align-items: start;
        }
        .compare {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .85rem;
        }
        .dataframe, [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
        .stButton>button, .stDownloadButton>button {
            border-radius: 8px;
            border: 1px solid rgba(98,211,255,.42);
            background: linear-gradient(90deg, rgba(98,211,255,.22), rgba(195,142,180,.20));
            color: var(--text);
            font-weight: 800;
            min-height: 2.55rem;
        }
        .stButton>button:hover { border-color: var(--cyan); color: white; }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background-color: rgba(16,29,45,.92);
            border-color: rgba(134,168,207,.35);
            color: var(--text);
            border-radius: 8px;
        }
        @media (max-width: 980px) {
            .hero, .sim-grid, .compare { grid-template-columns: 1fr; }
            .chain { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    cls = "badge-healthy"
    if status.lower() == "critical":
        cls = "badge-critical"
    elif status.lower() == "degraded":
        cls = "badge-degraded"
    return f'<span class="badge {cls}">{status.upper()}</span>'


def kpi(label: str, value: str, trend: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="trend">{trend}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric(label: str, value: str, status: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value" style="font-size:1.45rem;font-weight:800;margin-top:.35rem;">{value}</div>
            <div class="muted" style="font-size:.82rem;margin-top:.25rem;">{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_bar(score: float) -> str:
    return f"""
    <div style="display:flex;align-items:center;gap:.8rem;">
        <div class="risk-score" style="flex:1;"><div class="risk-fill" style="width:{min(max(score,0),100)}%;"></div></div>
        <strong>{score:.0f}</strong>
    </div>
    """

