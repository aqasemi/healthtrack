# IVI Presentation Outline
## Bupa Arabia Intelligent Value Index

---

## Slide 1: Title Slide
- **Title:** Intelligent Value Index (IVI) - Proactive Client Management
- **Subtitle:** Predicting Retention, Understanding Risk, Enabling Action
- **Team:** [Team Name]
- **Date:** February 2026

---

## Slide 2: Data Exploration - Understanding the Landscape

### Dataset Overview
- **4 core datasets:** Claims (86M rows), Pre-auth (305M rows), Calls (8.9M), Members (4.3M)
- **Coverage:** 2022-2023 contract periods, 143K contract-years
- **Total Premium:** 69B SAR across all contracts

### Key Patterns Discovered
- **Contract Size Distribution:** 82% of contracts have <5 members, but represent only 0.6% of premium
- **Retained vs Churned:** Retained contracts are 10x larger on average (143 members vs 12)
- **Premium Concentration:** Top 15% of contracts (by size) hold 75% of total premium
- **Regional Patterns:** Central and Western regions dominate (60%+ of claims)
- **Seasonal Claims:** Q4 shows highest claim activity (year-end utilization spike)

### Interesting Insight
- Small contracts (<5 members) churn at 92.8% rate
- Large contracts (100+ members) retain at 66% rate
- **"Size predicts stability"** - larger corporate clients invest in long-term relationships

---

## Slide 3: Data Cleaning & Preparation

### Filtering Strategy
- **Problem:** Small contracts create noise (high variance, easy to predict extremes)
- **Solution:** Filter to contracts with 5+ members
- **Impact:**
  - Removed 82.8% of contracts
  - Retained 97% of members and 99.4% of premium
  - Class balance improved from 85/15 to 44/56

### Data Quality Handling
- **Missing Values:** Imputed with 0 for count features, median for ratios
- **Outliers:** Capped at 99th percentile for cost metrics (extreme billing cases)
- **Infinite Values:** Replaced loss ratios >10 with cap value (prevents model instability)

### Temporal Considerations
- **Contract Period (CONT_YYMM):** 2022-2023 - when contract was active
- **Service Dates (INCUR_DATE):** 2023-2025 - when healthcare was used
- **Challenge:** Services can occur after contract period ends (claims processing lag)
- **Solution:** Aligned all features to contract year, not service year

---

## Slide 4: Feature Engineering

### Three Dimensions of Value (H, E, U)

#### H - Health Outcomes (12 features)
- Utilization rate, diagnoses per utilizer, claims per utilizer
- Average/P90/Max claim amounts
- Members with claims, claim line density

#### E - Experience Quality (15 features)
- Calls per member, resolution days
- Pre-auth approval/rejection rates
- Weekend vs weekday call patterns
- Call categories distribution

#### U - Utilization Efficiency (11 features)
- Loss ratio (claims/premium)
- Cost per member, cost per utilizer
- Premium metrics, estimated amounts

### Seasonal & Temporal Features
- **Quarterly claim distribution:** Q1, Q2, Q3, Q4 claim counts
- **Quarter concentration:** How concentrated are claims in one quarter?
- **Active months:** Number of months with claims activity
- **Year coverage:** Proportion of year with healthcare activity

### Geographic & Network Features
- Primary region and network encoding
- Region concentration (multi-region vs single-region clients)
- Provider diversity (unique providers used)

---

## Slide 5: Problem Approach - Real-World Alignment

### Business Context
- **Who uses this?** Bupa's account managers, underwriting team, renewal strategists
- **When?** 3-6 months before contract renewal
- **Goal:** Identify at-risk clients early, understand WHY, take action

### Our Design Principles

1. **Explainability First**
   - IVI score alone is not enough
   - Must explain: "This client is at risk BECAUSE of X, Y, Z"
   - Decompose score into H, E, U sub-components

2. **Actionable Segmentation**
   - Not just "high risk" vs "low risk"
   - Segment by: Risk Level + Contract Size + Profitability
   - Different segments need different interventions

3. **Forward-Looking**
   - Predict NEXT YEAR retention using THIS YEAR features
   - 2022 features -> 2023 retention (real validation)
   - Enables proactive outreach, not reactive scrambling

---

## Slide 6: Model Pipeline

### Architecture: Three-Phase Approach

#### Phase 1: Gradient Boosting Classifier (LightGBM)
- **Target:** Retention probability (0-1)
- **IVI Score = Retention Probability x 100**
- **Handling Imbalance:** scale_pos_weight, stratified splits
- **Regularization:** Early stopping, feature/bagging fraction

#### Phase 2: SHAP Decomposition
- Extract feature contributions from model
- Group by dimension: H, E, U
- **H_SCORE:** Sum of SHAP values from health features
- **E_SCORE:** Sum of SHAP values from experience features
- **U_SCORE:** Sum of SHAP values from utilization features

#### Phase 3: Multi-Dimensional Segmentation
- Combine: IVI Risk + Size + Profitability
- 12 segments with tailored recommendations
- Priority scoring for account manager workload

### Model Performance
| Metric | Value |
|--------|-------|
| AUC-ROC | 0.71 |
| Churned F1 | 0.62 |
| Retained F1 | 0.69 |
| Macro F1 | 0.65 |

---

## Slide 7: IVI Score Interpretation for Decision Makers

### What IVI Score Tells You
- **IVI 0-30 (High Risk):** Client likely to churn - immediate attention needed
- **IVI 30-60 (Moderate Risk):** Borderline - investigate sub-scores
- **IVI 60-100 (Low Risk):** Client likely to renew - maintain relationship

### Deep Dive: Why is this client at risk?

#### Example 1: High Risk due to Experience (E)
- **Symptom:** Low E_SCORE (e.g., 25/100)
- **Investigation:** High rejection rate (40%+), long resolution times
- **Root Cause:** Client primarily uses providers in underserved region (Northern)
- **Action:** Expand network in their region, assign dedicated claims handler

#### Example 2: High Risk due to Cost (U)
- **Symptom:** Low U_SCORE, Loss ratio > 1.5
- **Investigation:** High cost per member, frequent large claims
- **Root Cause:** Older workforce (demographics), chronic condition prevalence
- **Action:** Wellness program targeting chronic conditions, premium adjustment discussion

#### Example 3: High Risk due to Health Patterns (H)
- **Symptom:** Low H_SCORE, high utilization
- **Investigation:** Many diagnoses per utilizer, high claim frequency
- **Root Cause:** Insufficient preventive care, late-stage treatments
- **Action:** Proactive health screening, disease management programs

---

## Slide 8: Cost KPI Deep Dive

### Why is this client's cost high/low?

#### Cost Drivers Analysis
1. **Demographics**
   - Older workforce = higher chronic disease prevalence
   - Gender mix affects maternity/specific condition costs
   - Nationality patterns (some nationalities have higher utilization)

2. **Provider Network**
   - Premium network (NW1-NW2) = higher unit costs
   - Limited provider options = concentrated expensive care
   - Hospital vs clinic ratio

3. **Health Conditions**
   - Chronic condition load (diabetes, hypertension, etc.)
   - Catastrophic cases (oncology, transplants)
   - Mental health utilization trends

4. **Utilization Patterns**
   - Emergency vs planned care ratio
   - Specialist vs primary care balance
   - Seasonal spikes (Q4 rush)

### Dashboard Visualization
- Cost breakdown waterfall: Base -> Demographics -> Network -> Conditions -> Total
- Peer comparison: "This client costs 30% more than similar-sized contracts"
- Trend analysis: "Cost increased 15% YoY vs portfolio average of 8%"

---

## Slide 9: Integrated KPI View

### The IVI Dashboard Philosophy
- **Single View:** All KPIs visible at once
- **Drill-Down:** Click any KPI to see drivers
- **Comparison:** Benchmark against portfolio/segment
- **Action:** Recommendations per segment

### KPI Integration
```
IVI Score (Master)
    |
    +-- H Score (Health Outcomes)
    |       +-- Utilization Rate
    |       +-- Diagnoses per Utilizer
    |       +-- Claim Severity
    |
    +-- E Score (Experience)
    |       +-- Pre-auth Rejection Rate
    |       +-- Resolution Time
    |       +-- Call Volume
    |
    +-- U Score (Utilization/Cost)
            +-- Loss Ratio
            +-- Cost per Member
            +-- Provider Efficiency
```

### Segment-Specific Actions
| Segment | Priority | Action |
|---------|----------|--------|
| HIGH_RISK_LARGE_UNPROFITABLE | CRITICAL | Executive escalation, pricing review |
| HIGH_RISK_LARGE_PROFITABLE | HIGH | Retention meeting, service review |
| HIGH_RISK_SMALL_UNPROFITABLE | MEDIUM | Auto-renewal decline consideration |
| MODERATE_RISK_LARGE_* | MEDIUM | Proactive wellness program |
| LOW_RISK_LARGE_PROFITABLE | LOW | Maintain, upsell opportunities |

---

## Slide 10: Key Takeaways & Recommendations

### Technical Achievements
1. Processed 400M+ rows efficiently (Polars + pyreadstat)
2. Built explainable ML model with SHAP decomposition
3. Created multi-dimensional segmentation framework
4. Achieved 0.65 macro F1 with balanced class performance

### Business Value
1. **Early Warning:** Identify at-risk clients 6+ months before renewal
2. **Root Cause:** Understand WHY a client is at risk (not just that they are)
3. **Prioritization:** Focus account managers on highest-value interventions
4. **Measurable:** Track IVI trend over time to measure intervention success

### Recommended Next Steps
1. Deploy dashboard for pilot with 10 account managers
2. Track intervention success rate by segment
3. Integrate with CRM for automated alerts
4. Expand to individual member risk (B2C wellness)

---

## Appendix: Technical Details

### Data Pipeline
- SAS -> Parquet conversion (pyreadstat multiprocessing)
- Polars for aggregation (10x faster than pandas)
- Contract-year level granularity for ML

### Model Details
- LightGBM with 48 iterations (early stopping)
- 84 features (64 base + 20 encoded)
- Stratified 64/16/20 train/val/test split

### Feature Importance (Top 10)
1. AVG_PREMIUM_PER_MEMBER (U)
2. WRITTEN_PREMIUM (U)
3. QUARTER_CONCENTRATION (Seasonal)
4. Q4_CLAIMS (Seasonal)
5. MAX_EST_AMOUNT (U)
6. LOSS_RATIO (U)
7. CALLS_PER_MEMBER (E)
8. DIAGNOSES_PER_UTILIZER (H)
9. UTILIZATION_RATE (H)
10. REGION_Central (Geographic)
