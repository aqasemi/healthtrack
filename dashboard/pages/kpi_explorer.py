"""
KPI Explorer Page

Explore individual KPIs across the portfolio.
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
    load_feature_importance,
    KPI_DEFINITIONS,
    FEATURE_GROUPS
)
from components.charts import COLORS


def render_page():
    """Render the KPI explorer page."""
    
    # Header
    st.markdown('<p class="main-header">KPI Explorer</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Analyze individual KPIs and their impact on IVI scores</p>',
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
    
    # KPI selector
    st.markdown("### Select KPI to Analyze")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Group KPIs by dimension
        kpi_options = []
        for group, features in FEATURE_GROUPS.items():
            for feature in features:
                if feature in df.columns:
                    kpi_options.append(f"[{group[:1]}] {feature}")
        
        selected_kpi_display = st.selectbox(
            "KPI",
            kpi_options,
            index=0
        )
        
        # Extract actual KPI name
        selected_kpi = selected_kpi_display.split("] ")[1] if "] " in selected_kpi_display else selected_kpi_display
    
    with col2:
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Distribution", "Correlation", "Segmentation", "Top/Bottom"]
        )
    
    st.markdown("---")
    
    # Get KPI info
    kpi_info = KPI_DEFINITIONS.get(selected_kpi, {
        'name': selected_kpi.replace('_', ' ').title(),
        'description': 'No description available',
        'format': '.2f',
        'dimension': 'Unknown',
        'higher_is': 'neutral'
    })
    
    # KPI info card
    st.markdown(
        f"""
        <div style="background-color: #E8F4FD; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h4 style="margin: 0;">{kpi_info['name']}</h4>
            <p style="margin: 0.5rem 0; color: #666;">{kpi_info['description']}</p>
            <small>Dimension: {kpi_info['dimension']} | Higher values are: {kpi_info['higher_is']}</small>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Summary stats
    kpi_values = df[selected_kpi].drop_nulls()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Mean", f"{kpi_values.mean():.2f}")
    with col2:
        st.metric("Median", f"{kpi_values.median():.2f}")
    with col3:
        st.metric("Std Dev", f"{kpi_values.std():.2f}")
    with col4:
        st.metric("Min", f"{kpi_values.min():.2f}")
    with col5:
        st.metric("Max", f"{kpi_values.max():.2f}")
    
    st.markdown("---")
    
    # Render appropriate analysis
    if analysis_type == "Distribution":
        render_distribution_analysis(df, selected_kpi, kpi_info)
    elif analysis_type == "Correlation":
        render_correlation_analysis(df, selected_kpi)
    elif analysis_type == "Segmentation":
        render_segmentation_analysis(df, selected_kpi)
    else:
        render_top_bottom_analysis(df, selected_kpi, kpi_info)


def render_distribution_analysis(df: pl.DataFrame, kpi: str, kpi_info: dict):
    """Render distribution analysis for a KPI."""
    
    st.markdown("### Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram
        kpi_data = df[kpi].drop_nulls().to_list()
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=kpi_data,
            nbinsx=30,
            marker_color=COLORS['primary'],
            opacity=0.7
        ))
        fig.update_layout(
            title=f'{kpi_info["name"]} Distribution',
            xaxis_title=kpi_info['name'],
            yaxis_title='Count',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Box plot by risk level
        plot_df = df.select([kpi, 'IVI_RISK']).drop_nulls().to_pandas()
        
        fig = px.box(
            plot_df,
            x='IVI_RISK',
            y=kpi,
            color='IVI_RISK',
            color_discrete_map={
                'HIGH_RISK': COLORS['danger'],
                'MODERATE_RISK': COLORS['warning'],
                'LOW_RISK': COLORS['success']
            },
            title=f'{kpi_info["name"]} by Risk Level'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Percentile analysis
    st.markdown("### Percentile Analysis")
    
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    kpi_values = df[kpi].drop_nulls()
    
    pct_data = {
        'Percentile': [f'P{p}' for p in percentiles],
        'Value': [kpi_values.quantile(p/100) for p in percentiles]
    }
    
    import pandas as pd
    pct_df = pd.DataFrame(pct_data)
    pct_df['Value'] = pct_df['Value'].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(pct_df.T, use_container_width=True)


def render_correlation_analysis(df: pl.DataFrame, kpi: str):
    """Render correlation analysis for a KPI."""
    
    st.markdown("### Correlation with IVI Score")
    
    # Scatter plot with IVI
    plot_df = df.select([kpi, 'IVI_SCORE', 'IVI_RISK', 'TOTAL_MEMBERS']).drop_nulls().to_pandas()
    
    # Cap outliers for visualization
    upper_cap = plot_df[kpi].quantile(0.99)
    plot_df[kpi] = plot_df[kpi].clip(upper=upper_cap)
    
    fig = px.scatter(
        plot_df,
        x=kpi,
        y='IVI_SCORE',
        color='IVI_RISK',
        size='TOTAL_MEMBERS',
        color_discrete_map={
            'HIGH_RISK': COLORS['danger'],
            'MODERATE_RISK': COLORS['warning'],
            'LOW_RISK': COLORS['success']
        },
        title=f'{kpi} vs IVI Score',
        opacity=0.6
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation coefficient
    kpi_clean = df.select([kpi, 'IVI_SCORE']).drop_nulls()
    correlation = kpi_clean[kpi].to_numpy().flatten()
    ivi_scores = kpi_clean['IVI_SCORE'].to_numpy().flatten()
    
    import numpy as np
    corr = np.corrcoef(correlation, ivi_scores)[0, 1]
    
    st.markdown(
        f"""
        <div style="background-color: #F8F9FA; padding: 1rem; border-radius: 10px; text-align: center;">
            <h4>Correlation with IVI Score</h4>
            <p style="font-size: 2rem; font-weight: bold; color: {'#2E8B57' if abs(corr) > 0.3 else '#6C757D'};">{corr:.3f}</p>
            <p style="color: #666;">{"Strong" if abs(corr) > 0.5 else "Moderate" if abs(corr) > 0.3 else "Weak"} {"positive" if corr > 0 else "negative"} correlation</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Correlation with other KPIs
    st.markdown("### Correlation with Other KPIs")
    
    # Select numeric columns
    numeric_cols = [c for c in df.columns if df[c].dtype in [pl.Float64, pl.Int64, pl.UInt32] 
                   and c not in ['YEAR', 'RETAINED_NEXT_YEAR', 'RETAINED_ACTUAL']][:20]
    
    correlations = []
    for col in numeric_cols:
        if col != kpi:
            try:
                clean_df = df.select([kpi, col]).drop_nulls()
                if clean_df.height > 100:
                    c = np.corrcoef(
                        clean_df[kpi].to_numpy().flatten(),
                        clean_df[col].to_numpy().flatten()
                    )[0, 1]
                    correlations.append({'KPI': col, 'Correlation': c})
            except Exception:
                pass
    
    if correlations:
        import pandas as pd
        corr_df = pd.DataFrame(correlations)
        corr_df = corr_df.sort_values('Correlation', key=abs, ascending=False).head(10)
        
        fig = px.bar(
            corr_df,
            x='Correlation',
            y='KPI',
            orientation='h',
            title='Top 10 Correlated KPIs',
            color='Correlation',
            color_continuous_scale='RdBu_r',
            range_color=[-1, 1]
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_segmentation_analysis(df: pl.DataFrame, kpi: str):
    """Render segmentation analysis for a KPI."""
    
    st.markdown("### KPI by Segment")
    
    # Calculate stats by segment
    segment_stats = df.group_by('SEGMENT').agg([
        pl.col(kpi).mean().alias('mean'),
        pl.col(kpi).median().alias('median'),
        pl.col(kpi).std().alias('std'),
        pl.count().alias('count')
    ]).sort('mean', descending=True).to_pandas()
    
    # Bar chart
    fig = px.bar(
        segment_stats,
        x='SEGMENT',
        y='mean',
        error_y='std',
        title=f'Average {kpi} by Segment',
        color='mean',
        color_continuous_scale='RdYlGn_r'
    )
    fig.update_layout(xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig, use_container_width=True)
    
    # Table
    st.markdown("### Segment Statistics")
    
    segment_stats['mean'] = segment_stats['mean'].apply(lambda x: f"{x:.2f}")
    segment_stats['median'] = segment_stats['median'].apply(lambda x: f"{x:.2f}")
    segment_stats['std'] = segment_stats['std'].apply(lambda x: f"{x:.2f}")
    segment_stats.columns = ['Segment', 'Mean', 'Median', 'Std Dev', 'Count']
    
    st.dataframe(segment_stats, use_container_width=True, hide_index=True)
    
    # By region
    st.markdown("### KPI by Region")
    
    region_stats = df.group_by('PRIMARY_REGION').agg([
        pl.col(kpi).mean().alias('mean'),
        pl.count().alias('count')
    ]).filter(pl.col('count') > 100).sort('mean', descending=True).to_pandas()
    
    fig = px.bar(
        region_stats,
        x='PRIMARY_REGION',
        y='mean',
        title=f'Average {kpi} by Region',
        color='mean',
        color_continuous_scale='RdYlGn_r'
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def render_top_bottom_analysis(df: pl.DataFrame, kpi: str, kpi_info: dict):
    """Render top/bottom performers analysis."""
    
    st.markdown("### Top & Bottom Performers")
    
    col1, col2 = st.columns(2)
    
    # Top performers (depends on higher_is setting)
    ascending = kpi_info.get('higher_is', 'neutral') == 'worse'
    
    with col1:
        st.markdown("#### Best Performers")
        
        top_df = df.filter(pl.col(kpi).is_not_null()).sort(kpi, descending=not ascending).head(10)
        
        display_df = top_df.select([
            'CONTRACT_NO',
            'YEAR',
            kpi,
            'IVI_SCORE',
            'SEGMENT'
        ]).to_pandas()
        
        display_df[kpi] = display_df[kpi].apply(lambda x: f"{x:.2f}")
        display_df['IVI_SCORE'] = display_df['IVI_SCORE'].apply(lambda x: f"{x:.0f}")
        display_df.columns = ['Contract', 'Year', kpi_info['name'], 'IVI', 'Segment']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### Worst Performers")
        
        bottom_df = df.filter(pl.col(kpi).is_not_null()).sort(kpi, descending=ascending).head(10)
        
        display_df = bottom_df.select([
            'CONTRACT_NO',
            'YEAR',
            kpi,
            'IVI_SCORE',
            'SEGMENT'
        ]).to_pandas()
        
        display_df[kpi] = display_df[kpi].apply(lambda x: f"{x:.2f}")
        display_df['IVI_SCORE'] = display_df['IVI_SCORE'].apply(lambda x: f"{x:.0f}")
        display_df.columns = ['Contract', 'Year', kpi_info['name'], 'IVI', 'Segment']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Analysis of what differentiates top vs bottom
    st.markdown("### What Differentiates Top vs Bottom?")
    
    # Get top and bottom 20%
    threshold_high = df[kpi].quantile(0.8)
    threshold_low = df[kpi].quantile(0.2)
    
    if ascending:
        top_group = df.filter(pl.col(kpi) <= threshold_low)
        bottom_group = df.filter(pl.col(kpi) >= threshold_high)
    else:
        top_group = df.filter(pl.col(kpi) >= threshold_high)
        bottom_group = df.filter(pl.col(kpi) <= threshold_low)
    
    # Compare key metrics
    comparison_metrics = ['IVI_SCORE', 'TOTAL_MEMBERS', 'LOSS_RATIO', 'UTILIZATION_RATE', 'CALLS_PER_MEMBER']
    
    comparison_data = []
    for metric in comparison_metrics:
        if metric in df.columns:
            top_val = top_group[metric].mean()
            bottom_val = bottom_group[metric].mean()
            diff = ((top_val - bottom_val) / bottom_val * 100) if bottom_val else 0
            comparison_data.append({
                'Metric': metric.replace('_', ' ').title(),
                'Top 20%': f"{top_val:.2f}",
                'Bottom 20%': f"{bottom_val:.2f}",
                'Difference': f"{diff:+.1f}%"
            })
    
    import pandas as pd
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
