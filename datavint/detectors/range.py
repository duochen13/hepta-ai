"""
Numeric range detector.

Identifies numeric features where serving data contains values outside the
range seen during training.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity


class NumericRangeDetector(BaseDetector):
    """
    Detector for numeric values outside training range.

    Out-of-range values occur when serving data contains:
    - Values below training minimum
    - Values above training maximum

    This indicates:
    - Data pipeline issues
    - Feature scaling problems
    - Model extrapolation (predictions outside training support)

    Severity:
    - HIGH: Always (model extrapolating outside training range)

    Note:
        Requires both training and serving statistics. Returns empty list
        if serving_statistics is None.

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> train = pd.DataFrame({"age": [20, 30, 40, 50, 60]})  # Range: 20-60
        >>> test = pd.DataFrame({"age": [25, 150]})  # 150 is way out of range!
        >>> train_stats = generate_statistics(train)
        >>> test_stats = generate_statistics(test)
        >>> detector = NumericRangeDetector()
        >>> issues = detector.detect(train_stats, serving_statistics=test_stats)
        >>> len(issues)
        1  # age has out-of-range value
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Numeric Range"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect numeric features with out-of-range values in serving data.

        Args:
            statistics: Training dataset statistics (defines expected ranges)
            serving_statistics: Serving/test dataset statistics (required!)

        Returns:
            List of issues for features with out-of-range values.
            Empty list if serving_statistics is None.
        """
        # Cannot detect range violations without serving data
        if serving_statistics is None:
            return []

        issues = []

        # Check each numeric feature present in both datasets
        for feat_name, train_feat in statistics.features.items():
            # Only check numeric features
            if train_feat.type != "numeric":
                continue

            # Skip if feature not in serving data
            if feat_name not in serving_statistics.features:
                continue

            serving_feat = serving_statistics.features[feat_name]

            # Skip if types don't match
            if serving_feat.type != "numeric":
                continue

            # Check if values are outside training range
            issue = self._check_numeric_range(feat_name, train_feat, serving_feat, serving_statistics)
            if issue:
                issues.append(issue)

        return issues

    def _check_numeric_range(
        self,
        feat_name: str,
        train_feat,
        serving_feat,
        serving_statistics: DatasetStatistics
    ) -> Optional[Issue]:
        """
        Check if serving values are outside training min/max range.

        Args:
            feat_name: Feature name
            train_feat: Training feature statistics
            serving_feat: Serving feature statistics
            serving_statistics: Serving dataset statistics

        Returns:
            Issue if values outside range, None otherwise
        """
        # Check if min/max are available
        if train_feat.min is None or train_feat.max is None:
            return None
        if serving_feat.min is None or serving_feat.max is None:
            return None

        # Check if serving data is outside training range
        below_range = serving_feat.min < train_feat.min
        above_range = serving_feat.max > train_feat.max

        if not below_range and not above_range:
            return None

        # Describe the violation
        violations = []
        if below_range:
            diff = train_feat.min - serving_feat.min
            pct = (diff / abs(train_feat.min)) * 100 if train_feat.min != 0 else float('inf')
            violations.append(f"min={serving_feat.min:.2f} < train_min={train_feat.min:.2f} ({diff:.2f} below, {pct:.0f}%)")
        if above_range:
            diff = serving_feat.max - train_feat.max
            pct = (diff / abs(train_feat.max)) * 100 if train_feat.max != 0 else float('inf')
            violations.append(f"max={serving_feat.max:.2f} > train_max={train_feat.max:.2f} ({diff:.2f} above, {pct:.0f}%)")

        violation_desc = " | ".join(violations)

        return Issue(
            type=IssueType.OUT_OF_RANGE,
            severity=IssueSeverity.HIGH,
            feature=feat_name,
            metric_value=float(below_range + above_range),  # 1 or 2 violations
            threshold=0.0,  # Any out-of-range value is a violation
            ne_direction="↑",  # Extrapolation increases prediction error
            auc_direction="↓",  # Model extrapolating outside training range
            description=f"Values outside training range: {violation_desc}",
            affected_samples=serving_statistics.n_rows,  # Could affect any sample
        )
