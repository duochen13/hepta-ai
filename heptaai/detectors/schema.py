"""
Schema violation detector.

Identifies unexpected values and out-of-range data that violate the schema
inferred from training data.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import DEFAULT_THRESHOLDS


class SchemaViolationDetector(BaseDetector):
    """
    Detector for schema violations between training and serving data.

    Schema violations occur when serving data contains:
    - Unexpected categorical values (new categories not in training)
    - Out-of-range numeric values (outside training min/max range)

    These violations indicate:
    - Data pipeline issues
    - Feature engineering bugs
    - Upstream data quality problems

    For categorical features:
    - Flags if new categories appear in serving data

    For numeric features:
    - Flags if serving min < training min or serving max > training max

    Severity:
    - HIGH: Always (schema violations are structural issues)

    Note:
        Requires both training and serving statistics. Returns empty list
        if serving_statistics is None.

    Example:
        >>> from heptaai.statistics import generate_statistics
        >>> import pandas as pd
        >>> train = pd.DataFrame({
        ...     "country": ["US", "UK", "CA"],
        ...     "age": [25, 30, 35],
        ... })
        >>> test = pd.DataFrame({
        ...     "country": ["US", "FR"],  # "FR" is new!
        ...     "age": [28, 150],  # 150 is way out of range
        ... })
        >>> train_stats = generate_statistics(train)
        >>> test_stats = generate_statistics(test)
        >>> detector = SchemaViolationDetector()
        >>> issues = detector.detect(train_stats, serving_statistics=test_stats)
        >>> len(issues)
        2  # country has new value, age is out of range
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Schema Violation"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect schema violations in serving data.

        Args:
            statistics: Training dataset statistics (defines expected schema)
            serving_statistics: Serving/test dataset statistics (required!)

        Returns:
            List of issues for features with schema violations.
            Empty list if serving_statistics is None.
        """
        # Cannot detect schema violations without serving data
        if serving_statistics is None:
            return []

        issues = []

        # Check each feature present in both datasets
        for feat_name, train_feat in statistics.features.items():
            # Skip if feature not in serving data (missing feature issue, not schema)
            if feat_name not in serving_statistics.features:
                continue

            serving_feat = serving_statistics.features[feat_name]

            # Skip if types don't match (handled separately)
            if train_feat.type != serving_feat.type:
                continue

            # Check schema based on feature type
            if train_feat.type == "categorical":
                issue = self._check_categorical_schema(feat_name, train_feat, serving_feat, serving_statistics)
            else:  # numeric
                issue = self._check_numeric_schema(feat_name, train_feat, serving_feat, serving_statistics)

            if issue:
                issues.append(issue)

        return issues

    def _check_categorical_schema(self, feat_name: str, train_feat, serving_feat, serving_statistics: DatasetStatistics) -> Optional[Issue]:
        """
        Check for unexpected categorical values.

        Args:
            feat_name: Feature name
            train_feat: Training feature statistics
            serving_feat: Serving feature statistics

        Returns:
            Issue if new categories found, None otherwise
        """
        # Get value counts from histograms
        if train_feat.histogram is None or serving_feat.histogram is None:
            return None

        train_values = set(train_feat.histogram.get("value_counts", {}).keys())
        serving_values = set(serving_feat.histogram.get("value_counts", {}).keys())

        # Find new values in serving data
        new_values = serving_values - train_values

        if len(new_values) == 0:
            return None

        # Create issue
        new_values_sample = sorted(list(new_values))[:5]  # Show up to 5 examples
        new_values_str = ", ".join(f"'{v}'" for v in new_values_sample)
        if len(new_values) > 5:
            new_values_str += f" (+{len(new_values) - 5} more)"

        return Issue(
            type=IssueType.SCHEMA_VIOLATION,
            severity=IssueSeverity.HIGH,
            feature=feat_name,
            metric_value=float(len(new_values)),
            threshold=0.0,  # Any new value is a violation
            ne_direction="↑",  # Unexpected values increase prediction error
            auc_direction="↓",  # Model not trained on these values
            description=f"{len(new_values)} unexpected value(s): {new_values_str}",
            affected_samples=serving_statistics.n_rows,  # Could affect any sample
        )

    def _check_numeric_schema(self, feat_name: str, train_feat, serving_feat, serving_statistics: DatasetStatistics) -> Optional[Issue]:
        """
        Check for out-of-range numeric values.

        Args:
            feat_name: Feature name
            train_feat: Training feature statistics
            serving_feat: Serving feature statistics

        Returns:
            Issue if values outside training range, None otherwise
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
            violations.append(f"min={serving_feat.min:.2f} < train_min={train_feat.min:.2f}")
        if above_range:
            violations.append(f"max={serving_feat.max:.2f} > train_max={train_feat.max:.2f}")

        violation_desc = ", ".join(violations)

        return Issue(
            type=IssueType.SCHEMA_VIOLATION,
            severity=IssueSeverity.HIGH,
            feature=feat_name,
            metric_value=float(below_range + above_range),  # 1 or 2 violations
            threshold=0.0,  # Any out-of-range value is a violation
            ne_direction="↑",  # Out-of-range values increase prediction error
            auc_direction="↓",  # Model extrapolating outside training range
            description=f"Values outside training range: {violation_desc}",
            affected_samples=serving_statistics.n_rows,  # Could affect any sample
        )
