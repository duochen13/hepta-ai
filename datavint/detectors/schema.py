"""
Schema violation detector.

Identifies schema inconsistencies between training and serving data:
- Type mismatches (feature changes from numeric to categorical or vice versa)
- Unexpected categorical values (new categories not in training)
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import DEFAULT_THRESHOLDS


class SchemaViolationDetector(BaseDetector):
    """
    Detector for schema violations between training and serving data.

    Schema violations occur when serving data has:
    - Type mismatches (feature changes type: numeric ↔ categorical)
    - Unexpected categorical values (new categories not in training)

    These violations indicate:
    - Data pipeline issues
    - Feature engineering bugs
    - Upstream data quality problems
    - Incorrect feature preprocessing

    Detection:
    - Type mismatch: Feature is numeric in train, categorical in test (or vice versa)
    - New categories: Categorical feature has values not seen in training

    Severity:
    - HIGH: Always (schema violations are structural issues)

    Note:
        Requires both training and serving statistics. Returns empty list
        if serving_statistics is None.

        For numeric range violations (values outside min/max), see NumericRangeDetector.

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> train = pd.DataFrame({
        ...     "country": ["US", "UK", "CA"],
        ...     "age": [25, 30, 35],
        ... })
        >>> test = pd.DataFrame({
        ...     "country": ["US", "FR"],  # "FR" is new!
        ...     "age": ["young", "old"],  # Type changed from numeric to categorical!
        ... })
        >>> train_stats = generate_statistics(train)
        >>> test_stats = generate_statistics(test)
        >>> detector = SchemaViolationDetector()
        >>> issues = detector.detect(train_stats, serving_statistics=test_stats)
        >>> len(issues)
        2  # country has new value, age has type mismatch
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

            # Check for type mismatch
            if train_feat.type != serving_feat.type:
                issue = self._check_type_mismatch(feat_name, train_feat, serving_feat, serving_statistics)
                if issue:
                    issues.append(issue)
                continue  # Skip further checks if types don't match

            # Check schema for categorical features only
            if train_feat.type == "categorical":
                issue = self._check_categorical_schema(feat_name, train_feat, serving_feat, serving_statistics)
                if issue:
                    issues.append(issue)

        return issues

    def _check_type_mismatch(
        self,
        feat_name: str,
        train_feat,
        serving_feat,
        serving_statistics: DatasetStatistics
    ) -> Optional[Issue]:
        """
        Check for type mismatch between train and serving.

        Args:
            feat_name: Feature name
            train_feat: Training feature statistics
            serving_feat: Serving feature statistics
            serving_statistics: Serving dataset statistics

        Returns:
            Issue if types don't match, None otherwise
        """
        return Issue(
            type=IssueType.SCHEMA_VIOLATION,
            severity=IssueSeverity.HIGH,
            feature=feat_name,
            metric_value=1.0,  # Binary: type mismatch occurred
            threshold=0.0,  # Any type mismatch is a violation
            ne_direction="↑",  # Type mismatch breaks model
            auc_direction="↓",  # Model cannot process wrong type
            description=f"Type changed from '{train_feat.type}' to '{serving_feat.type}'",
            affected_samples=serving_statistics.n_rows,  # All samples affected
        )

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

