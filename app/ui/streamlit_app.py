"""Placeholder Streamlit entrypoint for ExecMind AI.

This file will host the main upload UI and report display experience.
"""

import streamlit as st


st.set_page_config(page_title="ExecMind AI", page_icon="📊", layout="wide")

st.title("ExecMind AI")
st.write("Autonomous Multi-Agent Business Intelligence Platform")
st.info("Upload sales data to begin the analysis workflow.")

uploaded_file = st.file_uploader("Upload sales data", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    st.success("File uploaded. Agent workflow will be connected here.")
