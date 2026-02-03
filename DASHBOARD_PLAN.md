# IVI Dashboard - Streamlit Application Plan

## Overview
Interactive dashboard for Bupa Arabia account managers to:
1. View client IVI scores and risk segmentation
2. Understand WHY a client is at risk (drill-down into H, E, U)
3. Compare clients against benchmarks
4. Get actionable recommendations

---

## Dashboard Structure

### Page 1: Portfolio Overview (Home)

#### Header
- Bupa Arabia logo
- Date range selector (2022, 2023)
- Filter: Region, Network, Size segment

#### Key Metrics Cards (Top Row)
- Total Contracts
- Total Members
- Total Premium
- Average IVI Score
- At-Risk Contracts (IVI < 30)

#### Visualizations
1. **IVI Distribution Histogram**
   - X: IVI Score bins (0-10, 10-20, ..., 90-100)
   - Y: Number of contracts
   - Color: Risk tier (Red/Yellow/Green)

2. **Risk Tier Pie Chart**
   - High Risk, Moderate Risk, Low Risk proportions
   - Show premium at risk in each tier

3. **Segment Matrix Heatmap**
   - Rows: Risk Level (High/Moderate/Low)
   - Columns: Size (Large/Small) x Profitability (Profitable/Unprofitable)
   - Color intensity: Number of contracts

4. **Top At-Risk Contracts Table**
   - Contract ID, IVI Score, Members, Premium, Loss Ratio
   - Sortable, clickable to drill down

---

### Page 2: Client Deep Dive

#### Client Selector
- Dropdown: Select contract by ID or search
- Quick filters: Show only High Risk, Large contracts, etc.

#### Client Overview Card
- Contract ID, Company Name (if available)
- IVI Score (large gauge/dial)
- H/E/U Sub-scores (3 small gauges)
- Size class, Profitability class, Risk tier

#### KPI Breakdown Section

##### Health (H) Panel
```
+---------------------------+
|  H SCORE: 45/100          |
|  [===========----------]  |
+---------------------------+
| Utilization Rate: 78%     | HIGH (vs 52% avg)
| Diagnoses/Utilizer: 4.2   | HIGH (vs 2.8 avg)  
| Avg Claim Amount: 2,450   | NORMAL
| P90 Claim Amount: 8,200   | HIGH
+---------------------------+
| ROOT CAUSE ANALYSIS:      |
| - High chronic condition  |
|   prevalence (diabetes,   |
|   hypertension)           |
| - Older workforce         |
|   demographics            |
+---------------------------+
| RECOMMENDED ACTIONS:      |
| - Wellness screening      |
| - Chronic disease mgmt    |
+---------------------------+
```

##### Experience (E) Panel
```
+---------------------------+
|  E SCORE: 32/100          |
|  [======----------------] |
+---------------------------+
| Calls/Member: 0.45        | HIGH (vs 0.22 avg)
| Resolution Days: 12.3     | HIGH (vs 5.1 avg)
| Rejection Rate: 38%       | HIGH (vs 15% avg)
| Approval Rate: 55%        | LOW (vs 78% avg)
+---------------------------+
| ROOT CAUSE ANALYSIS:      |
| - Primary region: Northern|
|   (limited providers)     |
| - Network NW5 (basic tier)|
| - High pre-auth volume    |
+---------------------------+
| RECOMMENDED ACTIONS:      |
| - Assign dedicated handler|
| - Network upgrade discuss |
| - Provider expansion      |
+---------------------------+
```

##### Utilization/Cost (U) Panel
```
+---------------------------+
|  U SCORE: 28/100          |
|  [=====----------------]  |
+---------------------------+
| Loss Ratio: 1.45          | UNPROFITABLE
| Cost/Member: 8,200        | HIGH (vs 4,500 avg)
| Cost/Utilizer: 12,800     | HIGH
| Premium/Member: 5,650     | NORMAL
+---------------------------+
| COST WATERFALL:           |
| Base cost:        4,000   |
| + Demographics:   +1,200  |
| + Network tier:   +800    |
| + Chronic load:   +1,500  |
| + Catastrophic:   +700    |
| = Total:          8,200   |
+---------------------------+
| RECOMMENDED ACTIONS:      |
| - Premium adjustment      |
| - Benefit redesign        |
| - Cost sharing discussion |
+---------------------------+
```

#### Trend Analysis
- Line chart: IVI Score over time (if multi-year data)
- Comparison: This client vs segment average vs portfolio average

#### Peer Comparison
- Radar chart: This client vs similar-sized contracts
- Axes: H, E, U, Loss Ratio, Premium, Retention probability

---

### Page 3: Segment Analysis

#### Segment Selector
- Grid of 12 segments (3 risk x 2 size x 2 profitability)
- Click to filter

#### Selected Segment Overview
- Segment name (e.g., "HIGH_RISK_LARGE_UNPROFITABLE")
- Count, total premium, average IVI
- Retention rate in this segment

#### Segment Characteristics
- Bar charts: Average H, E, U scores
- Distribution: Loss ratio, utilization rate
- Top reasons for risk in this segment

#### Contracts in Segment
- Paginated table with all contracts
- Quick actions: Mark for follow-up, export list

#### Recommended Actions for Segment
- Prioritized list of interventions
- Expected impact (estimated retention lift)

---

### Page 4: KPI Explorer

#### KPI Selector
- Dropdown: Select any KPI from H, E, U dimensions
- E.g., "Loss Ratio", "Rejection Rate", "Utilization Rate"

#### KPI Distribution
- Histogram of selected KPI across all contracts
- Highlight where selected client falls

#### KPI Drivers Analysis
- For selected KPI, show what drives it:
  - Demographics correlation
  - Regional patterns
  - Network tier impact
  - Seasonal patterns

#### Top/Bottom Performers
- Top 10 contracts with best KPI value
- Bottom 10 with worst KPI value
- What's different about them?

---

### Page 5: Recommendations Dashboard

#### Priority Queue
- Sorted list of contracts needing attention
- Priority score = IVI Risk x Premium x Actionability
- Columns: Contract, IVI, Premium, Primary Issue, Recommended Action

#### Action Tracking
- Status: Pending, In Progress, Completed
- Outcome: Retained, Lost, Pending renewal
- Notes field for account manager

#### Impact Dashboard
- Contracts with improved IVI after intervention
- Retention rate: Acted-on vs Not acted-on
- ROI calculation: Premium saved vs effort invested

---

## Technical Implementation

### Tech Stack
- **Framework:** Streamlit
- **Data:** Polars (fast loading), cached with st.cache_data
- **Visualizations:** Plotly (interactive), Altair
- **Styling:** Custom CSS for Bupa branding

### File Structure
```
dashboard/
    app.py                  # Main entry point
    pages/
        1_Portfolio.py      # Portfolio overview
        2_Client_Dive.py    # Client deep dive
        3_Segments.py       # Segment analysis
        4_KPI_Explorer.py   # KPI exploration
        5_Recommendations.py# Action tracking
    components/
        kpi_card.py         # Reusable KPI display
        gauge_chart.py      # Score gauges
        waterfall.py        # Cost waterfall
        radar.py            # Peer comparison
    utils/
        data_loader.py      # Load parquet files
        scoring.py          # IVI calculation
        recommendations.py  # Action generator
    assets/
        style.css           # Custom styling
        bupa_logo.png       # Branding
```

### Data Loading
```python
import streamlit as st
import polars as pl
from pathlib import Path

DATA_DIR = Path('/volume/data/processed')

@st.cache_data
def load_contract_data():
    return pl.read_parquet(DATA_DIR / 'contract_level.parquet')

@st.cache_data
def load_ivi_scores():
    return pl.read_parquet(DATA_DIR / 'models' / 'ivi_scores.parquet')
```

### Key Components

#### 1. IVI Gauge
```python
import plotly.graph_objects as go

def ivi_gauge(score, title="IVI Score"):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "#D64045"},
                {'range': [30, 60], 'color': "#FF6B35"},
                {'range': [60, 100], 'color': "#2E8B57"}
            ],
        }
    ))
    return fig
```

#### 2. Cost Waterfall
```python
def cost_waterfall(base, demographics, network, chronic, catastrophic):
    fig = go.Figure(go.Waterfall(
        name = "Cost Breakdown",
        orientation = "v",
        measure = ["absolute", "relative", "relative", "relative", "relative", "total"],
        x = ["Base", "Demographics", "Network", "Chronic", "Catastrophic", "Total"],
        y = [base, demographics, network, chronic, catastrophic, 0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    return fig
```

#### 3. Recommendation Generator
```python
def generate_recommendations(client_data):
    recommendations = []
    
    # Experience issues
    if client_data['REJECTION_RATE'] > 0.25:
        recommendations.append({
            'priority': 'HIGH',
            'issue': 'High pre-auth rejection rate',
            'cause': f"Rejection rate {client_data['REJECTION_RATE']:.0%} vs 15% avg",
            'action': 'Review rejection reasons, consider network expansion',
            'impact': 'Could improve E_SCORE by 15-20 points'
        })
    
    # Cost issues
    if client_data['LOSS_RATIO'] > 1.2:
        recommendations.append({
            'priority': 'HIGH',
            'issue': 'Unprofitable loss ratio',
            'cause': f"Loss ratio {client_data['LOSS_RATIO']:.2f} (break-even = 1.0)",
            'action': 'Premium adjustment or benefit redesign discussion',
            'impact': 'Required for sustainable renewal'
        })
    
    # Health issues
    if client_data['UTILIZATION_RATE'] > 0.7:
        recommendations.append({
            'priority': 'MEDIUM',
            'issue': 'High healthcare utilization',
            'cause': f"Utilization {client_data['UTILIZATION_RATE']:.0%} vs 52% avg",
            'action': 'Wellness program, preventive screenings',
            'impact': 'Long-term cost reduction'
        })
    
    return sorted(recommendations, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['priority']])
```

---

## Development Phases

### Phase 1: Core Dashboard (MVP)
- Portfolio overview with IVI distribution
- Basic client lookup with H/E/U scores
- Segment filtering
- **Timeline:** 2-3 days

### Phase 2: Deep Dive Features
- Cost waterfall analysis
- Root cause analysis per KPI
- Peer comparison radar
- **Timeline:** 2-3 days

### Phase 3: Recommendations & Tracking
- Auto-generated recommendations
- Action tracking (requires backend/DB)
- Impact measurement
- **Timeline:** 3-4 days

### Phase 4: Polish & Demo
- Bupa branding
- Performance optimization
- Demo script preparation
- **Timeline:** 1-2 days

---

## Demo Script

### Scenario 1: Portfolio Review
"Let's start with the portfolio overview. We can see we have X contracts with Y billion in premium. Notice that Z% of our premium is currently in high-risk contracts. Let's drill down..."

### Scenario 2: At-Risk Client Investigation
"Let's look at Contract ABC - they have an IVI score of 28, which puts them in the high-risk category. Looking at the sub-scores, we see their E score is particularly low at 32. Drilling into Experience, we see high rejection rates at 38%. The root cause analysis shows they're primarily using providers in the Northern region where we have limited network coverage..."

### Scenario 3: Taking Action
"Based on this analysis, the system recommends three actions: 1) Assign a dedicated claims handler, 2) Discuss network upgrade options, 3) Consider expanding our provider network in their region. Let's mark this for follow-up..."

### Scenario 4: Segment-Level Strategy
"Now let's look at all HIGH_RISK_LARGE_PROFITABLE contracts - these are our priority retention targets because they're at risk but still valuable. We have 45 contracts in this segment representing 2.3B in premium. The common issues are..."
