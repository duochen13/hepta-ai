"""
Validation Demo: Measure HeptaAI's Impact on Model Performance

This example shows the correct workflow:
1. Train baseline model on raw dirty data
2. Run HeptaAI detection
3. Apply fixes
4. Train on clean data
5. Compare metrics (prove ROI)

⚠️ MVP LIMITATION: This assumes data < 10GB that fits in memory.
   For production scale (>10GB), use manifest-based approach (v0.2+).
"""

import pandas as pd
import numpy as np
import heptaai as hepta
from validation import fix_dataset, train_and_evaluate
from validation.metrics import compare_metrics

# For reproducibility
np.random.seed(42)


def main():
    print("=" * 70)
    print("HeptaAI Validation Demo: Proving Data Quality Impact")
    print("=" * 70)
    print()

    # =========================================================================
    # 1. Load Raw Data (MovieLens Anomalous - has injected quality issues)
    # =========================================================================
    print("Step 1: Loading raw dirty data...")
    print("-" * 70)

    # Use anomalous dataset with injected quality issues
    train_raw = pd.read_csv("playground/raw_data/movielens_anomalous.csv")
    test = pd.read_csv("playground/raw_data/movielens_test.csv")

    print(f"Train: {len(train_raw):,} rows (with injected quality issues)")
    print(f"Test:  {len(test):,} rows (clean)")
    print()

    # Define features and label
    features = ["userId", "movieId", "rating", "year", "month", "user_activity"]
    label = "label"

    # =========================================================================
    # 2. Baseline: Train on Raw Data
    # =========================================================================
    print("Step 2: Training baseline model on raw data...")
    print("-" * 70)

    metrics_before = train_and_evaluate(
        train_raw,
        test,
        features,
        label,
        model_type="logistic",
    )

    print("Baseline Metrics (Raw Data):")
    print(f"  AUC:       {metrics_before['auc']:.3f}")
    print(f"  F1:        {metrics_before['f1']:.3f}")
    print(f"  NE:        {metrics_before['ne']:.3f}")
    print(f"  Precision: {metrics_before['precision']:.3f}")
    print(f"  Recall:    {metrics_before['recall']:.3f}")
    print()

    # =========================================================================
    # 3. HeptaAI Detection
    # =========================================================================
    print("Step 3: Running HeptaAI quality detection...")
    print("-" * 70)

    # Profile first (quick overview)
    print("\n📊 Quick Profile:")
    hepta.profile_dataset(train_raw, label_col=label)
    print()

    # Generate detailed statistics
    stats = hepta.generate_statistics(train_raw, label_col=label)

    # Detect issues
    issues = hepta.detect_issues(stats)

    print(f"\n🔍 Issues Detected: {len(issues)}")
    hepta.display_issues(issues)
    print()

    # =========================================================================
    # 4. Apply Fixes
    # =========================================================================
    print("Step 4: Applying data quality fixes...")
    print("-" * 70)

    train_clean, fix_report = fix_dataset(train_raw, issues, label_col=label)

    print(fix_report.summary())
    print()

    # =========================================================================
    # 5. Train on Clean Data
    # =========================================================================
    print("Step 5: Training improved model on clean data...")
    print("-" * 70)

    metrics_after = train_and_evaluate(
        train_clean,
        test,
        features,
        label,
        model_type="logistic",
        class_weights=fix_report.class_weights,  # Use computed weights
    )

    print("Improved Metrics (Clean Data):")
    print(f"  AUC:       {metrics_after['auc']:.3f}")
    print(f"  F1:        {metrics_after['f1']:.3f}")
    print(f"  NE:        {metrics_after['ne']:.3f}")
    print(f"  Precision: {metrics_after['precision']:.3f}")
    print(f"  Recall:    {metrics_after['recall']:.3f}")
    print()

    # =========================================================================
    # 6. Compare Metrics (ROI)
    # =========================================================================
    print("Step 6: Impact of HeptaAI")
    print("=" * 70)

    print(compare_metrics(metrics_before, metrics_after))
    print()

    # Summary
    auc_delta = metrics_after['auc'] - metrics_before['auc']
    auc_pct = (auc_delta / metrics_before['auc']) * 100

    print("=" * 70)
    print("✅ HeptaAI Validation Complete")
    print("=" * 70)
    print(f"AUC Improvement: {auc_delta:+.3f} ({auc_pct:+.1f}%)")
    print(f"Issues Fixed: {len(issues)}")
    print(f"Rows Cleaned: {fix_report.rows_before:,} → {fix_report.rows_after:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
