"""
Uniqueness detector.

Uniqueness is the fraction of unique values over the total number of values.
Unique values occur exactly once.

Example: [a, a, b] has 1 unique value (b) out of 3 total values, so uniqueness = 1/3.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import config


class UniquenessDetector(BaseDetector):
    """
    Detector for features with low uniqueness.

    Low uniqueness means most values appear multiple times,
    which could indicate excessive duplication or data quality issues.

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> df = pd.DataFrame({"col1": [1, 2, 3, 4, 5] + [10] * 95})  # 5% unique
        >>> stats = generate_statistics(df)
        >>> detector = UniquenessDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues)
        1
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Uniqueness"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect features with low uniqueness.

        Args:
            statistics: Dataset statistics
            serving_statistics: Unused (uniqueness is single-dataset metric)

        Returns:
            List of issues for features with low uniqueness
        """
        issues = []

        # Get thresholds from config
        thresholds = self.config.get("thresholds", {
            "low": 0.1,  # <10% unique values = many duplicates
        })

        for feat_name, feat_stats in statistics.features.items():
            # Skip features with all null values
            if feat_stats.completeness is None or feat_stats.completeness == 0.0:
                continue

            if feat_stats.uniqueness is None:
                continue

            # Low uniqueness: <10% unique values
            if feat_stats.uniqueness < thresholds["low"]:
                issues.append(
                    Issue(
                        type=IssueType.LOW_UNIQUENESS,
                        severity=IssueSeverity.LOW,
                        feature=feat_name,
                        metric_value=feat_stats.uniqueness,
                        threshold=thresholds["low"],
                        ne_direction="↑",  # Low uniqueness = less information per sample
                        auc_direction="?",  # Context-dependent
                        description=f"Only {feat_stats.uniqueness:.1%} of values are unique (many duplicates)",
                        affected_samples=feat_stats.count,
                    )
                )

        return issues
