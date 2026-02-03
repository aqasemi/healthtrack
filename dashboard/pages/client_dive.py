"""
Client Deep Dive Page

Provides detailed analysis of individual client contracts.
"""

import streamlit as st
import polars as pl
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_ivi_scores,
    load_shap_subscores,
    get_client_details,
    get_benchmark_stats,
    KPI_DEFINITIONS,
    SEGMENT_RECOMMENDATIONS
)
from utils.recommendations import generate_recommendations, get_kpi_assessment
from components.charts import (
    create_ivi_gauge,
    create_subscore_gauges,
    create_kpi_bar_comparison,
    create_radar_comparison,
    COLORS
)


def render_page():
    """Render the client deep dive page."""
    
    # Header
    st.markdown('<p class="main-header">Client Deep Dive</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Analyze individual client performance and get actionable insights</p>',
        unsafe_allow_html=True
    )
    
    # Load data
    try:
        df = load_ivi_scores()
        shap_df = load_shap_subscores()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Apply year filter
    selected_year = st.session_state.get('selected_year', '2022')
    if selected_year:
        df_filtered = df.filter(pl.col('YEAR') == selected_year)
    else:
        df_filtered = df
    
    # Apply minimum members filter
    min_members = st.session_state.get('min_members', 5)
    df_filtered = df_filtered.filter(pl.col('TOTAL_MEMBERS') >= min_members)
    
    # Client selector
    st.markdown("### Select Client")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Get unique contract numbers
        contracts = df_filtered['CONTRACT_NO'].unique().sort().to_list()
        
        # Search/select contract
        selected_contract = st.selectbox(
            "Contract Number",
            contracts,
            index=0 if contracts else None,
            placeholder="Search or select a contract..."
        )
    
    with col2:
        # Quick filter by risk
        quick_filter = st.selectbox(
            "Quick Filter",
            ["All", "High Risk Only", "Large Contracts", "Unprofitable"]
        )
    
    with col3:
        year_select = st.selectbox(
            "Year",
            ["2022", "2023"],
            index=0 if selected_year == "2022" else 1
        )
    
    # Apply quick filter to contract list
    # Quick filter updates the selectable contracts list (for future enhancement)
    # Currently informational - shows which filter is active
    _ = quick_filter  # Acknowledge the filter selection
    
    if not selected_contract:
        st.info("Please select a contract to view details.")
        return
    
    # Get client details
    client_data = get_client_details(df, selected_contract, year_select)
    
    if not client_data:
        st.warning(f"No data found for contract {selected_contract} in {year_select}")
        return
    
    # Get benchmark stats
    benchmark = get_benchmark_stats(df_filtered)
    
    # Get SHAP subscores if available
    shap_client = shap_df.filter(pl.col('CONTRACT_NO') == selected_contract)
    has_shap = shap_client.height > 0
    
    st.markdown("---")
    
    # Client overview section
    st.markdown("### Client Overview")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Contract info card
        st.markdown(
            f"""
            <div style="background-color: #F8F9FA; padding: 1rem; border-radius: 10px;">
                <h4 style="margin: 0 0 1rem 0;">Contract Info</h4>
                <p><strong>Contract:</strong> {client_data['CONTRACT_NO']}</p>
                <p><strong>Year:</strong> {client_data['YEAR']}</p>
                <p><strong>Members:</strong> {client_data['TOTAL_MEMBERS']:,}</p>
                <p><strong>Premium:</strong> {client_data['WRITTEN_PREMIUM']:,.0f} SAR</p>
                <p><strong>Region:</strong> {client_data.get('PRIMARY_REGION', 'N/A')}</p>
                <p><strong>Network:</strong> {client_data.get('PRIMARY_NETWORK', 'N/A')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        # IVI Score gauge
        ivi_score = client_data.get('IVI_SCORE', 0)
        fig = create_ivi_gauge(ivi_score, "IVI Score", height=280)
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Risk and segment badges
        risk = client_data.get('IVI_RISK', 'UNKNOWN')
        risk_color = {
            'HIGH_RISK': '#D64045',
            'MODERATE_RISK': '#FF6B35',
            'LOW_RISK': '#2E8B57'
        }.get(risk, '#6C757D')
        
        segment = client_data.get('SEGMENT', 'N/A')
        profit_class = client_data.get('PROFIT_CLASS', 'N/A')
        size_class = client_data.get('SIZE_CLASS', 'N/A')
        
        st.markdown(
            f"""
            <div style="background-color: #F8F9FA; padding: 1rem; border-radius: 10px;">
                <h4 style="margin: 0 0 1rem 0;">Classification</h4>
                <p><span style="background-color: {risk_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: bold;">{risk.replace('_', ' ')}</span></p>
                <p style="margin-top: 1rem;"><strong>Size:</strong> {size_class}</p>
                <p><strong>Profitability:</strong> {profit_class}</p>
                <p><strong>Segment:</strong><br/><small>{segment}</small></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # H, E, U Subscores
    st.markdown("### Dimension Scores (H, E, U)")
    
    # Get subscores from SHAP or rule-based
    if has_shap:
        shap_row = shap_client.row(0, named=True)
        h_score = shap_row.get('H_SCORE', 50)
        e_score = shap_row.get('E_SCORE', 50)
        u_score = shap_row.get('U_SCORE', 50)
    else:
        # Fall back to rule-based scores
        h_score = client_data.get('H_SCORE_RULE', 50)
        e_score = client_data.get('E_SCORE_RULE', 50)
        u_score = client_data.get('U_SCORE_RULE', 50)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_dimension_panel(
            "Health (H)",
            h_score,
            client_data,
            benchmark,
            [
                ('UTILIZATION_RATE', 'Utilization Rate', '.1%'),
                ('DIAGNOSES_PER_UTILIZER', 'Diagnoses/Utilizer', '.1f'),
                ('AVG_CLAIM_AMOUNT', 'Avg Claim (SAR)', ',.0f'),
                ('P90_CLAIM_AMOUNT', 'P90 Claim (SAR)', ',.0f'),
            ],
            "#E74C3C"
        )
    
    with col2:
        render_dimension_panel(
            "Experience (E)",
            e_score,
            client_data,
            benchmark,
            [
                ('CALLS_PER_MEMBER', 'Calls/Member', '.2f'),
                ('AVG_RESOLUTION_DAYS', 'Resolution Days', '.1f'),
                ('REJECTION_RATE', 'Rejection Rate', '.1%'),
                ('APPROVAL_RATE', 'Approval Rate', '.1%'),
            ],
            "#3498DB"
        )
    
    with col3:
        render_dimension_panel(
            "Cost (U)",
            u_score,
            client_data,
            benchmark,
            [
                ('LOSS_RATIO', 'Loss Ratio', '.2f'),
                ('COST_PER_MEMBER', 'Cost/Member (SAR)', ',.0f'),
                ('COST_PER_UTILIZER', 'Cost/Utilizer (SAR)', ',.0f'),
                ('AVG_PREMIUM_PER_MEMBER', 'Premium/Member (SAR)', ',.0f'),
            ],
            "#27AE60"
        )
    
    st.markdown("---")
    
    # Recommendations section
    st.markdown("### Recommended Actions")
    
    recommendations = generate_recommendations(client_data, benchmark)
    
    if recommendations:
        for rec in recommendations:
            priority_color = {
                'HIGH': '#D64045',
                'MEDIUM': '#FF6B35',
                'LOW': '#6C757D'
            }.get(rec['priority'], '#6C757D')
            
            dimension_label = {
                'H': 'Health',
                'E': 'Experience',
                'U': 'Cost'
            }.get(rec['dimension'], rec['dimension'])
            
            st.markdown(
                f"""
                <div style="background-color: #F8F9FA; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid {priority_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: {priority_color};">{rec['issue']}</h4>
                        <span style="background-color: {priority_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem;">{rec['priority']} - {dimension_label}</span>
                    </div>
                    <p style="margin: 0.5rem 0; color: #666;"><strong>Cause:</strong> {rec['cause']}</p>
                    <p style="margin: 0.5rem 0;"><strong>Action:</strong> {rec['action']}</p>
                    <p style="margin: 0; color: #27AE60; font-size: 0.9rem;"><strong>Expected Impact:</strong> {rec['impact']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.success("No critical issues identified for this client. Maintain current relationship.")
    
    # Segment-specific guidance
    segment = client_data.get('SEGMENT', '')
    if segment in SEGMENT_RECOMMENDATIONS:
        seg_rec = SEGMENT_RECOMMENDATIONS[segment]
        st.markdown("### Segment Strategy")
        st.markdown(
            f"""
            <div style="background-color: #E8F4FD; padding: 1rem; border-radius: 10px;">
                <h4 style="margin: 0;">Priority: {seg_rec['priority']}</h4>
                <p style="margin: 0.5rem 0;"><strong>Focus:</strong> {seg_rec['focus']}</p>
                <p style="margin: 0.5rem 0;"><strong>Standard Actions:</strong></p>
                <ul style="margin: 0;">
                    {"".join([f"<li>{action}</li>" for action in seg_rec['actions']])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_dimension_panel(
    title: str,
    score: float,
    client_data: dict,
    benchmark: dict,
    kpis: list,
    color: str
):
    """Render a dimension panel with score and KPIs."""
    
    # Score display
    score_color = '#D64045' if score < 30 else '#FF6B35' if score < 60 else '#2E8B57'
    
    st.markdown(
        f"""
        <div style="background-color: #F8F9FA; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: {color};">{title}</h4>
            <div style="display: flex; align-items: center; margin: 1rem 0;">
                <span style="font-size: 2.5rem; font-weight: bold; color: {score_color};">{score:.0f}</span>
                <span style="font-size: 1rem; color: #666; margin-left: 0.5rem;">/100</span>
            </div>
            <div style="background-color: #E8E8E8; height: 10px; border-radius: 5px; overflow: hidden;">
                <div style="background-color: {score_color}; height: 100%; width: {score}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # KPI list
    for kpi_key, kpi_name, kpi_format in kpis:
        client_val = client_data.get(kpi_key, 0)
        
        # Get benchmark key (convert to lowercase with prefix)
        benchmark_key = f"avg_{kpi_key.lower()}"
        bench_val = benchmark.get(benchmark_key, client_val)
        
        # Handle percentage formatting
        if '%' in kpi_format and client_val is not None:
            display_val = f"{client_val:{kpi_format}}"
            bench_display = f"{bench_val:{kpi_format}}" if bench_val else "N/A"
        elif client_val is not None:
            display_val = f"{client_val:{kpi_format}}"
            bench_display = f"{bench_val:{kpi_format}}" if bench_val else "N/A"
        else:
            display_val = "N/A"
            bench_display = "N/A"
        
        # Determine status color
        # For most KPIs, lower is better (except approval rate)
        if 'APPROVAL' in kpi_key:
            status_color = '#2E8B57' if client_val >= bench_val else '#D64045'
        else:
            if bench_val and client_val:
                status_color = '#2E8B57' if client_val <= bench_val * 1.1 else '#D64045'
            else:
                status_color = '#6C757D'
        
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #E8E8E8;">
                <span style="color: #666;">{kpi_name}</span>
                <span style="font-weight: bold; color: {status_color};">{display_val}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Benchmark note
    st.markdown(
        f"<small style='color: #999;'>Benchmark shown for comparison</small>",
        unsafe_allow_html=True
    )
