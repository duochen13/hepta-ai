"""
Configuration for DataVint SDK.

Contains default thresholds for issue detection and logging setup.
Users can override thresholds in v0.2+.
"""

import logging

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


# Default thresholds for v0.1 (hardcoded rules)
# Based on ML best practices and industry standards
DEFAULT_THRESHOLDS = {
    "missing_values": {
        "high": 0.5,   # >50% null → HIGH severity
        "medium": 0.2,  # >20% null → MEDIUM severity
    },
    "class_imbalance": {
        "min_positive_rate": 0.01,  # <1% positive → HIGH severity
        "target_ratio": 0.1,         # Target 10% positive rate
    },
    "train_test_skew": {
        "js_high": 0.2,    # JS divergence > 0.2 → HIGH severity
        "js_medium": 0.1,  # JS divergence > 0.1 → MEDIUM severity
    },
    "duplicates": {
        "high": 0.05,   # >5% duplicates → HIGH severity
        "medium": 0.02,  # >2% duplicates → MEDIUM severity
    },
    "schema": {
        "null_tolerance": 0.05,  # Allow 5% nulls before flagging schema violation
        "out_of_range_threshold": 0.01,  # >1% out-of-range values → flag
    },
}
