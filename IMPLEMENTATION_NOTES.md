# IVI Project - Implementation Notes

## Experiments Log (Feb 2026)

### Experiment: MIN_MEMBERS=5 Filtering (Feb 3, 2026)

**Configuration:**
- Filtering threshold: MIN_MEMBERS=5 (changed from 15)
- Model: LightGBM with regularization

**Results:**
| Metric | Before (MIN=15) | After (MIN=5) |
|--------|-----------------|---------------|
| Churned F1 | 0.29 | **0.62** |
| Retained F1 | ~0.70 | 0.69 |
| Macro F1 | ~0.50 | **0.65** |
| AUC-ROC | ~0.75 | 0.71 |
| IVI Correlation | 0.50 | 0.44 |
| Class Balance | 85/15 | 44/56 |

**Analysis:**
- MIN_MEMBERS=5 dramatically improved class balance (from 85/15 to 44/56)
- Churned F1 improved from 0.29 to 0.62 (+114%)
- IVI correlation decreased from 0.50 to 0.44 (expected with more balanced data)
- AUC decreased slightly from ~0.75 to 0.71 (model has less "easy" small contracts to classify)

**Conclusion:**
- The MIN_MEMBERS=5 filter is BETTER for business relevance
- Small contracts (1-4 members) are very noisy and not representative
- The improved churned F1 means we can better identify at-risk contracts
- Trade-off: Lower overall AUC but more balanced, actionable predictions

**Key Insight:** The original "high" correlation (0.5) was inflated by:
1. Small contracts clustering at extremes (easy to classify)
2. Severe class imbalance making "always predict churn" seem accurate

---

## Recent Fixes (Feb 2026)

### Notebook 03_IVI_ML_Model.ipynb - Code Reorganization

**Issues Fixed:**
1. **Cell execution order issues** - Cell 22 (IVI scoring) used `available_features` before it was defined
2. **Missing segmentation code** - `IVI_RISK` and `SEGMENT` columns were used before being created
3. **Variable definitions out of order** - `KPI_DEFINITIONS`, `REGION_INFO`, `NETWORK_TIERS` were defined late in the notebook but used earlier
4. **Visualization dependencies** - Cells referenced columns that didn't exist yet

**Changes Made:**
- Moved `KPI_DEFINITIONS`, `REGION_INFO`, `NETWORK_TIERS`, and `RULE_FEATURES` to the IVI scoring cell (cell 22)
- Added segmentation logic (`IVI_RISK`, `SIZE_CLASS`, `PROFIT_CLASS`, `SEGMENT`) directly in the IVI scoring cell
- Added `IVI_SCORE_ML`, `IVI_SCORE_RULE`, `IVI_SCORE_RULE_NL` columns for compatibility
- Added defensive checks (`if 'column' in df.columns`) to prevent errors
- Fixed `analyze_client` and `visualize_client_analysis` functions to handle missing keys gracefully

**Key Learning:** In notebooks, ensure variables are defined before they are used, even if cells can be run out of order. Always add defensive checks for column existence.

---

### Small Contractor Filtering (Feb 2026)

**Problem:** IVI score distribution was bimodal (clustered around 0 and 100) because:
1. Small contractors (<15 members) have high variance in metrics
2. They constitute majority of contracts but small portion of premium
3. Model easily predicts them as "will churn" or "will stay" with high confidence

**Solution:** Filter out contracts with <15 members before modeling

**Impact Analysis (before removing small contractors):**
- ~85% of contracts were <15 members
- They represented ~10% of total premium
- Removal gives better IVI score distribution and business relevance

**Contract Dynamics Analysis Added:**
- Churned contracts (2022 only): Analyzed size, region, premium
- New contracts (2023 only): Same analysis
- Retained contracts (both years): Baseline comparison

---

## CRITICAL DATA CAVEATS

### 1. Data Imbalance (SEVERE)
- **Retention Rate: 15%** (9,892 contracts retained)
- **Churn Rate: 85%** (55,887 contracts churned)
- This is a highly imbalanced classification problem
- **Impact:** Naive models will predict "churn" for everything and get 85% accuracy
- **Mitigation Strategies:**
  - Use `class_weight='balanced'` in models
  - Use SMOTE or other oversampling techniques
  - Use appropriate metrics: AUC-ROC, Precision-Recall AUC, F1-score
  - Stratified train/test splits

### 2. Limited Temporal Data (2 Years Only)
- **Available:** 2022 and 2023 contract periods only
- **Original assumption (wrong):** 3 years (2021-2023)
- **Impact:** Cannot do Year 1-2 features -> Year 3 validation as originally planned
- **Approach:** Use 2022 features to predict 2023 retention
- **Limitation:** No true out-of-time validation set

### 3. Date Field Confusion
- `CONT_YYMM`: Contract period (2022-2023) - NOT actual service dates
- `INCUR_DATE_FROM`: Actual service dates (2023-2025) - extends beyond contract period
- `CRT_DATE` (Calls): Actual call dates (2021-2025)
- Claims data shows services in 2023-2025 but tied to 2022-2023 contracts

### 4. Segmentation Considerations
- IVI score alone is insufficient for segmentation
- Need multi-dimensional segmentation considering:
  - Contract size (small vs large)
  - Industry/sector (if available)
  - Loss ratio thresholds
  - Premium tier
- Risk that model segments by "easy to predict" rather than "business relevant"

---

---

## IVI ML Model Approach (03_IVI_ML_Model.ipynb)

### Three-Phase Architecture

**Phase 1: Baseline Gradient Boosting**
- LightGBM classifier predicting retention (2022 -> 2023)
- `scale_pos_weight` to handle 85/15 class imbalance
- IVI Score = Retention Probability * 100

**Phase 2: SHAP Decomposition**
- Extract H, E, U sub-scores from SHAP values
- Group features by dimension (Health, Experience, Utilization)
- Normalize to 0-100 scale for interpretability

**Phase 3: Multi-Dimensional Segmentation**
- NOT just IVI score - combine with business metrics
- Segment by: IVI Risk + Contract Size + Profitability
- Actionable recommendations per segment

### Handling Class Imbalance

**Problem:** 85% churn, 15% retained - naive model gets 85% accuracy by always predicting churn.

**Solutions Implemented:**
1. `scale_pos_weight = neg_count / pos_count` in LightGBM
2. Stratified train/test split to maintain class proportions
3. Focus on AUC-ROC and Average Precision (not accuracy)
4. Lift analysis to validate business value

### Feature Groups

```python
FEATURE_GROUPS = {
    'H_HEALTH': ['MEMBERS_WITH_CLAIMS', 'UNIQUE_DIAGNOSES', 'UTILIZATION_RATE', ...],
    'E_EXPERIENCE': ['TOTAL_CALLS', 'APPROVAL_RATE', 'AVG_RESOLUTION_DAYS', ...],
    'U_UTILIZATION': ['LOSS_RATIO', 'COST_PER_MEMBER', 'EARNED_PREMIUM', ...],
    'DEMOGRAPHICS': ['TOTAL_MEMBERS', 'MALE_RATIO', 'NATIONALITY_COUNT', ...],
    'SEASONAL': ['Q1_CLAIMS', 'Q2_CLAIMS', 'QUARTER_CONCENTRATION', ...],
}
```

### Segmentation Logic

```
IVI Risk: HIGH (< 33rd percentile), MODERATE (33-67), LOW (> 67th)
Size: LARGE (>= median members), SMALL (< median)
Profitability: PROFITABLE (loss_ratio <= 1), UNPROFITABLE (> 1)

Combined Segment = IVI_RISK + SIZE + PROFITABILITY
Example: HIGH_RISK_LARGE_UNPROFITABLE -> CRITICAL priority
```

---

## Data Loading Pipeline

### Problem
- Raw SAS datasets are extremely large:
  - `sampled_member.sas7bdat`: ~4.3M rows
  - `sampled_calls.sas7bdat`: ~8.9M rows
  - `sampled_claims.sas7bdat`: ~86M rows
  - `sampled_preauth.sas7bdat`: ~305M rows
- `pandas.read_sas()` is very slow (single-threaded, inefficient)

### Solution: Optimized Loading Strategy

**Libraries Used:**
- `pyreadstat` - C-based SAS reader, supports multiprocessing
- `polars` - Fast DataFrame library with lazy evaluation
- Parquet caching for instant subsequent loads

**Loading Function:**
```python
import pyreadstat
import polars as pl

def load_sas_to_polars(sas_path, cache_path, name, use_cache=True):
    cache_file = cache_path / f'{name}.parquet'
    
    # Check cache first
    if use_cache and cache_file.exists():
        return pl.scan_parquet(cache_file)
    
    # Read SAS with multiprocessing
    df_pd, meta = pyreadstat.read_file_multiprocessing(
        pyreadstat.read_sas7bdat,
        str(sas_path),
        num_processes=NUM_CORES
    )
    
    # Convert to Polars and cache
    df = pl.from_pandas(df_pd)
    df.write_parquet(cache_file)
    
    return pl.scan_parquet(cache_file)
```

**Performance:**
- First run: Uses all CPU cores for parallel SAS reading
- Subsequent runs: Instant load from parquet cache
- Memory efficient: Uses Polars lazy evaluation (LazyFrame)

---

## Output Data Structure

### Multi-Level Aggregation Strategy

We preserve data at multiple granularities to avoid losing information:

| Level | File | Rows | Purpose |
|-------|------|------|---------|
| Contract | `contract_level.parquet` | ~unique contracts | IVI scoring, corporate analysis |
| Member | `member_level.parquet` | ~unique members | Individual health patterns |
| Dimension | `dim_*.parquet` | varies | Drill-down analysis |

### Output Files

**Location:** `/volume/data/processed/` (or `../data/processed/`)

#### 1. Contract-Level Data (`contract_level.parquet`)
Main dataset for IVI model development.

**Key Columns:**
- `CONTRACT_NO` - Unique contract identifier
- `TOTAL_MEMBERS` - Member count
- `TOTAL_WRITTEN_PREMIUM` - Premium collected
- `TOTAL_EARNED` - Earned premium
- `TOTAL_NET_BILLED` - Total claims amount
- `LOSS_RATIO` - Claims / Earned (sustainability metric)
- `UTILIZATION_RATE` - Members with claims / Total members
- `COST_PER_MEMBER` - Average cost per member
- `COST_PER_UTILIZER` - Average cost per utilizing member
- `CLAIMS_PER_MEMBER` - Claim frequency
- `CALLS_PER_MEMBER` - Service interaction rate
- `PREAUTH_PER_MEMBER` - Pre-auth activity rate
- `MALE_RATIO` - Gender distribution
- `*_RATE` columns - Preauth status rates

#### 2. Member-Level Data (`member_level.parquet`)
Individual member features with demographics.

**Key Columns:**
- `ADHERENT_NO` - Unique member identifier
- `CONTRACT_NO` - Parent contract
- `GENDER`, `NATIONALITY` - Demographics
- `PLAN_ID`, `PLAN_NETWORK` - Plan info
- `TOTAL_PREMIUM`, `TOTAL_EARNED` - Financial
- `TOTAL_BILLED`, `UNIQUE_CLAIMS` - Claims activity
- `IS_UTILIZER` - Flag for members with claims
- `MEMBER_LOSS_RATIO` - Individual loss ratio

#### 3. Dimension Tables (for drill-downs)

| File | Granularity | Use Case |
|------|-------------|----------|
| `dim_nationality.parquet` | Contract x Nationality | Nationality-based patterns |
| `dim_provider.parquet` | Contract x Provider | Provider utilization |
| `dim_diagnosis.parquet` | Contract x Diagnosis | Health conditions |
| `dim_calls.parquet` | Contract x Call Category | Service patterns |

#### 4. Reference Data
- `ref_provider.parquet` - Provider metadata (name, network, region, practice type)

---

## How to Load Data in Other Notebooks

```python
import polars as pl
from pathlib import Path

DATA_PATH = Path('/volume/data/processed')  # Adjust as needed

# Load full datasets
def load_contract_data() -> pl.DataFrame:
    """Load contract-level data for IVI analysis."""
    return pl.read_parquet(DATA_PATH / 'contract_level.parquet')

def load_member_data() -> pl.DataFrame:
    """Load member-level data for individual analysis."""
    return pl.read_parquet(DATA_PATH / 'member_level.parquet')

def load_dimension(name: str) -> pl.DataFrame:
    """Load dimension table. Options: nationality, provider, diagnosis, calls"""
    return pl.read_parquet(DATA_PATH / f'dim_{name}.parquet')

# Lazy loading (memory efficient for large queries)
def scan_contract_data() -> pl.LazyFrame:
    return pl.scan_parquet(DATA_PATH / 'contract_level.parquet')

def scan_member_data() -> pl.LazyFrame:
    return pl.scan_parquet(DATA_PATH / 'member_level.parquet')
```

**Usage Examples:**
```python
# For IVI model
df_contract = load_contract_data()

# For member analysis
df_members = load_member_data()

# For nationality drill-down
df_nat = load_dimension('nationality')

# Memory-efficient query
result = (
    scan_contract_data()
    .filter(pl.col('LOSS_RATIO') > 1.0)
    .select(['CONTRACT_NO', 'LOSS_RATIO', 'TOTAL_MEMBERS'])
    .collect()
)
```

---

## Experiments Log

### 2026-02-01: Data Loading Optimization

**Experiment:** Compare SAS reading methods

| Method | Time (estimated) | Notes |
|--------|------------------|-------|
| `pandas.read_sas()` | Very slow | Single-threaded |
| `pyreadstat.read_sas7bdat()` | Faster | Still single-threaded |
| `pyreadstat.read_file_multiprocessing()` | Much faster | Uses all cores |
| Parquet cache (subsequent) | Instant | Best for repeated access |

**Conclusion:** Use pyreadstat multiprocessing for initial load, cache to parquet for all future access.

---

## Key Decisions

1. **Polars over Pandas**: Faster, better memory management, lazy evaluation
2. **Multi-level aggregation**: Preserves granularity for flexible analysis
3. **Parquet format**: Fast columnar storage, good compression
4. **Dimension tables**: Enable drill-downs without re-processing raw data

---

## Next Steps

- [ ] Develop IVI scoring model using `contract_year_level.parquet`
- [x] Analyze health patterns by nationality using dimension tables
- [x] Build temporal feature engineering pipeline
- [x] Define retention target variable
- [ ] Train ML model to learn non-linear IVI relationships
- [ ] Create visualization dashboard

---

## 2026-02-03: Data Analysis and Temporal Feature Engineering

### Key Discovery: Date Fields in Data

The data has multiple date concepts that were initially confusing:

| Field | Meaning | Date Range |
|-------|---------|------------|
| `CONT_YYMM` | Contract period (policy active) | 2022-2023 |
| `INCUR_DATE_FROM` | When service was used | 2023-2025 |
| `T_PERIOD` | When claim was processed | 2023-2025 |
| `CRT_DATE` (Calls) | Actual call date | **2021-2025** |

**Insight:** The calls data has the longest history (2021-2025), while other data is tied to 2022-2023 contract periods.

### Retention Analysis

Analyzed contract retention from 2022 to 2023:

| Metric | Count | Rate |
|--------|-------|------|
| Contracts in 2022 | 65,779 | - |
| Contracts in 2023 | 77,817 | - |
| Retained (both years) | 9,892 | 15.0% |
| Churned (2022 only) | 55,887 | 85.0% |
| New in 2023 | 67,925 | - |

**Note:** High churn rate (85%) - this is the target we want to predict and reduce.

### New Output: Contract-Year Level Data

Created `contract_year_level.parquet` with:

**Features by Category:**
- **Member**: TOTAL_MEMBERS, MALE_RATIO, NATIONALITY_COUNT, YEAR_COVERAGE
- **Claims Volume**: CLAIM_LINES, UNIQUE_CLAIMS, MEMBERS_WITH_CLAIMS
- **Claims Cost**: TOTAL_BILLED, AVG_CLAIM_AMOUNT, MAX_CLAIM_AMOUNT, P90_CLAIM_AMOUNT
- **Claims Derived**: LOSS_RATIO, COST_PER_MEMBER, COST_PER_UTILIZER, UTILIZATION_RATE
- **Experience**: TOTAL_CALLS, CALLS_PER_MEMBER, AVG_RESOLUTION_DAYS
- **Preauth**: PREAUTH_EPISODES, APPROVAL_RATE, REJECTION_RATE
- **Seasonal**: Q1-Q4_CLAIMS, Q1-Q4_CALLS, QUARTER_CONCENTRATION
- **Engagement**: ACTIVE_MONTHS, WEEKEND_CALLS, WEEKDAY_CALLS
- **Target**: RETAINED_NEXT_YEAR (1=retained, 0=churned for 2022 contracts)

### ML Approach for Non-Linear IVI

**Problem:** Linear weighted averages of H, E, U dimensions don't capture the reality that one bad dimension can sink a client.

**Solution:** Train a model to predict retention, let it learn non-linear relationships:
1. Use 2022 features as X
2. Use RETAINED_NEXT_YEAR as y (binary target)
3. Model learns: "low U + low E = disaster" automatically
4. IVI Score = model.predict_proba() * 100
5. Use SHAP to decompose into H, E, U contributions

**Benefits:**
- Data-driven non-linearity
- Automatic feature interactions
- Validated on real outcomes
- Interpretable via SHAP

### 2026-02-03: Non-Linear IVI Aggregation + ML Hygiene Fixes (Notebook 03)

#### Issue 1: `LOSS_RATIO` was miscomputed (premium denominator problem)
- In `contract_year_level.parquet`, `EARNED_PREMIUM` behaves like **exposure** (often ~1), not monetary premium.
- The original `LOSS_RATIO = TOTAL_BILLED / EARNED_PREMIUM` produces extreme values (2022 median ~0, but 95th percentile ~11k).
- Practical fix (applied in `notebooks/03_IVI_ML_Model.ipynb`): recompute:
  - `LOSS_RATIO = TOTAL_BILLED / WRITTEN_PREMIUM` (safe divide)
  - This yields sensible distribution (2022: q95 ~0.87, q99 ~2.62).

#### Issue 2: Early stopping leakage
- The baseline LightGBM training was using the **test set** as the early-stopping evaluation set.
- Fix: split 2022 into **train/validation/test**.
  - Early stopping + probability calibration on validation set
  - Final metrics reported on the held-out test set

#### Issue 3: IVI aggregation was too compensatory (weakest-link requirement)
- Even with ML-driven retention probability, we want IVI to drop when **any core dimension** (H/E/U) is weak.
- Added a rule-based H/E/U scoring path:
  - Convert selected KPIs into **percentile scores** via ECDF using the 2022 distribution
  - Aggregate into `H_SCORE_RULE`, `E_SCORE_RULE`, `U_SCORE_RULE` (0–100)
- Added a **non-linear** aggregator:
  - Base: power mean across H/E/U with \(p=-2\) (more penalty than arithmetic mean; tends toward min as \(p\\to-\\infty\))
  - Floor penalty: if `min(H,E,U) < floor`, apply \( (min/floor)^{\\gamma} \)
- Added a hybrid final IVI:
  - `IVI_SCORE_HYBRID` = geometric mean of `IVI_SCORE_ML` and `IVI_SCORE_RULE_NL`

#### Outputs
- Saved a model bundle with calibration + metadata: `ivi_model_bundle.joblib`
- Saved IVI scores:
  - 2022 (labelled): `ivi_scores_segments_2022.parquet`
  - 2023 (forward scoring): `ivi_scores_forward_2023.parquet`
  - All years: `ivi_scores_all_years.parquet`

---

## Notebook 02: Business Insights Analysis

**Created:** 2026-02-01  
**File:** `notebooks/02_Business_Insights_Analysis.ipynb`

### Purpose
Creative business insights and strategic recommendations for the IVI initiative.

### Analysis Framework

1. **Portfolio Segmentation**
   - Contract size segments: Micro, Small, Medium, Large, Enterprise
   - Risk tiers based on Loss Ratio: Low Risk (<0.6), Moderate (0.6-0.85), Break-even (0.85-1.0), Elevated (1.0-1.3), High Risk (>1.3)

2. **Demographic Deep Dive**
   - Nationality-based cost analysis
   - Gender utilization patterns
   - Nationality diversity impact on contract performance

3. **Provider Intelligence**
   - Provider type cost analysis (Hospital, Pharmacy, Clinic, etc.)
   - Regional cost efficiency comparison
   - Network utilization patterns

4. **Service Experience Analysis**
   - Call category distribution
   - Call intensity correlation with contract health

5. **Cost Driver Analysis**
   - Correlation analysis with Loss Ratio
   - High-risk vs Low-risk contract profile comparison

6. **Strategic Recommendations Framework**
   - Action categories: HIGH PRIORITY, REVIEW, STAR CLIENTS, HEALTHY, MONITOR
   - Specific recommendations per segment

### Key Visualizations Created
- `contract_size_analysis.png` - Contract distribution and premium share
- `risk_tier_analysis.png` - Risk distribution across portfolio
- `nationality_analysis.png` - Cost and utilization by nationality
- `gender_analysis.png` - Gender-based healthcare patterns
- `provider_analysis.png` - Provider type cost distribution
- `regional_analysis.png` - Healthcare spend by region
- `call_analysis.png` - Call center patterns
- `cost_drivers.png` - Correlation analysis
- `diagnosis_analysis.png` - Top diagnoses by cost
- `recommendations.png` - Strategic action segmentation

### Output Files
- `contract_recommendations.parquet` - Contract data with ACTION_CATEGORY, RETENTION_RISK_SCORE, VALUE_SCORE
- `action_summary.parquet` - Summary by action category

### Key Insights Discovered
1. Enterprise accounts generate most premium but require monitoring
2. Nationality-based cost variations suggest targeted wellness opportunities
3. Hospital costs dominate spend - network management is critical
4. High call intensity correlates with higher costs
5. Gender mix impacts utilization patterns

### Strategic Recommendations Summary

| Segment | Action | Target KPI |
|---------|--------|------------|
| HIGH PRIORITY | Deploy care managers, wellness programs | 15% loss ratio reduction |
| REVIEW | Repricing, benefit design changes | 85% target loss ratio |
| STAR CLIENTS | Premium service, early renewal | 95%+ retention |
| HEALTHY | Standard management | Maintain <85% loss ratio |
| MONITOR | Automated tracking | Trend toward target |

---

## 2026-02-03: IVI Model Simplification & Region/Network Features

### Changes Made

#### 1. Removed Calibration/Sigmoid Transformations
**Problem:** The Platt scaling calibration + logit transforms were compressing the IVI score range, making it harder to interpret.

**Solution:** 
- Removed the `calibrator` and `_logit` function
- Use LightGBM's direct probability output (already well-calibrated with proper training)
- IVI_SCORE_ML = model.predict_proba() * 100

#### 2. Simplified IVI Scoring Formula
**Old Approach:**
- Power mean with p=-2 (complex, unintuitive)
- Floor penalty with gamma exponent
- Geometric mean of ML + rule-based scores

**New Approach:**
- Rule-based H/E/U scores: Simple ECDF percentile scoring (0-100)
- IVI_SCORE_RULE = Weighted average: H(30%) + E(30%) + U(40%)
- Final IVI = 50% ML Score + 50% Rule-based Score
- Clean 0-100 range, easy to explain to business stakeholders

#### 3. Added Region/Network Features to KPI Definitions
**New KPI dimension "R" (Region/Network):**
```python
'R': [
    ('REGION_COUNT', True, 'Region Coverage', 'Higher = broader coverage'),
    ('NETWORK_COUNT_USED', True, 'Network Diversity', 'Higher = better access'),
    ('PRACTICE_TYPE_COUNT', True, 'Practice Types', 'Hospital/Clinic/Pharmacy'),
    ('REGION_CONCENTRATION', False, 'Region Concentration', 'Lower = less risk'),
]
```

**Added Reference Data:**
- `REGION_INFO`: Provider density and population info per region
- `NETWORK_TIERS`: Network tier classification (NW1=Premium to NW7=Basic)

#### 4. Enhanced Client Analysis with Regional Insights
The `analyze_client()` function now includes:
- Primary region and network identification
- Provider density context for the region
- Network tier information
- Regional concentration risk assessment
- Actionable insights based on region/network patterns

#### 5. Updated Recommendations Framework
Added region/network specific recommendations:
- Single-region clients: Telemedicine recommendations
- Low-tier network clients: Network upgrade suggestions
- High regional concentration: Business continuity considerations
- Provider density awareness for service quality

### Why These Changes Matter

1. **Interpretability:** Stakeholders can easily understand "IVI = 73 means 73% health index" 
2. **Actionability:** Region/network insights provide concrete intervention points
3. **Explainability:** Client analysis now shows which regions/networks are driving issues
4. **Business Value:** Network/region recommendations can directly address access-related rejections

### Model Output Changes
- Model bundle no longer includes `calibrator` or `calibration_method`
- Added `weights_heu`, `region_info`, `network_tiers`, `kpi_definitions` to bundle
- IVI score range is now natural 0-100 (was compressed before)

---

## Dashboard Implementation (Feb 3, 2026)

### Overview
Implemented a full Streamlit dashboard for IVI visualization and analysis.

### Dashboard Structure
```
dashboard/
    app.py                  # Main entry point with navigation
    pages/
        portfolio.py        # Portfolio Overview page
        client_dive.py      # Client Deep Dive page
        segments.py         # Segment Analysis page
        kpi_explorer.py     # KPI Explorer page
    components/
        charts.py           # Reusable Plotly chart components
    utils/
        data_loader.py      # Data loading with caching
        recommendations.py  # Recommendation generation logic
```

### Features Implemented

#### 1. Portfolio Overview
- Key metrics: Total contracts, members, premium, avg IVI
- IVI score distribution histogram with risk coloring
- Risk tier pie chart
- Segment heatmap (Risk x Size x Profitability)
- At-risk contracts table (top 20 by premium)
- Premium at risk breakdown by tier

#### 2. Client Deep Dive
- Contract search and selection
- IVI gauge with 0-100 scale
- H, E, U dimension panels with KPIs
- Comparison vs benchmarks
- Auto-generated recommendations based on KPI thresholds
- Segment-specific action plans

#### 3. Segment Analysis
- Segment summary with priority levels
- Segment comparison charts (premium, contracts, IVI vs Loss Ratio)
- Risk tier distribution by segment
- Detailed contract list with export option

#### 4. KPI Explorer
- KPI selection by dimension (H, E, U)
- Distribution analysis with histograms and box plots
- Correlation with IVI score
- Segmentation breakdown
- Top/bottom performer analysis

### Technical Details
- **Framework:** Streamlit
- **Visualizations:** Plotly for interactive charts
- **Data:** Polars for fast data loading
- **Caching:** st.cache_data with 1-hour TTL
- **Styling:** Custom CSS for Bupa branding (blue #003087)

### Color Scheme
- Primary (Bupa Blue): #003087
- High Risk: #D64045 (red)
- Moderate Risk: #FF6B35 (orange)
- Low Risk: #2E8B57 (green)

### Recommendation Logic
Auto-generates recommendations based on:
- Rejection rate > 25% -> Pre-auth handling issues
- Resolution days > 10 -> Support quality issues
- Calls per member > 0.35 -> High complaint volume
- Loss ratio > 1.2 -> Unprofitable contract
- Cost per member > 1.5x benchmark -> High cost client
- Utilization > 75% -> High healthcare usage
- Diagnoses per utilizer > 4 -> Chronic burden

### Running the Dashboard
```bash
cd /workspace/dashboard
streamlit run app.py --server.port 8501
```

### Data Dependencies
- `/volume/data/models/ivi_scores_all_years.parquet` - Main IVI scores with features
- `/volume/data/models/shap_subscores.parquet` - SHAP-based H, E, U subscores
- `/volume/data/processed/contract_level.parquet` - Contract-level data
---

## Diagram Documentation (Feb 3, 2026)

### Created Pipeline Diagrams

Created comprehensive diagrams documenting the IVI system architecture in two formats:

**Location:** `/workspace/diagrams/`

**Files:**
1. `ivi_pipeline_diagrams.puml` - PlantUML format (3 diagrams)
2. `IVI_PIPELINE_DIAGRAMS.md` - Mermaid format with documentation

**Diagrams Included:**

1. **Data Preprocessing & Feature Engineering Pipeline**
   - Raw data sources (4 SAS datasets, 404M+ total rows)
   - Optimized loading (pyreadstat multiprocessing + Polars + Parquet cache)
   - Data cleaning steps (missing values, outliers, date alignment)
   - Contract filtering (MIN_MEMBERS >= 5)
   - Feature engineering by dimension (H, E, U + Temporal/Geographic)
   - Output datasets

2. **IVI ML Model Pipeline - Three-Phase Architecture**
   - Phase 1: LightGBM classifier with imbalance handling and calibration
   - Phase 2: SHAP decomposition for H/E/U sub-scores
   - Rule-based scoring path (ECDF percentiles + power mean aggregation)
   - Phase 3: Multi-dimensional segmentation (12 segments)
   - Model outputs (scores, bundles)

3. **Complete IVI System Architecture**
   - End-to-end flow from data sources to dashboard
   - Segmentation to recommended actions mapping
   - Dashboard components

**Rendering Options:**
- PlantUML: Use PlantUML server or VS Code extension
- Mermaid: Renders natively in GitHub, GitLab, and many markdown viewers