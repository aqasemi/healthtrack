# IVI Pipeline Diagrams

This file contains diagrams for the IVI (Intelligent Value Index) system architecture, including data preprocessing, feature engineering, and ML model pipelines.

## 1. Data Preprocessing & Feature Engineering Pipeline

```mermaid
flowchart TB
    subgraph RAW["Raw SAS Datasets"]
        claims["sampled_claims<br/>(86M rows)"]
        preauth["sampled_preauth<br/>(305M rows)"]
        calls["sampled_calls<br/>(8.9M rows)"]
        members["sampled_member<br/>(4.3M rows)"]
    end

    subgraph LOAD["Optimized Data Loading"]
        pyread["pyreadstat<br/>multiprocessing"]
        polars["Polars LazyFrame"]
        cache["Parquet Cache"]
    end

    subgraph CLEAN["Data Cleaning"]
        missing["Missing Values<br/>(Impute 0/median)"]
        outliers["Outlier Capping<br/>(99th percentile)"]
        infinite["Infinite Values<br/>(Cap loss ratio > 10)"]
        dates["Date Alignment<br/>(Contract year)"]
    end

    subgraph FILTER["Contract Filtering"]
        minfilter["MIN_MEMBERS >= 5<br/>(Remove 82.8% contracts)"]
        retain["Retain 97% members<br/>99.4% premium"]
        balance["Class balance:<br/>85/15 -> 44/56"]
    end

    subgraph FEATURES["Feature Engineering (38+ Features)"]
        subgraph H["H - Health Outcomes (12)"]
            h1["Utilization Rate"]
            h2["Diagnoses per Utilizer"]
            h3["Claims per Utilizer"]
            h4["Avg/P90/Max Claim Amount"]
        end
        
        subgraph E["E - Experience Quality (15)"]
            e1["Calls per Member"]
            e2["Resolution Days"]
            e3["Approval/Rejection Rates"]
            e4["Call Category Distribution"]
        end
        
        subgraph U["U - Utilization Efficiency (11)"]
            u1["Loss Ratio (Claims/Premium)"]
            u2["Cost per Member"]
            u3["Cost per Utilizer"]
            u4["Premium Metrics"]
        end
        
        subgraph T["Temporal & Geographic"]
            t1["Q1-Q4 Claims Distribution"]
            t2["Quarter Concentration"]
            t3["Primary Region/Network"]
            t4["Provider Diversity"]
        end
    end

    subgraph OUTPUT["Output Datasets"]
        contract_out["contract_year_level.parquet<br/>(Features + Target)"]
        member_out["member_level.parquet"]
        dim_out["dim_*.parquet<br/>(Dimension tables)"]
    end

    claims --> pyread
    preauth --> pyread
    calls --> pyread
    members --> pyread
    
    pyread --> polars --> cache
    cache --> missing --> outliers --> infinite --> dates
    dates --> minfilter --> retain --> balance
    
    balance --> H
    balance --> E
    balance --> U
    balance --> T
    
    H --> contract_out
    E --> contract_out
    U --> contract_out
    T --> contract_out
    
    balance --> member_out
    balance --> dim_out

    style RAW fill:#FFE4B5,stroke:#333
    style LOAD fill:#B0E0E6,stroke:#333
    style CLEAN fill:#FFA07A,stroke:#333
    style FILTER fill:#FFA07A,stroke:#333
    style FEATURES fill:#98FB98,stroke:#333
    style OUTPUT fill:#DDA0DD,stroke:#333
```

---

## 2. IVI ML Model Pipeline - Three-Phase Architecture

```mermaid
flowchart TB
    subgraph INPUT["Input: 2022 Contract Features"]
        input_data["contract_year_level.parquet"]
        target["Target: RETAINED_NEXT_YEAR<br/>(Binary: 0=Churn, 1=Retain)"]
    end

    subgraph SPLIT["Data Split (Stratified)"]
        train["Train Set (70%)"]
        val["Validation Set (15%)"]
        test["Test Set (15%)"]
    end

    subgraph PHASE1["Phase 1: Gradient Boosting Classifier"]
        lgbm["LightGBM Model"]
        imbalance["Imbalance Handling:<br/>scale_pos_weight"]
        regularization["Regularization:<br/>Early stopping<br/>Feature/Bagging fraction"]
        calibration["Probability Calibration<br/>(CalibratedClassifierCV)"]
        phase1_out["Output:<br/>Retention Probability (0-1)"]
    end

    subgraph PHASE2["Phase 2: SHAP Decomposition"]
        shap_explainer["TreeExplainer"]
        shap_values["Feature Contributions<br/>(SHAP Values)"]
        
        subgraph DIM_GROUP["Dimension Grouping"]
            h_score["H_SCORE_ML<br/>(Health features)"]
            e_score["E_SCORE_ML<br/>(Experience features)"]
            u_score["U_SCORE_ML<br/>(Utilization features)"]
        end
        
        normalize["Normalize to 0-100"]
    end

    subgraph RULES["Rule-Based Scoring (Parallel)"]
        ecdf["ECDF Percentile Scoring<br/>(2022 distribution)"]
        h_rule["H_SCORE_RULE"]
        e_rule["E_SCORE_RULE"]
        u_rule["U_SCORE_RULE"]
        nonlinear["Non-Linear Aggregation:<br/>Power mean (p=-2)<br/>Floor penalty"]
    end

    subgraph PHASE3["Phase 3: Multi-Dimensional Segmentation"]
        subgraph IVI_CALC["IVI Score Calculation"]
            ivi_ml["IVI_SCORE_ML =<br/>Retention Prob x 100"]
            ivi_rule["IVI_SCORE_RULE_NL =<br/>Power Mean(H,E,U)"]
            ivi_hybrid["IVI_SCORE_HYBRID =<br/>Geomean(ML, Rule)"]
        end
        
        subgraph SEG_DIMS["Segmentation Dimensions"]
            risk_seg["IVI_RISK:<br/>High / Moderate / Low"]
            size_seg["SIZE_CLASS:<br/>Small / Large"]
            profit_seg["PROFIT_CLASS:<br/>Profitable / Unprofitable"]
        end
        
        segments["12 Combined Segments<br/>e.g., HIGH_RISK_LARGE_UNPROFITABLE"]
    end

    subgraph OUTPUTS["Model Outputs"]
        model_bundle["ivi_model_bundle.joblib"]
        scores_2022["ivi_scores_segments_2022.parquet"]
        scores_2023["ivi_scores_forward_2023.parquet"]
    end

    input_data --> SPLIT
    target --> SPLIT
    
    train --> lgbm --> imbalance --> regularization --> calibration
    val --> calibration
    calibration --> phase1_out
    
    phase1_out --> shap_explainer --> shap_values
    shap_values --> h_score & e_score & u_score --> normalize
    
    train --> ecdf --> h_rule & e_rule & u_rule --> nonlinear
    
    phase1_out --> ivi_ml
    normalize --> ivi_ml
    nonlinear --> ivi_rule
    ivi_ml --> ivi_hybrid
    ivi_rule --> ivi_hybrid
    
    ivi_hybrid --> risk_seg & size_seg & profit_seg --> segments
    
    segments --> model_bundle & scores_2022 & scores_2023

    style INPUT fill:#FFE4B5,stroke:#333
    style PHASE1 fill:#87CEEB,stroke:#333
    style PHASE2 fill:#98FB98,stroke:#333
    style RULES fill:#98FB98,stroke:#333
    style PHASE3 fill:#DDA0DD,stroke:#333
    style OUTPUTS fill:#FFB6C1,stroke:#333
```

---

## 3. Complete IVI System Architecture

```mermaid
flowchart LR
    subgraph DATA["Data Sources"]
        direction TB
        claims["Claims (86M)"]
        preauth["Pre-auth (305M)"]
        calls["Calls (8.9M)"]
        members["Members (4.3M)"]
    end

    subgraph PREPROCESS["Preprocessing Pipeline"]
        direction TB
        load["Data Loading<br/>(pyreadstat + Polars)"]
        clean["Cleaning<br/>(Missing, Outliers)"]
        filter["Filtering<br/>(MIN_MEMBERS >= 5)"]
        features["Feature Engineering<br/>(38+ features: H, E, U)"]
    end

    subgraph MODEL["ML Pipeline"]
        direction TB
        lgbm["LightGBM<br/>Retention Classifier"]
        shap["SHAP<br/>Decomposition"]
        calibrate["Probability<br/>Calibration"]
    end

    subgraph SCORING["IVI Scoring Engine"]
        direction TB
        ivi_ml["IVI_SCORE_ML"]
        ivi_rule["IVI_SCORE_RULE"]
        ivi_hybrid["IVI_SCORE_HYBRID"]
        subscores["Sub-Scores:<br/>H / E / U"]
    end

    subgraph SEGMENTS["Segmentation"]
        direction TB
        seg1["Critical<br/>(High Risk, Large, Unprofitable)"]
        seg2["Priority<br/>(High Risk, Large, Profitable)"]
        seg3["Monitoring<br/>(Moderate Risk)"]
        seg4["Nurture<br/>(Low Risk)"]
    end

    subgraph ACTIONS["Recommended Actions"]
        direction TB
        a1["Immediate Intervention"]
        a2["Account Manager Review"]
        a3["Wellness Programs"]
        a4["Maintain Relationship"]
    end

    subgraph DASHBOARD["Dashboard"]
        direction TB
        port["Portfolio Overview"]
        dive["Client Deep Dive"]
        kpi["KPI Explorer"]
        seg_view["Segment Analysis"]
    end

    DATA --> PREPROCESS --> MODEL --> SCORING --> SEGMENTS --> ACTIONS
    SEGMENTS --> DASHBOARD

    style DATA fill:#FFE4B5,stroke:#333
    style PREPROCESS fill:#B0E0E6,stroke:#333
    style MODEL fill:#98FB98,stroke:#333
    style SCORING fill:#DDA0DD,stroke:#333
    style SEGMENTS fill:#FFB6C1,stroke:#333
    style ACTIONS fill:#90EE90,stroke:#333
    style DASHBOARD fill:#87CEEB,stroke:#333
```

---

## 4. Model Performance Summary

```mermaid
graph LR
    subgraph METRICS["Model Performance Metrics"]
        auc["AUC-ROC: 0.71"]
        churn_f1["Churned F1: 0.62"]
        retain_f1["Retained F1: 0.69"]
        macro_f1["Macro F1: 0.65"]
    end

    subgraph IMPROVEMENT["Improvement from MIN_MEMBERS=5 Filter"]
        before["Before:<br/>Churned F1: 0.29<br/>Class Balance: 85/15"]
        after["After:<br/>Churned F1: 0.62 (+114%)<br/>Class Balance: 44/56"]
    end

    before --> after

    style METRICS fill:#98FB98,stroke:#333
    style IMPROVEMENT fill:#87CEEB,stroke:#333
```

---

## 5. IVI Score Interpretation

| IVI Score Range | Risk Level | Interpretation | Recommended Action |
|-----------------|------------|----------------|-------------------|
| 0-30 | High Risk | Client likely to churn | Immediate intervention needed |
| 30-60 | Moderate Risk | Borderline - investigate sub-scores | Account review required |
| 60-100 | Low Risk | Client likely to renew | Maintain relationship |

### Sub-Score Investigation

| Sub-Score | Low Score Symptom | Root Cause Examples | Action |
|-----------|-------------------|---------------------|--------|
| **H Score** | High utilization, many diagnoses | Insufficient preventive care | Health screening, disease management |
| **E Score** | High rejection rate, long resolution | Poor provider coverage in region | Expand network, dedicated handler |
| **U Score** | Loss ratio > 1.5, high cost/member | Older workforce, chronic conditions | Wellness programs, premium adjustment |

---

## File Locations

- **PlantUML Diagrams:** [ivi_pipeline_diagrams.puml](ivi_pipeline_diagrams.puml)
- **Data Pipeline Notebook:** [01_Data_Exploration_Cleaning.ipynb](../notebooks/01_Data_Exploration_Cleaning.ipynb)
- **Business Insights:** [02_Business_Insights_Analysis.ipynb](../notebooks/02_Business_Insights_Analysis.ipynb)
- **ML Model:** [03_IVI_ML_Model.ipynb](../notebooks/03_IVI_ML_Model.ipynb)
- **Dashboard:** [../dashboard/app.py](../dashboard/app.py)
