# IVI Presentation Outline
## Bupa Arabia Intelligent Value Index

---

## Slide 1: Title Slide
- **Title:** Intelligent Value Index (IVI)
- **Subtitle:** Proactive Client Management for Sustainable Healthcare Value
- **Team:** [Team Name]
- **Date:** February 2026
- **Event:** Bupa Arabia Health Hackathon - Futurethon

---

## Slide 2: The Current Situation - Why IVI Matters

### The Challenge Bupa Arabia Faces
- **High Churn Rate:** 85% of contracts do not renew year-over-year
- **Reactive Management:** Account managers only discover problems at renewal time
- **Limited Visibility:** No unified view of client health, experience, and cost sustainability
- **Resource Misallocation:** Equal attention given to high-value and low-value accounts

### Business Impact
- Lost premium revenue from preventable churn
- Higher acquisition costs vs retention costs
- Missed early intervention opportunities
- No quantified link between health outcomes and client retention

### The Question We Need to Answer
> "How can we identify at-risk clients 6+ months before renewal, understand WHY they're at risk, and take targeted action to improve retention?"

---

## Slide 3: Our Solution - The Intelligent Value Index

### What is IVI?
A **predictive scoring system** that combines health outcomes, service experience, and cost sustainability into a single actionable metric.

### IVI Score = f(H, E, U)
| Dimension | What it Measures | Key Question |
|-----------|------------------|--------------|
| **H - Health Outcomes** | Medical need intensity, chronic conditions | Are members getting healthier? |
| **E - Experience Quality** | Pre-auth approvals, call resolution, complaints | Are customers satisfied with service? |
| **U - Utilization Efficiency** | Loss ratio, cost per member, claims patterns | Is this contract financially sustainable? |

### How IVI Helps Decision Makers
1. **Predict:** Identify at-risk clients before they churn
2. **Explain:** Understand WHY a client is at risk (which dimension is failing)
3. **Prioritize:** Focus resources on high-value, high-risk contracts
4. **Act:** Recommend tailored interventions per segment
5. **Track:** Monitor intervention effectiveness over time

---

## Slide 4: Data Overview & Cleaning

### Dataset Summary
| Dataset | Rows | Description |
|---------|------|-------------|
| Claims | 86M | Healthcare services, billing, diagnoses |
| Pre-auth | 305M | Treatment authorization requests |
| Calls | 8.9M | Customer service interactions |
| Members | 4.3M | Demographics, enrollment, premium |

**Coverage:** 2022-2023 contract periods, 143K contract-years

### Data Cleaning Strategy

#### Filtering Small Contracts
**Problem:** 82% of contracts have <5 members but represent only 0.6% of premium
- High variance, noisy metrics
- Fundamentally different behavior (individual vs corporate)
- Class imbalance: 85% churn vs 15% retained

**Solution:** Filter to contracts with 5+ members
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Contracts | 100% | 17.2% | -82.8% |
| Members | 100% | 97% | -3% |
| Premium | 100% | 99.4% | -0.6% |
| Class Balance | 85/15 | 44/56 | Balanced |

#### Data Quality Handling
- **Missing Values:** Imputed with 0 for counts, median for ratios
- **Outliers:** Capped at 99th percentile for cost metrics
- **Infinite Values:** Loss ratios >10 capped to prevent model instability
- **Date Alignment:** Aligned features to contract year (not service year)

---

## Slide 5: Feature Engineering - Building the H, E, U Dimensions

### Health Outcomes (H) - 12 Features
| Feature | Description |
|---------|-------------|
| `UTILIZATION_RATE` | % of members who filed claims |
| `DIAGNOSES_PER_UTILIZER` | Avg conditions per active member |
| `CLAIMS_PER_UTILIZER` | Claim frequency per utilizer |
| `AVG_CLAIM_AMOUNT` | Mean cost per claim |
| `P90_CLAIM_AMOUNT` | 90th percentile - high-cost exposure |
| `MAX_CLAIM_AMOUNT` | Largest single claim (catastrophic cases) |

### Experience Quality (E) - 15 Features
| Feature | Description |
|---------|-------------|
| `CALLS_PER_MEMBER` | Service contact intensity |
| `AVG_RESOLUTION_DAYS` | Ticket closure time |
| `APPROVAL_RATE` | Pre-auth success rate |
| `REJECTION_RATE` | Pre-auth denial rate |
| `COMPLAINT_RATE` | Proportion of complaint calls |
| `WEEKEND_CALLS` | After-hours contact (urgency indicator) |

### Utilization Efficiency (U) - 11 Features
| Feature | Description |
|---------|-------------|
| `LOSS_RATIO` | Claims / Premium (profitability) |
| `COST_PER_MEMBER` | Avg cost burden per head |
| `COST_PER_UTILIZER` | Active member cost |
| `PREMIUM_PER_MEMBER` | Revenue per head |
| `BILLED_VS_ESTIMATED` | Actual vs expected ratio |

---

## Slide 6: Feature Engineering - Seasonal & Temporal Features

### Quarterly Distribution
| Feature | Purpose |
|---------|---------|
| `Q1_CLAIMS`, `Q2_CLAIMS`, `Q3_CLAIMS`, `Q4_CLAIMS` | Seasonal utilization patterns |
| `QUARTER_CONCENTRATION` | How concentrated claims are in one quarter (Herfindahl index) |
| `ACTIVE_MONTHS` | Number of months with activity |
| `YEAR_COVERAGE` | Proportion of year with healthcare activity |

### Why Seasonal Features Matter
- **Q4 Spike:** End-of-year utilization surge (use it or lose it mentality)
- **Ramadan Effect:** Different utilization patterns during holy month
- **Back-to-School:** September claims increase for families with children
- **Consistent Utilization:** Clients with even quarterly distribution may have better health management

---

## Slide 7: Feature Engineering - Chronic & Catastrophic Conditions

### Encoding Diagnosis Codes (DIAG_CODE)

We extracted meaningful health indicators from ICD diagnosis codes at the contract level:

#### Chronic Condition Features
| Feature | Description | Calculation |
|---------|-------------|-------------|
| `CHRONIC_PREVALENCE` | % of members with chronic conditions | Members with chronic ICD codes / Total members |
| `UNIQUE_CHRONIC_CODES` | Diversity of chronic conditions | Count of distinct chronic diagnosis codes |
| `CHRONIC_CLAIM_RATIO` | Cost burden from chronic conditions | Chronic claims / Total claims |

#### Catastrophic Case Features
| Feature | Description | Calculation |
|---------|-------------|-------------|
| `CATASTROPHIC_CASES` | Count of high-severity cases | Claims > 99th percentile threshold |
| `MAX_CLAIM_AMOUNT` | Largest single claim | Identifies oncology, transplants, etc. |
| `HIGH_COST_MEMBER_RATIO` | % of members with expensive care | Members with claims > threshold / Total |

### Business Insight
- Contracts with high `CHRONIC_PREVALENCE` need **wellness programs**
- Contracts with `CATASTROPHIC_CASES` need **case management**
- These features help explain HIGH U_SCORE (cost) issues

---

## Slide 8: Feature Engineering - Geographic & Network Features

### Regional Features
| Feature | Description |
|---------|-------------|
| `PRIMARY_REGION` | Most common provider region (Central, Western, Eastern, Southern, Northern) |
| `REGION_CONCENTRATION` | Single-region vs multi-region utilization |
| `REGION_COUNT` | Number of distinct regions used |

### Network Tier Features
| Feature | Description |
|---------|-------------|
| `PRIMARY_NETWORK` | Most used network tier (NW1-NW7) |
| `NETWORK_TIER_MIX` | Distribution across network levels |
| `PROVIDER_DIVERSITY` | Number of unique providers used |

### Why These Matter
- **Network NW1-NW2:** Premium providers = higher unit costs
- **Central/Western regions:** Higher claim volumes, more provider options
- **Single-region clients:** May face limited provider choices
- **High provider diversity:** Could indicate shopping behavior or chronic condition management

---

## Slide 9: Model Methodology & Pipeline

### Problem Formulation
- **Objective:** Predict client retention (binary classification)
- **Target:** `RETAINED_NEXT_YEAR` (1 = renewed, 0 = churned)
- **Temporal Setup:** 2022 features predict 2023 retention

### Three-Phase Pipeline

#### Phase 1: Gradient Boosting Classifier (LightGBM)
```
IVI_SCORE = Retention_Probability x 100
```
- Handles non-linear feature interactions
- Built-in missing value handling
- Fast training on 84 features

#### Phase 2: SHAP Decomposition
- Extract feature contributions per prediction
- Group by dimension (H, E, U)
- **H_SCORE** = Sum of SHAP values from health features
- **E_SCORE** = Sum of SHAP values from experience features
- **U_SCORE** = Sum of SHAP values from utilization features

#### Phase 3: Business Segmentation
- Combine IVI Risk + Contract Size + Profitability
- 12 actionable segments with tailored recommendations

### Model Performance
| Metric | Value | Interpretation |
|--------|-------|----------------|
| AUC-ROC | 0.71 | Good discrimination |
| Churned F1 | 0.62 | Identifies at-risk clients |
| Retained F1 | 0.69 | Identifies stable clients |
| Macro F1 | 0.65 | Balanced performance |

---

## Slide 10: Customer Health Risk Segmentation

### Purpose
Categorize clients based on the **health profile** of their member population to enable targeted health interventions.

**Key Question:** "How healthy is this client's member population, and what health interventions are needed?"

### Health Risk Index (HRI) Methodology

| Health Indicator | Weight | Measures |
|------------------|--------|----------|
| Utilization Rate | 25% | % of members using healthcare services |
| Diagnoses per Utilizer | 30% | Chronic condition burden per active member |
| Average Claim Amount | 25% | Claim severity and treatment complexity |
| Cost per Member | 20% | Overall healthcare consumption |

Each indicator is converted to a **percentile rank** relative to the portfolio, then weighted to compute the Health Risk Index.

### Health Risk Segments

| Segment | Threshold | Description | Recommended Interventions |
|---------|-----------|-------------|---------------------------|
| **HIGH** | HRI >= P90 | Top 10% - highest health risk | Chronic disease management, care coordination |
| **MODERATE_HIGH** | HRI P84-P90 | Elevated risk | Early intervention, health education |
| **MODERATE** | HRI P16-P84 | Average population health | Standard preventive care |
| **LOW_MODERATE** | HRI P10-P16 | Below average risk | Maintain engagement |
| **LOW** | HRI <= P10 | Healthiest population | Preserve health status |

### Health Risk vs Business Risk

| Aspect | Health Risk Segmentation | Business Risk (IVI-based) |
|--------|--------------------------|---------------------------|
| **Focus** | Population health profile | Financial and retention risk |
| **Indicators** | Utilization, diagnoses, claims | IVI score, loss ratio, premium |
| **Purpose** | Target health interventions | Prioritize account management |
| **Actions** | Wellness programs, care management | Pricing, service recovery |

**Key Insight:** A client can have HIGH health risk but LOW business risk (if profitable), or vice versa. Both perspectives inform complementary interventions.

---

## Slide 11: Business Segmentation Framework

### Multi-Dimensional Business Segmentation
IVI score alone is not enough - we segment by:

1. **IVI Risk Level** (Retention Risk)
   - HIGH RISK: IVI < 33rd percentile
   - MODERATE RISK: IVI 33-67th percentile
   - LOW RISK: IVI > 67th percentile

2. **Contract Size**
   - LARGE: >= median members
   - SMALL: < median members

3. **Profitability**
   - PROFITABLE: Loss ratio <= 1.0
   - UNPROFITABLE: Loss ratio > 1.0

### Resulting Segments (12 total)
| Segment | Priority | Example Action |
|---------|----------|----------------|
| HIGH_RISK_LARGE_UNPROFITABLE | CRITICAL | Executive escalation, pricing review |
| HIGH_RISK_LARGE_PROFITABLE | HIGH | Retention meeting, service review |
| HIGH_RISK_SMALL_UNPROFITABLE | MEDIUM | Auto-renewal decline consideration |
| MODERATE_RISK_LARGE_* | MEDIUM | Proactive wellness program |
| LOW_RISK_LARGE_PROFITABLE | LOW | Maintain, upsell opportunities |

### Prioritization Logic
```
PRIORITY = f(IVI_Risk, Contract_Size, Premium_Value, Profitability)
```
Account managers focus on HIGH/CRITICAL priority first.

---

## Slide 12: Interpretability - Understanding Why

### The "Why" Behind Each Score

#### IVI Sub-Score Decomposition
Every client gets three sub-scores explaining the overall IVI:
- **H_SCORE (Health):** Is this population healthy?
- **E_SCORE (Experience):** Is service quality good?
- **U_SCORE (Utilization):** Is this contract sustainable?

### Example Interpretations

#### Case 1: Low IVI due to Experience (E)
- **Symptom:** E_SCORE = 25/100
- **Investigation:** 40% pre-auth rejection rate, 5+ day resolution times
- **Root Cause:** Client uses providers in underserved region (Southern)
- **Action:** Expand network coverage, assign dedicated claims handler

#### Case 2: Low IVI due to Cost (U)
- **Symptom:** U_SCORE = 20/100, Loss ratio = 1.8
- **Investigation:** High cost per member, frequent large claims
- **Root Cause:** Older workforce, high chronic condition prevalence
- **Action:** Launch wellness program, negotiate premium adjustment

#### Case 3: Low IVI due to Health (H)
- **Symptom:** H_SCORE = 30/100
- **Investigation:** High utilization, many diagnoses per member
- **Root Cause:** Reactive care (emergency visits), late-stage treatments
- **Action:** Preventive screening campaigns, chronic disease management

---

## Slide 13: Interesting Findings - Seasonality & Ramadan

### Q4 Utilization Spike
- Claims increase 20-30% in Q4 (October-December)
- "Use it or lose it" behavior before year-end
- **Insight:** High `QUARTER_CONCENTRATION` in Q4 may indicate poor health management

### Ramadan Effect
- Different utilization patterns during holy month
- Lower elective procedures, higher emergency visits
- Timing of Ramadan shifts each year (lunar calendar)

### Monthly Cost Patterns
| Month | Relative Cost Index | Note |
|-------|---------------------|------|
| January | 0.95 | Post-holiday recovery |
| March-April | 1.05 | Ramadan period (varies) |
| September | 1.10 | Back-to-school |
| December | 1.25 | Year-end spike |

### Business Implication
- Plan interventions BEFORE Q4 rush
- Communicate benefits usage early in policy year
- Consider Ramadan-specific health programs

---

## Slide 14: Interesting Findings - Demographics & Regional Patterns

### New Contracts in 2023 Were Mostly Small Corporates
- 2023 saw influx of small/micro contracts
- Average size of new contracts: 12 members (vs 143 for retained)
- **Implication:** Bupa's growth strategy attracted SMB segment

### Demographic Insights
| Factor | High Cost | Low Cost |
|--------|-----------|----------|
| Nationality Diversity | High (15+ nationalities) | Low (1-5) |
| Male Ratio | 50-60% | 70%+ |
| Average Age (inferred) | Older workforce | Younger workforce |

### Regional & Network Patterns
| Region | Avg Cost/Claim | Claim Volume | Notes |
|--------|----------------|--------------|-------|
| Central (Riyadh) | High | Very High | Premium providers, full services |
| Western (Jeddah) | Medium | High | Diverse provider mix |
| Eastern | Medium | Medium | Industrial workforce |
| Southern | Low | Low | Limited provider options |

### Network Tier Impact
- **NW1-NW2 (Premium):** 40% higher unit costs but faster approvals
- **NW5-NW7 (Basic):** Lower costs but higher rejection rates

---

## Slide 15: Interesting Findings - Health Condition Patterns

### Members with Chronic Conditions
- Contracts with >20% chronic prevalence have 2x loss ratio
- Top chronic conditions by cost: Diabetes, Hypertension, Cardiovascular
- **Insight:** Early intervention in chronic management = lower future costs

### Catastrophic Cases Impact
- 5% of members generate 40% of claims
- Oncology, cardiac surgery, NICU are top cost drivers
- Single catastrophic case can flip a contract from profitable to loss-making

### Provider Shopping Behavior
- High `UNIQUE_PROVIDERS` per member may indicate:
  - Chronic condition management (good)
  - Doctor shopping / misuse (bad)
- Need to analyze alongside diagnosis patterns

### Mental Health Trend
- Mental health claims increasing year-over-year
- Higher in corporate contracts with high-stress industries
- **Opportunity:** Employee wellness programs addressing mental health

---

## Slide 16: Case Study 1 - High-Value Client at Risk

### Client Profile: Al-Rajhi Holdings (Hypothetical)
| Metric | Value | Benchmark |
|--------|-------|-----------|
| Members | 2,500 | Large |
| Premium | 15M SAR | Top 5% |
| Loss Ratio | 1.35 | Above target |
| IVI Score | 28/100 | HIGH RISK |

### Sub-Score Analysis
| Dimension | Score | Key Driver |
|-----------|-------|------------|
| H (Health) | 45 | High chronic prevalence (25%) |
| E (Experience) | 55 | Moderate - some long resolution times |
| U (Utilization) | 18 | Very high cost per member |

### Root Cause Investigation
1. Older workforce (avg age 48)
2. 3 catastrophic oncology cases in past year
3. High utilization of premium network (NW1)
4. Low preventive care participation

### Recommended Actions
1. **Immediate:** Executive meeting to discuss concerns
2. **30 days:** Deploy chronic disease management program
3. **60 days:** Propose narrow network option with incentives
4. **90 days:** Launch health screening campaign
5. **Renewal:** Adjust premium +15% with wellness commitment

---

## Slide 17: Case Study 2 - Hidden Churn Risk

### Client Profile: Tech Startup Co (Hypothetical)
| Metric | Value | Benchmark |
|--------|-------|-----------|
| Members | 150 | Medium |
| Premium | 1.2M SAR | Average |
| Loss Ratio | 0.65 | Profitable |
| IVI Score | 42/100 | MODERATE RISK |

### Surprising Risk Despite Profitability
This client is profitable but at risk - why?

### Sub-Score Analysis
| Dimension | Score | Key Driver |
|-----------|-------|------------|
| H (Health) | 70 | Young, healthy workforce |
| E (Experience) | 22 | Very poor service experience |
| U (Utilization) | 85 | Excellent cost efficiency |

### Root Cause Investigation
1. 60% pre-auth rejection rate (network mismatch)
2. Avg call resolution: 8 days (vs 2 day target)
3. 15 complaint calls in past quarter
4. HR mentioned they're "shopping alternatives"

### Recommended Actions
1. **Immediate:** Apologize, assign dedicated account manager
2. **7 days:** Review all pending pre-auths, expedite approvals
3. **14 days:** Conduct service recovery meeting
4. **30 days:** Offer service credits / premium discount
5. **Ongoing:** Weekly check-ins until trust restored

---

## Slide 18: Case Study 3 - Upsell Opportunity

### Client Profile: Saudi Construction Corp (Hypothetical)
| Metric | Value | Benchmark |
|--------|-------|-----------|
| Members | 800 | Large |
| Premium | 5M SAR | Good |
| Loss Ratio | 0.55 | Very Profitable |
| IVI Score | 85/100 | LOW RISK |

### Sub-Score Analysis
| Dimension | Score | Key Driver |
|-----------|-------|------------|
| H (Health) | 82 | Healthy workforce, low utilization |
| E (Experience) | 90 | Excellent service satisfaction |
| U (Utilization) | 78 | Sustainable, room for growth |

### Opportunity Identified
- Client is stable and satisfied
- Low healthcare utilization may mean:
  - Young workforce (growth potential)
  - Under-utilization of benefits (education needed)
  - Opportunity to add dependents

### Recommended Actions
1. **Relationship:** Assign senior account manager (VIP)
2. **Retention:** Offer early renewal with loyalty discount
3. **Upsell:** Propose dental/vision add-ons
4. **Expansion:** Market family coverage to employees
5. **Multi-year:** Lock in 3-year agreement

---

## Slide 19: Dashboard & Tool Overview

### IVI Dashboard Features

#### 1. Portfolio Overview
- Total contracts by risk segment
- Premium at risk visualization
- Trend over time

#### 2. Client Deep-Dive
- IVI score with H, E, U breakdown
- Feature importance for this client
- Peer comparison (vs similar contracts)
- Historical trend

#### 3. KPI Explorer
- Drill into any KPI
- Filter by segment, region, size
- Correlation analysis

#### 4. Recommendations Engine
- Auto-generated actions per segment
- Priority scoring for account managers
- Intervention tracking

### How Account Managers Use It
1. **Morning:** Check dashboard for new HIGH RISK alerts
2. **Planning:** Sort by priority, plan outreach
3. **Meeting Prep:** Pull client deep-dive report
4. **Action:** Log intervention, track outcome
5. **Review:** Monthly analysis of intervention effectiveness

---

## Slide 20: Key Takeaways & Business Value

### Technical Achievements
1. Processed 400M+ rows efficiently (Polars + pyreadstat)
2. Built explainable ML model with SHAP decomposition
3. Created multi-dimensional segmentation framework
4. Achieved 0.65 macro F1 with balanced class performance

### Business Value Delivered
1. **Early Warning:** Identify at-risk clients 6+ months before renewal
2. **Root Cause:** Understand WHY a client is at risk (not just that they are)
3. **Prioritization:** Focus account managers on highest-value interventions
4. **Measurability:** Track IVI trend over time to measure intervention success

### Estimated Impact
| Metric | Current | With IVI | Improvement |
|--------|---------|----------|-------------|
| Retention Rate | 15% | 25% (est.) | +67% |
| Premium Saved | - | 500M SAR | At-risk premium retained |
| Account Manager Efficiency | - | 2x | Focused prioritization |

---

## Slide 21: Next Steps & Recommendations

### Immediate (0-3 months)
1. Deploy IVI dashboard pilot with 10 account managers
2. Integrate with existing CRM system
3. Train teams on interpreting IVI scores

### Short-term (3-6 months)
1. Track intervention success rates by segment
2. Refine model with new retention data
3. Expand to include NPS/survey data

### Long-term (6-12 months)
1. Member-level IVI for B2C wellness recommendations
2. Real-time IVI updates (streaming data)
3. Automated intervention triggers
4. Integration with provider quality scores

### Vision: Proactive Healthcare Management
> IVI transforms Bupa Arabia from reactive claims processing to proactive health value management - improving member health, client satisfaction, and business sustainability.

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

### Chronic Condition ICD Codes Used
- Diabetes: E10-E14
- Hypertension: I10-I15
- Cardiovascular: I20-I25, I60-I69
- Respiratory: J40-J47
- Mental Health: F30-F39