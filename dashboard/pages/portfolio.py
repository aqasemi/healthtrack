"""
Portfolio Overview Page

Displays high-level portfolio metrics, risk distribution, and key insights.
"""

import streamlit as st
import polars as pl
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_ivi_scores, 
    get_portfolio_summary, 
    get_segment_summary,
    SEGMENT_PRIORITY
)
from components.charts import (
    create_ivi_distribution,
    create_risk_pie_chart,
    create_segment_heatmap,
    COLORS
)


def render_page():
    """Render the portfolio overview page."""
    
    # Header
    st.markdown('<p class="main-header">Portfolio Overview</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Monitor overall portfolio health and identify at-risk contracts</p>',
        unsafe_allow_html=True
    )
    
    # Load data
    try:
        df = load_ivi_scores()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Please ensure the data files are available in /volume/data/models/")
        return
    
    # Apply year filter
    selected_year = st.session_state.get('selected_year')
    if selected_year:
        df = df.filter(pl.col('YEAR') == selected_year)
    
    # Apply minimum members filter (model trained on 5+ members)
    min_members = st.session_state.get('min_members', 5)
    df = df.filter(pl.col('TOTAL_MEMBERS') >= min_members)
    
    # Apply risk filter
    risk_filter = st.session_state.get('risk_filter', ['HIGH_RISK', 'MODERATE_RISK', 'LOW_RISK'])
    df = df.filter(pl.col('IVI_RISK').is_in(risk_filter))
    
    # Get summary stats
    summary = get_portfolio_summary(df)
    
    # Key metrics row
    st.markdown("### Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Contracts",
            value=f"{summary['total_contracts']:,}"
        )
    
    with col2:
        st.metric(
            label="Total Members",
            value=f"{summary['total_members']:,}"
        )
    
    with col3:
        premium_b = summary['total_premium'] / 1e9
        st.metric(
            label="Total Premium",
            value=f"{premium_b:.1f}B SAR"
        )
    
    with col4:
        st.metric(
            label="Avg IVI Score",
            value=f"{summary['avg_ivi_score']:.0f}",
            delta=f"Median: {summary['median_ivi_score']:.0f}"
        )
    
    with col5:
        at_risk_pct = summary['high_risk_count'] / summary['total_contracts'] * 100
        st.metric(
            label="At-Risk Contracts",
            value=f"{summary['high_risk_count']:,}",
            delta=f"{at_risk_pct:.1f}% of portfolio",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Visualizations row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### IVI Score Distribution")
        scores = df['IVI_SCORE'].to_list()
        fig = create_ivi_distribution(scores)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Risk Tier Breakdown")
        fig = create_risk_pie_chart(
            high_risk=summary['high_risk_count'],
            moderate_risk=summary['moderate_risk_count'],
            low_risk=summary['low_risk_count']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Segment heatmap
    st.markdown("### Contract Distribution by Segment")
    segment_counts = df.group_by('SEGMENT').agg(pl.count().alias('count'))
    segment_dict = dict(zip(
        segment_counts['SEGMENT'].to_list(),
        segment_counts['count'].to_list()
    ))
    fig = create_segment_heatmap(segment_dict)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # At-risk contracts table
    st.markdown("### Top At-Risk Contracts (Requiring Attention)")
    
    # Filter to high-risk and sort by premium
    at_risk = df.filter(pl.col('IVI_RISK') == 'HIGH_RISK').sort(
        'WRITTEN_PREMIUM', descending=True
    ).head(20)
    
    if at_risk.height > 0:
        # Select display columns
        display_df = at_risk.select([
            'CONTRACT_NO',
            'YEAR',
            'IVI_SCORE',
            'TOTAL_MEMBERS',
            'WRITTEN_PREMIUM',
            'LOSS_RATIO',
            'SEGMENT',
            'PRIMARY_REGION'
        ]).to_pandas()
        
        # Format columns
        display_df['IVI_SCORE'] = display_df['IVI_SCORE'].apply(lambda x: f"{x:.0f}")
        display_df['WRITTEN_PREMIUM'] = display_df['WRITTEN_PREMIUM'].apply(lambda x: f"{x:,.0f}")
        display_df['LOSS_RATIO'] = display_df['LOSS_RATIO'].apply(lambda x: f"{x:.2f}")
        
        display_df.columns = [
            'Contract', 'Year', 'IVI', 'Members', 'Premium (SAR)', 
            'Loss Ratio', 'Segment', 'Region'
        ]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No high-risk contracts found with current filters.")
    
    st.markdown("---")
    
    # Summary statistics by segment
    st.markdown("### Segment Summary")
    segment_summary = get_segment_summary(df)
    
    if segment_summary.height > 0:
        summary_df = segment_summary.to_pandas()
        summary_df['total_premium'] = summary_df['total_premium'].apply(lambda x: f"{x/1e6:.1f}M")
        summary_df['avg_ivi_score'] = summary_df['avg_ivi_score'].apply(lambda x: f"{x:.0f}")
        summary_df['avg_loss_ratio'] = summary_df['avg_loss_ratio'].apply(lambda x: f"{x:.2f}")
        summary_df['retention_rate'] = summary_df['retention_rate'].apply(
            lambda x: f"{x:.1%}" if x is not None else "N/A"
        )
        
        summary_df.columns = [
            'Segment', 'Contracts', 'Members', 'Premium', 
            'Avg IVI', 'Avg Loss Ratio', 'Retention Rate'
        ]
        
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Premium at risk calculation
    st.markdown("---")
    st.markdown("### Premium at Risk")
    
    # Calculate actual retention rates by risk level
    high_risk_df = df.filter(pl.col('IVI_RISK') == 'HIGH_RISK')
    moderate_risk_df = df.filter(pl.col('IVI_RISK') == 'MODERATE_RISK')
    low_risk_df = df.filter(pl.col('IVI_RISK') == 'LOW_RISK')
    
    high_risk_premium = high_risk_df['WRITTEN_PREMIUM'].sum()
    moderate_risk_premium = moderate_risk_df['WRITTEN_PREMIUM'].sum()
    low_risk_premium = low_risk_df['WRITTEN_PREMIUM'].sum()
    total_premium = summary['total_premium']
    
    # Calculate actual retention if available
    high_retention = high_risk_df['RETAINED_NEXT_YEAR'].mean() if high_risk_df.height > 0 else 0
    mod_retention = moderate_risk_df['RETAINED_NEXT_YEAR'].mean() if moderate_risk_df.height > 0 else 0
    low_retention = low_risk_df['RETAINED_NEXT_YEAR'].mean() if low_risk_df.height > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div style="background-color: #FFCCCB; padding: 1rem; border-radius: 10px; text-align: center;">
                <h4 style="color: #D64045; margin: 0;">High Risk Premium</h4>
                <p style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">{high_risk_premium/1e9:.2f}B SAR</p>
                <p style="color: #666; margin: 0;">{high_risk_premium/total_premium*100:.1f}% of portfolio</p>
                <p style="color: #D64045; font-size: 0.85rem; margin-top: 0.5rem;">Actual retention: {high_retention:.1%}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="background-color: #FFEAA7; padding: 1rem; border-radius: 10px; text-align: center;">
                <h4 style="color: #FF6B35; margin: 0;">Moderate Risk Premium</h4>
                <p style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">{moderate_risk_premium/1e9:.2f}B SAR</p>
                <p style="color: #666; margin: 0;">{moderate_risk_premium/total_premium*100:.1f}% of portfolio</p>
                <p style="color: #FF6B35; font-size: 0.85rem; margin-top: 0.5rem;">Actual retention: {mod_retention:.1%}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div style="background-color: #90EE90; padding: 1rem; border-radius: 10px; text-align: center;">
                <h4 style="color: #2E8B57; margin: 0;">Low Risk Premium</h4>
                <p style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">{low_risk_premium/1e9:.2f}B SAR</p>
                <p style="color: #666; margin: 0;">{low_risk_premium/total_premium*100:.1f}% of portfolio</p>
                <p style="color: #2E8B57; font-size: 0.85rem; margin-top: 0.5rem;">Actual retention: {low_retention:.1%}</p>
            </div>
            """,
            unsafe_allow_html=True
        )    
    # Add explanation note
    st.info(
        """
        **Note:** Large, established contracts with consistent activity tend to have higher IVI scores 
        (predicted retention). The model correctly identifies that premium-heavy contracts have better 
        retention (~60% for Low Risk vs <10% for High Risk). Focus retention efforts on the 
        HIGH_RISK and MODERATE_RISK segments where intervention can make a difference.
        """
    )