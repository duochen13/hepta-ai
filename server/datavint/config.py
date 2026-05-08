"""
Global Configuration for DataVint Thresholds

All detection thresholds are configurable via the global `config` singleton.

Example:
    >>> import datavint as dv
    >>>
    >>> # Use defaults
    >>> issues = dv.detect_issues(stats)
    >>>
    >>> # Override thresholds (more lenient)
    >>> dv.config.null_rate_high = 0.10  # 10% instead of 5%
    >>> dv.config.skew_high = 0.15       # More tolerant of skew
    >>> issues = dv.detect_issues(stats)
"""

import logging
from dataclasses import dataclass

# Logging setup
logger = logging.getLogger("datavint")
logger.setLevel(logging.INFO)

# Add console handler if not already present
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(name)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class DataVintConfig:
    """
    Global configuration for DataVint detection thresholds.

    All thresholds use a two-level system:
    - *_high: Triggers HIGH severity (red flag, address before training)
    - *_medium: Triggers MEDIUM severity (yellow flag, consider cleaning)

    Attributes:
        null_rate_high: Missing value % threshold for HIGH severity (default: 5%)
        null_rate_medium: Missing value % threshold for MEDIUM severity (default: 2%)

        skew_high: JS divergence threshold for HIGH severity train-test skew (default: 0.1)
        skew_medium: JS divergence threshold for MEDIUM severity (default: 0.05)

        imbalance_high: Minority class % threshold for HIGH severity (default: 30%)
        imbalance_medium: Minority class % threshold for MEDIUM severity (default: 40%)

        range_tolerance: Tolerance for out-of-range detection as % of range (default: 0.01 = 1%)
    """

    # Missing values thresholds
    null_rate_high: float = 0.05      # 5% missing → HIGH
    null_rate_medium: float = 0.02    # 2% missing → MEDIUM

    # Train-test skew thresholds (Jensen-Shannon divergence)
    skew_high: float = 0.1            # JS divergence > 0.1 → HIGH
    skew_medium: float = 0.05         # JS divergence > 0.05 → MEDIUM

    # Class imbalance thresholds (minority class percentage)
    imbalance_high: float = 0.30      # Minority < 30% → HIGH
    imbalance_medium: float = 0.40    # Minority < 40% → MEDIUM

    # Out-of-range detection tolerance
    range_tolerance: float = 0.01     # 1% beyond training range → flag


# Global singleton instance
config = DataVintConfig()


# Legacy support for v0.1 code (deprecated)
DEFAULT_THRESHOLDS = {
    "missing_values": {
        "high": config.null_rate_high,
        "medium": config.null_rate_medium,
    },
    "class_imbalance": {
        "min_positive_rate": 0.01,
        "target_ratio": 0.1,
    },
    "train_test_skew": {
        "js_high": config.skew_high,
        "js_medium": config.skew_medium,
    },
    "duplicates": {
        "high": 0.05,
        "medium": 0.02,
    },
    "schema": {
        "null_tolerance": 0.05,
        "out_of_range_threshold": config.range_tolerance,
    },
}
