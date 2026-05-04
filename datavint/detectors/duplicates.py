"""
Duplicates detector.

Identifies datasets with excessive duplicate rows that can cause data leakage
and overfitting.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import DEFAULT_THRESHOLDS


class DuplicatesDetector(BaseDetector):
    """
    Detector for exact duplicate rows in dataset.

    Duplicate samples can cause:
    - Data leakage if same sample appears in train and test
    - Overfitting (model memorizes duplicates)
    - Inflated performance metrics
    - Biased class distributions

    Severity levels:
    - HIGH: >5% duplicate rate (default threshold)
    - MEDIUM: >2% duplicate rate (default threshold)

    Note:
        Duplicate detection is performed during generate_statistics() for
        performance. This detector only checks the pre-computed duplicate_rate.

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "user_id": [1, 2, 2, 3, 3, 3],  # 50% duplicates
        ...     "clicks": [5, 10, 10, 15, 15, 15],
        ... })
        >>> stats = generate_statistics(df)
        >>> stats.duplicate_count
        3
        >>> stats.duplicate_rate
        0.5
        >>> detector = DuplicatesDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues)
        1
        >>> issues[0].severity
        <IssueSeverity.HIGH: 'high'>
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Duplicate Samples"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect excessive duplicate rows.

        Args:
            statistics: Dataset statistics with pre-computed duplicate_count
            serving_statistics: Unused (duplicates is a single-dataset issue)

        Returns:
            List with single Issue if duplicate rate exceeds thresholds,
            empty list otherwise
        """
        # Get thresholds from config or use defaults
        thresholds = self.config.get("thresholds") or DEFAULT_THRESHOLDS["duplicates"]
        high_threshold = thresholds["high"]
        medium_threshold = thresholds["medium"]

        duplicate_rate = statistics.duplicate_rate

        # No duplicates - no issue
        if duplicate_rate == 0.0:
            return []

        # Determine severity
        if duplicate_rate > high_threshold:
            severity = IssueSeverity.HIGH
            threshold = high_threshold
        elif duplicate_rate > medium_threshold:
            severity = IssueSeverity.MEDIUM
            threshold = medium_threshold
        else:
            # Below both thresholds - not an issue
            return []

        # Create dataset-level issue (feature=None)
        issue = Issue(
            type=IssueType.DUPLICATE_SAMPLES,
            severity=severity,
            feature=None,  # Dataset-level issue
            metric_value=duplicate_rate,
            threshold=threshold,
            ne_direction="↑",  # Duplicates increase overfitting risk
            auc_direction="↑",  # Duplicates artificially inflate metrics
            description=f"{duplicate_rate:.1%} of rows are exact duplicates",
            affected_samples=statistics.duplicate_count,
        )

        return [issue]
