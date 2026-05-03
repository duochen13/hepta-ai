"""
Data fixing strategies based on detected issues.

⚠️ MVP LIMITATION: Creates in-memory copies of data.
   Assumes datasets < 10GB that fit in memory.

   For production (>10GB data):
   - Use manifest-based approach (no copying)
   - Stream data from S3/data lake
   - Apply transformations during model training

   See: heptaai/manifest.py (coming in v0.2)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from heptaai.types import Issue


@dataclass
class FixReport:
    """Report of fixes applied to dataset."""

    fixes_applied: List[Dict[str, Any]] = field(default_factory=list)
    rows_before: int = 0
    rows_after: int = 0

    # For class imbalance - return weights instead of resampling
    class_weights: Optional[Dict[int, float]] = None

    def summary(self) -> str:
        """Return human-readable summary."""
        lines = []
        lines.append("=" * 60)
        lines.append("Data Fixes Applied")
        lines.append("=" * 60)
        lines.append(f"Rows: {self.rows_before:,} → {self.rows_after:,}")
        lines.append(f"Removed: {self.rows_before - self.rows_after:,} rows")
        lines.append("")

        for i, fix in enumerate(self.fixes_applied, 1):
            lines.append(f"{i}. {fix['issue']}")
            lines.append(f"   Action: {fix['action']}")
            if 'details' in fix:
                lines.append(f"   Details: {fix['details']}")

        if self.class_weights:
            lines.append("")
            lines.append("Class Weights:")
            for label, weight in self.class_weights.items():
                lines.append(f"  Label {label}: {weight:.3f}")

        lines.append("=" * 60)
        return "\n".join(lines)


def fix_dataset(
    df: pd.DataFrame,
    issues: List[Issue],
    label_col: str,
) -> tuple[pd.DataFrame, FixReport]:
    """
    Apply simple fixes based on detected issues.

    ⚠️ WARNING: Creates a copy of the dataframe.
       For datasets > 10GB, use manifest-based approach instead.

    Fixing Strategies:
    - missing_values: Median (numeric) or mode (categorical) imputation
    - duplicates: Drop exact duplicates, keep first occurrence
    - class_imbalance: Compute class weights (no data resampling)
    - high_null_rate (>50%): Drop feature entirely

    Args:
        df: Raw dataframe (will not be modified)
        issues: List of issues from detect_issues()
        label_col: Name of label column

    Returns:
        (df_clean, report): Cleaned dataframe and fix report

    Example:
        >>> import heptaai as hepta
        >>> from validation import fix_dataset
        >>>
        >>> # Detect issues
        >>> stats = hepta.generate_statistics("train.csv", label_col="click")
        >>> issues = hepta.detect_issues(stats)
        >>>
        >>> # Apply fixes
        >>> df = pd.read_csv("train.csv")
        >>> df_clean, report = fix_dataset(df, issues, label_col="click")
        >>> print(report.summary())
    """
    # ⚠️ MVP: Create copy (doesn't scale to >10GB)
    df_clean = df.copy()

    report = FixReport()
    report.rows_before = len(df)

    # Track features to drop (>50% missing)
    features_to_drop = []

    # Process each issue
    for issue in issues:

        # 1. DUPLICATES: Drop exact duplicates
        if issue.type.value == "duplicates":
            before = len(df_clean)
            df_clean = df_clean.drop_duplicates()
            after = len(df_clean)

            report.fixes_applied.append({
                "issue": "duplicates",
                "action": f"Removed {before - after:,} duplicate rows",
                "rows_removed": before - after,
            })

        # 2. MISSING VALUES: Imputation
        elif issue.type.value == "missing_values":
            feature = issue.feature

            # If >50% missing, drop feature instead of imputing
            if issue.metric_value > 0.5:
                features_to_drop.append(feature)
                report.fixes_applied.append({
                    "issue": "missing_values",
                    "action": f"Marked '{feature}' for removal ({issue.metric_value:.1%} missing)",
                    "feature": feature,
                })
                continue

            # Otherwise, impute
            if df_clean[feature].dtype in ['int64', 'float64', 'float32', 'int32']:
                # Numeric: Use median
                median_val = df_clean[feature].median()
                null_count = df_clean[feature].isnull().sum()
                df_clean[feature].fillna(median_val, inplace=True)

                report.fixes_applied.append({
                    "issue": "missing_values",
                    "action": f"Imputed {null_count:,} missing values in '{feature}' with median",
                    "feature": feature,
                    "details": f"median = {median_val:.2f}",
                })
            else:
                # Categorical: Use mode
                mode_val = df_clean[feature].mode()[0]
                null_count = df_clean[feature].isnull().sum()
                df_clean[feature].fillna(mode_val, inplace=True)

                report.fixes_applied.append({
                    "issue": "missing_values",
                    "action": f"Imputed {null_count:,} missing values in '{feature}' with mode",
                    "feature": feature,
                    "details": f"mode = '{mode_val}'",
                })

        # 3. CLASS IMBALANCE: Compute class weights (no resampling)
        elif issue.type.value == "class_imbalance":
            if label_col not in df_clean.columns:
                continue

            # Count positive/negative
            value_counts = df_clean[label_col].value_counts()

            if len(value_counts) == 2:  # Binary classification
                # Compute balanced class weights
                n_samples = len(df_clean)
                n_classes = 2

                class_weights = {}
                for label_value, count in value_counts.items():
                    weight = n_samples / (n_classes * count)
                    class_weights[label_value] = weight

                report.class_weights = class_weights

                report.fixes_applied.append({
                    "issue": "class_imbalance",
                    "action": f"Computed class weights for imbalanced data",
                    "details": f"Positive: {class_weights.get(1, 1.0):.3f}, Negative: {class_weights.get(0, 1.0):.3f}",
                })

    # Drop features with >50% missing
    if features_to_drop:
        df_clean = df_clean.drop(columns=features_to_drop)
        report.fixes_applied.append({
            "issue": "high_null_rate",
            "action": f"Dropped {len(features_to_drop)} feature(s) with >50% missing values",
            "features": features_to_drop,
        })

    report.rows_after = len(df_clean)

    return df_clean, report


def fix_dataset_simple(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    """
    Quick and dirty fix: Just handle missing values and duplicates.

    Use this for baseline comparison when you don't have issue detection.

    Args:
        df: Raw dataframe
        label_col: Label column name

    Returns:
        df_clean: Cleaned dataframe
    """
    df_clean = df.copy()

    # Drop duplicates
    df_clean = df_clean.drop_duplicates()

    # Simple imputation
    for col in df_clean.columns:
        if col == label_col:
            continue

        if df_clean[col].isnull().any():
            if df_clean[col].dtype in ['int64', 'float64', 'float32', 'int32']:
                df_clean[col].fillna(df_clean[col].median(), inplace=True)
            else:
                df_clean[col].fillna(df_clean[col].mode()[0], inplace=True)

    return df_clean


# Future: Manifest-based fixing (v0.2+)
# TODO: Implement for production scale (>10GB data)
"""
Example future implementation:

from heptaai.manifest import DataManifest

def generate_manifest(df: pd.DataFrame, issues: List[Issue]) -> DataManifest:
    '''
    Generate lightweight manifest without copying data.

    For production use with:
    - S3 data sources
    - Streaming data
    - Datasets > 10GB

    The manifest stores:
    - Row filters (which rows to include)
    - Sample weights (for class imbalance)
    - Feature transformations (imputation values)
    - No actual data copying
    '''
    manifest = DataManifest()

    # Build row mask (boolean array: True = keep row)
    row_mask = np.ones(len(df), dtype=bool)

    # Build sample weights (float array: weight per row)
    sample_weights = np.ones(len(df))

    # Build feature fixes (dict: feature -> transformation)
    feature_fixes = {}

    for issue in issues:
        if issue.type.value == "duplicates":
            # Mark duplicates for exclusion
            duplicate_mask = df.duplicated(keep='first')
            row_mask &= ~duplicate_mask

        elif issue.type.value == "missing_values":
            # Store imputation values (don't apply yet)
            feature = issue.feature
            if df[feature].dtype in ['int64', 'float64']:
                feature_fixes[feature] = {
                    "method": "median",
                    "value": df[feature].median()
                }

    manifest.row_mask = row_mask
    manifest.sample_weights = sample_weights
    manifest.feature_fixes = feature_fixes

    return manifest
"""
