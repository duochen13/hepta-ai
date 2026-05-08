"""
Missing values detector.

Identifies features with high null rates that can degrade model performance.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import config


class MissingValuesDetector(BaseDetector):
    """
    Detector for features with excessive missing values.

    Missing values can cause:
    - Reduced effective training data
    - Biased models if missingness is non-random
    - Increased noise in predictions

    Severity levels:
    - HIGH: >50% null rate (default threshold)
    - MEDIUM: >20% null rate (default threshold)

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "user_age": [25, None, None, None, None],  # 80% null
        ...     "user_id": [1, 2, 3, 4, 5],  # 0% null
        ... })
        >>> stats = generate_statistics(df)
        >>> detector = MissingValuesDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues)
        1
        >>> issues[0].feature
        'user_age'
        >>> issues[0].severity
        <IssueSeverity.HIGH: 'high'>
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Missing Values"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect features with high null rates.

        Args:
            statistics: Dataset statistics
            serving_statistics: Unused (missing values is a single-dataset issue)

        Returns:
            List of issues for features exceeding null rate thresholds
        """
        # Get thresholds from global config
        high_threshold = config.null_rate_high
        medium_threshold = config.null_rate_medium

        issues = []

        for feat_name, feat_stats in statistics.features.items():
            null_rate = feat_stats.null_rate

            # Skip features with no missing values
            if null_rate == 0.0:
                continue

            # Determine severity using base class helper (D6 refactor)
            severity = self._classify_severity(null_rate, high_threshold, medium_threshold)

            # Skip if below both thresholds
            if severity == IssueSeverity.LOW:
                continue

            # Create issue
            issues.append(
                Issue(
                    type=IssueType.HIGH_NULL_RATE,
                    severity=severity,
                    feature=feat_name,
                    metric_value=null_rate,
                    threshold=high_threshold if severity == IssueSeverity.HIGH else medium_threshold,
                    ne_direction="↑",  # Missing values increase noise/error
                    auc_direction="↓",  # Missing values reduce discriminative power
                    description=f"{null_rate:.1%} of values are missing",
                    affected_samples=feat_stats.null_count,
                )
            )

        return issues
