# Gotchas & Things to Remember

## Gstack

- `/context-save` and `/context-restore` are separate from `/checkpoint`
- Learnings stored in `~/.gstack/projects/{project}/learnings.jsonl`
- Upgrade available: 1.21.1.0 → 1.26.0.0 (not yet applied)

## Validation Files

- New untracked validation files in working directory:
  - `validation/` directory
  - `docs/features/validation.md`
  - `examples/demo_validation.py`
  - `examples/demo_validation_corrupted.py`
## Amazon Dataset Test Results

**Date**: 2026-05-02
**Dataset**: Amazon Electronics (100K reviews, 1.4GB)

### Key Findings

1. **Data Quality**: Very clean - no issues detected
   - No missing values
   - No duplicates
   - All fields populated

2. **Data Leakage Issue**: Using 'rating' as a feature creates leakage
   - Label = (rating >= 4.0)
   - Model achieves perfect AUC=1.0
   - Not a realistic test

3. **Class Imbalance**: 80.7% positive, typical for product reviews

### Recommendations

- Use movielens_anomalous.csv for realistic quality issue testing
- Or inject quality issues into Amazon dataset
- Remove rating feature to avoid leakage


## Training Performance

### Why Validation Training is So Fast (3ms)

**Titanic Demo:**
- Dataset: 712 rows × 7 features (fits in CPU cache)
- Model: LogisticRegression (8 parameters)
- Runs: 1 (no hyperparameter search)
- Time: **3.3 milliseconds**

**Production Reality:**
- Dataset: 10M+ rows × 100+ features
- Model: XGBoost/Neural Net (50K+ parameters)
- Runs: 500+ (grid search + cross-validation)
- Time: **Hours to days**

**Scale Factors:**
- Data: 200,000× larger
- Model: 10,000× more complex
- Runs: 500× more iterations
- Total: ~1,000,000,000× slower

**Key Insight:** Demo is intentionally tiny for fast iteration. Real ML at scale requires distributed training (Spark, Ray, etc.)

## Architecture - Single Source of Truth

### Detector Implementation
- **ONLY** `/datavint/detectors/` - 11 detectors (v0.1 + v0.2 enriched)
- **NEVER** import from `server.core` - removed in 2026-05-08

### API Flow
```
User chatbox → /server/api/routes/chat.py
            → import datavint as vint
            → vint.profile(df)
            → /datavint/statistics.py (computes stats)
            → /datavint/detectors/* (runs all detectors)
            → returns (stats, issues)
```

All routes import `datavint` as a library dependency. No duplicate implementations.

## Common API Errors & Fixes

### "Issue object is not subscriptable" Error

**Fixed**: 2026-05-08 (commit 5c169b0)

**Error Message**: `'Issue' object is not subscriptable`

**Root Cause**:
- `Issue` is a dataclass that only supports attribute access (`issue.type`)
- Frontend expects dictionaries that support bracket notation (`issue['type']`)
- LLM-generated code calls `vint.profile(df)` without `return_dict=True`
- Raw Issue objects were being returned in JSON API responses

**Fix**:
- Convert Issue objects to dictionaries using `issue.to_dict()` in chat.py
- Convert DatasetStatistics objects using `stats.to_dict()` in chat.py
- Added serialization logic at lines 203-221 in server/api/routes/chat.py

**Prevention**:
- Always use `vint.profile(df, return_dict=True)` in API endpoints
- Or manually serialize Issue objects before JSON response

## Import Best Practices

### Use Absolute Imports in Routes Directory

**Fixed**: 2026-05-08 (commit 7667bde)

**Problem**:
- Relative imports (`from ..services.llm_client`) break when file structure changes
- Hard to understand where modules come from
- Refactoring-unfriendly

**Solution**:
- Use absolute imports: `from server.api.services.llm_client`
- Applied to all files in `server/api/routes/` directory

**Benefits**:
- More explicit and easier to understand
- No dependency on file location - safer refactoring
- Consistent import style across all route modules

## Missing Value Detection Thresholds

**Configuration**: `datavint/config.py`

**Default Thresholds**:
- `null_rate_high = 0.05` (5% missing → HIGH severity)
- `null_rate_medium = 0.02` (2% missing → MEDIUM severity)

**Important**: The threshold is **5%, not 50%**. This means:
- Any column with >5% missing values triggers HIGH severity
- Columns with 2-5% missing values trigger MEDIUM severity
- Very strict thresholds for production ML pipelines

**Override Example**:
```python
import datavint as dv

# Use more lenient thresholds
dv.config.null_rate_high = 0.50  # 50% instead of 5%
dv.config.null_rate_medium = 0.20  # 20% instead of 2%

# Now run detection with custom thresholds
stats, issues = dv.profile(df)
```

## NumPy Boolean Subtract Error

**Fixed**: 2026-05-09 (skill_executor.py + datavint/statistics.py)

**Error Message**: `numpy boolean subtract, the '-' operator, is not supported, use the bitwise_xor, the '^' operator, or the logical_xor function instead.`

**Root Causes:**

### 1. Boolean Column Quantile Calculation (PRIMARY FIX)
NumPy 2.0+ cannot calculate quantiles (p25, p50, p75) for boolean dtype columns. When `vint.profile(df)` processes a dataset with boolean columns (e.g., `is_active: bool`), the error occurs during `series.quantile()` calls.

**Fix in `datavint/statistics.py:204`**:
```python
# ❌ BAD - boolean dtypes incorrectly treated as numeric
if pd.api.types.is_numeric_dtype(s):
    # This fails for boolean columns
    p25=float(s_clean.quantile(0.25))

# ✅ GOOD - check boolean dtype first
if pd.api.types.is_bool_dtype(s):
    # Boolean feature - treat as categorical
    # Boolean dtypes can't have quantiles calculated on them in NumPy 2.0+
    top_vals = s_clean.value_counts(normalize=True).head(10).to_dict()
    return FeatureStats(type="categorical", ...)
elif pd.api.types.is_numeric_dtype(s):
    # Now safe to calculate quantiles
    p25=float(s_clean.quantile(0.25))
```

### 2. Arithmetic on NumPy Arrays
In `skill_executor.py`, calculating `missing_rate = 1 - completeness` where `completeness` is a NumPy boolean/array triggers this error.

**Fix**:
```python
# ❌ BAD - Can trigger error with NumPy booleans
missing_rate = 1 - feat_stats.completeness

# ✅ GOOD - Convert to float first
completeness_val = float(feat_stats.completeness)
missing_rate = 1.0 - completeness_val
```

**Where to apply**:
- Always check for boolean dtype before calculating quantiles
- Convert NumPy values to Python `float()` before arithmetic operations
- Applied in: `datavint/statistics.py` (primary), `skill_executor.py` (defensive)

## Hybrid Routing Implementation (2026-05-09)

**Location**: `server/api/services/skill_router.py` + `skill_executor.py`

**Key Decisions**:
- Skills route at 70% confidence threshold (keyword matches)
- Command matches (`/check-*`) get highest confidence (1.0)
- LLM fallback always available if skill execution fails
- Routing metadata included in API response for debugging

**Monitoring**:
- Use `/api/chat/metrics` to track skill vs LLM usage
- Expect 70-90% skill routing for healthy performance
- Cost savings should be 60-80% vs all-LLM approach

**See**: `memory/hybrid-routing.md` for implementation details
