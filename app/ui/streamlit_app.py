"""Streamlit executive dashboard for ExecMind AI.

Preserves the existing upload flow while presenting a professional, dark-theme
business analysis experience that coordinates the specialist agents and the
manager synthesis layer.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from typing import Any, Dict

import pandas as pd
import streamlit as st

from app.agents.manager_agent import build_report
from app.mcp.report_tools import export_json, export_markdown, export_text
from app.utils.file_utils import parse_uploaded_file


st.set_page_config(page_title="ExecMind AI", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    .stApp {
        background: linear-gradient(135deg, #07111f 0%, #0d1728 45%, #111827 100%);
        color: #f8fafc;
    }
    .stApp, .stMarkdown, div, span, label, p, button, .stTextInput, .stSelectbox {
        font-family: 'Outfit', sans-serif !important;
    }
    .main-title {
        font-weight: 700;
        background: linear-gradient(90deg, #5ee7ff, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0.1rem;
    }
    .tagline {
        color: #9aa7bb;
        font-size: 1.15rem;
        margin-bottom: 1.5rem;
        font-weight: 300;
    }
    .panel-card {
        background: rgba(12, 18, 31, 0.88);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
    }
    .section-header {
        color: #f8fafc;
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .health-pill {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.9rem;
        background: rgba(94, 231, 255, 0.15);
        color: #5ee7ff;
        border: 1px solid rgba(94, 231, 255, 0.25);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.7rem !important;
        font-weight: 600 !important;
        color: #f8fafc !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 400 !important;
        color: #9aa7bb !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def _render_report_sections(report: Dict[str, Any]) -> None:
    """Render the executive business report into professional dashboard sections."""
    if not report:
        st.info("No report is available yet. Upload a dataset and run analysis.")
        return

    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    st.markdown(f"<div class='health-pill'>Business Health: {report.get('business_health', 'Healthy')}</div>", unsafe_allow_html=True)
    for summary_item in report.get("executive_summary", []):
        st.write(f"• {summary_item}")

    st.markdown("---")
    st.markdown('<div class="section-header">Business Health</div>', unsafe_allow_html=True)
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        st.metric("Business Health", report.get("business_health", "Healthy"))
    with hc2:
        finance_assessment = report.get("financial_assessment", {})
        revenue_health = finance_assessment.get("revenue_health", {})
        st.metric("Revenue Status", revenue_health.get("status", "Stable"))
    with hc3:
        st.metric("Risk Count", len(report.get("overall_risks", [])))

    st.markdown("---")
    st.markdown('<div class="section-header">KPI Cards</div>', unsafe_allow_html=True)
    sales_insights = report.get("sales_insights", {})
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Sales", _format_currency(sales_insights.get("total_sales", 0)))
    with k2:
        st.metric("Total Orders", _format_number(sales_insights.get("total_orders", 0)))
    with k3:
        st.metric("Average Order Value", _format_currency(sales_insights.get("average_order_value", 0)))
    with k4:
        st.metric("Top Priority Count", len(report.get("top_priorities", [])))

    st.markdown("---")
    st.markdown('<div class="section-header">Sales Insights</div>', unsafe_allow_html=True)
    if sales_insights.get("key_observations"):
        for observation in sales_insights.get("key_observations", []):
            st.write(f"• {observation}")
    if sales_insights.get("top_products_by_revenue"):
        top_products = pd.DataFrame(
            {
                "Product": list(sales_insights.get("top_products_by_revenue", {}).keys()),
                "Revenue": list(sales_insights.get("top_products_by_revenue", {}).values()),
            }
        )
        st.dataframe(top_products, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="section-header">Marketing Recommendations</div>', unsafe_allow_html=True)
    marketing = report.get("marketing_recommendations", {})
    for promotion in marketing.get("suggested_promotions", [])[:3]:
        st.write(f"• {promotion.get('campaign_name', 'Campaign')} - {promotion.get('target_segment', 'segment')} | Discount: {promotion.get('discount_percentage', 0)}%")
    for cross_sell in marketing.get("cross_sell_opportunities", [])[:3]:
        st.write(f"• Bundle {cross_sell.get('product_1')} with {cross_sell.get('product_2')} for higher basket value")

    st.markdown("---")
    st.markdown('<div class="section-header">Financial Assessment</div>', unsafe_allow_html=True)
    financial = report.get("financial_assessment", {})
    revenue_health = financial.get("revenue_health", {})
    st.write(f"• Revenue status: {revenue_health.get('status', 'Stable')}")
    st.write(f"• Trend: {revenue_health.get('trend', 'Stable')}")
    for observation in financial.get("profitability_observations", [])[:3]:
        st.write(f"• {observation}")

    st.markdown("---")
    st.markdown('<div class="section-header">Risks</div>', unsafe_allow_html=True)
    risks = report.get("overall_risks", [])
    if risks:
        risk_df = pd.DataFrame(risks)
        st.dataframe(risk_df[["risk_type", "severity", "source", "description"]], use_container_width=True)
    else:
        st.write("No significant risks flagged.")

    st.markdown("---")
    st.markdown('<div class="section-header">Top Priorities</div>', unsafe_allow_html=True)
    for priority in report.get("top_priorities", []):
        st.write(f"• {priority}")

    st.markdown("---")
    st.markdown('<div class="section-header">Recommended Next Steps</div>', unsafe_allow_html=True)
    for step in report.get("recommended_next_steps", []):
        st.write(f"• {step}")


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


st.markdown('<div class="main-title">ExecMind AI</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Autonomous executive intelligence for modern businesses</div>', unsafe_allow_html=True)
st.info("Upload sales data to begin the analysis workflow.")

uploaded_file = st.file_uploader(
    "Upload sales data",
    type=["csv", "xlsx", "xls"],
    key="sales_data_uploader",
    help="Upload your small business sales records in CSV or Excel format.",
)

if uploaded_file is not None:
    try:
        df = parse_uploaded_file(uploaded_file)
        st.session_state["uploaded_df"] = df
        st.success(f"Successfully loaded '{uploaded_file.name}'!")

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total Records", f"{df.shape[0]:,}")
        with metric_col2:
            st.metric("Total Attributes", df.shape[1])
        with metric_col3:
            st.metric("Columns", ", ".join(list(df.columns)[:4]) + ("..." if len(df.columns) > 4 else ""))

        with st.expander("View raw dataset", expanded=False):
            st.dataframe(df, use_container_width=True)

        st.markdown("---")
        analyze_clicked = st.button("Analyze Business", type="primary", use_container_width=True)

        if analyze_clicked:
            st.session_state["analysis_report"] = None
            with st.status("Executing analysis workflow", expanded=True) as status:
                st.write("Sales → analyzing performance, revenue trend, and order mix")
                status.update(label="Sales analysis complete", state="complete")
                st.write("Marketing → identifying promotion and cross-sell opportunities")
                status.update(label="Marketing analysis complete", state="complete")
                st.write("Finance → evaluating revenue health and financial risks")
                status.update(label="Finance analysis complete", state="complete")
                st.write("Manager → synthesizing the executive business report")
                report = build_report(df)
                st.session_state["analysis_report"] = report
                status.update(label="Executive report generated", state="complete")

        if st.session_state.get("analysis_report"):
            report = st.session_state["analysis_report"]
            st.markdown("---")
            st.subheader("Executive Business Report")
            _render_report_sections(report)

            export_paths = _export_report_files(report)
            st.markdown("---")
            st.caption("Download the generated report")
            d1, d2, d3 = st.columns(3)
            with d1:
                with open(export_paths["json"], "rb") as handle:
                    st.download_button(
                        label="Download JSON",
                        data=handle.read(),
                        file_name="executive_report.json",
                        mime="application/json",
                    )
            with d2:
                with open(export_paths["markdown"], "rb") as handle:
                    st.download_button(
                        label="Download Markdown",
                        data=handle.read(),
                        file_name="executive_report.md",
                        mime="text/markdown",
                    )
            with d3:
                with open(export_paths["text"], "rb") as handle:
                    st.download_button(
                        label="Download Text",
                        data=handle.read(),
                        file_name="executive_report.txt",
                        mime="text/plain",
                    )

    except ValueError as exc:
        st.error(f"Failed to process file: {str(exc)}")

