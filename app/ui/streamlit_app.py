"""Streamlit executive dashboard for ExecMind AI.

This UI layer is deliberately isolated from backend agent logic and focuses
on presenting the generated report through a clean executive dashboard.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.manager_agent import build_report
from app.mcp.report_tools import export_json, export_markdown, export_text
from app.utils.file_utils import parse_uploaded_file


st.set_page_config(page_title="ExecMind AI", page_icon=None, layout="wide")

# ---------------------------------------------------------------------------
# Design System
# ---------------------------------------------------------------------------
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root {
    --bg-base: #06090f;
    --bg-card: #101722;
    --bg-card-elevated: #151d2b;
    --border: #223042;
    --text-primary: #f4f7fb;
    --text-secondary: #a4b0bf;
    --text-muted: #74829a;
    --accent: #4f7cff;
    --accent-soft: rgba(79,124,255,.16);
    --success: #2fbf71;
    --warning: #f0b429;
    --danger: #ef5d5d;
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --shadow: 0 1px 2px rgba(0,0,0,.24), 0 10px 32px rgba(0,0,0,.24);
}
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}
.stApp { background-color: var(--bg-base); }
.block-container { padding: 2.2rem 2.4rem 3rem !important; max-width: 1280px !important; }

.em-header {
    border-bottom: 1px solid var(--border);
    padding: 1rem 0 1.4rem;
    margin-bottom: 1.5rem;
}
.em-header-title {
    font-size: clamp(2.4rem, 4.2vw, 4.2rem);
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -.04em;
    line-height: 0.95;
    margin: 0 0 .45rem;
}
.em-header-sub {
    font-size: 1rem;
    color: var(--text-secondary);
    margin: 0;
    max-width: 700px;
    line-height: 1.55;
}

.em-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.35rem 1.45rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
}
.em-card-accent {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: var(--radius-lg);
    padding: 1.35rem 1.45rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
}
.em-section-label {
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 .85rem;
}
.em-section-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 1rem;
}
.em-helper-text {
    font-size: .9rem;
    color: var(--text-muted);
    margin-top: .25rem;
}
.em-spacer { height: 1.1rem; }
.em-spacer-sm { height: .6rem; }

.em-kpi {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1rem 1.1rem;
    height: 100%;
    overflow: hidden;
}
.em-kpi-label {
    font-size: .72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--text-muted);
    margin-bottom: .45rem;
}
.em-kpi-value {
    display: flex;
    align-items: center;
    gap: .6rem;
    flex-wrap: wrap;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -.02em;
    line-height: 1.1;
}
.em-kpi-suffix {
    font-size: .95rem;
    font-weight: 500;
    color: var(--text-muted);
}

.em-badge {
    display: inline-block;
    padding: .22rem .6rem;
    border-radius: 999px;
    font-size: .72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
}
.em-badge-healthy { background: rgba(47,191,113,.14); color: var(--success); border: 1px solid rgba(47,191,113,.28); }
.em-badge-moderate { background: rgba(240,180,41,.14); color: var(--warning); border: 1px solid rgba(240,180,41,.28); }
.em-badge-critical { background: rgba(239,93,93,.14); color: var(--danger); border: 1px solid rgba(239,93,93,.28); }

.em-summary-point {
    display: flex;
    align-items: flex-start;
    gap: .6rem;
    padding: .5rem 0;
    border-bottom: 1px solid var(--border);
    font-size: .9rem;
    color: var(--text-primary);
    line-height: 1.55;
}
.em-summary-point:last-child { border-bottom: none; }
.em-summary-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); margin-top: .45rem; flex-shrink: 0; }

.em-list-item {
    display: flex;
    align-items: flex-start;
    gap: .6rem;
    padding: .45rem 0;
    font-size: .9rem;
    color: var(--text-secondary);
    line-height: 1.5;
    border-bottom: 1px solid var(--border);
}
.em-list-item:last-child { border-bottom: none; }
.em-list-marker { color: var(--accent); font-weight: 600; flex-shrink: 0; font-size: .85rem; }

.em-divider { border: none; border-top: 1px solid var(--border); margin: 1.3rem 0; }

.em-step {
    background: var(--bg-card-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: .75rem .9rem;
    text-align: center;
}
.em-step-label { font-size: .78rem; font-weight: 600; color: var(--text-primary); margin-bottom: .25rem; }
.em-step-status { font-size: .68rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .06em; }

.em-upload-card {
    background: var(--bg-card-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1rem 1.1rem;
    margin-top: .8rem;
}
.em-upload-title { font-size: .95rem; font-weight: 600; color: var(--text-primary); margin-bottom: .65rem; }
.em-upload-meta { display: grid; gap: .45rem; }
.em-upload-stat { display: flex; justify-content: space-between; gap: 1rem; font-size: .9rem; color: var(--text-secondary); }
.em-upload-label { color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; font-size: .7rem; }

.em-downloads { display: flex; gap: .75rem; flex-wrap: wrap; }

[data-testid="stMetric"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; padding: 1rem 1.1rem !important; }
[data-testid="stMetricLabel"] { font-size: .72rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: .08em !important; color: var(--text-muted) !important; }
[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700 !important; color: var(--text-primary) !important; }
[data-testid="stDataFrame"] { border-radius: var(--radius-md) !important; border: 1px solid var(--border) !important; overflow: hidden !important; }

[data-testid="stTabs"] [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid var(--border) !important; gap: 0 !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: transparent !important; border: none !important; padding: .55rem 1.05rem !important; font-size: .82rem !important; font-weight: 500 !important; color: var(--text-secondary) !important; }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] { padding: 1.1rem 0 0 !important; }

[data-testid="stButton"] > button { background: var(--accent) !important; border: none !important; border-radius: var(--radius-sm) !important; color: #fff !important; font-size: .82rem !important; font-weight: 600 !important; padding: .58rem 1.2rem !important; }
[data-testid="stDownloadButton"] > button { background: var(--bg-card-elevated) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important; color: var(--text-primary) !important; font-size: .8rem !important; font-weight: 500 !important; width: 100% !important; }

[data-testid="stExpander"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; }
[data-testid="stExpander"] summary { font-size: .82rem !important; font-weight: 500 !important; color: var(--text-secondary) !important; padding: .75rem 1rem !important; }

[data-testid="stAlert"] { border-radius: var(--radius-md) !important; border-left-width: 3px !important; font-size: .85rem !important; }
[data-testid="stCaptionContainer"] { font-size: .78rem !important; color: var(--text-muted) !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _format_currency(value: Any) -> str:
    """Format numeric values as currency for executive summaries."""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _format_number(value: Any) -> str:
    """Format numeric values as readable integers or floats."""
    try:
        if float(value).is_integer():
            return f"{int(float(value)):,}"
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _health_score(report: Dict[str, Any]) -> int:
    """Read the generated business health score, with a legacy fallback."""
    financial = report.get("financial_assessment", {})
    score = financial.get("business_health_score")
    if isinstance(score, (int, float)):
        return max(0, min(100, int(round(float(score)))))

    health = str(report.get("business_health", "Healthy")).lower()
    if health == "critical":
        return 35
    if health == "moderate":
        return 65
    return 85


def _health_badge_class(health: str) -> str:
    """Return the CSS class for the health badge."""
    h = health.lower()
    if h == "critical":
        return "em-badge-critical"
    if h == "moderate":
        return "em-badge-moderate"
    return "em-badge-healthy"


def _export_report_files(report: Dict[str, Any]) -> Dict[str, str]:
    """Export the report into JSON, Markdown, and Text files using MCP helpers."""
    temp_dir = tempfile.gettempdir()
    export_dir = os.path.join(temp_dir, "execmind_exports")
    os.makedirs(export_dir, exist_ok=True)
    stem = f"executive_report_{uuid.uuid4().hex}"
    return {
        "json": export_json(report, os.path.join(export_dir, f"{stem}.json")),
        "markdown": export_markdown(report, os.path.join(export_dir, f"{stem}.md")),
        "text": export_text(report, os.path.join(export_dir, f"{stem}.txt")),
    }


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------

def _render_header() -> None:
    """Render the premium page header."""
    st.markdown(
        '''<div class="em-header">
            <h1 class="em-header-title">ExecMind AI</h1>
            <p class="em-header-sub">An Autonomous Multi-Agent Business Strategy & Decision Intelligence Platform</p>
        </div>''',
        unsafe_allow_html=True,
    )


def _render_kpis(report: Dict[str, Any]) -> None:
    """Render the four KPI cards with consistent scale and spacing."""
    sales = report.get("sales_insights", {})
    health = str(report.get("business_health", "Healthy"))
    score = _health_score(report)
    badge_cls = _health_badge_class(health)

    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        st.markdown(
            f'''<div class="em-kpi">
                <div class="em-kpi-label">Total Revenue</div>
                <div class="em-kpi-value">{_format_currency(sales.get("total_sales", 0))}</div>
            </div>''',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'''<div class="em-kpi">
                <div class="em-kpi-label">Total Orders</div>
                <div class="em-kpi-value">{_format_number(sales.get("total_orders", 0))}</div>
            </div>''',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'''<div class="em-kpi">
                <div class="em-kpi-label">Avg. Order Value</div>
                <div class="em-kpi-value">{_format_currency(sales.get("average_order_value", 0))}</div>
            </div>''',
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f'''<div class="em-kpi">
                <div class="em-kpi-label">Health Score</div>
                <div class="em-kpi-value">
                    <span>{score}</span>
                    <span class="em-kpi-suffix">/ 100</span>
                    <span class="em-badge {badge_cls}">{health}</span>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )


def _render_executive_summary(report: Dict[str, Any]) -> None:
    """Render executive summary inside a highlighted accent card."""
    points = report.get("executive_summary", [])
    pts = "".join(
        f'''<div class="em-summary-point">
                <div class="em-summary-dot"></div>
                <span>{p}</span>
            </div>'''
        for p in points
    )
    st.markdown(
        f'''<div class="em-card-accent">
            <p class="em-section-label">Executive Summary</p>
            {pts}
        </div>''',
        unsafe_allow_html=True,
    )


def _render_execution_flow() -> None:
    """Render the multi-agent pipeline as a compact orchestration footer."""
    steps = [
        ("Sales Agent", "Completed"),
        ("Marketing Agent", "Completed"),
        ("Finance Agent", "Completed"),
        ("Manager Agent", "Completed"),
    ]
    cols = st.columns(4, gap="small")
    for col, (label, status) in zip(cols, steps):
        with col:
            st.markdown(
                f'''<div class="em-step">
                    <div class="em-step-label">{label}</div>
                    <div class="em-step-status">{status}</div>
                </div>''',
                unsafe_allow_html=True,
            )


def _render_analysis_tabs(report: Dict[str, Any]) -> None:
    """Render Sales / Marketing / Finance output tabs."""
    sales_insights = report.get("sales_insights", {})
    marketing = report.get("marketing_recommendations", {})
    financial = report.get("financial_assessment", {})

    sales_tab, marketing_tab, finance_tab = st.tabs(["Sales", "Marketing", "Finance"])

    with sales_tab:
        st.markdown('<p class="em-section-title">Sales Insights</p>', unsafe_allow_html=True)
        observations = sales_insights.get("key_observations", [])
        if observations:
            items = "".join(
                f'<div class="em-list-item"><span class="em-list-marker">&#8212;</span><span>{o}</span></div>'
                for o in observations
            )
            st.markdown(items, unsafe_allow_html=True)

        if sales_insights.get("top_products_by_revenue"):
            st.markdown(
                '<p class="em-section-label" style="margin-top:1.25rem;">Top Products by Revenue</p>',
                unsafe_allow_html=True,
            )
            product_df = pd.DataFrame(
                {
                    "Product": list(sales_insights["top_products_by_revenue"].keys()),
                    "Revenue": list(sales_insights["top_products_by_revenue"].values()),
                }
            )
            st.dataframe(product_df, use_container_width=True, hide_index=True)

    with marketing_tab:
        st.markdown('<p class="em-section-title">Marketing Recommendations</p>', unsafe_allow_html=True)

        promotions = marketing.get("suggested_promotions", [])[:3]
        if promotions:
            st.markdown('<p class="em-section-label">Suggested Promotions</p>', unsafe_allow_html=True)
            for promo in promotions:
                text = (
                    f"{promo.get('campaign_type', 'Campaign')} -- "
                    f"{promo.get('promotion_detail', 'No details available')}"
                )
                st.markdown(
                    f'<div class="em-list-item"><span class="em-list-marker">&#8212;</span><span>{text}</span></div>',
                    unsafe_allow_html=True,
                )

        cross_sells = marketing.get("cross_sell_opportunities", [])[:3]
        if cross_sells:
            st.markdown(
                '<p class="em-section-label" style="margin-top:1.25rem;">Cross-Sell Opportunities</p>',
                unsafe_allow_html=True,
            )
            for cs in cross_sells:
                text = f"Bundle '{cs.get('product_1')}' with '{cs.get('product_2')}' to increase basket value"
                st.markdown(
                    f'<div class="em-list-item"><span class="em-list-marker">&#8212;</span><span>{text}</span></div>',
                    unsafe_allow_html=True,
                )

    with finance_tab:
        st.markdown('<p class="em-section-title">Financial Assessment</p>', unsafe_allow_html=True)

        revenue_health = financial.get("revenue_health", {})
        st.markdown(
            f'''<div style="display:flex;gap:1.5rem;margin-bottom:1rem;">
                <div>
                    <span style="font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;color:var(--text-muted);">Revenue Status</span><br>
                    <span style="font-size:.9rem;font-weight:600;color:var(--text-primary);">{revenue_health.get("status", "Stable")}</span>
                </div>
                <div>
                    <span style="font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;color:var(--text-muted);">Trend</span><br>
                    <span style="font-size:.9rem;font-weight:600;color:var(--text-primary);">{revenue_health.get("trend", "Stable")}</span>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )

        observations = financial.get("profitability_observations", [])[:3]
        if observations:
            st.markdown('<p class="em-section-label">Profitability Observations</p>', unsafe_allow_html=True)
            for obs in observations:
                st.markdown(
                    f'<div class="em-list-item"><span class="em-list-marker">&#8212;</span><span>{obs}</span></div>',
                    unsafe_allow_html=True,
                )


def _render_health_and_risks(report: Dict[str, Any]) -> None:
    """Render Business Health and Risks side-by-side."""
    left_col, right_col = st.columns([1, 2], gap="medium")

    with left_col:
        health = str(report.get("business_health", "Healthy"))
        score = _health_score(report)
        badge_cls = _health_badge_class(health)
        st.markdown(
            f'''<div class="em-card" style="height:100%;">
                <p class="em-section-label">Business Health</p>
                <div style="text-align:center;padding:1rem 0;">
                    <div style="font-size:3rem;font-weight:700;color:var(--text-primary);letter-spacing:-.04em;line-height:1;">{score}</div>
                    <div style="font-size:.78rem;color:var(--text-muted);margin:.3rem 0 .75rem;">/ 100</div>
                    <span class="em-badge {badge_cls}">{health}</span>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )

    with right_col:
        risks = report.get("overall_risks", [])
        st.markdown(
            '<div class="em-card"><p class="em-section-label">Risk Register</p>',
            unsafe_allow_html=True,
        )
        no_critical = not risks or risks[0].get("risk_type") == "No Critical Risks Detected"
        if not no_critical:
            risk_df = pd.DataFrame(risks)[["risk_type", "severity", "source", "description"]]
            risk_df.columns = ["Risk Type", "Severity", "Source", "Description"]
            st.dataframe(risk_df, use_container_width=True, hide_index=True)
        else:
            st.success("No significant risks flagged.")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_priorities_and_steps(report: Dict[str, Any]) -> None:
    """Render Top Priorities and Next Steps side-by-side."""
    left_col, right_col = st.columns(2, gap="medium")

    with left_col:
        priorities = report.get("top_priorities", [])
        items = "".join(
            f'''<div class="em-list-item">
                    <span class="em-list-marker" style="min-width:1.1rem;text-align:right;">{i}.</span>
                    <span>{p}</span>
                </div>'''
            for i, p in enumerate(priorities, start=1)
        )
        st.markdown(
            f'<div class="em-card"><p class="em-section-label">Top Priorities</p>{items}</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        steps = report.get("recommended_next_steps", [])
        items = "".join(
            f'<div class="em-list-item"><span class="em-list-marker">&#8212;</span><span>{s}</span></div>'
            for s in steps
        )
        st.markdown(
            f'<div class="em-card"><p class="em-section-label">Recommended Next Steps</p>{items}</div>',
            unsafe_allow_html=True,
        )


def _render_downloads(report: Dict[str, Any]) -> None:
    """Render the export download buttons as a polished footer action block."""
    export_paths = _export_report_files(report)
    st.markdown('<hr class="em-divider">', unsafe_allow_html=True)
    st.markdown('<p class="em-section-label">Downloads</p>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3, gap="small")
    with d1:
        with open(export_paths["json"], "rb") as handle:
            st.download_button(
                label="Download JSON",
                data=handle.read(),
                file_name="executive_report.json",
                mime="application/json",
                use_container_width=True,
            )
    with d2:
        with open(export_paths["markdown"], "rb") as handle:
            st.download_button(
                label="Download Markdown",
                data=handle.read(),
                file_name="executive_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
    with d3:
        with open(export_paths["text"], "rb") as handle:
            st.download_button(
                label="Download Text",
                data=handle.read(),
                file_name="executive_report.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Main report renderer
# ---------------------------------------------------------------------------

def render_report(report: Dict[str, Any]) -> None:
    """Render the generated executive report in structured UI sections."""
    if not report:
        st.info("No report is available yet. Upload a dataset and run analysis.")
        return

    _render_kpis(report)
    st.markdown('<div class="em-spacer"></div>', unsafe_allow_html=True)
    _render_executive_summary(report)
    st.markdown('<div class="em-spacer"></div>', unsafe_allow_html=True)
    _render_health_and_risks(report)
    _render_priorities_and_steps(report)
    st.markdown('<div class="em-spacer"></div>', unsafe_allow_html=True)

    st.markdown('<p class="em-section-label">Agent Analysis</p>', unsafe_allow_html=True)
    _render_analysis_tabs(report)

    st.markdown('<div class="em-spacer-sm"></div>', unsafe_allow_html=True)
    st.markdown('<p class="em-section-label">Execution Pipeline</p>', unsafe_allow_html=True)
    _render_execution_flow()
    st.markdown('<div class="em-spacer"></div>', unsafe_allow_html=True)
    _render_downloads(report)


# ---------------------------------------------------------------------------
# App shell
# ---------------------------------------------------------------------------

def render_app() -> None:
    """Render the executive dashboard layout with isolated sections."""
    _render_header()

    st.markdown('<p class="em-section-label">Data Source</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload sales data (CSV or Excel)",
        type=["csv", "xlsx", "xls"],
        key="sales_data_uploader",
        help="Upload your small business sales records in CSV or Excel format.",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        try:
            df = parse_uploaded_file(uploaded_file)
            st.markdown(
                f'''<div class="em-upload-card">
                    <div class="em-upload-title">Dataset ready for analysis</div>
                    <div class="em-upload-meta">
                        <div class="em-upload-stat"><span class="em-upload-label">File</span><span>{uploaded_file.name}</span></div>
                        <div class="em-upload-stat"><span class="em-upload-label">Rows</span><span>{len(df):,}</span></div>
                        <div class="em-upload-stat"><span class="em-upload-label">Columns</span><span>{len(df.columns)}</span></div>
                        <div class="em-upload-stat"><span class="em-upload-label">Status</span><span>Upload successful</span></div>
                    </div>
                </div>''',
                unsafe_allow_html=True,
            )

            with st.expander("View Dataset", expanded=False):
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown('<div class="em-spacer-sm"></div>', unsafe_allow_html=True)
            btn_col, _ = st.columns([2, 5])
            with btn_col:
                if st.button("Analyze Business", type="primary", use_container_width=True):
                    with st.spinner("Running autonomous analysis -- Sales, Marketing, Finance..."):
                        try:
                            report = build_report(df)
                            st.session_state["report"] = report
                        except Exception as exc:  # pragma: no cover - UI safety guard
                            st.session_state["report"] = None
                            st.error(f"Analysis failed: {exc}")

        except ValueError as exc:
            st.error(f"Failed to process file: {str(exc)}")
    else:
        st.markdown(
            '<p class="em-helper-text">Accepted formats: CSV, XLSX, XLS</p>',
            unsafe_allow_html=True,
        )

    if st.session_state.get("report"):
        st.markdown('<div class="em-spacer"></div>', unsafe_allow_html=True)
        render_report(st.session_state["report"])


with st.container():
    render_app()
