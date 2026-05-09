"""
Cardinality detector.

Detects features with high cardinality (too many unique values).
High cardinality in categorical features often indicates:
- ID columns that should not be used as features
- Features that need encoding/grouping
- Data quality issues

Example: A "user_id" column with 10,000 unique values in 10,000 rows has 100% cardinality.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import config


class CardinalityDetector(BaseDetector):
    """
    Detector for features with high cardinality.

    High cardinality means a large proportion of values are unique,
    which can indicate ID-like features or categorical features that
    need special handling.

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> df = pd.DataFrame({"user_id": [f"user_{i}" for i in range(100)]})  # 100% unique
        >>> stats = generate_statistics(df)
        >>> detector = CardinalityDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues)
        1
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Cardinality"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect categorical features with high cardinality.

        Args:
            statistics: Dataset statistics
            serving_statistics: Unused (cardinality is single-dataset metric)

        Returns:
            List of issues for features with high cardinality
        """
        issues = []

        # Get thresholds from config
        thresholds = self.config.get("thresholds", {
            "high_cardinality": 0.9,  # >90% unique values in categorical features
        })

        for feat_name, feat_stats in statistics.features.items():
            # Only check categorical features
            if feat_stats.type != "categorical":
                continue

            # Skip features with all null values
            if feat_stats.completeness is None or feat_stats.completeness == 0.0:
                continue

            if feat_stats.distinct_count is None:
                continue

            # Calculate cardinality ratio (distinct values / total values)
            cardinality_ratio = feat_stats.distinct_count / feat_stats.count

            # High cardinality: >90% unique values
            if cardinality_ratio > thresholds["high_cardinality"]:
                issues.append(
                    Issue(
                        type=IssueType.HIGH_CARDINALITY,
                        severity=IssueSeverity.LOW,
                        feature=feat_name,
                        metric_value=cardinality_ratio,
                        threshold=thresholds["high_cardinality"],
                        ne_direction="↑",  # High cardinality increases noise
                        auc_direction="↓",  # Reduces discriminative power
                        description=f"{cardinality_ratio:.1%} of values are unique (potential ID column)",
                        affected_samples=feat_stats.distinct_count,
                    )
                )

        return issues
