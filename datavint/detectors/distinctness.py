"""
Distinctness detector.

Distinctness is the fraction of distinct values over the total number of values.
Distinct values occur at least once.

Example: [a, a, b] has 2 distinct values (a, b) out of 3 total values, so distinctness = 2/3.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import config


class DistinctnessDetector(BaseDetector):
    """
    Detector for features with unusual distinctness.

    Low distinctness (many repeated values) or high distinctness (many unique values)
    can indicate data quality issues.

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> df = pd.DataFrame({"col1": ["A"] * 99 + ["B"]})  # Low distinctness
        >>> stats = generate_statistics(df)
        >>> detector = DistinctnessDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues) > 0
        True
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Distinctness"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect features with unusually low distinctness.

        Args:
            statistics: Dataset statistics
            serving_statistics: Unused (distinctness is single-dataset metric)

        Returns:
            List of issues for features with low distinctness
        """
        issues = []

        # Get thresholds from config
        thresholds = self.config.get("thresholds", {
            "low": 0.1,  # <10% distinct values = potential data quality issue
        })

        for feat_name, feat_stats in statistics.features.items():
            # Skip features with all null values
            if feat_stats.completeness is None or feat_stats.completeness == 0.0:
                continue

            if feat_stats.distinctness is None:
                continue

            # Low distinctness: very few distinct values
            if feat_stats.distinctness < thresholds["low"]:
                issues.append(
                    Issue(
                        type=IssueType.HIGH_CARDINALITY,  # Reusing existing type
                        severity=IssueSeverity.LOW,
                        feature=feat_name,
                        metric_value=feat_stats.distinctness,
                        threshold=thresholds["low"],
                        ne_direction="↑",  # Low distinctness = less information
                        auc_direction="?",  # Context-dependent
                        description=f"Only {feat_stats.distinctness:.1%} of values are distinct ({feat_stats.distinct_count}/{feat_stats.count})",
                        affected_samples=feat_stats.count,
                    )
                )

        return issues
