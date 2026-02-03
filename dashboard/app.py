"""
IVI Dashboard - Main Application Entry Point

Intelligent Value Index (IVI) Dashboard for Bupa Arabia
Provides real-time monitoring of corporate client health, experience, and cost metrics.
"""

import streamlit as st
from pathlib import Path

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="IVI Dashboard - Bupa Arabia",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Bupa branding
st.markdown("""
<style>
    /* Main colors */
    :root {
        --bupa-blue: #003087;
        --bupa-light-blue: #00A9E0;
        --bupa-green: #7AB800;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #003087;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #6C757D;
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #003087;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6C757D;
    }
    
    /* Risk badges */
    .risk-high {
        background-color: #D64045;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: bold;
    }
    
    .risk-moderate {
        background-color: #FF6B35;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: bold;
    }
    
    .risk-low {
        background-color: #2E8B57;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: bold;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Table styling */
    .dataframe {
        font-size: 0.85rem;
    }
    
    /* Section dividers */
    .section-divider {
        border-top: 2px solid #E8E8E8;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Sidebar navigation
    st.sidebar.markdown("### Bupa Arabia")
    st.sidebar.markdown("## IVI Dashboard")
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Portfolio Overview", "Client Deep Dive", "Segment Analysis", "KPI Explorer"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # Year filter (global)
    st.sidebar.markdown("### Filters")
    selected_year = st.sidebar.selectbox(
        "Contract Year",
        ["2022", "2023", "All Years"],
        index=0,
        help="2022 is recommended for retention prediction (model was trained on 2022 data)"
    )
    
    # Store in session state
    st.session_state['selected_year'] = selected_year if selected_year != "All Years" else None
    
    # Minimum members filter
    min_members = st.sidebar.selectbox(
        "Minimum Members",
        [1, 5, 10, 25, 50, 100],
        index=1,  # Default to 5
        help="Filter out small contracts (model trained on 5+ members)"
    )
    st.session_state['min_members'] = min_members
    
    # Additional filters
    st.sidebar.markdown("### Risk Filter")
    risk_filter = st.sidebar.multiselect(
        "Risk Levels",
        ["HIGH_RISK", "MODERATE_RISK", "LOW_RISK"],
        default=["HIGH_RISK", "MODERATE_RISK", "LOW_RISK"]
    )
    st.session_state['risk_filter'] = risk_filter
    
    # Route to appropriate page
    if page == "Portfolio Overview":
        render_portfolio_overview()
    elif page == "Client Deep Dive":
        render_client_deep_dive()
    elif page == "Segment Analysis":
        render_segment_analysis()
    elif page == "KPI Explorer":
        render_kpi_explorer()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<small>IVI Model v1.0 | Feb 2026</small>",
        unsafe_allow_html=True
    )


def render_portfolio_overview():
    """Render the portfolio overview page."""
    from pages.portfolio import render_page
    render_page()


def render_client_deep_dive():
    """Render the client deep dive page."""
    from pages.client_dive import render_page
    render_page()


def render_segment_analysis():
    """Render the segment analysis page."""
    from pages.segments import render_page
    render_page()


def render_kpi_explorer():
    """Render the KPI explorer page."""
    from pages.kpi_explorer import render_page
    render_page()


if __name__ == "__main__":
    main()
