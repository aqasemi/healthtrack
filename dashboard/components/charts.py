"""
Reusable chart components for IVI Dashboard.
Uses Plotly for interactive visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, List, Dict


# Bupa Arabia color scheme
COLORS = {
    'primary': '#003087',      # Bupa blue
    'secondary': '#00A9E0',    # Light blue
    'accent': '#7AB800',       # Green
    'warning': '#FF6B35',      # Orange
    'danger': '#D64045',       # Red
    'success': '#2E8B57',      # Sea green
    'neutral': '#6C757D',      # Gray
    'background': '#F8F9FA',   # Light gray
    'text': '#212529',         # Dark gray
}

RISK_COLORS = {
    'HIGH_RISK': COLORS['danger'],
    'MODERATE_RISK': COLORS['warning'],
    'LOW_RISK': COLORS['success'],
}


def create_ivi_gauge(
    score: float,
    title: str = "IVI Score",
    height: int = 250
) -> go.Figure:
    """
    Create a gauge chart for IVI score display.
    
    Args:
        score: IVI score (0-100)
        title: Chart title
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    # Determine color based on score
    if score < 30:
        bar_color = COLORS['danger']
    elif score < 60:
        bar_color = COLORS['warning']
    else:
        bar_color = COLORS['success']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'color': COLORS['text']}},
        number={'font': {'size': 36, 'color': COLORS['text']}, 'suffix': ''},
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': COLORS['neutral'],
                'tickvals': [0, 30, 60, 100],
                'ticktext': ['0', '30', '60', '100']
            },
            'bar': {'color': bar_color, 'thickness': 0.75},
            'bgcolor': 'white',
            'borderwidth': 2,
            'bordercolor': COLORS['neutral'],
            'steps': [
                {'range': [0, 30], 'color': '#FFCCCB'},    # Light red
                {'range': [30, 60], 'color': '#FFEAA7'},   # Light orange
                {'range': [60, 100], 'color': '#90EE90'}   # Light green
            ],
            'threshold': {
                'line': {'color': COLORS['text'], 'width': 2},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial, sans-serif'}
    )
    
    return fig


def create_subscore_gauges(
    h_score: float,
    e_score: float,
    u_score: float,
    height: int = 200
) -> go.Figure:
    """
    Create a row of three mini gauges for H, E, U subscores.
    
    Args:
        h_score: Health score (0-100)
        e_score: Experience score (0-100)
        u_score: Utilization score (0-100)
        height: Chart height in pixels
    
    Returns:
        Plotly figure object with subplots
    """
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
        horizontal_spacing=0.1
    )
    
    scores = [
        (h_score, 'Health (H)', '#E74C3C'),
        (e_score, 'Experience (E)', '#3498DB'),
        (u_score, 'Cost (U)', '#27AE60')
    ]
    
    for i, (score, title, color) in enumerate(scores, 1):
        # Determine color based on score
        if score < 30:
            indicator_color = COLORS['danger']
        elif score < 60:
            indicator_color = COLORS['warning']
        else:
            indicator_color = COLORS['success']
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={'text': title, 'font': {'size': 12}},
                number={'font': {'size': 20}},
                gauge={
                    'axis': {'range': [0, 100], 'visible': False},
                    'bar': {'color': indicator_color, 'thickness': 0.8},
                    'bgcolor': '#E8E8E8',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 30], 'color': '#FFCCCB'},
                        {'range': [30, 60], 'color': '#FFEAA7'},
                        {'range': [60, 100], 'color': '#90EE90'}
                    ],
                }
            ),
            row=1, col=i
        )
    
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig


def create_ivi_distribution(
    scores: List[float],
    selected_score: Optional[float] = None,
    height: int = 300
) -> go.Figure:
    """
    Create a histogram showing IVI score distribution.
    
    Args:
        scores: List of IVI scores
        selected_score: Optional score to highlight
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Create histogram with risk-based coloring
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=20,
        marker_color=[
            COLORS['danger'] if s < 30 else 
            COLORS['warning'] if s < 60 else 
            COLORS['success']
            for s in scores
        ],
        opacity=0.7,
        name='Contracts'
    ))
    
    # Add selected score marker if provided
    if selected_score is not None:
        fig.add_vline(
            x=selected_score,
            line_dash="dash",
            line_color=COLORS['primary'],
            line_width=3,
            annotation_text=f"Selected: {selected_score:.0f}",
            annotation_position="top"
        )
    
    # Add risk zone annotations
    fig.add_vrect(x0=0, x1=30, fillcolor=COLORS['danger'], opacity=0.1, layer="below", line_width=0)
    fig.add_vrect(x0=30, x1=60, fillcolor=COLORS['warning'], opacity=0.1, layer="below", line_width=0)
    fig.add_vrect(x0=60, x1=100, fillcolor=COLORS['success'], opacity=0.1, layer="below", line_width=0)
    
    fig.update_layout(
        title='IVI Score Distribution',
        xaxis_title='IVI Score',
        yaxis_title='Number of Contracts',
        height=height,
        margin=dict(l=50, r=20, t=50, b=50),
        showlegend=False,
        bargap=0.05
    )
    
    return fig


def create_risk_pie_chart(
    high_risk: int,
    moderate_risk: int,
    low_risk: int,
    height: int = 300
) -> go.Figure:
    """
    Create a pie chart showing risk tier distribution.
    
    Args:
        high_risk: Count of high risk contracts
        moderate_risk: Count of moderate risk contracts
        low_risk: Count of low risk contracts
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    labels = ['High Risk', 'Moderate Risk', 'Low Risk']
    values = [high_risk, moderate_risk, low_risk]
    colors = [COLORS['danger'], COLORS['warning'], COLORS['success']]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='outside',
        pull=[0.05, 0, 0]  # Slightly pull out high risk slice
    )])
    
    fig.update_layout(
        title='Risk Tier Distribution',
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
        annotations=[dict(
            text=f'{sum(values):,}',
            x=0.5, y=0.5,
            font_size=20,
            showarrow=False
        )]
    )
    
    return fig


def create_segment_heatmap(segment_data: Dict[str, int], height: int = 400) -> go.Figure:
    """
    Create a heatmap showing contract counts by segment.
    
    Args:
        segment_data: Dictionary with segment names as keys and counts as values
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    # Parse segment data into matrix
    risk_levels = ['HIGH_RISK', 'MODERATE_RISK', 'LOW_RISK']
    size_profit_combos = ['LARGE_PROFITABLE', 'LARGE_UNPROFITABLE', 'SMALL_PROFITABLE', 'SMALL_UNPROFITABLE']
    
    z_values = []
    for risk in risk_levels:
        row = []
        for combo in size_profit_combos:
            segment_name = f"{risk}_{combo}"
            row.append(segment_data.get(segment_name, 0))
        z_values.append(row)
    
    # Labels for display
    y_labels = ['High Risk', 'Moderate Risk', 'Low Risk']
    x_labels = ['Large Profitable', 'Large Unprofitable', 'Small Profitable', 'Small Unprofitable']
    
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0, '#F8F9FA'],
            [0.25, '#90EE90'],
            [0.5, '#FFEAA7'],
            [0.75, '#FF6B35'],
            [1, '#D64045']
        ],
        text=[[f'{v:,}' for v in row] for row in z_values],
        texttemplate='%{text}',
        textfont={'size': 14},
        hoverongaps=False,
        showscale=True,
        colorbar={'title': 'Contracts'}
    ))
    
    fig.update_layout(
        title='Contract Distribution by Segment',
        height=height,
        margin=dict(l=100, r=50, t=50, b=100),
        xaxis={'tickangle': -45}
    )
    
    return fig


def create_cost_waterfall(
    base: float,
    demographics: float,
    network: float,
    chronic: float,
    catastrophic: float,
    height: int = 350
) -> go.Figure:
    """
    Create a waterfall chart showing cost breakdown.
    
    Args:
        base: Base cost
        demographics: Demographic adjustment
        network: Network tier adjustment
        chronic: Chronic condition adjustment
        catastrophic: Catastrophic case adjustment
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    total = base + demographics + network + chronic + catastrophic
    
    fig = go.Figure(go.Waterfall(
        name="Cost Breakdown",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "total"],
        x=["Base Cost", "Demographics", "Network Tier", "Chronic Load", "Catastrophic", "Total"],
        textposition="outside",
        text=[f'{v:,.0f}' for v in [base, demographics, network, chronic, catastrophic, total]],
        y=[base, demographics, network, chronic, catastrophic, 0],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": COLORS['danger']}},
        decreasing={"marker": {"color": COLORS['success']}},
        totals={"marker": {"color": COLORS['primary']}}
    ))
    
    fig.update_layout(
        title="Cost per Member Breakdown (SAR)",
        height=height,
        margin=dict(l=50, r=50, t=50, b=80),
        showlegend=False,
        yaxis_title="SAR"
    )
    
    return fig


def create_radar_comparison(
    client_values: Dict[str, float],
    benchmark_values: Dict[str, float],
    categories: List[str],
    height: int = 400
) -> go.Figure:
    """
    Create a radar chart comparing client to benchmark.
    
    Args:
        client_values: Client metric values (normalized 0-100)
        benchmark_values: Benchmark metric values (normalized 0-100)
        categories: List of category names
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Client trace
    fig.add_trace(go.Scatterpolar(
        r=[client_values.get(c, 0) for c in categories],
        theta=categories,
        fill='toself',
        name='Client',
        line_color=COLORS['primary'],
        fillcolor='rgba(0, 48, 135, 0.3)'
    ))
    
    # Benchmark trace
    fig.add_trace(go.Scatterpolar(
        r=[benchmark_values.get(c, 0) for c in categories],
        theta=categories,
        fill='toself',
        name='Benchmark',
        line_color=COLORS['neutral'],
        fillcolor='rgba(108, 117, 125, 0.2)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        title='Client vs Benchmark',
        height=height,
        margin=dict(l=80, r=80, t=80, b=40)
    )
    
    return fig


def create_kpi_bar_comparison(
    client_value: float,
    benchmark_value: float,
    kpi_name: str,
    higher_is_better: bool = False,
    height: int = 150
) -> go.Figure:
    """
    Create a horizontal bar chart comparing KPI values.
    
    Args:
        client_value: Client's KPI value
        benchmark_value: Portfolio benchmark value
        kpi_name: Name of the KPI
        higher_is_better: Whether higher values are better
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    # Determine if client is performing well
    if higher_is_better:
        client_is_good = client_value >= benchmark_value
    else:
        client_is_good = client_value <= benchmark_value
    
    client_color = COLORS['success'] if client_is_good else COLORS['danger']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=['Benchmark', 'Client'],
        x=[benchmark_value, client_value],
        orientation='h',
        marker_color=[COLORS['neutral'], client_color],
        text=[f'{benchmark_value:,.2f}', f'{client_value:,.2f}'],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=kpi_name,
        height=height,
        margin=dict(l=20, r=100, t=40, b=20),
        showlegend=False,
        xaxis_title='',
        yaxis_title=''
    )
    
    return fig


def create_trend_line(
    dates: List[str],
    values: List[float],
    title: str = 'Trend',
    height: int = 300
) -> go.Figure:
    """
    Create a line chart showing trends over time.
    
    Args:
        dates: List of date strings
        values: List of values
        title: Chart title
        height: Chart height in pixels
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=8, color=COLORS['primary']),
        fill='tozeroy',
        fillcolor='rgba(0, 48, 135, 0.1)'
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=50, r=20, t=50, b=50),
        xaxis_title='',
        yaxis_title='',
        showlegend=False
    )
    
    return fig


def format_metric(value: float, format_spec: str) -> str:
    """
    Format a metric value for display.
    
    Args:
        value: Numeric value to format
        format_spec: Format specification (e.g., '.1%', ',.0f')
    
    Returns:
        Formatted string
    """
    if value is None:
        return 'N/A'
    
    try:
        if '%' in format_spec:
            return f'{value:{format_spec}}'
        else:
            return f'{value:{format_spec}}'
    except (ValueError, TypeError):
        return str(value)
