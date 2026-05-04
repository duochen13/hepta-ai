"""
Quick profiling example - show dataset overview before quality checks.
"""

import sys
sys.path.insert(0, '.')

import datavint as dv

# Simple workflow: Profile → Stats → Detect → Display

print("\n" + "🔍 DataVint Data Quality Workflow" + "\n")

# Step 1: Quick profile to understand the data
print("Step 1: Profile dataset (quick overview)")
print("-" * 60)
dv.profile_dataset(
    "playground/raw_data/movielens_anomalous.csv",
    label_col="label"
)

# Step 2: Generate detailed statistics
print("\nStep 2: Generate detailed statistics")
print("-" * 60)
stats = dv.generate_statistics(
    "playground/raw_data/movielens_anomalous.csv",
    label_col="label"
)
print(f"✅ Computed statistics for {stats.n_rows:,} rows, {len(stats.features)} features")

# Step 3: Detect issues
print("\nStep 3: Detect data quality issues")
print("-" * 60)
issues = dv.detect_issues(stats)
print(f"✅ Ran {6} detectors")

# Step 4: Display results
print("\nStep 4: Review detected issues")
print("-" * 60)
dv.display_issues(issues)

print("\n✅ Workflow complete!")
print("Next: Apply fixes using dv.generate_manifest() (coming in v0.2)")
