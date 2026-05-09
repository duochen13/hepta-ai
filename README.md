**Website:** [www.datavint.io](https://www.datavint.io)<br>
**Demo:** [www.datavint.io/playground](https://www.datavint.io/playground)

# DataVint

**Data Quality Detection & Optimization for Machine Learning**

From raw data to vintage quality—refine your training set before burning GPUs on unpromising results.

> A compiler for your training data—optimize datasets without changing your model.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/duochen13/datavint/releases)

## 🎉 What's New in v0.2

✨ **Manifest Generation & Application** - Automatically fix data quality issues!
- Generate manifests from detected issues
- Apply corrections: filter rows, reweight samples, impute missing values
- Validate improvements with before/after metrics
- See `notebooks/quickstart.ipynb` for examples

---

## 🚀 Quick Start (30 seconds)

```python
import datavint as dv

# 1. Quick profile - understand your data (< 1 sec)
dv.profile_dataset("train.csv", label_col="click")

# 2. Detailed statistics (2-5 sec)
stats = dv.generate_statistics("train.csv", label_col="click")

# 3. Detect quality issues (< 1 sec)
issues = dv.detect_issues(stats)
dv.display_issues(issues)

# 4. Generate manifest to fix issues (NEW in v0.2!)
manifest = dv.generate_manifest(stats)

# 5. Apply corrections
corrected_df = manifest.apply("train.csv")
# Returns: filtered rows + sample weights + imputed values
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
```

---

## 📦 Installation

```bash
# From source (development)
git clone https://github.com/duochen13/datavint.git
cd datavint
pip install -e .

# PyPI (coming soon)
# pip install datavint
```

---

## 🎯 Why DataVint?

### The Problem

**Traditional workflow:**
```python
# Train model on raw data
model.fit(train_data)  # → AUC: 0.762

# Discover issues AFTER training:
# - 20% duplicates
# - 50% missing values in key feature
# - Severe class imbalance (1:1000)
# - Train-test distribution mismatch
```

**Result:** Wasted GPU hours, poor model performance, debugging nightmare.

### The Solution

**DataVint workflow:**
```python
# Detect issues BEFORE training (< 10 seconds total)
dv.profile_dataset("train.csv")              # Quick overview
stats = dv.generate_statistics("train.csv")  # Detailed analysis
issues = dv.detect_issues(stats)             # Find problems
manifest = dv.generate_manifest(stats)       # Generate fixes ✨

# Train on cleaned data
cleaned_data = manifest.apply("train.csv")
model.fit(cleaned_data)  # → AUC: 0.824 (+6.2%)
```

**Result:** Better models, faster iteration, no surprises.

---

## ✨ Features

### Current (v0.2)

✅ **Data Profiling** - Quick dataset overview (< 1 sec)
- Shape, types, missing values, label distribution
- Automatic quality warnings
- Train vs test comparison

✅ **Statistics Generation** - Detailed feature analysis (2-5 sec)
- Per-feature: count, null%, mean, p25/p50/p75/p99, histogram
- Label entropy per segment
- Adaptive binning based on dataset size

✅ **Issue Detection** - 11 automated detectors (< 1 sec)
1. Missing values (high null rates)
2. Duplicates (exact row duplicates)
3. Schema violations (type mismatches, unexpected values)
4. Numeric range violations (values outside training range)
5. Train-test skew (distribution shifts)
6. Class imbalance (extreme ratios)
7. Completeness (features with low completeness/high missing rates)
8. Distinctness (features with few distinct values)
9. Uniqueness (features with many duplicate values)
10. Entropy (unusually low or high information content)
11. Cardinality (categorical features with too many unique values)

✅ **Manifest Generation & Application** - Automatic data quality optimization (NEW!)
- Generate manifests from detected issues
- Apply corrections: row filtering, sample reweighting, feature imputation
- Validate improvements with before/after metrics
- Configurable thresholds via `dv.config`

### Coming Soon (v0.3)

⏳ **Additional Detectors** - Expand further
- Near-duplicates
- Label noise
- Temporal drift
- Underrepresented segments
- Feature-label correlation drops
- Approximate distinct counts (HyperLogLog)
- Compliance & pattern matching

⏳ **Advanced Manifest Features**
- Serialization (save/load JSON)
- Custom correction strategies
- What-if simulation mode

### Roadmap (v1.0+)

🔮 **Learned Policy** - Cross-customer quality optimization
- Data Shapley-based quality scoring
- Contextual bandit policy learning
- What-if simulation (Mode 3)

---

## 📊 Comparison

| Feature | TFDV | Deepchecks | cleanlab | **DataVint** |
|---------|------|------------|----------|-------------|
| **Quick profiling** | ❌ | ❌ | ❌ | ✅ < 1 sec |
| **Train-test skew** | ✅ | ✅ | ❌ | ✅ |
| **Label errors** | ❌ | Partial | ✅ | ⏳ (v0.3) |
| **Actionable manifest** | ❌ | ❌ | ❌ | ✅ **NEW!** |
| **Auto-apply corrections** | ❌ | ❌ | ❌ | ✅ **NEW!** |
| **What-if simulation** | ❌ | ❌ | ❌ | ⏳ (v1.0) |
| **Framework** | TF-only | Any | Any | Any |
| **Speed** | Slow | Medium | Slow | **Fast** |

---

## 📚 Documentation

### Getting Started
- **[Quickstart Notebook](notebooks/quickstart.ipynb)** - 5-minute interactive tutorial
- **[Getting Started Guide](notebooks/GETTING_STARTED.md)** - Setup instructions
- **[Complete Demo Notebook](notebooks/data_profiling_demo.ipynb)** - In-depth guide

### API Reference
- **[Profiling API](docs/api/profiling.md)** - `profile_dataset()`, `compare_datasets()`
- **[Detectors API](docs/api/detectors.md)** - `detect_issues()`, `display_issues()`
- **[Statistics API](docs/api/)** - `generate_statistics()` (coming soon)

### Examples
- **[Python Examples](examples/)** - Working code examples
- **[Notebooks](notebooks/)** - Interactive Jupyter notebooks

### Architecture
- **[Product Design Spec](docs/changelog/2026-04-27-datavint-design.md)** - Complete vision
- **[Data Profiling Feature](docs/features/data-profiling.md)** - Implementation details

---

## 🎓 Examples

### Example 1: Quick Dataset Exploration

```python
import datavint as dv

# Profile a new dataset in < 1 second
dv.profile_dataset("mystery_data.csv", label_col="target")
```

**Output:**
```
═══════════════════════════════════════════════════════════════
📊 Dataset Profile
═══════════════════════════════════════════════════════════════
📁 Source: mystery_data.csv
📏 Shape: 100,000 rows × 25 columns
💾 Memory: 19.1 MB

📋 Column Types:
   • Numeric: 20 columns
   • Categorical: 5 columns

⚠️  Missing Values:
   • Total: 15,000 missing cells (6.0%)
     - session_duration: 5,000 (5.0%)
     - user_age: 10,000 (10.0%)

🎯 Label Distribution (target):
   • Positive (1): 3.0% (3,000 samples)
   • Negative (0): 97.0% (97,000 samples)
   • Balance: Poor ⚠️  (ratio 1:32)

💡 Quick Assessment:
   ⚠️  High missing value rate (>5%)
   ⚠️  Severe class imbalance (<5% minority class)
```

### Example 2: Pre-Training Validation

```python
# Before training, check train vs test similarity
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
Label (1)              48.2%           47.8%        -0.4%

✅ Datasets are similar - no major distribution shift detected
```

### Example 3: Complete Quality Check

```python
# Full workflow: Profile → Stats → Detect → Display
dv.profile_dataset("train.csv", label_col="click")

stats = dv.generate_statistics("train.csv", label_col="click")
issues = dv.detect_issues(stats)

dv.display_issues(issues)
```

### Example 4: Generate and Apply Manifest (v0.2)

```python
import pandas as pd
import datavint as dv

# Generate statistics from training data
train_stats = dv.generate_statistics("train.csv", label_col="click")
test_stats = dv.generate_statistics("test.csv", label_col="click")

# Detect issues (train-test skew, missing values, etc.)
issues = dv.detect_issues(train_stats, serving_statistics=test_stats)
print(f"Found {len(issues)} issues")

# Generate manifest to fix issues
manifest = dv.generate_manifest(train_stats, serving_statistics=test_stats)
print(f"Manifest: {manifest.row_mask.sum()} rows kept, {len(manifest.feature_fixes)} features fixed")

# Apply manifest to training data
train_df = pd.read_csv("train.csv")
corrected_df = manifest.apply(train_df)

# Verify improvements
corrected_stats = dv.generate_statistics(corrected_df, label_col="click")
corrected_issues = dv.detect_issues(corrected_stats, serving_statistics=test_stats)
print(f"After correction: {len(corrected_issues)} issues (fixed {len(issues) - len(corrected_issues)})")
```

---

## 🗂️ Project Structure

```
datavint/
├── datavint/                    # Core package
│   ├── __init__.py            # Public API
│   ├── profiling.py           # Data profiling
│   ├── statistics.py          # Statistics generation
│   ├── issues.py              # Issue detection orchestration
│   ├── manifest.py            # Manifest generation & application (v0.2)
│   ├── config.py              # Configuration & thresholds
│   ├── types.py               # Dataclasses
│   └── detectors/             # 11 issue detectors
│       ├── missing_values.py
│       ├── duplicates.py
│       ├── schema.py
│       ├── range.py
│       ├── skew.py
│       ├── imbalance.py
│       ├── completeness.py
│       ├── distinctness.py
│       ├── uniqueness.py
│       ├── entropy.py
│       └── cardinality.py
│
├── docs/                       # Documentation
│   ├── api/                   # API reference
│   ├── features/              # Feature specs
│   └── changelog/             # Product design & architecture
│
├── notebooks/                  # Jupyter notebooks
│   ├── quickstart.ipynb       # 5-minute intro
│   └── data_profiling_demo.ipynb  # Complete guide
│
├── examples/                   # Python examples
│   ├── demo_profiling.py
│   └── quick_profile.py
│
├── tests/                      # Unit & integration tests
│   └── detectors/
│
└── playground/                 # Test data
    └── raw_data/
        ├── movielens_train.csv
        ├── movielens_test.csv
        └── movielens_anomalous.csv
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=datavint --cov-report=html

# Run specific test
pytest tests/detectors/test_missing_values.py
```

---

## 🚀 Deployment

Ready to deploy DataVint to production? Check out the **[deployment/](deployment/)** directory for complete guides:

- **[Quick Deploy to datavint.io](deployment/DEPLOY_DATAVINT_IO.md)** - Step-by-step guide (~30 min)
  - Domain registration
  - Railway backend deployment
  - Vercel frontend deployment
  - DNS configuration

- **[General Deployment Guide](deployment/DEPLOYMENT.md)** - Platform comparisons and alternatives

- **[Deployment README](deployment/README.md)** - Overview of all deployment files

**Cost estimate:** ~$8/month (domain + hosting)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development setup:**
```bash
git clone https://github.com/duochen13/datavint.git
cd datavint
pip install -e ".[dev]"  # Install with dev dependencies
pytest  # Run tests
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

**Inspired by:**
- **TensorFlow Data Validation (TFDV)** - Statistics generation patterns
- **Deepchecks** - Issue detection framework
- **cleanlab** - Label error detection
- **Data Shapley** - Sample quality scoring (v1.0 roadmap)

**Research references:**
- Northcutt et al. "Confident Learning" (NeurIPS 2021)
- Ghorbani & Zou "Data Shapley" (ICML 2019)
- Katharopoulos et al. "Chunked Data Shapley" (CIKM 2025)

---

## 📬 Contact

- **GitHub Issues:** [Report bugs or request features](https://github.com/duochen13/datavint/issues)
- **Email:** your.email@example.com
- **LinkedIn:** [Your Profile](https://linkedin.com/in/yourprofile)

---

## ⭐ Star History

If DataVint helps you build better ML models, consider giving it a star! ⭐

---

**Built with ❤️ for the ML community**
