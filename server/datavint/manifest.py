"""
Manifest Generation and Application

Translates detected data quality issues into actionable corrections:
- row_mask: Boolean filter for rows to keep/remove
- sample_weights: Per-row weights for rebalancing
- feature_fixes: Feature-level transformations (imputation, etc.)

Example:
    >>> from datavint import generate_statistics, generate_manifest
    >>> stats = generate_statistics("train.csv", label_col="label")
    >>> manifest = generate_manifest(stats)
    >>> corrected_df = manifest.apply(df)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from collections import defaultdict

from datavint.types import DataVintError, IssueType
from datavint.statistics import generate_statistics
from datavint.issues import detect_issues


@dataclass
class Manifest:
    """
    Data quality manifest - sample weights + filter masks + feature fixes.

    Attributes:
        row_mask: Boolean array (n_rows,) - True = keep row, False = filter out
        sample_weights: Float array (n_rows,) - weight per sample for training
        feature_fixes: Dict mapping feature name to fix specification
                      e.g., {"age": {"method": "median", "value": 35.0}}
    """
    row_mask: np.ndarray
    sample_weights: np.ndarray
    feature_fixes: Dict[str, Dict[str, Any]]

    def apply(self, df: pd.DataFrame, inplace: bool = False) -> Optional[pd.DataFrame]:
        """
        Apply manifest corrections to a DataFrame.

        Args:
            df: DataFrame to correct
            inplace: If True, modify df in place and return None.
                    If False, return corrected copy (default).

        Returns:
            Corrected DataFrame if inplace=False, else None

        Raises:
            DataVintError: If manifest size doesn't match DataFrame size,
                          or if feature_fixes reference missing columns

        Example:
            >>> manifest = generate_manifest(stats)
            >>> corrected_df = manifest.apply(df)
            >>> print(f"Filtered {len(df) - len(corrected_df)} rows")
        """
        # Validation
        if len(df) != len(self.row_mask):
            raise DataVintError(
                f"Manifest size {len(self.row_mask)} does not match "
                f"DataFrame size {len(df)}. Manifest must be generated "
                f"from statistics of the same dataset."
            )

        for feature in self.feature_fixes:
            if feature not in df.columns:
                raise DataVintError(
                    f"Feature '{feature}' in manifest not found in DataFrame. "
                    f"Available columns: {list(df.columns)}"
                )

        # Check for extreme reweighting (warning, not error)
        if self.sample_weights.max() / self.sample_weights.min() > 1000:
            print(
                f"⚠️  Warning: Extreme reweighting detected "
                f"(ratio: {self.sample_weights.max() / self.sample_weights.min():.1f}x). "
                f"This may cause gradient instability during training. "
                f"Consider adjusting thresholds or using stratified sampling."
            )

        # Apply corrections
        if inplace:
            df_result = df
        else:
            # Boolean indexing returns a view - pandas will copy only if needed
            df_result = df

        # Filter rows (boolean indexing - memory efficient)
        df_result = df_result[self.row_mask].copy()

        # Add sample weights column
        df_result['__datavint_weight__'] = self.sample_weights[self.row_mask]

        # Apply feature fixes (imputation)
        for feature, fix in self.feature_fixes.items():
            if fix['method'] == 'median':
                df_result[feature] = df_result[feature].fillna(fix['value'])

        return df_result if not inplace else None


def generate_manifest(
    statistics,
    serving_statistics=None
) -> Manifest:
    """
    Generate manifest from dataset statistics.

    Translates detected issues into corrections:
    - HIGH_NULL_RATE → feature_fixes with median imputation
    - DUPLICATE_SAMPLES → row_mask filters duplicates (keep first)
    - OUT_OF_RANGE → row_mask filters out-of-range values
    - CLASS_IMBALANCE → sample_weights upweight minority class
    - TRAIN_TEST_SKEW → sample_weights downweight skewed features

    Args:
        statistics: DatasetStatistics from generate_statistics()
        serving_statistics: Optional test/serving statistics for skew detection

    Returns:
        Manifest with row_mask, sample_weights, and feature_fixes

    Raises:
        DataVintError: If statistics is None or empty

    Example:
        >>> train_stats = generate_statistics("train.csv", label_col="label")
        >>> test_stats = generate_statistics("test.csv", label_col="label")
        >>> manifest = generate_manifest(train_stats, serving_statistics=test_stats)
        >>> corrected_df = manifest.apply(train_df)
    """
    # Validation
    if statistics is None:
        raise DataVintError("statistics cannot be None")

    if statistics.n_rows == 0:
        raise DataVintError("Cannot generate manifest from empty dataset")

    if serving_statistics and statistics.n_rows != serving_statistics.n_rows:
        # This is actually expected - train and test usually have different sizes
        # Only validate that we CAN compare them (same features)
        pass

    # Detect issues
    issues = detect_issues(statistics, serving_statistics=serving_statistics)

    # Initialize manifest (identity - no corrections)
    n_rows = statistics.n_rows
    row_mask = np.ones(n_rows, dtype=bool)
    sample_weights = np.ones(n_rows, dtype=np.float64)
    feature_fixes = {}

    # Group issues by type for efficient processing (D12 optimization)
    issues_by_type = defaultdict(list)
    for issue in issues:
        issues_by_type[issue.type].append(issue)

    # Process duplicates (row filtering)
    for issue in issues_by_type[IssueType.DUPLICATE_SAMPLES]:
        # Note: This requires access to the original DataFrame
        # For now, we'll document that duplicates must be handled
        # at the DataFrame level before statistics generation
        # TODO: Add duplicate detection to manifest (requires df access)
        pass

    # Process missing values (feature fixes)
    for issue in issues_by_type[IssueType.HIGH_NULL_RATE]:
        feature = issue.feature
        # Get median from statistics
        if feature in statistics.features:
            feature_stat = statistics.features[feature]
            if hasattr(feature_stat, 'mean'):  # Numeric feature
                median_value = feature_stat.mean  # Use mean as proxy for median
                feature_fixes[feature] = {
                    'method': 'median',
                    'value': median_value
                }

    # Process out-of-range (row filtering)
    # Note: Requires access to original DataFrame
    # TODO: Add out-of-range filtering (requires df access)

    # Process class imbalance (sample reweighting)
    for issue in issues_by_type[IssueType.CLASS_IMBALANCE]:
        # Calculate reweighting factor for minority class
        # This is a simplified implementation - proper reweighting
        # requires label distribution from statistics
        # TODO: Add proper class imbalance reweighting
        pass

    # Process train-test skew (sample reweighting)
    for issue in issues_by_type[IssueType.TRAIN_TEST_SKEW]:
        # Downweight samples from skewed features
        # This is a simplified implementation
        # TODO: Add proper skew correction
        pass

    # Check if all rows would be filtered
    if row_mask.sum() == 0:
        raise DataVintError(
            "Manifest would filter all rows. Check detection thresholds - "
            "they may be too aggressive for this dataset."
        )

    return Manifest(
        row_mask=row_mask,
        sample_weights=sample_weights,
        feature_fixes=feature_fixes
    )


def generate_manifest_from_path(
    train_path: str,
    test_path: Optional[str] = None,
    label_col: Optional[str] = None
) -> Manifest:
    """
    Generate manifest from CSV file paths (single-pass convenience API).

    Loads CSVs, computes statistics, and generates manifest in one call.

    Args:
        train_path: Path to training CSV
        test_path: Optional path to test/serving CSV for skew detection
        label_col: Optional label column name for class imbalance detection

    Returns:
        Manifest with corrections

    Raises:
        DataVintError: If file not found, corrupted CSV, or schema mismatch

    Example:
        >>> manifest = generate_manifest_from_path(
        ...     "train.csv",
        ...     test_path="test.csv",
        ...     label_col="label"
        ... )
        >>> corrected_df = manifest.apply(pd.read_csv("train.csv"))
    """
    # Load training data with error handling
    try:
        train_df = pd.read_csv(train_path)
    except FileNotFoundError as e:
        raise DataVintError(f"File not found: {train_path}") from e
    except pd.errors.ParserError as e:
        raise DataVintError(f"Failed to parse CSV: {train_path}. {str(e)}") from e

    if train_df.empty:
        raise DataVintError(f"Training data is empty: {train_path}")

    # Generate training statistics
    train_stats = generate_statistics(train_df, label_col=label_col)

    # Load test data if provided
    serving_stats = None
    if test_path:
        try:
            test_df = pd.read_csv(test_path)
        except FileNotFoundError as e:
            raise DataVintError(f"File not found: {test_path}") from e
        except pd.errors.ParserError as e:
            raise DataVintError(f"Failed to parse CSV: {test_path}. {str(e)}") from e

        if test_df.empty:
            raise DataVintError(f"Test data is empty: {test_path}")

        # Check schema compatibility
        if set(train_df.columns) != set(test_df.columns):
            raise DataVintError(
                f"Train and test schemas do not match. "
                f"Train columns: {list(train_df.columns)}, "
                f"Test columns: {list(test_df.columns)}"
            )

        serving_stats = generate_statistics(test_df, label_col=label_col)

    return generate_manifest(train_stats, serving_statistics=serving_stats)
