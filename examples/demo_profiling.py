"""
Demo: Data profiling workflow

Shows how to use DataVint's profiling features to understand your dataset
before running quality detection.
"""

import datavint as dv

# ═══════════════════════════════════════════════════════════════════════════
# Example 1: Quick profile of a single dataset
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("Example 1: Profile Single Dataset")
print("="*70)

dv.profile_dataset(
    "playground/raw_data/movielens_train.csv",
    label_col="label"
)


# ═══════════════════════════════════════════════════════════════════════════
# Example 2: Compare train vs test datasets
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("Example 2: Compare Train vs Test")
print("="*70)

dv.compare_datasets(
    train_data="playground/raw_data/movielens_train.csv",
    test_data="playground/raw_data/movielens_test.csv",
    label_col="label"
)


# ═══════════════════════════════════════════════════════════════════════════
# Example 3: Complete workflow - Profile → Stats → Detect
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("Example 3: Complete Workflow")
print("="*70)

# Step 1: Quick profile
print("\n[Step 1] Quick Profile:")
dv.profile_dataset("playground/raw_data/movielens_anomalous.csv", label_col="label")

# Step 2: Detailed statistics
print("\n[Step 2] Computing detailed statistics...")
stats = dv.generate_statistics(
    "playground/raw_data/movielens_anomalous.csv",
    label_col="label"
)
print(f"✅ Statistics generated for {stats.n_rows:,} rows")

# Step 3: Issue detection
print("\n[Step 3] Detecting quality issues...")
issues = dv.detect_issues(stats)

# Step 4: Display results
dv.display_issues(issues)


# ═══════════════════════════════════════════════════════════════════════════
# Example 4: Profile with in-memory DataFrame
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("Example 4: Profile In-Memory DataFrame")
print("="*70)

import pandas as pd

# Create sample DataFrame
df = pd.DataFrame({
    'user_id': range(1000),
    'age': [25, 30, None, 35] * 250,
    'country': ['US', 'UK', 'FR', 'DE'] * 250,
    'purchase': [1, 0, 1, 0] * 250,
    'amount': [100.5, 200.0, None, 150.0] * 250
})

dv.profile_dataset(df, label_col="purchase")
