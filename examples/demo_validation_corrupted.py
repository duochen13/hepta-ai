"""
Validation Demo with Properly Corrupted Data

This demo injects SEVERE quality issues to clearly demonstrate DataVint's impact:
- 30% missing values in key feature
- 10% duplicate rows
- 5% class imbalance (from 50%)

⚠️ This is for demonstration purposes only.
   For production validation, use naturally dirty datasets.
"""

import pandas as pd
import numpy as np
import datavint as dv
from validation import fix_dataset, train_and_evaluate
from validation.metrics import compare_metrics

# For reproducibility
np.random.seed(42)


def corrupt_dataset(df, label_col):
    """
    Inject severe quality issues for demonstration.

    Returns:
        Corrupted dataframe with known issues
    """
    df_corrupted = df.copy()

    print("\n🔧 Injecting Quality Issues...")
    print("-" * 70)

    # 1. Inject 30% missing values in 'rating'
    missing_mask = np.random.random(len(df_corrupted)) < 0.30
    df_corrupted.loc[missing_mask, 'rating'] = np.nan
    print(f"✓ Injected 30% missing values in 'rating' ({missing_mask.sum():,} rows)")

    # 2. Inject 10% duplicates
    n_duplicates = int(len(df_corrupted) * 0.10)
    duplicate_indices = np.random.choice(len(df_corrupted), n_duplicates, replace=True)
    df_duplicates = df_corrupted.iloc[duplicate_indices]
    df_corrupted = pd.concat([df_corrupted, df_duplicates], ignore_index=True)
    print(f"✓ Injected 10% duplicates ({n_duplicates:,} rows)")

    # 3. Inject class imbalance (downsample to 5% positive)
    positive = df_corrupted[df_corrupted[label_col] == 1]
    negative = df_corrupted[df_corrupted[label_col] == 0]

    # Downsample positive class to 5%
    n_positive = int(len(negative) * 0.05 / 0.95)
    positive_sample = positive.sample(n=n_positive, random_state=42)

    df_corrupted = pd.concat([positive_sample, negative], ignore_index=True)
    print(f"✓ Created class imbalance: {len(positive_sample):,} positive, {len(negative):,} negative")
    print(f"  Positive rate: {len(positive_sample) / len(df_corrupted):.1%}")

    return df_corrupted


def main():
    print("=" * 70)
    print("DataVint Validation Demo: Proving Data Quality Impact")
    print("With Severely Corrupted Data")
    print("=" * 70)
    print()

    # =========================================================================
    # 1. Load Clean Data and Corrupt It
    # =========================================================================
    print("Step 1: Loading data and injecting quality issues...")
    print("-" * 70)

    # Load clean data
    train_clean_original = pd.read_csv("playground/raw_data/movielens_train.csv")
    test = pd.read_csv("playground/raw_data/movielens_test.csv")

    print(f"Clean Train: {len(train_clean_original):,} rows")
    print(f"Test:        {len(test):,} rows")

    # Corrupt the training data
    train_raw = corrupt_dataset(train_clean_original, label_col="label")

    print(f"\nCorrupted Train: {len(train_raw):,} rows")
    print()

    # Define features and label
    features = ["userId", "movieId", "rating", "year", "month", "user_activity"]
    label = "label"

    # =========================================================================
    # 2. Baseline: Train on Raw Corrupted Data
    # =========================================================================
    print("Step 2: Training baseline model on corrupted data...")
    print("-" * 70)

    metrics_before = train_and_evaluate(
        train_raw,
        test,
        features,
        label,
        model_type="logistic",
    )

    print("Baseline Metrics (Corrupted Data):")
    print(f"  AUC:       {metrics_before['auc']:.3f}")
    print(f"  F1:        {metrics_before['f1']:.3f}")
    print(f"  NE:        {metrics_before['ne']:.3f}")
    print(f"  Precision: {metrics_before['precision']:.3f}")
    print(f"  Recall:    {metrics_before['recall']:.3f}")
    print()

    # =========================================================================
    # 3. DataVint Detection
    # =========================================================================
    print("Step 3: Running DataVint quality detection...")
    print("-" * 70)

    # Profile first (quick overview)
    print("\n📊 Quick Profile:")
    dv.profile_dataset(train_raw, label_col=label)
    print()

    # Generate detailed statistics
    stats = dv.generate_statistics(train_raw, label_col=label)

    # Detect issues
    issues = dv.detect_issues(stats)

    print(f"\n🔍 Issues Detected: {len(issues)}")
    dv.display_issues(issues)
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
    print("Step 6: Impact of DataVint")
    print("=" * 70)

    print(compare_metrics(metrics_before, metrics_after))
    print()

    # Summary
    auc_delta = metrics_after['auc'] - metrics_before['auc']
    auc_pct = (auc_delta / metrics_before['auc']) * 100 if metrics_before['auc'] > 0 else 0

    print("=" * 70)
    print("✅ DataVint Validation Complete")
    print("=" * 70)
    print(f"AUC Improvement: {auc_delta:+.3f} ({auc_pct:+.1f}%)")
    print(f"Issues Fixed: {len(issues)}")
    print(f"Rows Cleaned: {fix_report.rows_before:,} → {fix_report.rows_after:,}")
    print()
    print("💡 Key Takeaway:")
    print("   DataVint detected and fixed data quality issues, improving")
    print("   model performance without any feature engineering or")
    print("   hyperparameter tuning.")
    print("=" * 70)


if __name__ == "__main__":
    main()
