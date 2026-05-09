"""
Completeness detector.

Identifies features with low completeness (high null rates).
Completeness is the fraction of non-null values in a column.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import config


class CompletenessDetector(BaseDetector):
    """
    Detector for features with low completeness.

    Completeness = 1 - null_rate
    A low completeness value indicates many missing values.

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> df = pd.DataFrame({"col1": [1, None, None, 4, 5]})  # 60% complete
        >>> stats = generate_statistics(df)
        >>> detector = CompletenessDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues)
        1
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Completeness"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect features with low completeness.

        Args:
            statistics: Dataset statistics
            serving_statistics: Unused (completeness is single-dataset metric)

        Returns:
            List of issues for features with low completeness
        """
        issues = []

        # Get thresholds from config
        thresholds = self.config.get("thresholds", {
            "high": 0.5,    # <50% complete = HIGH severity
            "medium": 0.8,  # <80% complete = MEDIUM severity
        })

        for feat_name, feat_stats in statistics.features.items():
            if feat_stats.completeness is None:
                continue

            # High severity: <50% completeness
            if feat_stats.completeness < thresholds["high"]:
                issues.append(
                    Issue(
                        type=IssueType.LOW_COMPLETENESS,
                        severity=IssueSeverity.HIGH,
                        feature=feat_name,
                        metric_value=feat_stats.completeness,
                        threshold=thresholds["high"],
                        ne_direction="↑",  # Low completeness increases noise
                        auc_direction="↓",  # Reduces model performance
                        description=f"Only {feat_stats.completeness:.1%} of values are present ({feat_stats.null_rate:.1%} missing)",
                        affected_samples=feat_stats.null_count,
                    )
                )
            # Medium severity: <80% completeness
            elif feat_stats.completeness < thresholds["medium"]:
                issues.append(
                    Issue(
                        type=IssueType.LOW_COMPLETENESS,
                        severity=IssueSeverity.MEDIUM,
                        feature=feat_name,
                        metric_value=feat_stats.completeness,
                        threshold=thresholds["medium"],
                        ne_direction="↑",
                        auc_direction="↓",
                        description=f"Only {feat_stats.completeness:.1%} of values are present ({feat_stats.null_rate:.1%} missing)",
                        affected_samples=feat_stats.null_count,
                    )
                )

        return issues
