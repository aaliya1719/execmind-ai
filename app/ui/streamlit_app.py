"""Streamlit user interface for ExecMind AI.

Manages data upload, displays file summaries, and visualizes basic analytics.
"""

import streamlit as st
from app.utils.file_utils import parse_uploaded_file

# Set page config
st.set_page_config(page_title="ExecMind AI", page_icon="📊", layout="wide")

# Inject premium theme stylesheet
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Force font styling */
    .stApp, .stMarkdown, div, span, label, p, button {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Title styling */
    .main-title {
        font-weight: 700;
        background: linear-gradient(90deg, #4A90E2, #9013FE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0.1rem;
    }
    
    .tagline {
        color: #7B8A99;
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
        font-weight: 300;
    }
    
    /* Modern card for metrics */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 600 !important;
        color: #4A90E2 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        font-weight: 400 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-title">ExecMind AI</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Your Autonomous AI Executive Team</div>', unsafe_allow_html=True)
st.info("Upload sales data to begin the analysis workflow.")

uploaded_file = st.file_uploader(
    "Upload sales data", 
    type=["csv", "xlsx", "xls"], 
    key="sales_data_uploader",
    help="Upload your small business sales records in CSV or Excel format."
)

if uploaded_file is not None:
    try:
        # Parse the uploaded file via utility layer
        df = parse_uploaded_file(uploaded_file)
        
        st.success(f"Successfully loaded '{uploaded_file.name}'!")
        
        # Display data summary in key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", f"{df.shape[0]:,}")
        with col2:
            st.metric("Total Attributes", df.shape[1])
        with col3:
            st.metric("Detected Columns", ", ".join(list(df.columns)[:4]) + ("..." if len(df.columns) > 4 else ""))
            
        st.subheader("Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Future agent workflow hooks
        st.info("Ready for analysis. The agent orchestration layer will process this dataset.")
        
    except ValueError as e:
        st.error(f"Failed to process file: {str(e)}")

