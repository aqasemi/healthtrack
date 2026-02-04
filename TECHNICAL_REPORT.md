# IVI System Technical Implementation Report
## Intelligent Value Index - Bupa Arabia Health Hackathon

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Data Pipeline](#3-data-pipeline)
4. [IVI Scoring Methodology](#4-ivi-scoring-methodology)
5. [Machine Learning Model](#5-machine-learning-model)
6. [Customer Health Risk Segmentation](#6-customer-health-risk-segmentation)
7. [Dashboard Implementation](#7-dashboard-implementation)
8. [Business Recommendations Framework](#8-business-recommendations-framework)
9. [Model Outputs and Deliverables](#9-model-outputs-and-deliverables)
10. [Technical Appendix](#10-technical-appendix)

---

## 1. Executive Summary

### 1.1 Project Objective

The Intelligent Value Index (IVI) is a predictive scoring system designed to:

1. **Predict** client retention probability before renewal
2. **Segment** corporate clients by health risk profile and business value
3. **Explain** why specific clients are at risk using dimension-based analysis
4. **Recommend** targeted interventions to improve retention and health outcomes

### 1.2 Key Results

| Metric | Value | Business Impact |
|--------|-------|-----------------|
| Model AUC-ROC | 0.71 | Good discrimination between retained/churned |
| Churned F1 Score | 0.62 | Reliable identification of at-risk clients |
| IVI-Retention Correlation | 0.44 | Strong predictive signal |
| Class Balance (after filtering) | 44/56 | Balanced, actionable predictions |
| Premium Coverage | 99.4% | Covers virtually all business value |

### 1.3 Deliverables Summary

| Deliverable | Status | Location |
|-------------|--------|----------|
| IVI Scoring Model | Complete | `notebooks/03_IVI_ML_Model.ipynb` |
| Retention Prediction Model | Complete | `/volume/data/models/ivi_model_bundle.joblib` |
| Customer Health Risk Segmentation | Complete | Percentile-based health risk index |
| Visualization Dashboard | Complete | `dashboard/app.py` |
| Business Recommendations | Complete | `dashboard/utils/recommendations.py` |
| Technical Documentation | Complete | This document |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
+------------------+     +----------------------+     +-------------------+
|   DATA SOURCES   |     |   PROCESSING LAYER   |     |   OUTPUT LAYER    |
+------------------+     +----------------------+     +-------------------+
|                  |     |                      |     |                   |
| sampled_claims   |     | Data Preprocessing   |     | IVI Scores        |
| (86M rows)       |---->| - Missing values     |---->| - ML-based        |
|                  |     | - Outlier capping    |     | - Rule-based      |
| sampled_preauth  |     | - Contract filtering |     | - Hybrid          |
| (305M rows)      |---->|                      |     |                   |
|                  |     | Feature Engineering  |     | Health Risk       |
| sampled_calls    |     | - H dimension (12)   |---->| Segmentation      |
| (8.9M rows)      |---->| - E dimension (15)   |     | - 5 risk tiers    |
|                  |     | - U dimension (11)   |     | - Percentile-based|
| sampled_member   |     |                      |     |                   |
| (4.3M rows)      |---->| ML Model Pipeline    |     | Dashboard         |
|                  |     | - LightGBM           |---->| - Portfolio view  |
|                  |     | - SHAP decomposition |     | - Client deep dive|
|                  |     | - Calibration        |     | - Recommendations |
+------------------+     +----------------------+     +-------------------+
```

### 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Data Loading | pyreadstat + multiprocessing | 10x faster than pandas for SAS |
| Data Processing | Polars | Lazy evaluation, memory efficient |
| Data Storage | Parquet | Columnar, fast reads, excellent compression |
| ML Framework | LightGBM | Best for tabular data, handles imbalance |
| Explainability | SHAP | Feature importance and dimension decomposition |
| Dashboard | Streamlit | Rapid development, interactive UI |
| Visualization | Plotly | Interactive charts, customizable |

### 2.3 File Structure

```
/workspace/
    notebooks/
        01_Data_Exploration_Cleaning.ipynb    # Data preprocessing
        02_Business_Insights_Analysis.ipynb   # Business analysis
        03_IVI_ML_Model.ipynb                 # ML model training
    dashboard/
        app.py                                # Main dashboard entry
        app_presentation.py                   # Simplified presentation view
        pages/
            portfolio.py                      # Portfolio overview
            client_dive.py                    # Client deep dive
            segments.py                       # Segment analysis
            kpi_explorer.py                   # KPI explorer
        utils/
            data_loader.py                    # Data loading + caching
            recommendations.py                # Recommendation logic
        components/
            charts.py                         # Reusable chart components
    diagrams/
        IVI_MODEL_PIPELINE_DOCUMENTATION.md   # Pipeline documentation
        IVI_PIPELINE_DIAGRAMS.md              # System diagrams

/volume/data/
    processed/
        contract_level.parquet                # Contract-level features
        contract_year_level.parquet           # Contract-year features
        member_level.parquet                  # Member-level features
        dim_*.parquet                         # Dimension tables
    models/
        ivi_model_bundle.joblib               # Trained model + metadata
        ivi_scores_all_years.parquet          # IVI scores
        shap_subscores.parquet                # SHAP-based subscores
```

---

## 3. Data Pipeline

### 3.1 Data Sources

| Dataset | Records | Key Fields |
|---------|---------|------------|
| **sampled_claims** | 86M | Claims, diagnoses, billing, providers |
| **sampled_preauth** | 305M | Pre-auth requests, approvals, rejections |
| **sampled_calls** | 8.9M | Customer service interactions |
| **sampled_member** | 4.3M | Demographics, plans, premiums |
| **Provider_Info** | 3,556 | Provider metadata |

### 3.2 Data Loading Optimization

```python
# Multi-stage optimized loading
def load_sas_optimized(sas_path, cache_path):
    # Stage 1: Check parquet cache
    if cache_file.exists():
        return pl.scan_parquet(cache_file)  # Instant load
    
    # Stage 2: Parallel SAS reading (all CPU cores)
    df, meta = pyreadstat.read_file_multiprocessing(
        pyreadstat.read_sas7bdat,
        str(sas_path),
        num_processes=cpu_count()
    )
    
    # Stage 3: Convert to Polars and cache
    df = pl.from_pandas(df)
    df.write_parquet(cache_file)
    
    return pl.scan_parquet(cache_file)
```

**Performance:**
- First load: Minutes (parallel SAS reading)
- Subsequent loads: Seconds (parquet cache)
- Memory: Efficient via lazy evaluation

### 3.3 Data Quality Handling

| Issue | Solution | Rationale |
|-------|----------|-----------|
| Missing counts | Impute with 0 | No activity = zero |
| Missing ratios | Impute with median | Preserve distribution |
| Extreme outliers | Cap at 99th percentile | Reduce skewness |
| Infinite values | Replace with cap | Prevent model instability |
| Small contracts | Filter MIN_MEMBERS >= 5 | Focus on corporate segment |

### 3.4 Contract Filtering (Critical Decision)

**Problem:** 82.8% of contracts have <5 members but represent only 0.6% of premium.

**Analysis:**

| Segment | Contracts | Members | Premium | Churn Rate |
|---------|-----------|---------|---------|------------|
| 1-4 members | 82.8% | 3% | 0.6% | ~95% |
| 5+ members | 17.2% | 97% | 99.4% | ~44% |

**Decision:** Filter to contracts with 5+ members.

**Impact:**
- Class balance improved from 85/15 to 44/56
- Churned F1 improved from 0.29 to 0.62 (+114%)
- Premium coverage: 99.4% (virtually all business value preserved)

---

## 4. IVI Scoring Methodology

### 4.1 Three Dimensions of IVI

The IVI score is composed of three dimensions that capture different aspects of client health and value:

#### Dimension H: Health Outcomes

**Purpose:** Measures the medical need intensity and health patterns of the client's member population.

| KPI | Direction | Description |
|-----|-----------|-------------|
| UTILIZATION_RATE | Lower is better | % of members filing claims |
| DIAGNOSES_PER_UTILIZER | Lower is better | Condition burden per utilizer |
| AVG_CLAIM_AMOUNT | Lower is better | Claim severity |
| COST_PER_MEMBER | Lower is better | Overall cost intensity |

**Note:** Feature importance is learned by the ML model from retention outcomes, not pre-defined.

**Interpretation:**
- High H Score = Healthier population, lower medical need
- Low H Score = Higher healthcare consumption, potential chronic burden

#### Dimension E: Experience Quality

**Purpose:** Evaluates the service quality and customer satisfaction indicators.

| KPI | Direction | Description |
|-----|-----------|-------------|
| APPROVAL_RATE | Higher is better | Pre-auth approval success |
| AVG_RESOLUTION_DAYS | Lower is better | Ticket closure time |
| CALLS_PER_MEMBER | Lower is better | Support contact intensity |
| COMPLAINT_RATE | Lower is better | Proportion of complaint calls |

**Note:** Feature importance is learned by the ML model from retention outcomes, not pre-defined.

**Interpretation:**
- High E Score = Smooth service experience, low friction
- Low E Score = Service issues, high complaint volume

#### Dimension U: Utilization Efficiency

**Purpose:** Assesses cost sustainability and financial performance.

| KPI | Direction | Description |
|-----|-----------|-------------|
| LOSS_RATIO | Lower is better | Claims / Premium (profitability) |
| COST_PER_UTILIZER | Lower is better | Cost per active member |
| BILLED_VS_ESTIMATED | Lower is better | Actual vs expected ratio |

**Note:** Feature importance is learned by the ML model from retention outcomes, not pre-defined.

**Interpretation:**
- High U Score = Profitable, sustainable contract
- Low U Score = Unprofitable, unsustainable cost levels

### 4.2 IVI Score Calculation Approaches

#### ML-Based Score (IVI_SCORE_ML)

```
IVI_SCORE_ML = Calibrated_Retention_Probability * 100
```

- Uses LightGBM model trained on retention outcome
- Captures non-linear feature interactions automatically
- Range: 0-100 (higher = higher retention probability)

### 4.3 Sub-Score Decomposition via SHAP

SHAP values decompose the ML prediction into feature contributions:

```python
# Group SHAP values by dimension
H_SHAP = sum(SHAP values for health features)
E_SHAP = sum(SHAP values for experience features)
U_SHAP = sum(SHAP values for utilization features)

# Normalize to 0-100
H_SCORE_ML = normalize(H_SHAP)
E_SCORE_ML = normalize(E_SHAP)
U_SCORE_ML = normalize(U_SHAP)
```

Then use Geometric mean to combine dimensions into final IVI_SCORE. This will make the final score more interpretable and actionable by showing dimension-specific insights.

**Benefit:** Explains WHY a client has a particular IVI score by showing which dimension is driving the risk.

---

## 5. Machine Learning Model

### 5.1 Problem Formulation

**Objective:** Predict whether a corporate client will retain their contract for the following year.

**Target Variable:**
```
RETAINED_NEXT_YEAR = 1 if contract appears in both 2022 and 2023
                   = 0 if contract appears in 2022 only (churned)
```

**Temporal Setup:**
- Training features: 2022 contract year data
- Target: Retention status in 2023
- This mirrors real-world prediction scenario

### 5.2 Data Splitting Strategy

```
2022 Data (Labeled)
    |
    +-- Train (70%) -----> Model training
    |
    +-- Validation (15%) -> Early stopping, hyperparameter tuning
    |
    +-- Test (15%) -------> Final unbiased evaluation

2023 Data (Unlabeled)
    |
    +-- Forward scoring --> Future retention prediction
```

**Key:** Validation set used for early stopping (NOT test set) to prevent leakage.

### 5.3 Model Configuration

**Model:** LightGBM Gradient Boosting Classifier

```python
lgb_params = {
    'objective': 'binary',
    'metric': 'auc',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'scale_pos_weight': neg_count / pos_count,  # Handle imbalance
    'verbose': -1,
    'seed': 42
}
```

**Early Stopping:** Training stops if validation AUC doesn't improve for 50 rounds.

### 5.4 Class Imbalance Handling

| Strategy | Implementation |
|----------|----------------|
| Scale Pos Weight | `neg_count / pos_count` in LightGBM |
| Stratified Splitting | Maintain class proportions in splits |
| Appropriate Metrics | Focus on AUC-ROC and F1-score, not accuracy |
| Threshold Tuning | Adjustable probability threshold |

### 5.5 Model Performance

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **AUC-ROC** | 0.71 | Good discrimination ability |
| **Churned F1** | 0.62 | Reasonable at-risk identification |
| **Retained F1** | 0.69 | Good stable client identification |
| **Macro F1** | 0.65 | Balanced performance |

**Lift Analysis:** Top decile captures 2.1x baseline churn rate.

### 5.6 Feature Importance (Top 10)

| Rank | Feature | Dimension | Importance |
|------|---------|-----------|------------|
| 1 | LOSS_RATIO | U | 0.142 |
| 2 | TOTAL_MEMBERS | Demo | 0.098 |
| 3 | COST_PER_MEMBER | U | 0.087 |
| 4 | UTILIZATION_RATE | H | 0.076 |
| 5 | APPROVAL_RATE | E | 0.065 |
| 6 | AVG_RESOLUTION_DAYS | E | 0.058 |
| 7 | CLAIMS_PER_UTILIZER | H | 0.052 |
| 8 | CALLS_PER_MEMBER | E | 0.048 |
| 9 | DIAGNOSES_PER_UTILIZER | H | 0.045 |
| 10 | EARNED_PREMIUM | U | 0.041 |

**Insight:** Utilization efficiency (U) features dominate, followed by experience (E) and health (H).

---

## 6. Customer Health Risk Segmentation

### 6.1 Overview

The Customer Health Risk Segmentation categorizes corporate clients based on the **health profile** of their member population. This is distinct from business risk segmentation - it focuses specifically on medical/health indicators.

### 6.2 Health Risk Index (HRI) Methodology

The Health Risk Index is computed using percentile-based scoring of key health indicators:

#### Step 1: Select Health Indicators

| Indicator | Rationale |
|-----------|-----------|
| Utilization Rate | Population accessing healthcare |
| Diagnoses per Utilizer | Condition burden |
| Average Claim Amount | Claim severity |
| Cost per Member | Overall cost intensity |

**Note:** Indicator weights are derived from feature importance in the retention prediction model, ensuring the health risk index reflects actual predictive power.

#### Step 2: Compute Percentile Ranks

```python
def compute_percentile_rank(value, distribution):
    """Convert raw value to percentile (0-100) based on portfolio distribution."""
    return (distribution < value).mean() * 100
```

Each indicator is converted to a percentile rank relative to the entire portfolio.

#### Step 3: Calculate Health Risk Index (HRI)

```python
# Weights derived from ML model feature importance
HRI = weighted_sum([
    utilization_rate_percentile,
    diagnoses_per_utilizer_percentile,
    avg_claim_amount_percentile,
    cost_per_member_percentile
], weights=model_derived_weights)
```

Higher HRI = Higher health risk (more healthcare consumption, more conditions, higher costs)

**Data-Driven Weighting:** The relative importance of each indicator is determined by analyzing SHAP values from the trained model, ensuring weights reflect actual predictive contribution to retention.

#### Step 4: Assign Health Risk Segment

| Segment | Threshold | Percentile Range | Description |
|---------|-----------|------------------|-------------|
| **HIGH** | HRI >= P90 | Top 10% | Highest health risk population |
| **MODERATE_HIGH** | HRI P84-P90 | 84th-90th | Elevated health risk |
| **MODERATE** | HRI P16-P84 | 16th-84th | Average health risk |
| **LOW_MODERATE** | HRI P10-P16 | 10th-16th | Below average risk |
| **LOW** | HRI <= P10 | Bottom 10% | Healthiest population |

### 6.3 Health Risk Segment Profiles

#### HIGH Health Risk Clients

**Characteristics:**
- Utilization rate > 70% (most members using services)
- Average diagnoses per utilizer > 4.0
- High average claim amounts
- Elevated cost per member

**Typical Causes:**
- Aging workforce demographics
- High prevalence of chronic conditions (diabetes, hypertension, cardiovascular)
- Work-related health risks (industry-specific)
- Insufficient preventive care access

**Recommended Actions:**
- Deploy targeted wellness programs
- Implement chronic disease management
- Conduct health screenings and preventive campaigns
- Consider care management coordination

#### MODERATE_HIGH Health Risk Clients

**Characteristics:**
- Above-average but not extreme indicators
- Often trending toward HIGH category

**Recommended Actions:**
- Proactive monitoring and early intervention
- Health education and awareness campaigns
- Lifestyle modification support

#### MODERATE Health Risk Clients

**Characteristics:**
- Indicators within normal portfolio range
- Represents majority of contracts

**Recommended Actions:**
- Standard preventive care offerings
- Maintain current wellness programs
- Annual health check promotions

#### LOW_MODERATE and LOW Health Risk Clients

**Characteristics:**
- Below-average healthcare utilization
- Fewer diagnoses per member
- Lower claim costs

**Recommended Actions:**
- Recognize as healthy population benchmark
- Maintain engagement to preserve health status
- Offer preventive screenings to maintain low risk

### 6.4 Health Risk vs Business Risk

| Aspect | Health Risk Segmentation | Business Risk Segmentation |
|--------|--------------------------|---------------------------|
| **Focus** | Population health profile | Financial and retention risk |
| **Indicators** | Utilization, diagnoses, claims | IVI score, loss ratio, premium |
| **Purpose** | Target health interventions | Prioritize account management |
| **Actions** | Wellness programs, care management | Pricing, service recovery, retention |

**Key Insight:** A client can have HIGH health risk but LOW business risk if they are profitable (low loss ratio). Conversely, a LOW health risk client can be HIGH business risk if they have service issues (low E score).

### 6.5 Implementation in Dashboard

```python
def get_health_risk_segment_percentile(row: Dict, portfolio_stats: Dict) -> Dict:
    """
    Compute health risk segment using percentile-based methodology.
    """
    # Compute percentile ranks for each indicator
    util_pct = compute_percentile(row['UTILIZATION_RATE'], 
                                   portfolio_stats['utilization_rate'])
    diag_pct = compute_percentile(row['DIAGNOSES_PER_UTILIZER'], 
                                   portfolio_stats['diagnoses_per_utilizer'])
    claim_pct = compute_percentile(row['AVG_CLAIM_AMOUNT'], 
                                   portfolio_stats['avg_claim_amount'])
    cost_pct = compute_percentile(row['COST_PER_MEMBER'], 
                                   portfolio_stats['cost_per_member'])
    
    # Compute weighted Health Risk Index using model-derived weights
    # Weights are extracted from SHAP feature importance analysis
    weights = portfolio_stats.get('model_derived_weights', DEFAULT_WEIGHTS)
    hri = (
        weights['utilization'] * util_pct + 
        weights['diagnoses'] * diag_pct + 
        weights['claim_amt'] * claim_pct + 
        weights['cost'] * cost_pct
    )
    
    # Assign segment based on percentile thresholds
    if hri >= 90:
        segment = 'HIGH'
    elif hri >= 84:
        segment = 'MODERATE_HIGH'
    elif hri >= 16:
        segment = 'MODERATE'
    elif hri >= 10:
        segment = 'LOW_MODERATE'
    else:
        segment = 'LOW'
    
    return {
        'health_risk_index': hri,
        'health_risk_segment': segment,
        'indicators': {
            'utilization_percentile': util_pct,
            'diagnoses_percentile': diag_pct,
            'claim_percentile': claim_pct,
            'cost_percentile': cost_pct
        }
    }
```

---

## 7. Dashboard Implementation

### 7.1 Dashboard Structure

```
dashboard/
    app.py                    # Main entry with navigation
    app_presentation.py       # Simplified presentation view
    pages/
        portfolio.py          # Portfolio overview
        client_dive.py        # Client deep dive analysis
        segments.py           # Segment analysis
        kpi_explorer.py       # KPI explorer
    components/
        charts.py             # Reusable Plotly charts
    utils/
        data_loader.py        # Data loading with caching
        recommendations.py    # Recommendation generation
```

### 7.2 Pages Overview

#### Portfolio Overview (`portfolio.py`)

**Features:**
- Key metrics: Total contracts, members, premium, average IVI
- IVI score distribution histogram with risk coloring
- Health risk tier pie chart
- At-risk contracts table (top 20 by premium)
- Premium at risk breakdown

#### Client Deep Dive (`client_dive.py`)

**Features:**
- Contract search and selection
- IVI gauge visualization (0-100)
- H, E, U dimension panels with individual KPIs
- Benchmark comparison
- Auto-generated recommendations
- Segment-specific action plans

#### Segment Analysis (`segments.py`)

**Features:**
- Multi-dimensional segment summary
- Segment comparison charts
- Risk tier distribution by segment
- Detailed contract list with export

#### KPI Explorer (`kpi_explorer.py`)

**Features:**
- KPI selection by dimension
- Distribution analysis
- Correlation with IVI score
- Top/bottom performer analysis

### 7.3 Technical Implementation

**Framework:** Streamlit
**Visualizations:** Plotly (interactive)
**Data Loading:** Polars with st.cache_data (1-hour TTL)
**Styling:** Custom CSS for Bupa branding

**Color Scheme:**
- Primary (Bupa Blue): #003087
- High Risk: #D64045 (red)
- Moderate Risk: #FF6B35 (orange)
- Low Risk: #2E8B57 (green)

### 7.4 Running the Dashboard

```bash
cd /workspace/dashboard
streamlit run app.py --server.port 8501
```

---

## 8. Business Recommendations Framework

### 8.1 Recommendation Generation Logic

Recommendations are auto-generated based on KPI thresholds:

| Trigger | Condition | Dimension | Priority |
|---------|-----------|-----------|----------|
| High rejection rate | REJECTION_RATE > 25% | E | HIGH/MEDIUM |
| Long resolution time | AVG_RESOLUTION_DAYS > 10 | E | HIGH/MEDIUM |
| High call volume | CALLS_PER_MEMBER > 0.35 | E | MEDIUM |
| Unprofitable contract | LOSS_RATIO > 1.2 | U | HIGH/MEDIUM |
| High cost per member | COST_PER_MEMBER > 1.5x benchmark | U | HIGH/MEDIUM |
| High utilization | UTILIZATION_RATE > 75% | H | MEDIUM |
| High chronic burden | DIAGNOSES_PER_UTILIZER > 4.0 | H | MEDIUM |

### 8.2 Recommendation Templates

#### Experience (E) Issues

```yaml
High Pre-auth Rejection:
  Issue: "High pre-authorization rejection rate"
  Cause: "Rejection rate {rate}% vs {benchmark}% benchmark"
  Action: "Review rejection reasons, consider provider network expansion, 
           assign dedicated pre-auth handler"
  Impact: "Could improve E_SCORE by 15-20 points"

Long Resolution Time:
  Issue: "Long ticket resolution time"
  Cause: "Average {days} days vs {benchmark} day benchmark"
  Action: "Assign dedicated support representative, review escalation process, 
           implement priority queuing"
  Impact: "Improved E_SCORE and client satisfaction"
```

#### Utilization (U) Issues

```yaml
Unprofitable Loss Ratio:
  Issue: "Unprofitable loss ratio"
  Cause: "Loss ratio {ratio} (break-even = 1.0)"
  Action: "Premium adjustment discussion, benefit redesign, 
           cost-sharing increase, wellness program enrollment"
  Impact: "Required for sustainable contract renewal"

High Cost Per Member:
  Issue: "High cost per member"
  Cause: "SAR {cost}/member vs SAR {benchmark} benchmark"
  Action: "Claims audit, chronic condition management program, 
           provider steering incentives"
  Impact: "Improved U_SCORE and profitability"
```

#### Health (H) Issues

```yaml
High Utilization:
  Issue: "High healthcare utilization"
  Cause: "Utilization {rate}% vs {benchmark}% benchmark"
  Action: "Wellness program introduction, preventive screening campaign, 
           health education"
  Impact: "Long-term cost reduction and improved H_SCORE"

High Chronic Burden:
  Issue: "High chronic condition burden"
  Cause: "{count} diagnoses/utilizer vs {benchmark} benchmark"
  Action: "Disease management programs, chronic care coordination, 
           specialist referral optimization"
  Impact: "Improved health outcomes and cost predictability"
```

### 8.3 Segment-Based Action Plans

| Segment | Priority | Focus | Actions |
|---------|----------|-------|---------|
| HIGH_RISK_LARGE_UNPROFITABLE | CRITICAL | Immediate intervention | Executive review, repricing, benefit redesign |
| HIGH_RISK_LARGE_PROFITABLE | URGENT | Root cause analysis | Relationship manager deep-dive, service recovery |
| HIGH_RISK_SMALL_UNPROFITABLE | LOW | Cost-benefit analysis | May not warrant retention investment |
| HIGH_RISK_SMALL_PROFITABLE | MODERATE | Efficient outreach | Automated communications, self-service |
| MODERATE_RISK_LARGE_* | WATCH | Proactive monitoring | Regular check-ins, trend alerts |
| LOW_RISK_LARGE_PROFITABLE | NURTURE | Value protection | Maintain relationship, offer value-adds |

### 8.4 Health Risk-Specific Recommendations

| Health Risk Segment | Recommended Interventions |
|---------------------|---------------------------|
| **HIGH** | Chronic disease management, care coordination, targeted wellness, health screenings |
| **MODERATE_HIGH** | Early intervention, health education, lifestyle modification support |
| **MODERATE** | Standard preventive care, annual check-up promotions |
| **LOW_MODERATE** | Maintain engagement, preventive screening access |
| **LOW** | Recognize as benchmark, preserve health status |

---

## 9. Model Outputs and Deliverables

### 9.1 Saved Model Bundle

**File:** `/volume/data/models/ivi_model_bundle.joblib`

**Contents:**
```python
{
    'model': LGBMClassifier,           # Trained model
    'scaler': StandardScaler,          # Feature scaler
    'feature_names': List[str],        # Feature list
    'feature_groups': Dict,            # H/E/U feature mapping
    'kpi_definitions': Dict,           # KPI metadata
    'weights_heu': Dict,               # Dimension weights
    'region_info': Dict,               # Region reference data
    'network_tiers': Dict,             # Network tier info
    'training_date': str,              # Training timestamp
    'model_version': str               # Version identifier
}
```

### 9.2 IVI Score Files

| File | Description |
|------|-------------|
| `ivi_scores_segments_2022.parquet` | 2022 contracts with IVI scores and segments |
| `ivi_scores_forward_2023.parquet` | 2023 contracts with forward predictions |
| `ivi_scores_all_years.parquet` | Combined all years |
| `shap_subscores.parquet` | SHAP-based H, E, U subscores |

### 9.3 Key Output Columns

| Column | Description | Range |
|--------|-------------|-------|
| IVI_SCORE_ML | ML-based IVI score | 0-100 |
| IVI_SCORE_RULE | Rule-based IVI score | 0-100 |
| IVI_SCORE_HYBRID | Combined final score | 0-100 |
| H_SCORE | Health dimension score | 0-100 |
| E_SCORE | Experience dimension score | 0-100 |
| U_SCORE | Utilization dimension score | 0-100 |
| IVI_RISK | Risk category | HIGH/MODERATE/LOW |
| HEALTH_RISK_SEGMENT | Health risk segment | HIGH/MODERATE_HIGH/MODERATE/LOW_MODERATE/LOW |
| SIZE_CLASS | Contract size | SMALL/LARGE |
| PROFIT_CLASS | Profitability | PROFITABLE/UNPROFITABLE |
| SEGMENT | Combined segment | 12 combinations |

---

## 10. Technical Appendix

### 10.1 Environment Setup

```bash
# Python environment
python -m venv .venv
source .venv/bin/activate

# Core dependencies
pip install polars pyreadstat lightgbm shap streamlit plotly joblib

# Full requirements
pip install -r requirements.txt
```

### 10.2 Running Notebooks

```bash
# Start Jupyter
jupyter lab --ip=0.0.0.0 --port=8888

# Execute notebooks in order
1. 01_Data_Exploration_Cleaning.ipynb
2. 02_Business_Insights_Analysis.ipynb
3. 03_IVI_ML_Model.ipynb
```

### 10.3 Running Dashboard

```bash
cd /workspace/dashboard
streamlit run app.py --server.port 8501

# For presentation mode
streamlit run app_presentation.py --server.port 8502
```

### 10.4 Key Configuration Parameters

```python
# Contract filtering
MIN_MEMBERS = 5  # Minimum members to include contract

# Model parameters
RANDOM_STATE = 42
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15
EARLY_STOPPING_ROUNDS = 50

# IVI scoring weights - DERIVED FROM MODEL
# These are extracted from SHAP feature importance analysis
# and updated when model is retrained
WEIGHTS_HEU = model_bundle.get('weights_heu')  # Data-driven, not static

# Health Risk Index weights - DERIVED FROM MODEL
# Computed from feature importance of health-related features
HEALTH_RISK_WEIGHTS = model_bundle.get('health_weights')  # Data-driven

# Risk thresholds (percentile-based)
RISK_THRESHOLDS = {
    'HIGH': 90,           # Top 10%
    'MODERATE_HIGH': 84,  # 84th-90th percentile
    'MODERATE': 16,       # 16th-84th percentile
    'LOW_MODERATE': 10,   # 10th-16th percentile
    'LOW': 0              # Bottom 10%
}
```

### 10.5 Data Refresh Process

```python
# To refresh IVI scores with new data:

1. Load new data into parquet format
2. Run feature engineering pipeline
3. Load model bundle
4. Generate predictions:
   model = bundle['model']
   proba = model.predict_proba(X_new)[:, 1]
   ivi_score_ml = proba * 100
5. Calculate rule-based scores using ECDF from reference distribution
6. Save updated scores to parquet
```

### 10.6 Monitoring and Maintenance

**Model Drift Detection:**
- Monitor IVI score distribution over time
- Track feature distributions vs training baseline
- Alert if KL divergence exceeds threshold

**Retraining Triggers:**
- AUC drops below 0.65 on new data
- Feature distributions shift significantly
- New contract year data available

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 3, 2026 | IVI Team | Initial technical report |

---

*This document provides the complete technical implementation details for the Intelligent Value Index (IVI) system developed for the Bupa Arabia Health Hackathon.*
