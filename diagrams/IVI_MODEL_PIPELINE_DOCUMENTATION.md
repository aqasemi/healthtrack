This document provides a comprehensive technical description of the data preprocessing, feature engineering, and machine learning pipelines that power the IVI system.

---

## Table of Contents

1. [Data Sources and Ingestion](#1-data-sources-and-ingestion)
2. [Data Preprocessing Pipeline](#2-data-preprocessing-pipeline)
3. [Feature Engineering](#3-feature-engineering)
4. [Machine Learning Model Pipeline](#4-machine-learning-model-pipeline)
5. [IVI Score Calculation](#5-ivi-score-calculation)
6. [Segmentation and Recommendations](#6-segmentation-and-recommendations)
---

## 1. Data Sources and Ingestion

### 1.1 Raw Data Sources

The IVI system ingests data from four primary SAS datasets that capture different aspects of the insurance business:

| Dataset | Records | Description |
|---------|---------|-------------|
| **sampled_claims** | 86 million | Claims and reimbursement transactions including diagnosis codes, billed amounts, provider information, and processing dates |
| **sampled_preauth** | 305 million | Pre-authorization requests capturing treatment approvals, rejections, estimated costs, and turnaround times |
| **sampled_calls** | 8.9 million | Customer service interactions including complaints, inquiries, resolution status, and timestamps |
| **sampled_member** | 4.3 million | Member demographics, enrollment information, plan details, and premium data |

### 1.2 Optimized Data Loading Strategy

Given the massive scale of the data (400+ million total records), a multi-stage optimized loading strategy was implemented:

**Stage 1: Parallel SAS Reading**
- The `pyreadstat` library's multiprocessing capability is used to read SAS7BDAT files
- All available CPU cores are utilized for parallel chunk reading
- This approach is significantly faster than single-threaded `pandas.read_sas()`

**Stage 2: Polars DataFrames**
- Data is immediately converted to Polars DataFrames for processing
- Polars provides superior performance through:
  - Lazy evaluation (query optimization before execution)
  - Efficient memory management
  - Multi-threaded operations by default
  - Arrow-based columnar storage

**Stage 3: Parquet Caching**
- Processed data is cached to Parquet format for instant subsequent loads
- Parquet provides excellent compression (typically 5-10x reduction)
- Columnar storage enables reading only required columns
- First load may take minutes; subsequent loads are near-instantaneous

### 1.3 Key Data Relationships

The datasets are linked through several key identifiers:

```
CONTRACT_NO (CONT_NO)
    |
    +-- Links to: sampled_member, sampled_claims, sampled_preauth, sampled_calls
    |
ADHERENT_NO (Member ID)
    |
    +-- Links to: sampled_member, sampled_claims
    |
PROV_CODE (Provider Code)
    |
    +-- Links to: Provider_Info reference table
```

---

## 2. Data Preprocessing Pipeline

### 2.1 Date Field Alignment

One of the critical preprocessing challenges was aligning multiple date concepts:

| Field | Meaning | Date Range in Data |
|-------|---------|-------------------|
| `CONT_YYMM` | Contract period (when policy was active) | 2022-2023 |
| `INCUR_DATE_FROM` | When healthcare service was used | 2023-2025 |
| `T_PERIOD` | When claim was processed | 2023-2025 |
| `CRT_DATE` | When customer call was made | 2021-2025 |

**Challenge:** Services can occur after the contract period ends due to claims processing lag. A member with a 2022 contract may have claims processed in 2024.

**Solution:** All features are aligned to the contract year (`CONT_YYMM`), not the service date. This ensures that when predicting 2023 retention using 2022 features, we use data that was actually available during the 2022 contract period.

### 2.2 Missing Value Handling

Different imputation strategies are applied based on feature type:

| Feature Type | Imputation Strategy | Rationale |
|--------------|---------------------|-----------|
| Count features (claims, calls) | Impute with 0 | No activity = zero count |
| Ratio features (loss ratio, rates) | Impute with median | Preserve distribution shape |
| Categorical features | Mode or "Unknown" | Maintain category integrity |
| Premium/Cost features | 0 or median | Depends on business context |

### 2.3 Outlier Treatment

Extreme values in cost metrics can destabilize model training:

- **Capping at 99th Percentile:** Extreme billing amounts (e.g., catastrophic claims) are capped to reduce skewness while preserving signal
- **Loss Ratio Handling:** Loss ratios exceeding 10 (1000%) are capped to prevent infinite or extreme values from dominating
- **Infinite Value Replacement:** Division by zero cases (e.g., claims with zero premium) are replaced with cap values

### 2.4 Contract Filtering (Critical Step)

**The Problem:** The raw data contains a heavily skewed contract size distribution:
- 82.8% of contracts have fewer than 5 members
- These small contracts represent only 0.6% of total premium
- Small contracts exhibit extreme variance in metrics (high noise, low signal)
- Class imbalance: 85% churn vs 15% retention

**The Solution:** Filter to contracts with 5+ members

**Impact of Filtering:**

| Metric | Before Filter | After Filter |
|--------|---------------|--------------|
| Total Contracts | 100% | 17.2% |
| Total Members | 100% | 97% |
| Total Premium | 100% | 99.4% |
| Class Balance | 85/15 (Churn/Retain) | 44/56 |
| Churned F1 Score | 0.29 | 0.62 |

**Business Justification:** 
- Small contracts (1-4 members) are typically individual or micro-business policies
- They have fundamentally different behavior patterns than corporate accounts
- Removing them focuses the model on the high-value corporate segment
- Premium retention is the primary business metric, and 99.4% is preserved

---

## 3. Feature Engineering

### 3.1 Feature Categories

The IVI system engineers 38+ features organized into the three core dimensions (H, E, U) plus supporting categories:

#### Health Outcomes (H) - 12 Features

These features capture the medical need intensity and health patterns of the client's member population:

| Feature | Description | Calculation |
|---------|-------------|-------------|
| `UTILIZATION_RATE` | Proportion of members who filed claims | Members with claims / Total members |
| `UNIQUE_DIAGNOSES` | Number of distinct diagnosis codes | Count of unique DIAG_CODE per contract |
| `DIAGNOSES_PER_UTILIZER` | Average conditions per active member | Unique diagnoses / Members with claims |
| `CLAIMS_PER_UTILIZER` | Claim frequency per active member | Total claim lines / Members with claims |
| `AVG_CLAIM_AMOUNT` | Mean cost per claim | Total billed / Number of claims |
| `P90_CLAIM_AMOUNT` | 90th percentile claim amount | Captures high-cost case exposure |
| `MAX_CLAIM_AMOUNT` | Largest single claim | Identifies catastrophic cases |
| `MEMBERS_WITH_CLAIMS` | Count of active utilizers | Members who filed at least one claim |
| `CLAIM_LINE_DENSITY` | Average line items per claim | Total lines / Unique vouchers |
| `UNIQUE_PROVIDERS` | Provider diversity | Count of distinct PROV_CODE |
| `UNIQUE_BENEFIT_HEADS` | Service type diversity | Count of distinct BEN_HEAD |
| `CHRONIC_INDICATOR` | Chronic disease presence | Flag based on ICD code patterns |

#### Experience Quality (E) - 15 Features

These features measure the service quality and customer satisfaction indicators:

| Feature | Description | Calculation |
|---------|-------------|-------------|
| `TOTAL_CALLS` | Customer service contact volume | Count of call records |
| `CALLS_PER_MEMBER` | Service intensity | Total calls / Total members |
| `AVG_RESOLUTION_DAYS` | Ticket closure time | Mean of (UPD_DATE - CRT_DATE) |
| `MAX_RESOLUTION_DAYS` | Worst case resolution | Maximum resolution time |
| `COMPLAINT_RATE` | Proportion of complaint calls | Complaint calls / Total calls |
| `INQUIRY_RATE` | Information-seeking ratio | Inquiry calls / Total calls |
| `WEEKEND_CALLS` | After-hours contact rate | Weekend calls / Total calls |
| `WEEKDAY_CALLS` | Business hours contact | Weekday calls / Total calls |
| `PREAUTH_EPISODES` | Pre-authorization requests | Count of unique episodes |
| `APPROVAL_RATE` | Pre-auth success rate | Approved / Total pre-auths |
| `REJECTION_RATE` | Pre-auth denial rate | Rejected / Total pre-auths |
| `PENDING_RATE` | Unresolved pre-auths | Pending / Total pre-auths |
| `AVG_PREAUTH_AMOUNT` | Mean requested amount | Sum of EST_AMT / Episodes |
| `PREAUTH_PER_MEMBER` | Pre-auth activity level | Episodes / Total members |
| `CALL_CATEGORY_ENTROPY` | Diversity of issues | Shannon entropy of call categories |

#### Utilization Efficiency (U) - 11 Features

These features assess cost sustainability and financial performance:

| Feature | Description | Calculation |
|---------|-------------|-------------|
| `LOSS_RATIO` | Core profitability metric | Total billed / Written premium |
| `COST_PER_MEMBER` | Average cost burden | Total billed / Total members |
| `COST_PER_UTILIZER` | Active member cost | Total billed / Members with claims |
| `WRITTEN_PREMIUM` | Contract revenue | Sum of WP from member data |
| `EARNED_PREMIUM` | Recognized revenue | Sum of WE from member data |
| `TOTAL_BILLED` | Total claims cost | Sum of SUM_of_NETBILLED |
| `PREMIUM_PER_MEMBER` | Revenue per head | Written premium / Total members |
| `EST_AMOUNT_TOTAL` | Pre-auth estimated costs | Sum of preauth EST_AMT |
| `BILLED_VS_ESTIMATED` | Actual vs expected ratio | Total billed / EST_AMT |
| `CLAIM_VOUCHERS` | Unique claim transactions | Count of distinct VOU_NO |
| `COST_VOLATILITY` | Claim amount variance | Std dev of claim amounts |

#### Temporal Features - 8 Features

| Feature | Description |
|---------|-------------|
| `Q1_CLAIMS`, `Q2_CLAIMS`, `Q3_CLAIMS`, `Q4_CLAIMS` | Quarterly claim distribution |
| `QUARTER_CONCENTRATION` | How concentrated claims are in one quarter (Herfindahl-like index) |
| `ACTIVE_MONTHS` | Number of months with claim activity |
| `YEAR_COVERAGE` | Proportion of year with activity |
| `CLAIMS_TREND` | Direction of claims over time (increasing/decreasing) |

#### Geographic & Network Features - 5 Features

| Feature | Description |
|---------|-------------|
| `PRIMARY_REGION` | Most common provider region (Central, Western, Eastern, etc.) |
| `PRIMARY_NETWORK` | Most used network tier (NW1-NW7) |
| `REGION_CONCENTRATION` | Single-region vs multi-region utilization |
| `NETWORK_TIER_MIX` | Distribution across network levels |
| `REGION_ENCODED` | Numeric encoding of primary region |

### 3.2 Feature Transformations

Several transformations are applied to improve model performance:

1. **Log Transformation:** Applied to highly skewed features (costs, counts) to reduce impact of extreme values

2. **Percentile Ranking:** Features are converted to percentile scores (0-100) using the empirical cumulative distribution function (ECDF) from the training year

3. **Interaction Features:** Key interactions like `LOSS_RATIO * UTILIZATION_RATE` capture combined effects

4. **Ratio Normalization:** All rates and ratios are clipped to [0, 1] or reasonable bounds

---

## 4. Machine Learning Model Pipeline

### 4.1 Problem Formulation

**Objective:** Predict whether a corporate client will retain (renew) their insurance contract for the following year.

**Target Variable:** `RETAINED_NEXT_YEAR`
- 1 = Contract renewed (appears in both 2022 and 2023)
- 0 = Contract churned (appears in 2022, not in 2023)

**Temporal Setup:**
- Training features: 2022 contract year data
- Target: Retention status in 2023
- This mirrors real-world usage where we predict next year using current year data

### 4.2 Data Splitting Strategy

The data is split into three sets using stratified sampling to preserve class proportions:

| Set | Proportion | Purpose |
|-----|------------|---------|
| Training | 70% | Model parameter learning |
| Validation | 15% | Early stopping, hyperparameter tuning, calibration |
| Test | 15% | Final unbiased evaluation (never seen during training) |

**Important:** Early stopping uses the validation set, NOT the test set. This prevents information leakage that would inflate performance estimates.

### 4.3 Model Architecture: LightGBM Classifier

**Why LightGBM?**
- Handles tabular data extremely well
- Built-in support for categorical features
- Efficient handling of missing values
- Fast training on large datasets
- Excellent interpretability via feature importance and SHAP

**Key Hyperparameters:**

```python
lgb_params = {
    'objective': 'binary',
    'metric': 'auc',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,      # Use 80% of features per tree
    'bagging_fraction': 0.8,      # Use 80% of data per iteration
    'bagging_freq': 5,            # Bagging every 5 iterations
    'scale_pos_weight': neg_count / pos_count,  # Handle imbalance
    'verbose': -1,
    'seed': 42
}
```

### 4.4 Handling Class Imbalance

Even after filtering small contracts, some class imbalance remains. Multiple strategies are employed:

1. **scale_pos_weight:** The positive class (retained) is up-weighted inversely proportional to its frequency. This prevents the model from always predicting the majority class.

2. **Stratified Splitting:** Train/validation/test splits maintain the same class proportions as the overall data.

3. **Appropriate Metrics:** We optimize for AUC-ROC and evaluate using F1-score for both classes, not just accuracy.

4. **Threshold Tuning:** The default 0.5 probability threshold can be adjusted to balance precision/recall based on business needs.

### 4.5 Early Stopping and Regularization

To prevent overfitting:

- **Early Stopping:** Training stops if validation AUC doesn't improve for 50 rounds
- **Feature Fraction:** Each tree uses a random 80% of features
- **Bagging Fraction:** Each iteration uses a random 80% of samples
- **Limited Depth:** `num_leaves=31` constrains tree complexity

### 4.6 Probability Calibration

Raw model probabilities from gradient boosting may not be well-calibrated (i.e., a predicted 70% probability may not correspond to 70% actual retention rate).

**Solution:** Apply `CalibratedClassifierCV` with isotonic regression on the validation set to produce calibrated probabilities.

**Benefit:** The IVI score (probability x 100) becomes more interpretable and actionable.

### 4.7 Model Performance

| Metric | Value | Interpretation |
|--------|-------|----------------|
| AUC-ROC | 0.71 | Good discrimination ability |
| Churned F1 | 0.62 | Reasonable identification of at-risk clients |
| Retained F1 | 0.69 | Good identification of stable clients |
| Macro F1 | 0.65 | Balanced performance across both classes |

**Lift Analysis:** The top decile (highest predicted churn risk) captures 2.1x the baseline churn rate, enabling efficient prioritization of intervention resources.

---

## 5. IVI Score Calculation

### 5.1 Three Scoring Approaches

The system calculates IVI scores using three complementary approaches:

#### Approach 1: ML-Based Score (IVI_SCORE_ML)

```
IVI_SCORE_ML = Calibrated_Retention_Probability x 100
```

- Directly uses the model's predicted probability of retention
- Range: 0-100
- Higher score = higher predicted retention probability
- Captures non-linear feature interactions automatically

#### Approach 2: Rule-Based Score (IVI_SCORE_RULE)

For each dimension (H, E, U), KPIs are converted to percentile scores:

```
H_SCORE_RULE = Mean percentile of health KPIs
E_SCORE_RULE = Mean percentile of experience KPIs
U_SCORE_RULE = Mean percentile of utilization KPIs
```

**KPI Scoring Direction:**
- Some KPIs are "higher is better" (e.g., APPROVAL_RATE): score = percentile
- Some KPIs are "lower is better" (e.g., LOSS_RATIO): score = 100 - percentile

#### Approach 3: Non-Linear Rule-Based Score (IVI_SCORE_RULE_NL)

Standard averaging allows a strong dimension to compensate for a weak one. In reality, a client with excellent health metrics but terrible service experience is still at risk.

**Power Mean Aggregation:**

```
IVI_SCORE_RULE_NL = ((H^p + E^p + U^p) / 3)^(1/p)

where p = -2 (penalizes weak dimensions more than arithmetic mean)
```

**Floor Penalty:**
```
if min(H, E, U) < 30:
    IVI_SCORE_RULE_NL *= (min_score / 30)^gamma
    
where gamma = 0.5 (moderate penalty)
```

This ensures that a single failing dimension significantly impacts the overall score.

### 5.2 Hybrid Score (IVI_SCORE_HYBRID)

The final recommended score combines model learning with business rules:

```
IVI_SCORE_HYBRID = sqrt(IVI_SCORE_ML * IVI_SCORE_RULE_NL)
```

**Rationale:** Geometric mean ensures both components must be reasonably good for a high final score. A client can't have a good hybrid score if either the ML prediction or the rule-based assessment is poor.

### 5.3 Sub-Score Decomposition via SHAP

SHAP (SHapley Additive exPlanations) values decompose the model's prediction into individual feature contributions:

1. **Extract SHAP values** for each feature for each contract
2. **Group by dimension:** Sum SHAP values for H-related, E-related, and U-related features
3. **Normalize:** Scale to 0-100 range

```python
H_SCORE_ML = normalize(sum(SHAP values for health features))
E_SCORE_ML = normalize(sum(SHAP values for experience features))
U_SCORE_ML = normalize(sum(SHAP values for utilization features))
```

**Benefit:** Explains WHY a client has a particular IVI score. "This client is at risk because their E_SCORE is low due to high rejection rates and long resolution times."

---

## 6. Segmentation and Recommendations

### 6.1 Customer Health Risk Segmentation

**IMPORTANT:** This is specifically **Customer Health Risk Segmentation** - it categorizes clients based on the **health profile** of their member population. This is distinct from IVI-based business risk segmentation.

#### Purpose
Identify clients whose member populations have elevated health risks (chronic conditions, high utilization, high claims) so that targeted health interventions can be deployed.

#### Health Risk Index (HRI) Methodology

The Health Risk Index is computed using percentile-based scoring of key health indicators:

| Indicator | Weight | Description | Health Relevance |
|-----------|--------|-------------|------------------|
| Utilization Rate | 25% | % of members using services | Population accessing healthcare |
| Diagnoses per Utilizer | 30% | Condition burden (most important) | Chronic disease prevalence |
| Average Claim Amount | 25% | Claim severity | Treatment complexity |
| Cost per Member | 20% | Overall cost intensity | Healthcare consumption |

Each indicator is converted to a percentile rank relative to the entire portfolio, then weighted and summed to produce the HRI.

#### Health Risk Segments

| Segment | Threshold | Description | Typical Profile |
|---------|-----------|-------------|-----------------|
| **HIGH** | HRI >= P90 | Top 10% - highest health risk | High chronic burden, aging workforce |
| **MODERATE_HIGH** | HRI P84-P90 | Elevated risk | Trending toward high risk |
| **MODERATE** | HRI P16-P84 | Average health risk | Typical population health |
| **LOW_MODERATE** | HRI P10-P16 | Below average risk | Healthier than average |
| **LOW** | HRI <= P10 | Bottom 10% - healthiest | Minimal healthcare needs |

#### Health Risk-Specific Interventions

| Segment | Recommended Health Interventions |
|---------|----------------------------------|
| **HIGH** | Chronic disease management, care coordination, targeted wellness programs, health screenings |
| **MODERATE_HIGH** | Early intervention, health education, lifestyle modification support |
| **MODERATE** | Standard preventive care, annual check-up promotions |
| **LOW_MODERATE** | Maintain engagement, preventive screening access |
| **LOW** | Recognize as healthy benchmark, preserve health status |

#### Health Risk vs Business Risk

| Aspect | Health Risk Segmentation | Business Risk (IVI-based) |
|--------|--------------------------|---------------------------|
| **Focus** | Population health profile | Financial and retention risk |
| **Indicators** | Utilization, diagnoses, claims | IVI score, loss ratio, premium |
| **Purpose** | Target health interventions | Prioritize account management |
| **Actions** | Wellness programs, care management | Pricing, service recovery |
| **Key Question** | "Are members getting healthier?" | "Will this client renew?" |

**Key Insight:** A client can have HIGH health risk but LOW business risk if they are profitable (low loss ratio). Conversely, a LOW health risk client can be HIGH business risk if they have service issues (low E score). The two segmentations serve complementary purposes.

### 6.2 Multi-Dimensional Business Segmentation

IVI score alone is insufficient for actionable segmentation. Different client profiles require different interventions even at the same risk level.

**Segmentation Dimensions:**

| Dimension | Categories | Logic |
|-----------|------------|-------|
| IVI Risk | High, Moderate, Low | Based on percentile thresholds (33rd, 67th) |
| Contract Size | Small, Large | Based on median member count |
| Profitability | Profitable, Unprofitable | Loss ratio <= 1.0 vs > 1.0 |

**Combined Segments:** 3 x 2 x 2 = 12 segments

### 6.2 Multi-Dimensional Business Segmentation

IVI score alone is insufficient for actionable segmentation. Different client profiles require different interventions even at the same risk level.

**Segmentation Dimensions:**

| Dimension | Categories | Logic |
|-----------|------------|-------|
| IVI Risk | High, Moderate, Low | Based on percentile thresholds (33rd, 67th) |
| Contract Size | Small, Large | Based on median member count |
| Profitability | Profitable, Unprofitable | Loss ratio <= 1.0 vs > 1.0 |

**Combined Segments:** 3 x 2 x 2 = 12 segments

### 6.3 Segment Definitions and Actions

| Segment | Characteristics | Priority | Recommended Action |
|---------|-----------------|----------|-------------------|
| HIGH_RISK_LARGE_UNPROFITABLE | High churn risk, many members, losing money | CRITICAL | Immediate executive intervention, consider repricing |
| HIGH_RISK_LARGE_PROFITABLE | High churn risk, many members, profitable | URGENT | Relationship manager deep-dive, address root cause |
| HIGH_RISK_SMALL_UNPROFITABLE | High churn risk, few members, losing money | LOW | May not be worth retention investment |
| HIGH_RISK_SMALL_PROFITABLE | High churn risk, few members, profitable | MODERATE | Automated outreach, self-service improvements |
| MODERATE_RISK_LARGE_* | Borderline, high value | WATCH | Monitor sub-scores, proactive check-in |
| LOW_RISK_LARGE_PROFITABLE | Stable, valuable | NURTURE | Maintain relationship, offer value-adds |

### 6.4 Root Cause Analysis Framework

When investigating a high-risk client, examine sub-scores to identify intervention targets:

**Low H_SCORE (Health Issues):**
- Symptoms: High utilization, many diagnoses, expensive claims
- Root Causes: Aging workforce, chronic conditions, insufficient preventive care
- Actions: Wellness programs, health screenings, disease management

**Low E_SCORE (Experience Issues):**
- Symptoms: High rejection rate, long resolution times, many complaints
- Root Causes: Poor provider coverage, process bottlenecks, communication gaps
- Actions: Network expansion, dedicated claims handler, service recovery

**Low U_SCORE (Cost Issues):**
- Symptoms: Loss ratio > 1, high cost per member
- Root Causes: Adverse selection, catastrophic cases, premium mispricing
- Actions: Premium adjustment discussion, benefit redesign, fraud investigation

