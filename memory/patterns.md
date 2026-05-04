# Coding Patterns

## Validation System

- Data validation follows TFDV-inspired functional API design
- Adaptive histogram binning scales with dataset size
- Schema detection split into type detection + range detection

## Recent Work (v0.1)

- Data profiling implementation complete
- Detector suite and orchestration in place
- Adaptive histogram binning based on dataset size

## Validation Metric Calculation Pattern

### How Impact Delta is Measured

**Pipeline:**
```
1. Train on DIRTY data → metrics_before
2. Detect issues with DataVint
3. Apply fixes (e.g., remove duplicates)
4. Retrain on CLEAN data → metrics_after
5. Compare: delta = metrics_after - metrics_before
```

**Key Principle:**
- **Same test set** for both measurements (ensures fair comparison)
- **Different training sets** (dirty vs clean)
- **Model retrained from scratch** (not fine-tuned)

**Titanic Example:**
```
Before: 712 rows with 72 duplicates → AUC = 0.842
After:  640 rows (duplicates removed) → AUC = 0.845
Delta: +0.0037 (+0.4%)
```

**Why Duplicates Hurt Performance:**
- Create sampling bias in training
- Model overweights repeated patterns
- Underweights unique patterns
- Result: Poor generalization to test set

**File References:**
- Detection: `datavint/issues.py` (detect_issues)
- Fixing: `validation/data_fixer.py` (fix_dataset)
- Training: `validation/model_trainer.py` (train_and_evaluate)
- Metrics: `validation/metrics.py` (compute_metrics)
