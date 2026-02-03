"""
Recommendation generation logic for IVI Dashboard.
"""

from typing import Dict, List, Optional


def generate_recommendations(client_data: Dict, benchmark_data: Dict) -> List[Dict]:
    """
    Generate actionable recommendations based on client KPIs vs benchmarks.
    
    Args:
        client_data: Dictionary with client metrics
        benchmark_data: Dictionary with benchmark metrics
    
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Experience issues - Pre-auth rejection
    if client_data.get('REJECTION_RATE', 0) > 0.25:
        severity = 'HIGH' if client_data['REJECTION_RATE'] > 0.40 else 'MEDIUM'
        recommendations.append({
            'priority': severity,
            'dimension': 'E',
            'issue': 'High pre-authorization rejection rate',
            'cause': f"Rejection rate {client_data['REJECTION_RATE']:.1%} vs {benchmark_data.get('avg_rejection_rate', 0.15):.1%} benchmark",
            'action': 'Review rejection reasons, consider provider network expansion, assign dedicated pre-auth handler',
            'impact': 'Could improve E_SCORE by 15-20 points'
        })
    
    # Experience issues - Resolution time
    if client_data.get('AVG_RESOLUTION_DAYS', 0) > 10:
        severity = 'HIGH' if client_data['AVG_RESOLUTION_DAYS'] > 15 else 'MEDIUM'
        recommendations.append({
            'priority': severity,
            'dimension': 'E',
            'issue': 'Long ticket resolution time',
            'cause': f"Average {client_data['AVG_RESOLUTION_DAYS']:.1f} days vs {benchmark_data.get('avg_resolution_days', 5):.1f} day benchmark",
            'action': 'Assign dedicated support representative, review escalation process, implement priority queuing',
            'impact': 'Improved E_SCORE and client satisfaction'
        })
    
    # Experience issues - High call volume
    if client_data.get('CALLS_PER_MEMBER', 0) > 0.35:
        severity = 'MEDIUM'
        recommendations.append({
            'priority': severity,
            'dimension': 'E',
            'issue': 'High support call volume',
            'cause': f"{client_data['CALLS_PER_MEMBER']:.2f} calls/member vs {benchmark_data.get('avg_calls_per_member', 0.2):.2f} benchmark",
            'action': 'Proactive communication, member education materials, digital self-service promotion',
            'impact': 'Reduced operational costs and improved member experience'
        })
    
    # Cost issues - Loss ratio
    if client_data.get('LOSS_RATIO', 0) > 1.2:
        severity = 'HIGH' if client_data['LOSS_RATIO'] > 1.5 else 'MEDIUM'
        recommendations.append({
            'priority': severity,
            'dimension': 'U',
            'issue': 'Unprofitable loss ratio',
            'cause': f"Loss ratio {client_data['LOSS_RATIO']:.2f} (break-even = 1.0)",
            'action': 'Premium adjustment discussion, benefit redesign, cost-sharing increase, wellness program enrollment',
            'impact': 'Required for sustainable contract renewal'
        })
    
    # Cost issues - High cost per member
    avg_cost = benchmark_data.get('avg_cost_per_member', 4500)
    if client_data.get('COST_PER_MEMBER', 0) > avg_cost * 1.5:
        severity = 'HIGH' if client_data['COST_PER_MEMBER'] > avg_cost * 2 else 'MEDIUM'
        recommendations.append({
            'priority': severity,
            'dimension': 'U',
            'issue': 'High cost per member',
            'cause': f"SAR {client_data['COST_PER_MEMBER']:,.0f}/member vs SAR {avg_cost:,.0f} benchmark",
            'action': 'Claims audit, chronic condition management program, provider steering incentives',
            'impact': 'Improved U_SCORE and profitability'
        })
    
    # Health issues - High utilization
    if client_data.get('UTILIZATION_RATE', 0) > 0.75:
        recommendations.append({
            'priority': 'MEDIUM',
            'dimension': 'H',
            'issue': 'High healthcare utilization',
            'cause': f"Utilization {client_data['UTILIZATION_RATE']:.1%} vs {benchmark_data.get('avg_utilization_rate', 0.52):.1%} benchmark",
            'action': 'Wellness program introduction, preventive screening campaign, health education',
            'impact': 'Long-term cost reduction and improved H_SCORE'
        })
    
    # Health issues - High diagnoses per utilizer
    if client_data.get('DIAGNOSES_PER_UTILIZER', 0) > 4.0:
        recommendations.append({
            'priority': 'MEDIUM',
            'dimension': 'H',
            'issue': 'High chronic condition burden',
            'cause': f"{client_data['DIAGNOSES_PER_UTILIZER']:.1f} diagnoses/utilizer vs {benchmark_data.get('avg_diagnoses_per_utilizer', 2.8):.1f} benchmark",
            'action': 'Disease management programs, chronic care coordination, specialist referral optimization',
            'impact': 'Improved health outcomes and cost predictability'
        })
    
    # Health issues - High maximum claim
    if client_data.get('MAX_CLAIM_AMOUNT', 0) > 100000:
        recommendations.append({
            'priority': 'LOW',
            'dimension': 'H',
            'issue': 'Catastrophic claim exposure',
            'cause': f"Max claim SAR {client_data['MAX_CLAIM_AMOUNT']:,.0f}",
            'action': 'Case management review, reinsurance consideration, large claim monitoring',
            'impact': 'Risk mitigation for future catastrophic events'
        })
    
    # Sort by priority
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    recommendations.sort(key=lambda x: priority_order[x['priority']])
    
    return recommendations


def get_segment_action_plan(segment: str) -> Dict:
    """
    Get pre-defined action plan for a segment.
    
    Args:
        segment: Segment name (e.g., 'HIGH_RISK_LARGE_UNPROFITABLE')
    
    Returns:
        Dictionary with action plan details
    """
    from .data_loader import SEGMENT_RECOMMENDATIONS
    
    return SEGMENT_RECOMMENDATIONS.get(segment, {
        'priority': 'UNKNOWN',
        'actions': ['Review client manually'],
        'focus': 'Segment not recognized'
    })


def calculate_priority_score(
    ivi_score: float,
    premium: float,
    loss_ratio: float,
    total_members: int
) -> float:
    """
    Calculate a priority score for account manager attention.
    
    Higher scores = higher priority for intervention.
    
    Args:
        ivi_score: Client's IVI score (0-100)
        premium: Written premium (SAR)
        loss_ratio: Loss ratio
        total_members: Number of members
    
    Returns:
        Priority score (higher = more urgent)
    """
    # Risk factor: inverse of IVI score (higher risk = higher priority)
    risk_factor = (100 - ivi_score) / 100
    
    # Value factor: log-scaled premium importance
    import math
    value_factor = math.log10(max(premium, 1000)) / 10  # Normalized 0-1 for typical premiums
    
    # Actionability: profitable but at-risk clients are more actionable
    if loss_ratio < 1.0:
        actionability = 1.2  # Profitable - worth saving
    elif loss_ratio < 1.5:
        actionability = 1.0  # Moderate loss - salvageable
    else:
        actionability = 0.7  # High loss - may not be worth saving
    
    # Size factor: larger clients deserve more attention
    size_factor = min(total_members / 100, 1.5)  # Cap at 1.5
    
    priority_score = risk_factor * value_factor * actionability * size_factor * 100
    
    return round(priority_score, 2)


def get_kpi_assessment(
    kpi_name: str,
    client_value: float,
    benchmark_value: float,
    higher_is_better: bool = False
) -> Dict:
    """
    Assess a KPI value relative to benchmark.
    
    Args:
        kpi_name: Name of the KPI
        client_value: Client's value
        benchmark_value: Benchmark value
        higher_is_better: Whether higher is better
    
    Returns:
        Dictionary with assessment details
    """
    if benchmark_value == 0:
        pct_diff = 0
    else:
        pct_diff = (client_value - benchmark_value) / benchmark_value * 100
    
    # Determine status
    if higher_is_better:
        if pct_diff > 20:
            status = 'EXCELLENT'
            color = 'green'
        elif pct_diff > -10:
            status = 'NORMAL'
            color = 'gray'
        else:
            status = 'CONCERN'
            color = 'red'
    else:
        if pct_diff < -20:
            status = 'EXCELLENT'
            color = 'green'
        elif pct_diff < 10:
            status = 'NORMAL'
            color = 'gray'
        else:
            status = 'CONCERN'
            color = 'red'
    
    return {
        'kpi': kpi_name,
        'client_value': client_value,
        'benchmark_value': benchmark_value,
        'pct_difference': pct_diff,
        'status': status,
        'color': color,
        'comparison': 'above' if pct_diff > 0 else 'below' if pct_diff < 0 else 'equal'
    }
