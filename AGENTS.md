Always read and write to and update IMPLEMENTATION_NOTES.md after making changes, trying expermints (write why they failed/succeeded) so that we can learn from them later on.

Do not read old notebooks from exp-notebooks/ folder.

The data is saved in /volume/data folder.

# Bupa Arabia Health Hackathon - Knowledge Base

> **Competition:** Intelligent Value Index (IVI) Challenge  
> **Organizer:** Bupa Arabia (Saudi Insurance Company)  
> **Context:** Saudi Vision 2030 - Preventive Healthcare & Digital Transformation

---

## 📋 Table of Contents

1. [Challenge Overview](#challenge-overview)
2. [IVI Model Framework](#ivi-model-framework)
3. [Data Dictionary](#data-dictionary)
4. [Evaluation Criteria](#evaluation-criteria)
5. [Required Deliverables](#required-deliverables)
6. [Methodology & Approach](#methodology--approach)
7. [Stakeholder Perspectives](#stakeholder-perspectives)
8. [Customer Journey](#customer-journey)
9. [Technical Implementation Notes](#technical-implementation-notes)
10. [Business Recommendations Framework](#business-recommendations-framework)

---

## Challenge Overview

### Definition
**Utilizing health outcomes, experience, and utilization to predict retention and unlock proactive actions that improve wellbeing and sustainable value.**

### Core Problem Statement
Design the next-generation **Intelligent Value Index (IVI)** model by combining:
- Real-world insurance data
- Healthcare analytics
- Machine learning
- Business intelligence

To help insurers and companies:
- Predict future client value
- Predict retention probability
- Recommend actions to improve member wellbeing

### Three Key Pillars (Corporate Client Assessment)

| Pillar | Key Question | Focus Areas |
|--------|--------------|-------------|
| **Health Outcomes (H)** | Are members becoming healthier? | Chronic condition management, preventable claims |
| **Experience Quality (E)** | Are customers receiving quality service? | Fast approvals, smooth reimbursement, complaint handling |
| **Cost Sustainability (U)** | Are costs reasonable? | Claims patterns, utilization efficiency |

### IMPORTANT: Questions IVI Should Answer
1. How healthy is this client's population today, and how will it impact future costs?
2. Are they receiving good health outcomes and service quality?
3. Is there a risk of dissatisfaction or churn due to cost or experience?
4. What preventive actions can be taken early to improve retention and health value?

---

## IVI Model Framework

### Final Formula
```
IVI Score = f(H, E, U)
```
**Score Range:** 0 to 100

### Dimension A: Health Outcomes (H)
Measures medical need intensity:

| KPI | Description | Data Source |
|-----|-------------|-------------|
| Visit Frequency | Visits per member per period | `sampled_claims` |
| High-Cost Cases | Count/ratio of expensive treatments | `sampled_claims` (SUM_of_NETBILLED) |
| Chronic Conditions | History and trends of chronic diagnoses | `sampled_claims` (DIAG_CODE) |
| Member Risk Profile | Demographics + health patterns | `sampled_member` + `sampled_claims` |

### Dimension B: Experience Performance (E)
Evaluates service quality:

| KPI | Description | Data Source |
|-----|-------------|-------------|
| Pre-auth Turnaround Time | Time from request to approval | `sampled_preauth` (TREATMENT_DATE, STATUS) |
| Pre-auth Rejection Rate | % of rejected pre-authorizations | `sampled_preauth` (Episode_STATUS, REJ_REASON_ID) |
| Reimbursement Processing Time | Time to process reimbursements | `sampled_claims` (INCUR_DATE_FROM, PROCESS_DATE) |
| Complaint Volume | Number of service complaints | `sampled_calls` (CALL_CAT) |
| Complaint Closure Time | Time to resolve complaints | `sampled_calls` (CRT_DATE, UPD_DATE) |
| Resolution Quality | Quality of complaint resolution | `sampled_calls` (STATUS) |

### Dimension C: Utilization Efficiency (U)
Measures sustainability:

| KPI | Formula | Interpretation |
|-----|---------|----------------|
| **Loss Ratio** | Net Bill / Earned Premium | Profitability indicator |
| **Risk Cost** | Net Bill / Number of Utilizers | Cost per using member |
| **Unit Cost** | Net Bill / Number of Visits | Cost per visit |
| **Excessive Billing** | Outlier detection in billing patterns | Fraud/misuse indicator |

---

## Data Dictionary

### Primary Data Files (SAS Format)

#### 1. `sampled_claims.sas7bdat` (86M rows)
Claims and reimbursement data.

| Column | Description | Type |
|--------|-------------|------|
| `Adherent_No` | Unique member identifier | ID |
| `PLAN_ID` | Insurance plan identifier | ID |
| `CONT_NO` | Contract number (corporate client) | ID |
| `CONT_YYMM` | Contract year-month | Date |
| `VOU_NO` | Voucher/transaction number | ID |
| `LINE_NO` | Line item number | ID |
| `PROV_CODE` | Provider code | ID |
| `T_PERIOD` | Transaction period | Date |
| `INCUR_DATE_FROM` | Service/incurred date | Date |
| `PROCESS_DATE` | Claim processing date | Date |
| `CLAIM_TYPE` | Type of claim | Category |
| `DIAG_CODE` | Diagnosis code (ICD) | Code |
| `BEN_HEAD` | Benefit head/category | Category |
| `SUBMIT_BY` | Submission channel | Category |
| `STATUS` | Claim status | Category |
| `SUM_of_NETBILLED` | Net billed amount | Numeric |

#### 2. `sampled_calls.sas7bdat` (8.9M rows)
Call center interaction records.

| Column | Description | Type |
|--------|-------------|------|
| `CONT_NO` | Contract number | ID |
| `CONT_YYMM` | Contract year-month | Date |
| `MBR_NO` | Member number | ID |
| `CALL_ID` | Unique call identifier | ID |
| `STATUS` | Call/ticket status | Category |
| `CALL_CAT` | Call category (complaint, inquiry, etc.) | Category |
| `CRT_DATE` | Creation date | Date |
| `UPD_DATE` | Last update date | Date |

#### 3. `sampled_member.sas7bdat` (4.3M rows)
Member demographic and enrollment data.

| Column | Description | Type |
|--------|-------------|------|
| `Adherent_No` | Unique member identifier | ID |
| `CONT_YYMM` | Contract year-month | Date |
| `PLAN_ID` | Insurance plan identifier | ID |
| `Contract_NO` | Contract number | ID |
| `PLAN_NETWORK` | Plan network tier | Category |
| `Gender` | Member gender | Category |
| `Nationality` | Member nationality | Category |
| `WE` | Written/Earned indicator | Numeric |
| `WP` | Written Premium | Numeric |

#### 4. `sampled_preauth.sas7bdat` (305M rows)
Pre-authorization requests and outcomes.

| Column | Description | Type |
|--------|-------------|------|
| `CONT_NO` | Contract number | ID |
| `CONT_YYMM` | Contract year-month | Date |
| `MBR_NO` | Member number | ID |
| `PLAN_ID` | Plan identifier | ID |
| `PREAUTH_EPISODE_ID` | Pre-auth episode ID | ID |
| `PREAUTH_EPISODE_ITEM_ID` | Pre-auth item ID | ID |
| `TREATMENT_DATE` | Treatment date | Date |
| `PROV_CODE` | Provider code | ID |
| `Episode_STATUS (STATUS)` | Episode approval status | Category |
| `Line_STATUS (STATUS)` | Line item status | Category |
| `ICD_CODE (DIAG_CODE)` | ICD diagnosis code | Code |
| `BEN_HEAD` | Benefit head | Category |
| `REJ_REASON_ID` | Rejection reason code | Code |
| `EST_AMT` | Estimated amount | Numeric |

### Reference Files (Excel)

#### `Data_dictionary.xlsx`
Contains metadata and field descriptions.

#### `Provider_Info.xlsx` (3,556 rows)
Provider information lookup.

| Column | Description |
|--------|-------------|
| `PROV_CODE` | Unique provider code |
| `PROV_NAME` | Provider name |
| `PROVIDER_NETWORK` | Network tier (NW1-NW7+) |
| `PROVIDER_PRACTICE` | Type: Hospital, Pharmacy, Clinic, etc. |
| `PROVIDER_REGION` | Region: Central, Western, Eastern, etc. |
| `PROVIDER_TOWN` | City: Riyadh, Jeddah, etc. |
| `AREA_CODE` | Regional/country code |

### Key Relationships
```
sampled_member.Adherent_No ─────┬──── sampled_claims.Adherent_No
                                │
sampled_member.Contract_NO ─────┼──── sampled_claims.CONT_NO
                                │
sampled_calls.CONT_NO ──────────┤
                                │
sampled_preauth.CONT_NO ────────┘

sampled_claims.PROV_CODE ───────────── Provider_Info.PROV_CODE
sampled_preauth.PROV_CODE ──────────── Provider_Info.PROV_CODE
```

---

## Evaluation Criteria

### Technical Strength (20%)
| # | Criterion | Focus |
|---|-----------|-------|
| 1 | Data cleaning, validation, and feature engineering quality | Data quality |
| 2 | Clear target definition & modeling rationale | Problem framing |
| 3 | Strong evaluation, model comparison | ML rigor |

### Business Value (27%)
| # | Criterion | Focus |
|---|-----------|-------|
| 4 | Identification of key business drivers | Root cause analysis |
| 5 | Insights connected to Bupa's business impact | Domain relevance |
| 6 | Practical recommendations & feasibility | Actionability |
| 7 | Value added to decision-making | Strategic impact |

### Innovation (27%)
| # | Criterion | Focus |
|---|-----------|-------|
| 8 | Creativity of approach | Novel thinking |
| 9 | Novel tools/techniques used | Technical innovation |
| 10 | Originality in feature engineering & modeling ideas | ML creativity |
| 11 | Practicality & forward-thinking recommendations | Future-proofing |

### Visualization & Storytelling (27%)
| # | Criterion | Focus |
|---|-----------|-------|
| 12 | Clear narrative, logical flow & insight generation | Story structure |
| 13 | Strong visuals/slides | Design quality |
| 14 | Ability to simplify technical concepts | Communication |
| 15 | Equal participation, confidence & time-management | Presentation |

---

## Required Deliverables

### 1. IVI Scoring Model
- Algorithm that produces IVI Score (0-100)
- Three sub-scores: H, E, U
- Clear methodology and weighting rationale

### 2. Predictive Model
- Future IVI prediction
- Retention probability model
- Driver Analysis (top KPIs influencing IVI)

### 3. Visualization Tool
- Interactive dashboard
- Real-time monitoring capability

### 4. Customer Health Risk Segmentation
- High/Medium/Low risk categories
- Segmentation criteria and thresholds

### 5. Recommended Actions and Insights
- Actionable recommendations per segment
- Preventive interventions
- ROI projections

### Submission Format
1. Executive Summary
2. IVI model logic & scoring methodology
3. Predictive modeling documentation (IVI + retention probability)
4. Visualizations
5. Business recommendations & action plan
6. Technical documentation (code/assumptions/process)

---

### Bupa Arabia (The Insurer)

#### Definition of Retention
**Portfolio Stability** - A renewed contract means predictable revenue and lower acquisition costs vs. finding new clients.

#### Primary Concern
> "Is this client profitable, or are they a high-risk loss?"

#### IVI Use Case: Early Warning System
- Dashboard shows "Red" IVI score 6 months before contract expiry
- **If low E score:** Send relationship manager to fix service issues
- **If low H score:** Propose wellness program to client
- **If low U score:** Review pricing strategy or benefit design

### Corporate Client (HR/Finance)

#### Definition of Retention
**Value for Money** - Decision to stay depends on employee satisfaction and "fair" cost increases at renewal.

#### Primary Concern
> "Are my employees healthy and productive? Is Bupa making my life easy?"

#### IVI Use Case: ROI Report
- High H score justifies insurance spend to board
- Implies healthier, more productive workforce
- Less sick leave = tangible business value

### Hackathon Team (Data Scientists)

#### Definition of Retention
**Binary Target Variable** - The "Y" in our Y = f(X) equation.

#### Primary Concern
> "Can we prove that a low IVI Score is a statistically significant predictor of churn?"

#### Success Metrics
- AUC-ROC > 0.75
- Clear feature importance ranking
- Actionable threshold identification

---

## Customer Journey

### Stage 1: Enrollment and Welcome
- Company signs contract with Bupa Arabia
- Members (employees + dependents) registered
- Digital insurance cards issued
- Bupa App access provided

**Data Generated:** `sampled_member` entries created

### Stage 2: Digital and Health Activation
- Digital account activation
- Wellness program introduction
- Preventive health campaigns
- Health awareness messages

**Data Generated:** Engagement metrics (not in current dataset)

### Stage 3: Healthcare and Service Use
- Medical services at hospitals, clinics, pharmacies
- Pre-authorization requests for treatments
- Claims logged when services billed
- Reimbursement applications

**Data Generated:** `sampled_claims`, `sampled_preauth`

### Stage 4: Experience and Support
- Customer care contacts (phone, chat, app, social)
- Feedback, questions, complaints
- Satisfaction measurement

**Data Generated:** `sampled_calls`

### Stage 5: Analytics and Insights
- Claims, usage, complaints data analyzed
- Health patterns identified
- Service quality evaluated
- Predictive analytics applied

**Data Generated:** IVI scores, risk segments

### Stage 6: Improvement and Retention
- Service improvements implemented
- Client health trend reports
- Personalized wellness programs
- Retention strategies developed

**Data Generated:** Intervention records, renewal outcomes

---

## NOTE: We need to build a Business Recommendations Framework, that will segment clients by IVI score and suggest tailored actions to improve retention and health outcomes.


## Innovation Opportunities
### Novel Approaches to Consider
1. **Survival Analysis** for time-to-churn modeling
2. **NLP on call transcripts** (if available) for sentiment
3. **Network Analysis** of provider utilization patterns
4. **Anomaly Detection** for fraud/misuse identification
5. **Causal Inference** for intervention effectiveness

### Advanced Feature Ideas
1. **Trend Features:** YoY change in KPIs
2. **Peer Comparison:** Client vs industry benchmarks
3. **Seasonality Encoding:** Cyclical patterns in claims
4. **Provider Quality Scores:** Derived from outcomes
5. **Member Journey Features:** Touchpoint sequences

### Visualization Innovation
1. **IVI Dashboard:** Real-time monitoring with drill-down
2. **Health Maps:** Geographic visualization of claims
3. **Cohort Analysis:** Time-series of client segments
4. **Intervention Tracker:** Before/after comparisons
5. **Predictive Alerts:** Automated risk notifications

--- 
## Questions to Explore

### Technical
- [ ] What's the baseline retention rate in the data?
- [ ] How many unique contracts per year?
- [ ] What's the distribution of contract sizes?
- [ ] Are there any data quality issues to address?

### Business
- [ ] Which dimension (H, E, U) has strongest correlation with retention?
- [ ] What are the top 5 predictors of churn?
- [ ] Are there industry-specific patterns (by client sector)?
- [ ] What's the optimal IVI threshold for intervention?

### Innovation
- [ ] Can we detect early warning signals 6+ months ahead?
- [ ] Are there member-level signals that aggregate to client risk?
- [ ] Can we quantify the ROI of specific interventions?
- [ ] What would a real-time IVI monitoring system look like?

---


Implementation rules:
- DO NOT USE EMOJIS IN ANY PART OF THE CODE.
- ALWAYS CHECK YOUR CODE AND LINTING WITH RUFF.
- Write the experiments, things we tried, results and conclusions in #IMPLEMENTATION_NOTES.md file.
