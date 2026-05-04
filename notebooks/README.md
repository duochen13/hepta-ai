# DataVint Notebooks

Interactive Jupyter notebooks demonstrating DataVint's data quality features.

## 📚 Available Notebooks

### 1. `quickstart.ipynb` - 5 Minute Introduction

**Perfect for:** First-time users, quick demos

**What you'll learn:**
- Basic profiling workflow
- Train vs test comparison
- Statistics generation
- Issue detection

**Time:** 5 minutes

```bash
jupyter notebook notebooks/quickstart.ipynb
```

### 2. `data_profiling_demo.ipynb` - Complete Guide

**Perfect for:** In-depth learning, production workflows

**What you'll learn:**
- All profiling features in detail
- Real-world use cases
- Performance benchmarks
- Best practices
- Pipeline monitoring examples

**Time:** 15-20 minutes

```bash
jupyter notebook notebooks/data_profiling_demo.ipynb
```

## 🚀 Getting Started

### Prerequisites

```bash
# Install Jupyter (if not already installed)
pip install jupyter

# Install DataVint (from project root)
cd /path/to/datavint
pip install -e .
```

### Launch Jupyter

From the **project root directory**:

```bash
# Start Jupyter server
jupyter notebook

# Navigate to: notebooks/quickstart.ipynb
```

**Important:** Start Jupyter from the project root, not from the `notebooks/` directory. This ensures the Python path is set correctly.

## 📖 Notebook Descriptions

### Quick Start Flow

```
1. Profile dataset (< 1 sec)
   └─> Quick overview of shape, types, missing values, labels

2. Compare train/test (< 1 sec)
   └─> Side-by-side comparison, detect distribution shifts

3. Generate statistics (2-5 sec)
   └─> Detailed per-feature stats

4. Detect issues (< 1 sec)
   └─> Run all 6 detectors, display results

5. [Coming in v0.2] Apply fixes
   └─> Generate manifest, apply to data
```

### Profiling Demo Topics

**Section 1-3:** Basic usage
- Single dataset profiling
- Anomalous data detection
- Train vs test comparison

**Section 4-5:** Advanced features
- In-memory DataFrame profiling
- Complete workflow demonstration

**Section 6-7:** Real-world scenarios
- Daily pipeline monitoring
- Performance benchmarking

**Section 8-9:** Best practices
- When to use which function
- Summary and recommendations

## 🎯 Use Cases Covered

### 1. **First-Time Dataset Exploration**
```python
# What is this dataset?
dv.profile_dataset("mystery_data.csv")
# → See shape, types, missing values, balance
```

### 2. **Pre-Training Sanity Check**
```python
# Is my data ready for training?
dv.compare_datasets("train.csv", "test.csv", label_col="target")
# → Catch distribution shifts before wasting GPU time
```

### 3. **Daily Pipeline Monitoring**
```python
# Did today's data refresh succeed?
dv.compare_datasets(f"{yesterday}/data.csv", f"{today}/data.csv")
# → Detect pipeline bugs immediately
```

### 4. **Debugging Model Performance**
```python
# Model performance degraded - is it the data?
dv.profile_dataset("recent_data.csv")
stats = dv.generate_statistics("recent_data.csv")
issues = dv.detect_issues(stats)
# → Find quality issues that might explain the degradation
```

## 📊 Example Outputs

### Profile Output
```
═══════════════════════════════════════════════════════════════
📊 Dataset Profile
═══════════════════════════════════════════════════════════════
📁 Source: train.csv
📏 Shape: 80,668 rows × 8 columns
💾 Memory: 9.2 MB

📋 Column Types:
   • Numeric: 6 columns (userId, movieId, rating, ...)
   • Categorical: 1 columns (genre)

⚠️  Missing Values:
   • Total: 4,082 missing cells (0.6%)
     - genre: 4,082 (5.0%)

🎯 Label Distribution (label):
   • Positive (1): 48.7% (39,670 samples)
   • Negative (0): 51.3% (41,804 samples)
   • Balance: Excellent ✅
```

### Comparison Output
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

Label (label):
  Positive (1)          48.2%           47.8%        -0.4%
  Negative (0)          51.8%           52.2%        +0.4%

✅ Datasets are similar - no major distribution shift detected
```

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'datavint'"

**Solution:** Make sure you're running Jupyter from the project root:

```bash
# From project root
cd /path/to/datavint
jupyter notebook
```

Or add this to the first cell:
```python
import sys
sys.path.insert(0, '..')
```

### "FileNotFoundError: playground/raw_data/..."

**Solution:** Download the MovieLens dataset first:

```bash
python playground/download_movielens.py
```

Or use your own dataset:
```python
dv.profile_dataset("path/to/your/data.csv", label_col="your_label")
```

### Kernel crashes on large datasets

**Solution:** Use profiling instead of full statistics for initial exploration:

```python
# Fast (< 1 sec)
dv.profile_dataset("large_data.csv")

# Slower (might crash on very large data)
# stats = dv.generate_statistics("large_data.csv")
```

## 📚 Additional Resources

- **Profiling API:** `docs/api/profiling.md`
- **Detectors API:** `docs/api/detectors.md`
- **Python Examples:** `examples/`
- **Design Spec:** `docs/changelog/2026-04-27-datavint-design.md`

## 🤝 Contributing

Found an issue or want to add a notebook?

1. Create a new notebook in `notebooks/`
2. Follow the existing naming convention
3. Add it to this README
4. Submit a PR

## 📝 License

Same as main DataVint project.
