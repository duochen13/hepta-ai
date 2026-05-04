# Issue Detection API

Complete API reference for detecting and displaying data quality issues.

> **Location:** `docs/api/detectors.md`
> **Version:** v0.1
> **Last updated:** 2026-05-02

---

## Overview

DataVint provides automated detection of 6 types of data quality issues that can degrade ML model performance:

1. **Missing Values** - Features with high null rates
2. **Duplicates** - Exact duplicate rows in the dataset
3. **Schema Violations** - Type mismatches or unexpected categorical values
4. **Numeric Range Violations** - Test values outside training min/max range
5. **Train-Test Skew** - Distribution shifts between train and test
6. **Class Imbalance** - Extreme label class ratios

---

## Quick Start

```python
import datavint as dv

# 1. Generate statistics
train_stats = dv.generate_statistics("train.csv", label_col="click")
test_stats = dv.generate_statistics("test.csv", label_col="click")

# 2. Detect issues
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# 3. Display results
dv.display_issues(issues)
```

**Output:**
```
3 issue(s) detected:

🔴 [missing_values] user_age
   58.0% of values are missing
   Direction: NE↑ AUC↓  Severity: HIGH

🟡 [train_test_skew] item_category
   Distribution differs between train and test (JS divergence: 0.156)
   Direction: NE↑ AUC↓  Severity: MEDIUM

🔴 [class_imbalance] Dataset-level
   Positive class rate is 0.50% (target: ~10%)
   Direction: NE↑ AUC↓  Severity: HIGH

============================================================
⚠ 2 HIGH severity issue(s) - address before training
ℹ 1 MEDIUM severity issue(s) - consider data cleaning
============================================================
```

---

## API Reference

### `detect_issues()`

Detect all data quality issues from dataset statistics.

```python
def detect_issues(
    statistics: DatasetStatistics,
    serving_statistics: Optional[DatasetStatistics] = None,
) -> List[Issue]:
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `statistics` | `DatasetStatistics` | ✅ Yes | Training dataset statistics from `generate_statistics()` |
| `serving_statistics` | `DatasetStatistics` | ⚠️ Optional | Test/serving dataset statistics. **Required** for schema and skew detection |

#### Returns

`List[Issue]` - List of detected issues, sorted by:
1. Severity (HIGH → MEDIUM → LOW)
2. Metric value (highest impact first)

#### Examples

**Example 1: Train-only detection**

```python
# Only detects: missing values, duplicates, class imbalance
train_stats = dv.generate_statistics("train.csv", label_col="target")
issues = dv.detect_issues(train_stats)

# Detects:
# ✅ Missing values
# ✅ Duplicates
# ✅ Class imbalance
# ❌ Schema violations (needs test set)
# ❌ Range violations (needs test set)
# ❌ Train-test skew (needs test set)
```

**Example 2: Train + Test detection (recommended)**

```python
# Detects all 6 issue types
train_stats = dv.generate_statistics("train.csv", label_col="click")
test_stats = dv.generate_statistics("test.csv", label_col="click")

issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# Detects:
# ✅ Missing values
# ✅ Duplicates
# ✅ Class imbalance
# ✅ Schema violations (unexpected categories in test)
# ✅ Range violations (test values outside train range)
# ✅ Train-test skew (distribution shifts)
```

**Example 3: Programmatic issue handling**

```python
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# Filter by severity
high_severity = [i for i in issues if i.severity.value == "high"]
print(f"⚠️ {len(high_severity)} critical issues require immediate attention")

# Filter by type
missing_issues = [i for i in issues if i.type.value == "missing_values"]
for issue in missing_issues:
    print(f"Feature '{issue.feature}' has {issue.metric_value:.1%} missing")

# Check if safe to train
if len(high_severity) > 0:
    print("❌ Do NOT train - fix high severity issues first")
else:
    print("✅ Safe to proceed with training")
```

---

### `display_issues()`

Display detected issues in human-readable format.

```python
def display_issues(issues: List[Issue]) -> None:
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issues` | `List[Issue]` | ✅ Yes | List of issues from `detect_issues()` |

#### Returns

`None` - Prints formatted output to console

#### Output Format

Each issue shows:
- **Severity icon**: 🔴 HIGH, 🟡 MEDIUM, 🔵 LOW
- **Issue type**: `[missing_values]`, `[train_test_skew]`, etc.
- **Feature name**: Affected feature (or "Dataset-level")
- **Description**: Human-readable explanation
- **ML impact**: Directional effects on NE (Normalized Entropy) and AUC
- **Severity**: HIGH/MEDIUM/LOW classification

#### Examples

**Example 1: Standard display**

```python
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)
dv.display_issues(issues)
```

**Example 2: No issues detected**

```python
issues = dv.detect_issues(clean_stats)
dv.display_issues(issues)
# Output: ✅ No issues detected!
```

**Example 3: Custom filtering before display**

```python
# Only show high severity issues
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)
high_only = [i for i in issues if i.severity.value == "high"]

print("=== CRITICAL ISSUES ONLY ===")
dv.display_issues(high_only)
```

---

## Issue Types

### 1. Missing Values

**Type:** `missing_values`
**Detects:** Features with high percentage of null/missing values

**When triggered:**
- HIGH: > 50% missing
- MEDIUM: 20-50% missing

**Example:**
```
🔴 [missing_values] user_age
   58.0% of values are missing
   Direction: NE↑ AUC↓  Severity: HIGH
```

**What this means:**
- 58% of rows have null values in `user_age`
- Model may learn biased patterns from missing value handling
- **Action:** Consider imputation or dropping feature

---

### 2. Duplicates

**Type:** `duplicates`
**Detects:** Exact duplicate rows in the dataset

**When triggered:**
- HIGH: > 10% duplicates
- MEDIUM: 5-10% duplicates

**Example:**
```
🟡 [duplicates] Dataset-level
   8.5% of rows are exact duplicates (8,500 / 100,000)
   Direction: NE↑ AUC↓  Severity: MEDIUM
```

**What this means:**
- 8,500 rows are exact copies of other rows
- May inflate model confidence on duplicated patterns
- **Action:** Remove duplicates before training

---

### 3. Schema Violations

**Type:** `schema_violation`
**Detects:** Unexpected categorical values in test set

**When triggered:**
- Any new categorical value in test that wasn't in train

**Example:**
```
🔴 [schema_violation] country_code
   Test set contains 3 unexpected values: ['XK', 'SS', 'BQ']
   Direction: NE↑ AUC↓  Severity: HIGH
```

**What this means:**
- Test set has country codes not seen during training
- Model has no learned representation for these values
- **Action:** Add unknown category handling or retrain

**Note:** Requires `serving_statistics` parameter

---

### 4. Numeric Range Violations

**Type:** `out_of_range`
**Detects:** Test values outside training min/max range

**When triggered:**
- Any numeric value in test outside train range

**Example:**
```
🟡 [out_of_range] price
   Test values [0.01, 9999.99] outside training range [1.00, 500.00]
   Direction: NE↑ AUC↓  Severity: MEDIUM
```

**What this means:**
- Test prices go below $1 and above $500 (train range)
- Model is extrapolating, not interpolating
- **Action:** Retrain with wider range or clip test values

**Note:** Requires `serving_statistics` parameter

---

### 5. Train-Test Skew

**Type:** `train_test_skew`
**Detects:** Distribution shifts between train and test

**When triggered:**
- HIGH: Jensen-Shannon divergence > 0.3
- MEDIUM: Jensen-Shannon divergence > 0.1

**Example:**
```
🟡 [train_test_skew] user_country
   Distribution differs between train and test (JS divergence: 0.156)
   Direction: NE↑ AUC↓  Severity: MEDIUM
```

**What this means:**
- User country distribution changed significantly
- May indicate data pipeline bug or temporal drift
- **Action:** Investigate why distributions differ, consider resampling

**Note:** Requires `serving_statistics` parameter

---

### 6. Class Imbalance

**Type:** `class_imbalance`
**Detects:** Extreme positive/negative class ratios

**When triggered:**
- HIGH: Minority class < 5%
- MEDIUM: Minority class 5-10%

**Example:**
```
🔴 [class_imbalance] Dataset-level
   Positive class rate is 0.50% (target: ~10%)
   Direction: NE↑ AUC↓  Severity: HIGH
```

**What this means:**
- Only 0.5% of samples are positive (1:200 ratio)
- Model may predict all-negative and achieve 99.5% accuracy
- **Action:** Use sampling techniques, class weights, or SMOTE

---

## Data Types

### `Issue`

Dataclass representing a detected quality issue.

**Attributes:**

| Field | Type | Description |
|-------|------|-------------|
| `type` | `IssueType` | Issue type enum (e.g., `IssueType.HIGH_NULL_RATE`) |
| `severity` | `IssueSeverity` | `HIGH`, `MEDIUM`, or `LOW` |
| `feature` | `Optional[str]` | Feature name (None for dataset-level issues) |
| `metric_value` | `float` | Measured value (e.g., 0.58 for 58% null rate) |
| `threshold` | `float` | Threshold used for detection (e.g., 0.5 for 50%) |
| `ne_direction` | `Optional[str]` | Impact on Normalized Entropy: "↑" or "↓" |
| `auc_direction` | `Optional[str]` | Impact on AUC: "↑" or "↓" |
| `description` | `str` | Human-readable description |
| `affected_samples` | `int` | Number of rows affected |

**Example:**

```python
issues = dv.detect_issues(train_stats)
for issue in issues:
    print(f"Type: {issue.type.value}")
    print(f"Feature: {issue.feature}")
    print(f"Severity: {issue.severity.value}")
    print(f"Metric: {issue.metric_value:.2%}")
    print(f"Affected rows: {issue.affected_samples:,}")
    print()
```

---

### `IssueType`

Enum of all issue types detected in v0.1.

**Values:**

```python
class IssueType(Enum):
    HIGH_NULL_RATE = "missing_values"
    DUPLICATE_SAMPLES = "duplicates"
    SCHEMA_VIOLATION = "schema_violation"
    OUT_OF_RANGE = "out_of_range"
    TRAIN_TEST_SKEW = "train_test_skew"
    CLASS_IMBALANCE = "class_imbalance"
```

**Example:**

```python
from datavint import IssueType

issues = dv.detect_issues(train_stats)

# Filter by type
skew_issues = [i for i in issues if i.type == IssueType.TRAIN_TEST_SKEW]
missing_issues = [i for i in issues if i.type == IssueType.HIGH_NULL_RATE]
```

---

### `IssueSeverity`

Enum of severity levels.

**Values:**

```python
class IssueSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
```

**Example:**

```python
from datavint import IssueSeverity

issues = dv.detect_issues(train_stats)

# Count by severity
high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
medium = sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)
low = sum(1 for i in issues if i.severity == IssueSeverity.LOW)

print(f"HIGH: {high}, MEDIUM: {medium}, LOW: {low}")
```

---

## Complete Workflow

### Pre-Training Quality Check

```python
import datavint as dv

# 1. Profile first (quick overview)
dv.profile_dataset("train.csv", label_col="click")
dv.compare_datasets("train.csv", "test.csv", label_col="click")

# 2. Generate detailed statistics
train_stats = dv.generate_statistics("train.csv", label_col="click")
test_stats = dv.generate_statistics("test.csv", label_col="click")

# 3. Detect issues
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# 4. Display results
dv.display_issues(issues)

# 5. Programmatic decision
high_severity = [i for i in issues if i.severity.value == "high"]
if len(high_severity) > 0:
    print("\n❌ BLOCKED: Fix high severity issues before training")
    for issue in high_severity:
        print(f"  - {issue.feature or 'Dataset'}: {issue.description}")
else:
    print("\n✅ APPROVED: Data quality check passed")
```

---

### CI/CD Integration

```python
# In your CI/CD pipeline
import sys
import datavint as dv

# Run quality checks
train_stats = dv.generate_statistics("data/train.csv", label_col="target")
test_stats = dv.generate_statistics("data/test.csv", label_col="target")

issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# Fail pipeline if high severity issues detected
high_severity_count = sum(1 for i in issues if i.severity.value == "high")

if high_severity_count > 0:
    print(f"❌ PIPELINE FAILED: {high_severity_count} high severity issue(s)")
    dv.display_issues(issues)
    sys.exit(1)
else:
    print("✅ Data quality check passed")
    sys.exit(0)
```

---

### Daily Pipeline Monitoring

```python
import datavint as dv
from datetime import datetime, timedelta

# Check today's data refresh
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
today = datetime.now().strftime("%Y-%m-%d")

yesterday_stats = dv.generate_statistics(f"data/{yesterday}/train.csv")
today_stats = dv.generate_statistics(f"data/{today}/train.csv")

# Detect any distribution shifts
issues = dv.detect_issues(yesterday_stats, serving_statistics=today_stats)

# Alert on any issues
if len(issues) > 0:
    print(f"🚨 Data pipeline alert for {today}")
    dv.display_issues(issues)
    # Send alert to Slack, PagerDuty, etc.
else:
    print(f"✅ Data pipeline healthy for {today}")
```

---

## Detection Thresholds

### Current Thresholds (v0.1)

| Detector | HIGH Threshold | MEDIUM Threshold |
|----------|----------------|------------------|
| **Missing Values** | > 50% null | 20-50% null |
| **Duplicates** | > 10% duplicates | 5-10% duplicates |
| **Schema** | Any new value | - |
| **Range** | Any out-of-range | - |
| **Skew** | JS divergence > 0.3 | JS divergence > 0.1 |
| **Imbalance** | < 5% minority | 5-10% minority |

### Customization (v0.2+)

Future versions will support custom thresholds:

```python
# Coming in v0.2
issues = dv.detect_issues(
    train_stats,
    thresholds={
        "missing_values": {"high": 0.3, "medium": 0.1},  # 30% / 10%
        "class_imbalance": {"high": 0.1, "medium": 0.2},  # 10% / 20%
    }
)
```

---

## ML Impact Directions

Each issue includes directional impact estimates:

| Symbol | Meaning | Example |
|--------|---------|---------|
| **NE↑** | Normalized Entropy increases | More uniform label distribution (less signal) |
| **NE↓** | Normalized Entropy decreases | More concentrated labels (potential overfitting) |
| **AUC↑** | AUC may increase | Better discrimination (rare, usually incorrect) |
| **AUC↓** | AUC may decrease | Worse discrimination (common for quality issues) |

**Typical pattern for quality issues:**
```
Direction: NE↑ AUC↓
```

This means:
- Labels become more uniform (noise)
- Model discrimination gets worse
- **Action:** Fix the issue to improve model performance

---

## Best Practices

### 1. Always Use Test Set

```python
# ❌ Bad - only detects 3 of 6 issue types
issues = dv.detect_issues(train_stats)

# ✅ Good - detects all 6 issue types
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)
```

### 2. Profile Before Detection

```python
# ✅ Good workflow
dv.profile_dataset("train.csv")  # Quick overview (< 1 sec)
stats = dv.generate_statistics("train.csv")  # Detailed (2-5 sec)
issues = dv.detect_issues(stats)  # Detection (< 1 sec)
```

### 3. Address High Severity First

```python
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# Sort and prioritize
high = [i for i in issues if i.severity.value == "high"]
medium = [i for i in issues if i.severity.value == "medium"]

print("=== FIX THESE FIRST ===")
dv.display_issues(high)

print("\n=== CONSIDER FIXING ===")
dv.display_issues(medium)
```

### 4. Track Issues Over Time

```python
import json
from datetime import datetime

issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# Log to file for trend tracking
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "issue_count": len(issues),
    "high_severity": sum(1 for i in issues if i.severity.value == "high"),
    "issues": [{"type": i.type.value, "feature": i.feature} for i in issues]
}

with open("quality_log.jsonl", "a") as f:
    f.write(json.dumps(log_entry) + "\n")
```

---

## Troubleshooting

### "No issues detected" but model performs poorly

**Possible causes:**
1. Missing test set (only 3 detectors run)
2. Thresholds too high for your domain
3. Issue type not covered in v0.1 (label noise, near-duplicates)

**Solution:**
```python
# Verify test set is used
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)

# Manually inspect statistics
print(f"Label rate: {train_stats.label_rate:.2%}")
print(f"Duplicate rate: {train_stats.duplicate_rate:.2%}")

# Check per-feature null rates
for name, stats in train_stats.features.items():
    if stats.null_rate > 0.1:  # Custom threshold
        print(f"{name}: {stats.null_rate:.1%} missing")
```

---

### High false positive rate

**Possible causes:**
1. Thresholds too strict for your domain
2. Expected distribution shifts (temporal drift)

**Solution:**
```python
# Filter by severity
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)
critical_only = [i for i in issues if i.severity.value == "high"]

# Or custom threshold checks (v0.2+)
```

---

## Related Documentation

- **[Profiling API](profiling.md)** - Quick dataset exploration
- **[Statistics API](statistics.md)** - Detailed feature statistics (coming soon)
- **[Feature Implementation](../features/issue-detection.md)** - How detectors work internally (coming soon)
- **[Design Spec](../changelog/2026-04-27-datavint-design.md)** - Product vision and architecture

---

## Version History

**v0.1 (current):**
- 6 detector types
- Binary classification support
- Fixed thresholds
- Directional impact estimates

**v0.2 (planned):**
- Custom thresholds
- Additional detectors (near-duplicates, label noise)
- Confidence scores
- What-if simulation

---

**Last updated:** 2026-05-02
**Maintained by:** DataVint Team
