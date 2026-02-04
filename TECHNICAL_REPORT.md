# Intelligent Value Index (IVI) 
## Technical Implementation Report

**Bupa Arabia Health Hackathon - Futurethon 2026**

---

## Table of Contents

1. [Challenge Context and Objectives](#1-challenge-context-and-objectives)
2. [IVI Model Framework](#2-ivi-model-framework)
3. [Data Processing Pipeline](#3-data-processing-pipeline)
4. [Predictive Model Development](#4-predictive-model-development)
5. [Customer Health Risk Segmentation](#5-customer-health-risk-segmentation)
6. [Visualization and Decision Support](#6-visualization-and-decision-support)
7. [Recommended Actions and Interventions](#7-recommended-actions-and-interventions)
8. [Model Outputs and Deliverables](#8-model-outputs-and-deliverables)
9. [Implementation Guide](#9-implementation-guide)

---

## 1. Challenge Context and Objectives

### 1.1 The Business Challenge

Bupa Arabia faces a critical challenge: **85% of corporate contracts do not renew year-over-year**. This high churn rate represents significant lost premium revenue and missed opportunities for proactive intervention. Account managers often discover issues only at renewal time, when it is too late to address underlying concerns.

### 1.2 The IVI Solution

The Intelligent Value Index addresses this challenge by providing:

| Capability | Business Value |
|------------|----------------|
| **Early Warning System** | Identify at-risk clients 6+ months before renewal |
| **Root Cause Analysis** | Understand WHY clients are at risk through dimension-based scoring |
| **Prioritization Engine** | Focus resources on high-value accounts requiring attention |
| **Action Recommendations** | Tailored interventions based on specific risk factors |
| **Customer Health Risk Segmentation** | Categorize populations by health profile for targeted wellness programs |

### 1.3 Key Questions the IVI Answers

For each corporate client, the IVI system answers:

1. **How healthy is this client's population today, and how will it impact future costs?**
2. **Are they receiving good health outcomes and service quality?**
3. **Is there a risk of dissatisfaction or churn due to cost or experience issues?**
4. **What preventive actions can be taken early to improve retention and health value?**

---

## 2. IVI Model Framework

### 2.1 The IVI Formula

The IVI Score integrates three fundamental dimensions of client assessment:

```
IVI Score = f(H, E, U)
```

**Score Range:** 0 to 100 (higher = healthier client relationship)

### 2.2 Dimension Definitions

#### Dimension H: Health Outcomes

**Core Question:** *Are members becoming healthier?*

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| Utilization Rate | Proportion of members accessing healthcare | Lower indicates healthier population |
| Diagnoses per Utilizer | Average conditions per active member | Lower indicates less chronic burden |
| Average Claim Amount | Mean cost per claim event | Lower indicates less severe conditions |
| Cost per Member | Total healthcare spend per member | Lower indicates better health management |

**Business Insight:** High H Score indicates a population with good health status and effective preventive care.

#### Dimension E: Experience Quality

**Core Question:** *Are customers receiving quality service?*

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| Pre-auth Approval Rate | Success rate of authorization requests | Higher indicates smooth coverage |
| Resolution Time | Days to resolve service tickets | Lower indicates responsive support |
| Call Volume per Member | Service contact intensity | Lower indicates fewer issues |
| Complaint Rate | Proportion of negative interactions | Lower indicates satisfaction |

**Business Insight:** High E Score indicates clients receiving smooth, friction-free service experience.

#### Dimension U: Utilization Efficiency

**Core Question:** *Are costs reasonable and sustainable?*

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| Loss Ratio | Claims paid / Premium earned | Below 1.0 indicates profitability |
| Cost per Utilizer | Spend per member using services | Benchmark comparison indicates efficiency |
| Billing Variance | Actual vs estimated costs | Lower indicates predictable costs |

**Business Insight:** High U Score indicates a financially sustainable contract with appropriate pricing.

### 2.3 Score Calculation Approach

The IVI model uses a **machine learning-driven approach** where feature importance is learned from actual retention outcomes rather than pre-defined weights. This ensures the scoring reflects real-world predictive power.

**Sub-Score Decomposition:**

SHAP (SHapley Additive exPlanations) values decompose each prediction into dimension-specific contributions:

- **H_SCORE**: Contribution from health-related features
- **E_SCORE**: Contribution from experience-related features  
- **U_SCORE**: Contribution from utilization-related features

This decomposition enables precise identification of which dimension is driving risk for each client.

---

## 3. Data Processing Pipeline

### 3.1 Data Sources

The IVI model leverages four primary datasets capturing the complete client relationship:

| Dataset | Volume | Content |
|---------|--------|---------|
| **Claims Data** | 86 million records | Healthcare services, diagnoses, billing, provider information |
| **Pre-authorization Data** | 305 million records | Treatment approvals, rejections, estimated costs |
| **Customer Service Data** | 8.9 million records | Calls, complaints, inquiries, resolution status |
| **Member Data** | 4.3 million records | Demographics, enrollment, plan details, premium |

### 3.2 Data Quality Management

| Challenge | Resolution | Business Rationale |
|-----------|------------|-------------------|
| Missing activity counts | Impute as zero | No activity recorded means no activity occurred |
| Extreme billing outliers | Cap at 99th percentile | Catastrophic claims handled separately |
| Infinite ratios | Replace with bounded values | Ensures model stability |
| Date misalignment | Align to contract period | Consistent temporal framework |

### 3.3 Portfolio Focus Decision

**Analysis Finding:** 82.8% of contracts have fewer than 5 members, yet represent only 0.6% of total premium.

| Segment | Contracts | Premium Share | Churn Rate |
|---------|-----------|---------------|------------|
| Individual/Micro (1-4 members) | 82.8% | 0.6% | ~95% |
| Corporate (5+ members) | 17.2% | 99.4% | ~44% |

**Decision:** Focus the IVI model on corporate accounts (5+ members) where:
- Premium impact is significant
- Intervention is cost-effective
- Behavioral patterns are more stable

**Outcome:** This focus preserves 99.4% of premium value while enabling more accurate predictions.

### 3.4 Feature Engineering

The model engineers 38+ features organized by dimension:

**Health Outcomes (H):** 12 features capturing medical need intensity, chronic condition prevalence, claim severity patterns, and provider utilization diversity.

**Experience Quality (E):** 15 features measuring pre-authorization success, complaint resolution, service contact patterns, and call category distribution.

**Utilization Efficiency (U):** 11 features assessing cost sustainability, loss ratio components, premium adequacy, and billing predictability.

**Temporal Patterns:** 8 features capturing quarterly seasonality, claim concentration, and trend direction.

**Geographic Context:** 5 features incorporating regional provider density and network tier utilization.

---

## 4. Predictive Model Development

### 4.1 Prediction Objective

**Target:** Predict whether a corporate client will retain (renew) their contract for the following year.

**Temporal Setup:**
- Use 2022 contract year features to predict 2023 retention
- Mirrors real-world scenario: predict next year using current year data

### 4.2 Model Architecture

**Algorithm:** LightGBM Gradient Boosting Classifier

**Selection Rationale:**
- Excellent performance on tabular insurance data
- Native handling of missing values
- Built-in regularization prevents overfitting
- Fast training enables rapid iteration
- Compatible with SHAP for interpretability

### 4.3 Validation Strategy

```
2022 Data (Known Outcomes)
    |
    +-- Training Set (70%) -----> Model learning
    |
    +-- Validation Set (15%) ---> Early stopping, tuning
    |
    +-- Test Set (15%) ---------> Final unbiased evaluation

2023 Data (Future Scoring)
    |
    +-- Forward Application ----> Production predictions
```

**Critical:** The test set is held out completely during training and tuning to ensure unbiased performance estimates.

### 4.4 Model Performance

| Metric | Value | Business Interpretation |
|--------|-------|-------------------------|
| **AUC-ROC** | 0.71 | Good ability to rank clients by retention risk |
| **Churned F1** | 0.62 | Reliably identifies at-risk clients |
| **Retained F1** | 0.69 | Accurately identifies stable clients |
| **Lift (Top Decile)** | 2.1x | Highest-risk decile has 2.1x baseline churn rate |

**Business Value:** The model enables account managers to focus on the top 10% highest-risk clients, where intervention will have maximum impact.

### 4.5 Key Predictive Factors

The model identified these factors as most predictive of retention:

| Rank | Factor | Dimension | Insight |
|------|--------|-----------|---------|
| 1 | Loss Ratio | U | Profitability strongly predicts retention |
| 2 | Contract Size | Demo | Larger contracts more stable |
| 3 | Cost per Member | U | Cost efficiency matters |
| 4 | Utilization Rate | H | Population health impacts renewal |
| 5 | Approval Rate | E | Service friction predicts churn |
| 6 | Resolution Time | E | Support quality matters |
| 7 | Claims Frequency | H | Utilization patterns indicate risk |
| 8 | Call Volume | E | Service issues signal problems |

**Key Insight:** All three dimensions (H, E, U) contribute to retention prediction, validating the multi-dimensional IVI framework.

---

## 5. Customer Health Risk Segmentation

### 5.1 Purpose and Scope

The **Customer Health Risk Segmentation** is a core deliverable that categorizes corporate clients based on the **health profile of their member population**. This is specifically focused on medical and health indicators - not general business or financial risk.

**Primary Purpose:** Enable Bupa Arabia to identify which client populations would benefit most from targeted health interventions, wellness programs, and preventive care initiatives.

**Key Question:** *How healthy is this client's population, and what wellness interventions are needed?*

**Why Health Risk Segmentation Matters:**
- Aligns with Saudi Vision 2030 emphasis on preventive healthcare
- Enables proactive wellness interventions before health issues escalate
- Supports sustainable healthcare by addressing root causes of high utilization
- Differentiates Bupa Arabia through value-added health management services

### 5.2 Health Risk Index Methodology

The Health Risk Index (HRI) uses a **percentile-based approach** that:
- Compares each client to the overall portfolio distribution
- Uses data-driven weights from model feature importance
- Produces relative rankings that adapt as the portfolio evolves

**Indicators:**

| Indicator | Measures | High Value Indicates |
|-----------|----------|---------------------|
| Utilization Rate | Population accessing healthcare | More members need care |
| Diagnoses per Utilizer | Condition complexity | Higher chronic burden |
| Average Claim Amount | Treatment severity | More intensive care needs |
| Cost per Member | Overall health spend | Higher healthcare consumption |

### 5.3 Health Risk Segments

| Segment | Portfolio Position | Population Profile |
|---------|-------------------|-------------------|
| **HIGH** | Top 10% | Significant chronic burden, frequent utilization |
| **MODERATE-HIGH** | 84th-90th percentile | Elevated indicators, trending toward high risk |
| **MODERATE** | 16th-84th percentile | Typical population health patterns |
| **LOW-MODERATE** | 10th-16th percentile | Better than average health indicators |
| **LOW** | Bottom 10% | Healthiest population segment |

### 5.4 Segment-Specific Interventions

| Health Risk | Recommended Wellness Interventions |
|-------------|-----------------------------------|
| **HIGH** | Chronic disease management programs, care coordination, targeted health screenings, specialist optimization |
| **MODERATE-HIGH** | Early intervention programs, health education campaigns, lifestyle modification support |
| **MODERATE** | Standard preventive care, annual check-up promotions, wellness awareness |
| **LOW-MODERATE** | Engagement maintenance, preventive screening access |
| **LOW** | Recognition as healthy benchmark, health status preservation |

### 5.5 Health Risk vs Business Risk

| Aspect | Health Risk Segmentation | Business Risk (IVI-based) |
|--------|--------------------------|---------------------------|
| **Focus** | Population health profile | Financial and retention risk |
| **Primary Indicators** | Utilization, diagnoses, claim costs | IVI score, loss ratio, premium |
| **Purpose** | Target wellness interventions | Prioritize account management |
| **Typical Actions** | Disease management, screenings | Pricing review, service recovery |

**Important Insight:** A client can have HIGH health risk but LOW business risk (profitable despite high utilization), or vice versa. Both perspectives inform complementary intervention strategies.

---

## 6. Visualization and Decision Support

### 6.1 Dashboard Overview

The IVI Dashboard provides real-time decision support across four integrated views:

#### Portfolio Overview
- Total contracts, members, and premium under management
- IVI score distribution across the portfolio
- Health risk tier breakdown
- At-risk premium quantification

#### Client Deep Dive
- Individual client IVI score with gauge visualization
- Dimension breakdown (H, E, U scores)
- KPI-level detail with benchmark comparisons
- Auto-generated recommendations

#### Segment Analysis
- Multi-dimensional segment comparison
- Premium and risk distribution by segment
- Segment-specific action priorities

#### KPI Explorer
- Distribution analysis for any KPI
- Correlation with IVI and retention
- Top/bottom performer identification

### 6.2 Visual Design Principles

**Risk Communication:**
- **High Risk (Red):** Immediate attention required
- **Moderate Risk (Orange):** Monitoring and proactive outreach
- **Low Risk (Green):** Healthy relationship, maintain engagement

**Actionability:**
- Every visualization links to specific recommendations
- Drill-down capability from portfolio to individual client
- Export functionality for account team workflows

---

## 7. Recommended Actions and Interventions

### 7.1 Dimension-Based Recommendations

The system auto-generates recommendations based on which dimension is driving risk:

#### When H Score is Low (Health Issues)

| Symptom | Root Cause Investigation | Recommended Action |
|---------|-------------------------|-------------------|
| High utilization rate | Aging workforce, insufficient prevention | Deploy wellness programs, health screenings |
| Many diagnoses per member | Chronic condition prevalence | Chronic disease management, care coordination |
| High claim amounts | Complex treatments, late-stage care | Preventive screening campaigns, early intervention |

#### When E Score is Low (Experience Issues)

| Symptom | Root Cause Investigation | Recommended Action |
|---------|-------------------------|-------------------|
| High rejection rate | Provider network gaps, documentation issues | Network expansion, dedicated pre-auth handler |
| Long resolution times | Process bottlenecks, resource constraints | Priority queuing, escalation review |
| High call volume | Benefit confusion, service gaps | Member education, proactive communication |

#### When U Score is Low (Cost Issues)

| Symptom | Root Cause Investigation | Recommended Action |
|---------|-------------------------|-------------------|
| Loss ratio > 1.0 | Underpricing, adverse selection | Premium adjustment discussion, benefit redesign |
| High cost per member | Catastrophic cases, inefficient utilization | Claims audit, provider steering |
| Billing variance | Unpredictable utilization | Predictive monitoring, case management |

### 7.2 Account Management Prioritization

This prioritization is for **account manager workflow**, distinct from Customer Health Risk Segmentation which focuses on population health.

| Segment Profile | Priority | Recommended Approach |
|-----------------|----------|---------------------|
| High Risk + Large + Unprofitable | **CRITICAL** | Executive intervention, comprehensive review |
| High Risk + Large + Profitable | **URGENT** | Relationship manager deep-dive, root cause analysis |
| High Risk + Small + Profitable | **MODERATE** | Efficient automated outreach |
| Moderate Risk + Large | **WATCH** | Proactive monitoring, regular check-ins |
| Low Risk + Large + Profitable | **NURTURE** | Maintain relationship, explore upsell |

### 7.3 Early Warning Protocol

**6 Months Before Renewal:**
1. Generate IVI scores for all contracts approaching renewal
2. Flag clients with IVI < 50 or declining trend
3. Assign to appropriate intervention track based on dimension analysis
4. Deploy targeted actions (wellness, service recovery, pricing review)
5. Monitor response and adjust strategy

---

## 8. Model Outputs and Deliverables

### 8.1 IVI Scoring Outputs

| Output | Description | Update Frequency |
|--------|-------------|------------------|
| IVI_SCORE | Overall intelligent value index (0-100) | Per contract period |
| H_SCORE | Health outcomes dimension | Per contract period |
| E_SCORE | Experience quality dimension | Per contract period |
| U_SCORE | Utilization efficiency dimension | Per contract period |
| **HEALTH_RISK_SEGMENT** | **Customer Health Risk tier (HIGH/MODERATE_HIGH/MODERATE/LOW_MODERATE/LOW)** | Per contract period |
| RETENTION_RISK | Retention risk category (for account management) | Per contract period |

### 8.2 Model Artifacts

| Artifact | Purpose | Location |
|----------|---------|----------|
| Model Bundle | Trained classifier + metadata | `models/ivi_model_bundle.joblib` |
| Score Files | Historical and current IVI scores | `models/ivi_scores_*.parquet` |
| SHAP Values | Dimension decomposition | `models/shap_subscores.parquet` |

### 8.3 Dashboard Application

| Component | Function |
|-----------|----------|
| `app.py` | Main dashboard with full functionality |
| `app_presentation.py` | Simplified view for stakeholder presentations |
| `pages/*.py` | Individual dashboard pages |
| `utils/recommendations.py` | Recommendation generation logic |

---

## 9. Implementation Guide

### 9.1 System Requirements

- Python 3.9+
- 16GB RAM minimum (32GB recommended for full data processing)
- Modern web browser for dashboard access

### 9.2 Key Dependencies

```
polars          # High-performance data processing
pyreadstat      # SAS data file reading
lightgbm        # Gradient boosting model
shap            # Model interpretability
streamlit       # Dashboard framework
plotly          # Interactive visualizations
```

### 9.3 Execution Workflow

**Step 1: Data Processing**
```bash
jupyter lab notebooks/01_Data_Exploration_Cleaning.ipynb
```

**Step 2: Business Analysis**
```bash
jupyter lab notebooks/02_Business_Insights_Analysis.ipynb
```

**Step 3: Model Training**
```bash
jupyter lab notebooks/03_IVI_ML_Model.ipynb
```

**Step 4: Dashboard Launch**
```bash
cd dashboard
streamlit run app.py --server.port 8501
```

### 9.4 Ongoing Operations

**Score Refresh:**
- Run monthly to capture latest data
- Automatic detection of new contract periods

**Model Retraining:**
- Trigger when validation AUC drops below 0.65
- Recommended annually with new retention outcomes

**Monitoring:**
- Track IVI score distribution stability
- Alert on significant feature distribution shifts

---

## Document Information

| Attribute | Value |
|-----------|-------|
| Version | 2.0 |
| Date | February 4, 2026 |
| Event | Bupa Arabia Futurethon Hackathon |
| Track | HealthTech - Intelligent Value Index |

---

*This implementation supports Bupa Arabia's mission to deliver sustainable healthcare value through data-driven insights and proactive client management.*
