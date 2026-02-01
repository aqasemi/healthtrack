# IVI Project - Implementation Notes

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

- [ ] Develop IVI scoring model using `contract_level.parquet`
- [ ] Analyze health patterns by nationality using dimension tables
- [ ] Build retention prediction model
- [ ] Create visualization dashboard
