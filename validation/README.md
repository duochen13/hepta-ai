# Validation Module

Measure HeptaAI's impact on model performance by comparing metrics before and after data quality fixes.

## ⚠️ MVP LIMITATIONS

**This module is for MVP demonstration only (<10GB datasets).**

**Current limitations:**
- ✅ Works with datasets < 10GB
- ✅ Local CSV/Parquet files only
- ✅ In-memory data copying
- ❌ Does NOT scale to production (>10GB)
- ❌ Does NOT support S3/BigQuery/HDFS
- ❌ Does NOT support distributed processing

**For production (v0.2+):**
- See `heptaai/manifest.py` (manifest-based, no copying)
- See `docs/features/validation.md` for scalability roadmap

---

## Quick Start

```python
import pandas as pd
import heptaai as hepta
from validation import fix_dataset, train_and_evaluate
from validation.metrics import compare_metrics

# 1. Load raw dirty data
train_raw = pd.read_csv("train.csv")
test = pd.read_csv("test.csv")

features = ["age", "income", "score"]
label = "click"

# 2. Baseline: Train on raw data
metrics_before = train_and_evaluate(
    train_raw, test, features, label, model_type="logistic"
)

# 3. HeptaAI detection
stats = hepta.generate_statistics(train_raw, label_col=label)
issues = hepta.detect_issues(stats)

# 4. Apply fixes
train_clean, fix_report = fix_dataset(train_raw, issues, label_col=label)

# 5. Train on clean data
metrics_after = train_and_evaluate(
    train_clean, test, features, label,
    model_type="logistic",
    class_weights=fix_report.class_weights
)

# 6. Show impact
print(compare_metrics(metrics_before, metrics_after))
```

---

## Modules

### `data_fixer.py`

Apply simple fixes based on detected issues.

```python
from validation import fix_dataset

df_clean, report = fix_dataset(df, issues, label_col="click")
print(report.summary())
```

**Fixing strategies:**
- Missing values → Median/mode imputation
- Duplicates → Drop duplicates
- Class imbalance → Compute class weights
- High null rate (>50%) → Drop feature

### `model_trainer.py`

Train lightweight models and evaluate.

```python
from validation import train_and_evaluate

metrics = train_and_evaluate(
    train_df, test_df, features, "click",
    model_type="logistic"  # or "random_forest"
)
```

### `metrics.py`

Compute performance metrics.

```python
from validation.metrics import compute_metrics, compare_metrics

metrics = compute_metrics(y_true, y_pred, y_pred_proba)
# Returns: {"auc": 0.82, "f1": 0.65, "ne": 0.35, ...}

print(compare_metrics(metrics_before, metrics_after))
```

---

## Examples

See `examples/demo_validation.py` for complete end-to-end demo.

---

## Documentation

- **[Validation Feature Spec](../docs/features/validation.md)** - Complete documentation
- **[Detectors API](../docs/api/detectors.md)** - Issue detection
- **[Profiling API](../docs/api/profiling.md)** - Quick data exploration

---

## Future: Production Scale (v0.2+)

**Manifest-based approach (no data copying):**

```python
# Future API
from heptaai.manifest import generate_manifest

# Generate lightweight manifest (no data copy)
manifest = generate_manifest(issues, label_col="click")

# Apply during training (data stays in S3)
model = manifest.apply_and_train(
    data_source="s3://bucket/train.parquet",
    model=LGBMClassifier(),
    features=features,
)
```

See `docs/features/validation.md` for full production roadmap.
