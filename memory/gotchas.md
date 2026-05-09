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
