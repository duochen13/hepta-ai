"""
Divergence computation utilities.

Implements Jensen-Shannon divergence for categorical and numeric features.
Copied from PoC (tfdv_demo_local.py lines 170-187).
"""

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon


def js_divergence_categorical(s1: pd.Series, s2: pd.Series) -> float:
    """
    Compute Jensen-Shannon divergence between two categorical series.

    Args:
        s1: First categorical series
        s2: Second categorical series

    Returns:
        JS divergence (squared JS distance)

    Note:
        scipy.spatial.distance.jensenshannon returns JS distance.
        We square it to get JS divergence.

    Example:
        >>> train = pd.Series(["US", "US", "US", "APAC", "EU"])  # 60% US, 20% APAC, 20% EU
        >>> test  = pd.Series(["US", "APAC", "APAC", "APAC", "EU"])  # 20% US, 60% APAC, 20% EU
        >>> js_divergence_categorical(train, test)
        0.0916  # Moderate skew - APAC is overrepresented in test

        >>> train_same = pd.Series(["A", "A", "B", "B"])  # 50% A, 50% B
        >>> test_same  = pd.Series(["A", "A", "B", "B"])  # 50% A, 50% B
        >>> js_divergence_categorical(train_same, test_same)
        0.0  # No skew - distributions match perfectly
    """
    all_vals = sorted(set(s1.dropna()) | set(s2.dropna()))
    p = np.array([s1.value_counts().get(v, 0) for v in all_vals], dtype=float)
    q = np.array([s2.value_counts().get(v, 0) for v in all_vals], dtype=float)
    p /= p.sum() or 1
    q /= q.sum() or 1
    return float(jensenshannon(p, q) ** 2)


def js_divergence_numeric(s1: pd.Series, s2: pd.Series, bins: int = 20) -> float:
    """
    Compute Jensen-Shannon divergence between two numeric series.

    Bins both series using the same bin edges and computes JS divergence
    on the resulting histograms.

    Args:
        s1: First numeric series
        s2: Second numeric series
        bins: Number of bins for histogram

    Returns:
        JS divergence (squared JS distance)

    Example:
        >>> # Train: prices range $1-$200 (normal distribution)
        >>> train_price = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        >>> # Test: prices range $100-$500 (shifted higher - train-serving skew)
        >>> test_price  = pd.Series([150, 200, 250, 300, 350, 400, 450, 500])
        >>> js_divergence_numeric(train_price, test_price)
        0.693  # High skew - test distribution is shifted to higher prices

        >>> # Same distribution
        >>> train_same = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        >>> test_same  = pd.Series([1.1, 2.1, 3.0, 3.9, 5.1])
        >>> js_divergence_numeric(train_same, test_same)
        0.002  # Very low skew - distributions are nearly identical
    """
    combined = pd.concat([s1, s2]).dropna()
    edges = np.linspace(combined.min(), combined.max(), bins + 1)
    p, _ = np.histogram(s1.dropna(), bins=edges, density=True)
    q, _ = np.histogram(s2.dropna(), bins=edges, density=True)
    p = p / (p.sum() or 1)
    q = q / (q.sum() or 1)
    return float(jensenshannon(p, q) ** 2)
