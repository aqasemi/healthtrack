"""
Segment Analysis Page

Analyze and compare different client segments.
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_ivi_scores,
    get_segment_summary,
    SEGMENT_PRIORITY,
    SEGMENT_RECOMMENDATIONS
)
from components.charts import COLORS


def render_page():
    """Render the segment analysis page."""
    
    # Header
    st.markdown('<p class="main-header">Segment Analysis</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Compare segments and develop targeted strategies</p>',
        unsafe_allow_html=True
    )
    
    # Load data
    try:
        df = load_ivi_scores()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Apply year filter
    selected_year = st.session_state.get('selected_year')
    if selected_year:
        df = df.filter(pl.col('YEAR') == selected_year)
    
    # Apply minimum members filter
    min_members = st.session_state.get('min_members', 5)
    df = df.filter(pl.col('TOTAL_MEMBERS') >= min_members)
    
    # Segment selector
    st.markdown("### Select Segment")
    
    # Get unique segments
    segments = sorted(df['SEGMENT'].unique().to_list(), 
                     key=lambda x: SEGMENT_PRIORITY.get(x, 99))
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_segment = st.selectbox(
            "Segment",
            ["All Segments"] + segments,
            index=0
        )
    
    with col2:
        view_type = st.selectbox(
            "View",
            ["Overview", "Comparison", "Detailed List"]
        )
    
    st.markdown("---")
    
    if view_type == "Overview":
        render_segment_overview(df, selected_segment)
    elif view_type == "Comparison":
        render_segment_comparison(df)
    else:
        render_segment_list(df, selected_segment)


def render_segment_overview(df: pl.DataFrame, selected_segment: str):
    """Render segment overview."""
    
    if selected_segment != "All Segments":
        segment_df = df.filter(pl.col('SEGMENT') == selected_segment)
    else:
        segment_df = df
    
    # Summary metrics
    st.markdown("### Segment Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Contracts", f"{segment_df.height:,}")
    
    with col2:
        total_members = segment_df['TOTAL_MEMBERS'].sum()
        st.metric("Members", f"{total_members:,}")
    
    with col3:
        total_premium = segment_df['WRITTEN_PREMIUM'].sum()
        st.metric("Premium", f"{total_premium/1e9:.2f}B SAR")
    
    with col4:
        avg_ivi = segment_df['IVI_SCORE'].mean()
        st.metric("Avg IVI", f"{avg_ivi:.0f}")
    
    with col5:
        avg_loss = segment_df['LOSS_RATIO'].mean()
        st.metric("Avg Loss Ratio", f"{avg_loss:.2f}")
    
    st.markdown("---")
    
    # Segment summary table
    st.markdown("### All Segments Summary")
    
    segment_summary = get_segment_summary(df)
    
    # Add priority and actions
    summary_data = []
    for row in segment_summary.iter_rows(named=True):
        seg_name = row['SEGMENT']
        seg_rec = SEGMENT_RECOMMENDATIONS.get(seg_name, {})
        summary_data.append({
            'Segment': seg_name,
            'Priority': seg_rec.get('priority', 'N/A'),
            'Contracts': row['contract_count'],
            'Members': f"{row['total_members']:,}",
            'Premium (M)': f"{row['total_premium']/1e6:.1f}",
            'Avg IVI': f"{row['avg_ivi_score']:.0f}",
            'Loss Ratio': f"{row['avg_loss_ratio']:.2f}",
            'Retention': f"{row['retention_rate']:.1%}" if row['retention_rate'] else "N/A"
        })
    
    import pandas as pd
    summary_df = pd.DataFrame(summary_data)
    
    # Color code by priority
    def highlight_priority(val):
        if val == 'CRITICAL':
            return 'background-color: #FFCCCB'
        elif val == 'HIGH':
            return 'background-color: #FFEAA7'
        elif val == 'MEDIUM':
            return 'background-color: #E8F4FD'
        return ''
    
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Segment action plan
    if selected_segment != "All Segments" and selected_segment in SEGMENT_RECOMMENDATIONS:
        st.markdown("---")
        st.markdown(f"### Action Plan: {selected_segment}")
        
        seg_rec = SEGMENT_RECOMMENDATIONS[selected_segment]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            priority_color = {
                'CRITICAL': '#D64045',
                'HIGH': '#FF6B35',
                'MEDIUM': '#F1C40F',
                'LOW': '#2E8B57'
            }.get(seg_rec['priority'], '#6C757D')
            
            st.markdown(
                f"""
                <div style="background-color: {priority_color}; color: white; padding: 1.5rem; border-radius: 10px; text-align: center;">
                    <h3 style="margin: 0;">Priority</h3>
                    <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{seg_rec['priority']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div style="background-color: #F8F9FA; padding: 1rem; border-radius: 10px;">
                    <h4 style="margin: 0 0 1rem 0;">Strategic Focus</h4>
                    <p style="margin: 0; font-size: 1.1rem;">{seg_rec['focus']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("#### Recommended Actions")
        for i, action in enumerate(seg_rec['actions'], 1):
            st.markdown(f"{i}. {action}")


def render_segment_comparison(df: pl.DataFrame):
    """Render segment comparison charts."""
    
    st.markdown("### Segment Comparison")
    
    # Group by segment
    segment_stats = df.group_by('SEGMENT').agg([
        pl.count().alias('contracts'),
        pl.col('TOTAL_MEMBERS').sum().alias('members'),
        pl.col('WRITTEN_PREMIUM').sum().alias('premium'),
        pl.col('IVI_SCORE').mean().alias('avg_ivi'),
        pl.col('LOSS_RATIO').mean().alias('avg_loss_ratio'),
        pl.col('UTILIZATION_RATE').mean().alias('avg_utilization'),
        pl.col('CALLS_PER_MEMBER').mean().alias('avg_calls'),
    ]).to_pandas()
    
    # Sort by priority
    segment_stats['priority'] = segment_stats['SEGMENT'].map(SEGMENT_PRIORITY)
    segment_stats = segment_stats.sort_values('priority')
    
    # Chart 1: Premium by segment
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            segment_stats,
            x='SEGMENT',
            y='premium',
            title='Premium by Segment (SAR)',
            color='avg_ivi',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            segment_stats,
            x='SEGMENT',
            y='contracts',
            title='Contract Count by Segment',
            color='avg_loss_ratio',
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Chart 2: IVI vs Loss Ratio scatter
    st.markdown("### IVI Score vs Loss Ratio by Segment")
    
    fig = px.scatter(
        segment_stats,
        x='avg_ivi',
        y='avg_loss_ratio',
        size='premium',
        color='SEGMENT',
        hover_data=['contracts', 'members'],
        title='Segment Positioning (size = premium)'
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="red", 
                  annotation_text="Break-even")
    fig.add_vline(x=50, line_dash="dash", line_color="gray",
                  annotation_text="Mid IVI")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Chart 3: Risk composition
    st.markdown("### Risk Tier Distribution")
    
    risk_by_segment = df.group_by(['SEGMENT', 'IVI_RISK']).agg(
        pl.count().alias('count')
    ).to_pandas()
    
    fig = px.bar(
        risk_by_segment,
        x='SEGMENT',
        y='count',
        color='IVI_RISK',
        title='Risk Tier by Segment',
        color_discrete_map={
            'HIGH_RISK': COLORS['danger'],
            'MODERATE_RISK': COLORS['warning'],
            'LOW_RISK': COLORS['success']
        }
    )
    fig.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_segment_list(df: pl.DataFrame, selected_segment: str):
    """Render detailed list of contracts in segment."""
    
    if selected_segment == "All Segments":
        st.info("Please select a specific segment to view detailed list.")
        return
    
    segment_df = df.filter(pl.col('SEGMENT') == selected_segment)
    
    st.markdown(f"### Contracts in {selected_segment}")
    st.markdown(f"**Total:** {segment_df.height:,} contracts")
    
    # Sorting options
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Premium (High to Low)", "IVI Score (Low to High)", "Members (High to Low)", "Loss Ratio (High to Low)"]
        )
    with col2:
        show_count = st.slider("Show contracts", 10, 100, 25)
    
    # Apply sorting
    if "Premium" in sort_by:
        segment_df = segment_df.sort('WRITTEN_PREMIUM', descending=True)
    elif "IVI Score" in sort_by:
        segment_df = segment_df.sort('IVI_SCORE', descending=False)
    elif "Members" in sort_by:
        segment_df = segment_df.sort('TOTAL_MEMBERS', descending=True)
    elif "Loss Ratio" in sort_by:
        segment_df = segment_df.sort('LOSS_RATIO', descending=True)
    
    # Display table
    display_df = segment_df.head(show_count).select([
        'CONTRACT_NO',
        'YEAR',
        'IVI_SCORE',
        'TOTAL_MEMBERS',
        'WRITTEN_PREMIUM',
        'LOSS_RATIO',
        'UTILIZATION_RATE',
        'CALLS_PER_MEMBER',
        'PRIMARY_REGION'
    ]).to_pandas()
    
    # Format columns
    display_df['IVI_SCORE'] = display_df['IVI_SCORE'].apply(lambda x: f"{x:.0f}")
    display_df['WRITTEN_PREMIUM'] = display_df['WRITTEN_PREMIUM'].apply(lambda x: f"{x:,.0f}")
    display_df['LOSS_RATIO'] = display_df['LOSS_RATIO'].apply(lambda x: f"{x:.2f}")
    display_df['UTILIZATION_RATE'] = display_df['UTILIZATION_RATE'].apply(lambda x: f"{x:.1%}")
    display_df['CALLS_PER_MEMBER'] = display_df['CALLS_PER_MEMBER'].apply(lambda x: f"{x:.2f}")
    
    display_df.columns = [
        'Contract', 'Year', 'IVI', 'Members', 'Premium (SAR)',
        'Loss Ratio', 'Utilization', 'Calls/Member', 'Region'
    ]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Export option
    csv = segment_df.to_pandas().to_csv(index=False)
    st.download_button(
        label="Export Full Segment Data (CSV)",
        data=csv,
        file_name=f"{selected_segment}_contracts.csv",
        mime="text/csv"
    )
