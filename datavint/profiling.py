"""
Data profiling - quick dataset overview before quality detection.

Provides a high-level summary of the dataset to help users understand
what they're working with before running detailed issue detection.
"""

from typing import Union, Optional
from pathlib import Path
import pandas as pd

from .types import DatasetStatistics
from .config import logger


def profile_dataset(
    data: Union[str, Path, pd.DataFrame],
    label_col: Optional[str] = None,
) -> None:
    """
    Display quick dataset profile before running quality checks.

    Shows:
    - Dataset shape (rows, columns)
    - Column types breakdown
    - Memory usage
    - Missing value summary
    - Label distribution (if supervised)
    - Sample preview

    This is a lightweight overview - detailed statistics come from
    generate_statistics().

    Args:
        data: DataFrame or path to CSV file
        label_col: Optional label column name

    Example:
        >>> import datavint as dv
        >>> dv.profile_dataset("train.csv", label_col="click")

        ═══════════════════════════════════════════════════════════
        📊 Dataset Profile
        ═══════════════════════════════════════════════════════════
        📁 Source: train.csv
        📏 Shape: 80,668 rows × 8 columns
        💾 Memory: 5.1 MB

        📋 Column Types:
           • Numeric: 5 columns (userId, movieId, rating, year, user_activity)
           • Categorical: 3 columns (genre, month, label)

        ⚠️  Missing Values:
           • Total: 0 missing values (0.0%)
           • Clean dataset ✅

        🎯 Label Distribution (click):
           • Positive (1): 48.2% (38,882 samples)
           • Negative (0): 51.8% (41,786 samples)
           • Balance: Good ✅

        📝 Sample Preview (first 5 rows):
        [Table preview]
        ═══════════════════════════════════════════════════════════
    """
    # Load data
    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_csv(path)
        source = str(path.name)
    else:
        df = data.copy()
        source = "DataFrame (in-memory)"

    # Basic info
    n_rows, n_cols = df.shape
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    # Column types
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    # Remove label from counts if present
    if label_col and label_col in numeric_cols:
        numeric_cols.remove(label_col)
    elif label_col and label_col in categorical_cols:
        categorical_cols.remove(label_col)

    # Missing values
    total_cells = n_rows * n_cols
    missing_cells = df.isna().sum().sum()
    missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
    cols_with_missing = df.columns[df.isna().any()].tolist()

    # Print profile
    print("\n" + "═" * 63)
    print("📊 Dataset Profile")
    print("═" * 63)

    # Source and shape
    print(f"📁 Source: {source}")
    print(f"📏 Shape: {n_rows:,} rows × {n_cols} columns")
    print(f"💾 Memory: {memory_mb:.1f} MB")
    print()

    # Column types
    print("📋 Column Types:")
    if numeric_cols:
        print(f"   • Numeric: {len(numeric_cols)} columns")
        print(f"     {', '.join(numeric_cols[:5])}" +
              (f", ... (+{len(numeric_cols)-5} more)" if len(numeric_cols) > 5 else ""))
    if categorical_cols:
        print(f"   • Categorical: {len(categorical_cols)} columns")
        print(f"     {', '.join(categorical_cols[:5])}" +
              (f", ... (+{len(categorical_cols)-5} more)" if len(categorical_cols) > 5 else ""))
    print()

    # Missing values summary
    print("⚠️  Missing Values:")
    if missing_cells == 0:
        print("   • No missing values ✅")
    else:
        print(f"   • Total: {missing_cells:,} missing cells ({missing_pct:.1f}%)")
        if len(cols_with_missing) <= 5:
            for col in cols_with_missing:
                col_missing = df[col].isna().sum()
                col_missing_pct = (col_missing / n_rows) * 100
                print(f"     - {col}: {col_missing:,} ({col_missing_pct:.1f}%)")
        else:
            print(f"   • Affected columns: {len(cols_with_missing)}")
            # Show top 3 worst columns
            missing_counts = df.isna().sum().sort_values(ascending=False)
            for col, count in missing_counts.head(3).items():
                pct = (count / n_rows) * 100
                print(f"     - {col}: {count:,} ({pct:.1f}%)")
            print(f"     ... and {len(cols_with_missing) - 3} more")
    print()

    # Label distribution (if supervised)
    if label_col:
        if label_col not in df.columns:
            print(f"⚠️  Label column '{label_col}' not found in dataset")
        else:
            print(f"🎯 Label Distribution ({label_col}):")
            label_counts = df[label_col].value_counts().sort_index()

            # Binary classification
            if len(label_counts) == 2:
                pos_label = label_counts.index[1] if len(label_counts.index) > 1 else 1
                neg_label = label_counts.index[0] if len(label_counts.index) > 0 else 0

                pos_count = label_counts.get(pos_label, 0)
                neg_count = label_counts.get(neg_label, 0)
                pos_pct = (pos_count / n_rows) * 100
                neg_pct = (neg_count / n_rows) * 100

                print(f"   • Positive ({pos_label}): {pos_pct:.1f}% ({pos_count:,} samples)")
                print(f"   • Negative ({neg_label}): {neg_pct:.1f}% ({neg_count:,} samples)")

                # Balance assessment
                ratio = max(pos_count, neg_count) / max(min(pos_count, neg_count), 1)
                # pos_pct is percentage (0-100), need to check properly
                if 45 <= pos_pct <= 55:
                    print("   • Balance: Excellent ✅ (perfectly balanced)")
                elif 40 <= pos_pct <= 60:
                    print(f"   • Balance: Good ✅ (nearly balanced, ratio 1:{ratio:.1f})")
                elif 20 <= pos_pct <= 80:
                    print(f"   • Balance: Fair ⚠️  (ratio 1:{ratio:.1f})")
                elif 10 <= pos_pct <= 90:
                    print(f"   • Balance: Poor ⚠️  (ratio 1:{ratio:.0f})")
                else:
                    print(f"   • Balance: Severe imbalance ❌ (ratio 1:{ratio:.0f}, rebalancing required)")

            # Multi-class
            else:
                print(f"   • Classes: {len(label_counts)}")
                for label, count in label_counts.head(5).items():
                    pct = (count / n_rows) * 100
                    print(f"     - {label}: {pct:.1f}% ({count:,} samples)")
                if len(label_counts) > 5:
                    print(f"     ... and {len(label_counts) - 5} more classes")
            print()

    # Sample preview
    print("📝 Sample Preview (first 5 rows):")
    # Limit column width for display
    with pd.option_context('display.max_columns', 10,
                          'display.width', 120,
                          'display.max_colwidth', 20):
        print(df.head(5).to_string(index=False))
    print()

    # Quick recommendations
    print("💡 Quick Assessment:")
    issues_found = []

    if missing_pct > 20:
        issues_found.append("⚠️  High missing value rate (>20%)")
    if label_col and label_col in df.columns:
        label_counts = df[label_col].value_counts()
        if len(label_counts) == 2:
            min_class_pct = (label_counts.min() / n_rows) * 100
            if min_class_pct < 5:
                issues_found.append("⚠️  Severe class imbalance (<5% minority class)")
            elif min_class_pct < 20:
                issues_found.append("⚠️  Moderate class imbalance (<20% minority class)")

    if df.duplicated().sum() / n_rows > 0.05:
        dup_pct = (df.duplicated().sum() / n_rows) * 100
        issues_found.append(f"⚠️  High duplicate rate ({dup_pct:.1f}%)")

    if memory_mb > 1000:
        issues_found.append(f"💾 Large dataset ({memory_mb:.0f} MB) - consider chunked processing")

    if issues_found:
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print("   ✅ No obvious issues detected in initial profile")

    print()
    print("=" * 63)
    print("Next step: Run dv.generate_statistics() for detailed analysis")
    print("=" * 63)


def compare_datasets(
    train_data: Union[str, Path, pd.DataFrame],
    test_data: Union[str, Path, pd.DataFrame],
    label_col: Optional[str] = None,
) -> None:
    """
    Compare two datasets (e.g., train vs test) side-by-side.

    Useful for quick sanity checks before running full skew detection.

    Args:
        train_data: Training dataset
        test_data: Test dataset
        label_col: Optional label column name

    Example:
        >>> dv.compare_datasets("train.csv", "test.csv", label_col="click")

        ═══════════════════════════════════════════════════════════
        📊 Dataset Comparison: Train vs Test
        ═══════════════════════════════════════════════════════════

                        Train           Test         Δ
        ───────────────────────────────────────────────────────
        Rows            80,668          20,168       -75.0%
        Columns         8               8            0
        Memory          5.1 MB          1.3 MB       -74.5%
        Missing %       0.0%            0.0%         +0.0%
        Duplicates %    1.2%            0.8%         -0.4%

        Label (click):
          Positive      48.2%           47.8%        -0.4%
          Negative      51.8%           52.2%        +0.4%

        ✅ Datasets are similar - no major distribution shift detected
        ═══════════════════════════════════════════════════════════
    """
    # Load both datasets
    train_df = pd.read_csv(train_data) if isinstance(train_data, (str, Path)) else train_data.copy()
    test_df = pd.read_csv(test_data) if isinstance(test_data, (str, Path)) else test_data.copy()

    # Compute statistics
    train_rows, train_cols = train_df.shape
    test_rows, test_cols = test_df.shape

    train_mem = train_df.memory_usage(deep=True).sum() / (1024 * 1024)
    test_mem = test_df.memory_usage(deep=True).sum() / (1024 * 1024)

    train_missing_pct = (train_df.isna().sum().sum() / (train_rows * train_cols)) * 100
    test_missing_pct = (test_df.isna().sum().sum() / (test_rows * test_cols)) * 100

    train_dup_pct = (train_df.duplicated().sum() / train_rows) * 100
    test_dup_pct = (test_df.duplicated().sum() / test_rows) * 100

    print("\n" + "═" * 63)
    print("📊 Dataset Comparison: Train vs Test")
    print("═" * 63)
    print()
    print(f"{'':20} {'Train':>15} {'Test':>15} {'Δ':>10}")
    print("─" * 63)

    # Rows
    row_delta = ((test_rows - train_rows) / train_rows) * 100 if train_rows > 0 else 0
    print(f"{'Rows':20} {train_rows:>15,} {test_rows:>15,} {row_delta:>9.1f}%")

    # Columns
    col_delta = test_cols - train_cols
    print(f"{'Columns':20} {train_cols:>15} {test_cols:>15} {col_delta:>10}")

    # Memory
    mem_delta = ((test_mem - train_mem) / train_mem) * 100 if train_mem > 0 else 0
    print(f"{'Memory':20} {train_mem:>14.1f} MB {test_mem:>14.1f} MB {mem_delta:>9.1f}%")

    # Missing
    missing_delta = test_missing_pct - train_missing_pct
    print(f"{'Missing %':20} {train_missing_pct:>14.1f}% {test_missing_pct:>14.1f}% {missing_delta:>+9.1f}%")

    # Duplicates
    dup_delta = test_dup_pct - train_dup_pct
    print(f"{'Duplicates %':20} {train_dup_pct:>14.1f}% {test_dup_pct:>14.1f}% {dup_delta:>+9.1f}%")

    print()

    # Label distribution
    if label_col and label_col in train_df.columns and label_col in test_df.columns:
        train_label_counts = train_df[label_col].value_counts(normalize=True) * 100
        test_label_counts = test_df[label_col].value_counts(normalize=True) * 100

        print(f"Label ({label_col}):")
        for label in sorted(train_label_counts.index):
            train_pct = train_label_counts.get(label, 0)
            test_pct = test_label_counts.get(label, 0)
            delta = test_pct - train_pct
            print(f"  {str(label):18} {train_pct:>14.1f}% {test_pct:>14.1f}% {delta:>+9.1f}%")
        print()

    # Assessment
    warnings = []
    if abs(row_delta) > 50:
        warnings.append("⚠️  Large difference in row count (>50%)")
    if col_delta != 0:
        warnings.append("⚠️  Column count mismatch - schema inconsistency!")
    if abs(missing_delta) > 10:
        warnings.append("⚠️  Missing value rate differs significantly (>10%)")
    if label_col and label_col in train_df.columns and label_col in test_df.columns:
        max_label_shift = max(
            abs(test_label_counts.get(label, 0) - train_label_counts.get(label, 0))
            for label in train_label_counts.index
        )
        if max_label_shift > 10:
            warnings.append(f"⚠️  Label distribution shift detected (>{max_label_shift:.1f}%)")

    if warnings:
        for warning in warnings:
            print(warning)
    else:
        print("✅ Datasets are similar - no major distribution shift detected")

    print()
    print("=" * 63)
    print("Next: Run dv.detect_issues() with serving_statistics for detailed skew analysis")
    print("=" * 63)
