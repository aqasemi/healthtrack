"""
Data loader utilities for IVI Dashboard.
Loads processed parquet files with caching for Streamlit.
"""

import streamlit as st
import polars as pl
from pathlib import Path
from typing import Optional

# Data paths
DATA_DIR = Path('/volume/data')
PROCESSED_DIR = DATA_DIR / 'processed'
MODELS_DIR = DATA_DIR / 'models'


@st.cache_data(ttl=3600)
def load_ivi_scores() -> pl.DataFrame:
    """Load IVI scores with all features and segmentation."""
    return pl.read_parquet(MODELS_DIR / 'ivi_scores_all_years.parquet')


@st.cache_data(ttl=3600)
def load_shap_subscores() -> pl.DataFrame:
    """Load SHAP-based H, E, U subscores."""
    return pl.read_parquet(MODELS_DIR / 'shap_subscores.parquet')


@st.cache_data(ttl=3600)
def load_contract_level() -> pl.DataFrame:
    """Load contract-level aggregated data."""
    return pl.read_parquet(PROCESSED_DIR / 'contract_level.parquet')


@st.cache_data(ttl=3600)
def load_provider_reference() -> pl.DataFrame:
    """Load provider reference data."""
    return pl.read_parquet(PROCESSED_DIR / 'ref_provider.parquet')


@st.cache_data(ttl=3600)
def load_feature_importance() -> pl.DataFrame:
    """Load feature importance from model."""
    import pandas as pd
    return pl.from_pandas(pd.read_csv(MODELS_DIR / 'feature_importance.csv'))


def get_portfolio_summary(df: pl.DataFrame, year: Optional[str] = None) -> dict:
    """
    Calculate portfolio-level summary statistics.
    
    Args:
        df: IVI scores dataframe
        year: Optional year filter ('2022' or '2023')
    
    Returns:
        Dictionary with summary metrics
    """
    if year:
        df = df.filter(pl.col('YEAR') == year)
    
    return {
        'total_contracts': df.height,
        'total_members': df['TOTAL_MEMBERS'].sum(),
        'total_premium': df['WRITTEN_PREMIUM'].sum(),
        'avg_ivi_score': df['IVI_SCORE'].mean(),
        'median_ivi_score': df['IVI_SCORE'].median(),
        'high_risk_count': df.filter(pl.col('IVI_RISK') == 'HIGH_RISK').height,
        'moderate_risk_count': df.filter(pl.col('IVI_RISK') == 'MODERATE_RISK').height,
        'low_risk_count': df.filter(pl.col('IVI_RISK') == 'LOW_RISK').height,
        'avg_loss_ratio': df['LOSS_RATIO'].mean(),
        'retention_rate': df['RETAINED_NEXT_YEAR'].mean() if 'RETAINED_NEXT_YEAR' in df.columns else None,
    }


def get_segment_summary(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculate summary statistics by segment.
    
    Args:
        df: IVI scores dataframe
    
    Returns:
        DataFrame with segment-level metrics
    """
    return df.group_by('SEGMENT').agg([
        pl.count().alias('contract_count'),
        pl.col('TOTAL_MEMBERS').sum().alias('total_members'),
        pl.col('WRITTEN_PREMIUM').sum().alias('total_premium'),
        pl.col('IVI_SCORE').mean().alias('avg_ivi_score'),
        pl.col('LOSS_RATIO').mean().alias('avg_loss_ratio'),
        pl.col('RETAINED_NEXT_YEAR').mean().alias('retention_rate'),
    ]).sort('contract_count', descending=True)


def get_client_details(df: pl.DataFrame, contract_no: str, year: str = '2022') -> Optional[dict]:
    """
    Get detailed information for a specific client.
    
    Args:
        df: IVI scores dataframe
        contract_no: Contract number to look up
        year: Year to filter
    
    Returns:
        Dictionary with client details or None if not found
    """
    client = df.filter(
        (pl.col('CONTRACT_NO') == contract_no) & 
        (pl.col('YEAR') == year)
    )
    
    if client.height == 0:
        return None
    
    return client.row(0, named=True)


def get_benchmark_stats(df: pl.DataFrame, segment: Optional[str] = None) -> dict:
    """
    Calculate benchmark statistics for comparison.
    
    Args:
        df: IVI scores dataframe
        segment: Optional segment to calculate benchmarks for
    
    Returns:
        Dictionary with benchmark metrics
    """
    if segment:
        df = df.filter(pl.col('SEGMENT') == segment)
    
    return {
        'avg_utilization_rate': df['UTILIZATION_RATE'].mean(),
        'avg_loss_ratio': df['LOSS_RATIO'].mean(),
        'avg_cost_per_member': df['COST_PER_MEMBER'].mean(),
        'avg_calls_per_member': df['CALLS_PER_MEMBER'].mean(),
        'avg_rejection_rate': df['REJECTION_RATE'].mean(),
        'avg_approval_rate': df['APPROVAL_RATE'].mean(),
        'avg_resolution_days': df['AVG_RESOLUTION_DAYS'].mean(),
        'avg_diagnoses_per_utilizer': df['DIAGNOSES_PER_UTILIZER'].mean(),
        'p50_ivi_score': df['IVI_SCORE'].median(),
        'p25_ivi_score': df['IVI_SCORE'].quantile(0.25),
        'p75_ivi_score': df['IVI_SCORE'].quantile(0.75),
    }


# Feature group definitions
FEATURE_GROUPS = {
    'H_HEALTH': [
        'MEMBERS_WITH_CLAIMS', 'UNIQUE_DIAGNOSES', 'DIAGNOSES_PER_UTILIZER',
        'CLAIM_LINES', 'UNIQUE_CLAIMS', 'CLAIMS_PER_UTILIZER', 'TOTAL_BILLED',
        'AVG_CLAIM_AMOUNT', 'MAX_CLAIM_AMOUNT', 'P90_CLAIM_AMOUNT',
        'STD_CLAIM_AMOUNT', 'UTILIZATION_RATE'
    ],
    'E_EXPERIENCE': [
        'TOTAL_CALLS', 'UNIQUE_CALLS', 'UNIQUE_CALLERS', 'CALLS_PER_MEMBER',
        'AVG_RESOLUTION_DAYS', 'MEDIAN_RESOLUTION_DAYS', 'CALL_CATEGORIES',
        'PREAUTH_EPISODES', 'PREAUTH_ITEMS', 'MEMBERS_WITH_PREAUTH',
        'APPROVAL_RATE', 'REJECTION_RATE', 'PREAUTH_PER_MEMBER',
        'WEEKEND_CALLS', 'WEEKDAY_CALLS'
    ],
    'U_UTILIZATION': [
        'LOSS_RATIO', 'COST_PER_MEMBER', 'COST_PER_UTILIZER',
        'TOTAL_EST_AMOUNT', 'AVG_EST_AMOUNT', 'MAX_EST_AMOUNT',
        'WRITTEN_PREMIUM', 'EARNED_PREMIUM', 'AVG_PREMIUM_PER_MEMBER',
        'CLAIM_LINES_PER_MEMBER', 'PROVIDERS_PER_UTILIZER'
    ],
    'DEMOGRAPHICS': [
        'TOTAL_MEMBERS', 'PLAN_COUNT', 'MALE_COUNT', 'FEMALE_COUNT',
        'MALE_RATIO', 'NATIONALITY_COUNT'
    ],
    'SEASONAL': [
        'Q1_CLAIMS', 'Q2_CLAIMS', 'Q3_CLAIMS', 'Q4_CLAIMS',
        'Q1_CALLS', 'Q2_CALLS', 'Q3_CALLS', 'Q4_CALLS',
        'QUARTER_CONCENTRATION', 'ACTIVE_MONTHS', 'ACTIVE_CALL_MONTHS',
        'ACTIVE_PREAUTH_MONTHS', 'YEAR_COVERAGE'
    ],
    'PROVIDER': [
        'UNIQUE_PROVIDERS', 'PREAUTH_PROVIDERS', 'PRACTICE_TYPE_COUNT'
    ]
}

# KPI definitions with display names and formatting
KPI_DEFINITIONS = {
    'UTILIZATION_RATE': {
        'name': 'Utilization Rate',
        'description': 'Percentage of members who used healthcare services',
        'format': '.1%',
        'dimension': 'H',
        'higher_is': 'neutral'
    },
    'DIAGNOSES_PER_UTILIZER': {
        'name': 'Diagnoses per Utilizer',
        'description': 'Average number of unique diagnoses per member who used services',
        'format': '.1f',
        'dimension': 'H',
        'higher_is': 'worse'
    },
    'AVG_CLAIM_AMOUNT': {
        'name': 'Average Claim Amount',
        'description': 'Average amount per claim (SAR)',
        'format': ',.0f',
        'dimension': 'H',
        'higher_is': 'worse'
    },
    'LOSS_RATIO': {
        'name': 'Loss Ratio',
        'description': 'Claims paid divided by premium earned (>1 = unprofitable)',
        'format': '.2f',
        'dimension': 'U',
        'higher_is': 'worse'
    },
    'COST_PER_MEMBER': {
        'name': 'Cost per Member',
        'description': 'Total claims divided by total members (SAR)',
        'format': ',.0f',
        'dimension': 'U',
        'higher_is': 'worse'
    },
    'CALLS_PER_MEMBER': {
        'name': 'Calls per Member',
        'description': 'Average number of support calls per member',
        'format': '.2f',
        'dimension': 'E',
        'higher_is': 'worse'
    },
    'AVG_RESOLUTION_DAYS': {
        'name': 'Resolution Days',
        'description': 'Average days to resolve support tickets',
        'format': '.1f',
        'dimension': 'E',
        'higher_is': 'worse'
    },
    'REJECTION_RATE': {
        'name': 'Pre-auth Rejection Rate',
        'description': 'Percentage of pre-authorization requests rejected',
        'format': '.1%',
        'dimension': 'E',
        'higher_is': 'worse'
    },
    'APPROVAL_RATE': {
        'name': 'Pre-auth Approval Rate',
        'description': 'Percentage of pre-authorization requests approved',
        'format': '.1%',
        'dimension': 'E',
        'higher_is': 'better'
    },
}

# Segment priority ordering
SEGMENT_PRIORITY = {
    'HIGH_RISK_LARGE_UNPROFITABLE': 1,
    'HIGH_RISK_LARGE_PROFITABLE': 2,
    'HIGH_RISK_SMALL_UNPROFITABLE': 3,
    'HIGH_RISK_SMALL_PROFITABLE': 4,
    'MODERATE_RISK_LARGE_UNPROFITABLE': 5,
    'MODERATE_RISK_LARGE_PROFITABLE': 6,
    'MODERATE_RISK_SMALL_UNPROFITABLE': 7,
    'MODERATE_RISK_SMALL_PROFITABLE': 8,
    'LOW_RISK_LARGE_UNPROFITABLE': 9,
    'LOW_RISK_LARGE_PROFITABLE': 10,
    'LOW_RISK_SMALL_UNPROFITABLE': 11,
    'LOW_RISK_SMALL_PROFITABLE': 12,
}

# Recommendations by segment
SEGMENT_RECOMMENDATIONS = {
    'HIGH_RISK_LARGE_UNPROFITABLE': {
        'priority': 'CRITICAL',
        'actions': [
            'Executive-level meeting to discuss contract renewal terms',
            'Premium adjustment negotiation required',
            'Review benefit design for cost optimization',
            'Conduct claims audit for potential fraud/misuse'
        ],
        'focus': 'Retain if profitable terms can be negotiated, otherwise consider non-renewal'
    },
    'HIGH_RISK_LARGE_PROFITABLE': {
        'priority': 'HIGH',
        'actions': [
            'Assign dedicated account manager',
            'Conduct service quality review',
            'Identify and address pain points (E-score drivers)',
            'Propose loyalty incentives or enhanced benefits'
        ],
        'focus': 'Retention is critical - valuable client at risk'
    },
    'HIGH_RISK_SMALL_UNPROFITABLE': {
        'priority': 'MEDIUM',
        'actions': [
            'Review pricing for renewal',
            'Consider benefit tier adjustment',
            'Standard renewal process with adjusted terms'
        ],
        'focus': 'Low priority - small impact, let natural churn occur or adjust pricing'
    },
    'HIGH_RISK_SMALL_PROFITABLE': {
        'priority': 'MEDIUM',
        'actions': [
            'Standard account outreach',
            'Identify quick wins for service improvement',
            'Consider pooling with similar clients for attention'
        ],
        'focus': 'Moderate effort retention - profitable but small'
    },
    'MODERATE_RISK_LARGE_UNPROFITABLE': {
        'priority': 'MEDIUM',
        'actions': [
            'Wellness program introduction',
            'Cost management consultation',
            'Premium review for next renewal'
        ],
        'focus': 'Proactive cost management to improve profitability'
    },
    'MODERATE_RISK_LARGE_PROFITABLE': {
        'priority': 'MEDIUM',
        'actions': [
            'Regular account check-ins',
            'Wellness program upsell',
            'Maintain service quality'
        ],
        'focus': 'Maintain relationship and monitor for risk changes'
    },
    'MODERATE_RISK_SMALL_UNPROFITABLE': {
        'priority': 'LOW',
        'actions': [
            'Standard renewal with pricing adjustment',
            'Automated communication'
        ],
        'focus': 'Minimal effort - adjust pricing at renewal'
    },
    'MODERATE_RISK_SMALL_PROFITABLE': {
        'priority': 'LOW',
        'actions': [
            'Standard renewal process',
            'Automated wellness content'
        ],
        'focus': 'Maintain current approach'
    },
    'LOW_RISK_LARGE_UNPROFITABLE': {
        'priority': 'MEDIUM',
        'actions': [
            'Cost management review',
            'Benefit optimization discussion',
            'Preventive care programs'
        ],
        'focus': 'Loyal client but unprofitable - work on sustainability'
    },
    'LOW_RISK_LARGE_PROFITABLE': {
        'priority': 'LOW',
        'actions': [
            'Relationship maintenance',
            'Upsell opportunities (dental, vision, wellness)',
            'Referral program engagement'
        ],
        'focus': 'Ideal client - maintain and grow relationship'
    },
    'LOW_RISK_SMALL_UNPROFITABLE': {
        'priority': 'LOW',
        'actions': [
            'Pricing adjustment at renewal',
            'Standard communication'
        ],
        'focus': 'Adjust pricing to improve margins'
    },
    'LOW_RISK_SMALL_PROFITABLE': {
        'priority': 'LOW',
        'actions': [
            'Standard renewal process',
            'Automated engagement'
        ],
        'focus': 'No action needed - healthy baseline'
    },
}
