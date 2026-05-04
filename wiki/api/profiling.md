# Data Profiling in DataVint

Quick dataset overview before running quality detection.

## Features

### 1. `profile_dataset()` - Single Dataset Profile

Get a comprehensive overview of your dataset in seconds:

```python
import datavint as dv

dv.profile_dataset("train.csv", label_col="click")
```

**Output:**
```
═══════════════════════════════════════════════════════════════
📊 Dataset Profile
═══════════════════════════════════════════════════════════════
📁 Source: train.csv
📏 Shape: 80,668 rows × 8 columns
💾 Memory: 9.2 MB

📋 Column Types:
   • Numeric: 6 columns
     userId, movieId, rating, year, month, user_activity
   • Categorical: 1 columns
     genre

⚠️  Missing Values:
   • Total: 4,082 missing cells (0.6%)
     - genre: 4,082 (5.0%)

🎯 Label Distribution (click):
   • Positive (1): 48.7% (39,670 samples)
   • Negative (0): 51.3% (41,804 samples)
   • Balance: Excellent ✅ (perfectly balanced)

📝 Sample Preview (first 5 rows):
[Table preview]

💡 Quick Assessment:
   ⚠️  High missing value rate in genre (5%)
   ✅ Class balance looks good

===============================================================
Next step: Run dv.generate_statistics() for detailed analysis
===============================================================
```

### 2. `compare_datasets()` - Train vs Test Comparison

Compare two datasets side-by-side to spot distribution shifts:

```python
dv.compare_datasets(
    train_data="train.csv",
    test_data="test.csv",
    label_col="click"
)
```

**Output:**
```
═══════════════════════════════════════════════════════════════
📊 Dataset Comparison: Train vs Test
═══════════════════════════════════════════════════════════════

                        Train           Test         Δ
───────────────────────────────────────────────────────────────
Rows                   80,668          20,168      -75.0%
Columns                     8               8           0
Memory                   9.2 MB           2.3 MB     -75.0%
Missing %                0.0%            0.0%        +0.0%
Duplicates %             1.2%            0.8%        -0.4%

Label (click):
  Positive (1)          48.2%           47.8%        -0.4%
  Negative (0)          51.8%           52.2%        +0.4%

✅ Datasets are similar - no major distribution shift detected
═══════════════════════════════════════════════════════════════
```

## Complete Workflow

### Recommended Usage Pattern

```python
import datavint as dv

# ═══════════════════════════════════════════════════════════════
# Step 1: Quick Profile (understand what you have)
# ═══════════════════════════════════════════════════════════════
dv.profile_dataset("train.csv", label_col="click")

# Quick sanity check: train vs test
dv.compare_datasets("train.csv", "test.csv", label_col="click")

# ═══════════════════════════════════════════════════════════════
# Step 2: Detailed Statistics
# ═══════════════════════════════════════════════════════════════
train_stats = dv.generate_statistics("train.csv", label_col="click")
test_stats = dv.generate_statistics("test.csv", label_col="click")

# ═══════════════════════════════════════════════════════════════
# Step 3: Issue Detection
# ═══════════════════════════════════════════════════════════════
issues = dv.detect_issues(
    statistics=train_stats,
    serving_statistics=test_stats  # Enables train-test skew detection
)

# ═══════════════════════════════════════════════════════════════
# Step 4: Review Results
# ═══════════════════════════════════════════════════════════════
dv.display_issues(issues)

# ═══════════════════════════════════════════════════════════════
# Step 5: Generate Manifest (v0.2+)
# ═══════════════════════════════════════════════════════════════
# manifest = dv.generate_manifest(train_stats, issues)
# cleaned_data = manifest.apply("train.csv")
```

## What Gets Detected in Profile

### Balance Assessment

| Positive Rate | Assessment | Recommendation |
|---------------|------------|----------------|
| 45-55% | ✅ Excellent (perfectly balanced) | Ready to train |
| 40-60% | ✅ Good (nearly balanced) | Ready to train |
| 20-80% | ⚠️  Fair | Consider reweighting |
| 10-90% | ⚠️  Poor | Resampling recommended |
| <10% or >90% | ❌ Severe imbalance | Rebalancing required |

### Quick Assessment Warnings

**Automatic detection of:**
- High missing value rate (>20%)
- Severe class imbalance (<5% minority class)
- High duplicate rate (>5%)
- Large datasets (>1GB) - suggests chunked processing

## Use Cases

### 1. **Quick Data Exploration**

```python
# New dataset from a colleague - what is this?
dv.profile_dataset("mystery_data.csv")

# Output shows:
# - 100K rows × 25 columns (user behavior data)
# - Mostly numeric features (engagement metrics)
# - 15% missing values in 'session_duration'
# - Severe imbalance (2% conversion rate)
```

### 2. **Pre-Training Sanity Check**

```python
# Before spending hours training, check the data
dv.compare_datasets("train.csv", "test.csv", label_col="converted")

# Output shows:
# ⚠️  Label distribution shift detected (>8% difference)
# → Train: 6.2% positive | Test: 14.1% positive
# → Train-test distribution mismatch - investigate before training!
```

### 3. **Data Pipeline Monitoring**

```python
# Daily data refresh - did something break?
import datetime

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

dv.compare_datasets(
    f"data/{yesterday}/train.csv",
    f"data/{today}/train.csv",
    label_col="click"
)

# Output shows:
# ⚠️  Large difference in row count (>50%)
# → Today's data is missing half the rows - pipeline issue!
```

### 4. **In-Memory DataFrame Profiling**

```python
import pandas as pd

# Working with DataFrames in Jupyter
df = pd.read_sql("SELECT * FROM user_events", connection)

dv.profile_dataset(df, label_col="conversion")
# No need to save to disk first!
```

## API Reference

### `profile_dataset()`

```python
def profile_dataset(
    data: Union[str, Path, pd.DataFrame],
    label_col: Optional[str] = None,
) -> None
```

**Parameters:**
- `data`: File path (CSV) or pandas DataFrame
- `label_col`: Target column name (None for unsupervised)

**Output:**
- Prints formatted profile to console
- No return value

### `compare_datasets()`

```python
def compare_datasets(
    train_data: Union[str, Path, pd.DataFrame],
    test_data: Union[str, Path, pd.DataFrame],
    label_col: Optional[str] = None,
) -> None
```

**Parameters:**
- `train_data`: Training dataset (file path or DataFrame)
- `test_data`: Test dataset (file path or DataFrame)
- `label_col`: Target column name (None for unsupervised)

**Output:**
- Prints side-by-side comparison to console
- No return value

## Performance

**Profiling is fast:**
- 100K rows: ~0.5 seconds
- 1M rows: ~2 seconds
- 10M rows: ~15 seconds

Much faster than full `generate_statistics()` because it only computes:
- Row/column counts
- Basic type inference
- Missing value counts
- Label distribution

**Use profiling when:**
- ✅ First time seeing a dataset
- ✅ Quick sanity check before training
- ✅ Debugging data pipeline issues
- ✅ Comparing multiple dataset versions

**Use `generate_statistics()` when:**
- ✅ Need detailed per-feature statistics
- ✅ Running full quality detection
- ✅ Need histograms, percentiles, correlations

## Examples

See `examples/demo_profiling.py` for complete examples.

Quick start:
```bash
python3 examples/quick_profile.py
```
