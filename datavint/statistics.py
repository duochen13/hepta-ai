"""
Statistics generation for datasets.

This module implements the generate_statistics() function, which computes
per-feature statistics and global dataset metrics.

Adaptive Histogram Binning:
- Histogram bin counts adapt to dataset size for optimal resolution vs memory
- Small datasets (< 1K rows): 10 bins (avoid over-binning sparse data)
- Medium datasets (1K - 100K rows): 20 bins (standard resolution)
- Large datasets (> 100K rows): Sturges' rule (log2(n) + 1), capped at 50 bins
- Rationale: Balances distribution fidelity with memory efficiency
"""

from typing import Union, Optional
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import entropy

from .types import DatasetStatistics, FeatureStats
from .config import logger


def _compute_adaptive_bins(n_rows: int) -> int:
    """
    Compute adaptive bin count based on dataset size.

    Strategy:
    - Small datasets (< 1000 rows): 10 bins (avoid over-binning sparse data)
    - Medium datasets (1000 - 100K rows): 20 bins (standard resolution)
    - Large datasets (> 100K rows): Sturges' rule, capped at 50 bins

    Sturges' rule: bins = ceil(log2(n) + 1)
    - Balances resolution with memory usage
    - 100K rows → 17 bins
    - 1M rows → 20 bins
    - 10M rows → 24 bins

    Args:
        n_rows: Number of rows in dataset

    Returns:
        Number of bins to use for histogram

    Example:
        >>> _compute_adaptive_bins(500)
        10
        >>> _compute_adaptive_bins(50000)
        20
        >>> _compute_adaptive_bins(1000000)
        20
    """
    if n_rows < 1000:
        return 10
    elif n_rows <= 100000:
        return 20
    else:
        # Sturges' rule: log2(n) + 1, capped at 50
        sturges_bins = int(np.log2(n_rows) + 1)
        return min(50, sturges_bins)


def generate_statistics(
    data: Union[str, Path, pd.DataFrame],
    label_col: Optional[str] = None,
) -> DatasetStatistics:
    """
    Generate statistics from dataset.

    Args:
        data: DataFrame or path to CSV file
        label_col: Target column name (None for unsupervised)

    Returns:
        DatasetStatistics dataclass with per-feature and global statistics

    Raises:
        FileNotFoundError: If path doesn't exist
        ValueError: If DataFrame has 0 rows
        KeyError: If label_col not in DataFrame columns

    Example:
        >>> import datavint as dv
        >>> stats = dv.generate_statistics("train.csv", label_col="click")
        >>> print(f"{stats.n_rows:,} rows, {stats.n_cols} columns")
        80,668 rows, 8 columns
    """
    # 1. Load data
    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        logger.info(f"Loading data from {path}")
        df = pd.read_csv(path)
    else:
        df = data.copy()

    # 2. Validation
    if len(df) == 0:
        raise ValueError("Cannot generate statistics from empty DataFrame")

    if label_col and label_col not in df.columns:
        raise KeyError(f"Label column '{label_col}' not found in DataFrame columns")

    logger.info(f"Computing statistics for {len(df):,} rows, {len(df.columns)} columns")

    # 3. Compute duplicate statistics (for DuplicatesDetector)
    duplicate_count = df.duplicated().sum()
    duplicate_rate = duplicate_count / len(df)

    # 4. Compute per-feature stats (with adaptive binning based on row count)
    features = {}
    n_rows = len(df)
    for col in df.columns:
        if col == label_col:
            continue  # Skip label column in feature stats

        features[col] = _compute_feature_stats(df, col, n_rows)

    # 5. Compute global label statistics (if label_col provided)
    label_rate = None
    label_entropy_val = None
    if label_col:
        label_series = df[label_col]
        # Compute label rate (mean for binary classification)
        label_rate = float(label_series.mean())
        # Compute label entropy
        label_entropy_val = _compute_entropy(label_series)

    logger.info(f"Generated statistics for {len(features)} features")

    return DatasetStatistics(
        n_rows=len(df),
        n_cols=len(df.columns),
        features=features,
        label_col=label_col,
        label_rate=label_rate,
        label_entropy=label_entropy_val,
        duplicate_count=int(duplicate_count),
        duplicate_rate=float(duplicate_rate),
    )


def _compute_feature_stats(df: pd.DataFrame, col: str, n_rows: int) -> FeatureStats:
    """
    Compute statistics for a single feature.

    Args:
        df: DataFrame
        col: Column name
        n_rows: Total number of rows in dataset (for adaptive binning)

    Returns:
        FeatureStats with computed statistics
    """
    s = df[col]

    # Basic stats
    count = len(s)
    null_count = int(s.isna().sum())
    null_rate = null_count / count

    # Type-specific stats
    if pd.api.types.is_numeric_dtype(s):
        # Numeric feature
        s_clean = s.dropna()
        if len(s_clean) > 0:
            # Store histogram for skew detection (adaptive bin count)
            bins = _compute_adaptive_bins(n_rows)
            hist_counts, hist_edges = np.histogram(s_clean, bins=bins)
            histogram = {
                "counts": hist_counts.tolist(),
                "edges": hist_edges.tolist(),
            }

            return FeatureStats(
                name=col,
                type="numeric",
                count=count,
                null_count=null_count,
                null_rate=null_rate,
                mean=float(s_clean.mean()),
                std=float(s_clean.std()),
                min=float(s_clean.min()),
                max=float(s_clean.max()),
                median=float(s_clean.median()),
                p25=float(s_clean.quantile(0.25)),
                p75=float(s_clean.quantile(0.75)),
                p99=float(s_clean.quantile(0.99)),
                histogram=histogram,
            )
        else:
            # All null
            logger.warning(f"Feature '{col}' has 100% null values")
            return FeatureStats(
                name=col,
                type="numeric",
                count=count,
                null_count=null_count,
                null_rate=null_rate,
            )
    else:
        # Categorical feature
        s_clean = s.dropna()
        top_vals = s_clean.value_counts(normalize=True).head(10).to_dict()

        # For skew detection, store value counts (histogram equivalent for categorical)
        value_counts = s_clean.value_counts().to_dict()
        histogram = {
            "type": "categorical",
            "value_counts": value_counts,
        }

        return FeatureStats(
            name=col,
            type="categorical",
            count=count,
            null_count=null_count,
            null_rate=null_rate,
            unique_count=int(s_clean.nunique()),
            top_values=top_vals,
            histogram=histogram,
        )


def _compute_entropy(series: pd.Series) -> float:
    """
    Compute Shannon entropy of a series.

    Args:
        series: Pandas series (typically label column)

    Returns:
        Shannon entropy value
    """
    value_counts = series.value_counts(normalize=True)
    return float(entropy(value_counts))
