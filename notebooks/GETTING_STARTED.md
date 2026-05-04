# Getting Started with DataVint Notebooks

Quick guide to running DataVint notebooks in 3 minutes.

## 🚀 Quick Start (3 steps)

### Step 1: Install Dependencies

```bash
# From project root directory
cd /path/to/datavint

# Install DataVint in development mode
pip install -e .

# Install Jupyter
pip install jupyter
```

### Step 2: Download Sample Data

```bash
# Download MovieLens dataset (for demo notebooks)
python playground/download_movielens.py
```

This creates:
- `playground/raw_data/movielens_train.csv` (80K rows)
- `playground/raw_data/movielens_test.csv` (20K rows)
- `playground/raw_data/movielens_anomalous.csv` (81K rows with injected issues)

### Step 3: Launch Jupyter

```bash
# From project root (important!)
jupyter notebook

# Your browser will open at: http://localhost:8888
```

Then navigate to:
- **New users:** `notebooks/quickstart.ipynb`
- **Detailed guide:** `notebooks/data_profiling_demo.ipynb`

## 📁 What's in Each Notebook?

### `quickstart.ipynb` ⚡ (5 minutes)

**Goal:** See DataVint in action immediately

**Contents:**
1. Profile a dataset (< 1 sec)
2. Compare train vs test (< 1 sec)
3. Generate statistics (2-5 sec)
4. Detect issues (< 1 sec)
5. Try with anomalous data

**Best for:**
- First-time users
- Quick demos to colleagues
- "Does this tool work?" validation

### `data_profiling_demo.ipynb` 📚 (15-20 minutes)

**Goal:** Learn all profiling features in depth

**Contents:**
1. Basic profiling
2. Anomalous data detection
3. Train vs test comparison
4. In-memory DataFrame profiling
5. Complete workflow walkthrough
6. Real-world pipeline monitoring
7. Performance benchmarks
8. When to use what
9. Best practices summary

**Best for:**
- Learning production workflows
- Understanding edge cases
- Preparing for real-world usage

## 🎯 Common Tasks

### Profile Your Own Dataset

```python
import datavint as dv

# Replace with your file path
dv.profile_dataset(
    "your_data.csv",
    label_col="your_label_column"
)
```

### Check Train/Test Similarity

```python
dv.compare_datasets(
    train_data="your_train.csv",
    test_data="your_test.csv",
    label_col="your_label"
)
```

### Detect Quality Issues

```python
# Generate stats
stats = dv.generate_statistics("your_data.csv", label_col="target")

# Detect issues
issues = dv.detect_issues(stats)

# Display results
dv.display_issues(issues)
```

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'datavint'"

**Cause:** Jupyter started from wrong directory

**Solution:**
```bash
# Make sure you're in project root
cd /path/to/datavint  # ← Important!
jupyter notebook
```

Or add this cell at the top of your notebook:
```python
import sys
sys.path.insert(0, '..')
```

### Problem: "FileNotFoundError: playground/raw_data/movielens_*.csv"

**Cause:** Sample data not downloaded

**Solution:**
```bash
python playground/download_movielens.py
```

### Problem: Kernel crashes on large datasets

**Cause:** Dataset too large for memory

**Solution:** Use profiling (lightweight) instead of full statistics:
```python
# This is fast and memory-efficient
dv.profile_dataset("large_file.csv")

# This might crash on very large files
# stats = dv.generate_statistics("large_file.csv")  # Skip for now
```

### Problem: Slow notebook performance

**Tip:** Profile first, then generate statistics only if needed:

```python
# Quick check (< 1 sec)
dv.profile_dataset("data.csv")
# ↑ Shows missing values, imbalance, duplicates

# If profile looks good, then run full stats
stats = dv.generate_statistics("data.csv")
# ↑ Takes longer, but gives detailed analysis
```

## 💡 Pro Tips

### 1. Always Profile First

```python
# ❌ Bad: Jump straight to statistics (slow)
stats = dv.generate_statistics("mystery_data.csv")

# ✅ Good: Profile first (fast overview)
dv.profile_dataset("mystery_data.csv")
# → See it's 10M rows with 50% missing values
# → Decide to clean data BEFORE running full stats
```

### 2. Use Compare for Every Training Run

```python
# Before training, always check:
dv.compare_datasets("train.csv", "test.csv", label_col="target")

# Catches:
# - Distribution shifts
# - Pipeline bugs
# - Schema mismatches
```

### 3. Profile In-Memory DataFrames

```python
import pandas as pd

# No need to save to disk
df = pd.read_sql("SELECT * FROM users", conn)
dv.profile_dataset(df, label_col="churned")
```

### 4. Bookmark Quick Cells

Keep these snippets handy for exploration:

```python
# Quick profile
dv.profile_dataset("data.csv", label_col="target")
```

```python
# Quick comparison
dv.compare_datasets("train.csv", "test.csv", label_col="target")
```

```python
# Full workflow
stats = dv.generate_statistics("data.csv", label_col="target")
issues = dv.detect_issues(stats)
dv.display_issues(issues)
```

## 🔗 Next Steps

After completing the notebooks:

1. **Try on your own data**
   - Profile your datasets
   - Compare train/test splits
   - Detect quality issues

2. **Integrate into your workflow**
   - Add profiling to data pipelines
   - Use in CI/CD for data validation
   - Monitor daily data refreshes

3. **Explore advanced features** (coming in v0.2)
   - Manifest generation
   - Automatic data cleaning
   - Quality score tracking

## 📚 Additional Resources

- **Profiling API:** `docs/api/profiling.md`
- **Detectors API:** `docs/api/detectors.md`
- **Design Spec:** `docs/changelog/2026-04-27-datavint-design.md`
- **Python Examples:** `examples/`

## 🤔 Questions?

- Check `notebooks/README.md` for detailed descriptions
- See `examples/` for non-notebook examples
- Read `docs/PROFILING.md` for API reference

Happy profiling! 🎉
