"""
Issue detection and display orchestration.

Provides high-level API for running all detectors and displaying results.
"""

from typing import List, Optional

from .types import DatasetStatistics, Issue, DataVintError
from .detectors.missing_values import MissingValuesDetector
from .detectors.duplicates import DuplicatesDetector
from .detectors.schema import SchemaViolationDetector
from .detectors.range import NumericRangeDetector
from .detectors.skew import TrainTestSkewDetector
from .detectors.imbalance import ClassImbalanceDetector
from .detectors.completeness import CompletenessDetector
from .detectors.distinctness import DistinctnessDetector
from .detectors.uniqueness import UniquenessDetector
from .detectors.entropy import EntropyDetector
from .detectors.cardinality import CardinalityDetector


def detect_issues(
    statistics: DatasetStatistics,
    serving_statistics: Optional[DatasetStatistics] = None,
) -> List[Issue]:
    """
    Detect all data quality issues from statistics.

    Runs all 11 detectors in v0.1:
    1. MissingValuesDetector - Features with high null rates
    2. DuplicatesDetector - Exact duplicate rows
    3. SchemaViolationDetector - Type mismatches, unexpected categorical values
    4. NumericRangeDetector - Numeric values outside training min/max range
    5. TrainTestSkewDetector - Distribution shift between train and test
    6. ClassImbalanceDetector - Extreme class imbalance
    7. CompletenessDetector - Features with low completeness (high null rates)
    8. DistinctnessDetector - Features with low distinctness (few distinct values)
    9. UniquenessDetector - Features with low uniqueness (many duplicate values)
    10. EntropyDetector - Features with unusually low or high entropy
    11. CardinalityDetector - Categorical features with high cardinality (ID-like columns)

    Args:
        statistics: Training dataset statistics (required)
        serving_statistics: Serving/test dataset statistics (optional).
                          Required for schema and skew detection.

    Returns:
        List of all detected issues, sorted by severity (HIGH first)

    Raises:
        DataVintError: If statistics is None

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> from datavint.issues import detect_issues, display_issues
        >>>
        >>> train_stats = generate_statistics("train.csv", label_col="click")
        >>> test_stats = generate_statistics("test.csv", label_col="click")
        >>>
        >>> issues = detect_issues(train_stats, serving_statistics=test_stats)
        >>> print(f"Found {len(issues)} issue(s)")
        >>> display_issues(issues)
    """
    # Validation
    if statistics is None:
        raise DataVintError("statistics cannot be None")

    all_issues = []

    # Initialize all detectors
    detectors = [
        MissingValuesDetector(),
        DuplicatesDetector(),
        SchemaViolationDetector(),
        NumericRangeDetector(),
        TrainTestSkewDetector(),
        ClassImbalanceDetector(),
        CompletenessDetector(),
        DistinctnessDetector(),
        UniquenessDetector(),
        EntropyDetector(),
        CardinalityDetector(),
    ]

    # Run each detector
    for detector in detectors:
        issues = detector.detect(statistics, serving_statistics)
        all_issues.extend(issues)

    # Sort by severity (HIGH first) then by metric_value (highest first)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(
        key=lambda issue: (
            severity_order.get(issue.severity.value, 99),
            -issue.metric_value,  # Higher metric values first
        )
    )

    return all_issues


def display_issues(issues: List[Issue]) -> None:
    """
    Display issues in human-readable format.

    Prints a formatted table with:
    - Severity icons (🔴 HIGH, 🟡 MEDIUM)
    - Issue type and feature name
    - Description
    - ML impact directions (NE, AUC)

    Args:
        issues: List of issues to display

    Example output:
        ```
        3 issue(s) detected:

        🔴 [missing_values] user_age
           58.0% of values are missing
           Direction: NE↑ AUC↓  Severity: HIGH

        🟡 [train_test_skew] user_country
           Distribution differs between train and test (JS divergence: 0.156)
           Direction: NE↑ AUC↓  Severity: MEDIUM

        🔴 [class_imbalance] Dataset-level
           Positive class rate is 0.50% (target: ~10%)
           Direction: NE↑ AUC↓  Severity: HIGH
        ```
    """
    if len(issues) == 0:
        print("✅ No issues detected!")
        return

    print(f"\n{len(issues)} issue(s) detected:\n")

    for issue in issues:
        # Severity icon
        if issue.severity.value == "high":
            icon = "🔴"
        elif issue.severity.value == "medium":
            icon = "🟡"
        else:
            icon = "🔵"

        # Feature name or "Dataset-level"
        feature_str = issue.feature if issue.feature else "Dataset-level"

        # Print issue
        print(f"{icon} [{issue.type.value}] {feature_str}")
        print(f"   {issue.description}")

        # Direction and severity
        direction_str = f"NE{issue.ne_direction} AUC{issue.auc_direction}" if issue.ne_direction else "N/A"
        print(f"   Direction: {direction_str}  Severity: {issue.severity.value.upper()}")
        print()

    # Summary
    high_count = sum(1 for i in issues if i.severity.value == "high")
    medium_count = sum(1 for i in issues if i.severity.value == "medium")

    print("=" * 60)
    if high_count > 0:
        print(f"⚠ {high_count} HIGH severity issue(s) - address before training")
    if medium_count > 0:
        print(f"ℹ {medium_count} MEDIUM severity issue(s) - consider data cleaning")
    print("=" * 60)
