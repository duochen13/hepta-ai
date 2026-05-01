"""
Class imbalance detector.

Identifies extreme class imbalance in binary classification tasks that can
cause model bias toward the majority class.
"""

from typing import List, Optional

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import DEFAULT_THRESHOLDS


class ClassImbalanceDetector(BaseDetector):
    """
    Detector for extreme class imbalance in classification tasks.

    Class imbalance occurs when one class is significantly underrepresented.
    This causes:
    - Models biased toward majority class
    - Poor recall for minority class
    - Misleading accuracy metrics (high accuracy, low F1)

    For binary classification, checks if positive class rate is below threshold.

    Severity levels:
    - HIGH: Positive rate < 1% (default threshold)
    - Target ratio: 10% (informational, not a threshold)

    Note:
        Only detects imbalance if label_col was provided during statistics
        generation. Returns empty list if no label column.

    Example:
        >>> from heptaai.statistics import generate_statistics
        >>> import pandas as pd
        >>> # Highly imbalanced fraud detection dataset
        >>> df = pd.DataFrame({
        ...     "transaction_id": range(1000),
        ...     "amount": [100] * 1000,
        ...     "is_fraud": [1] * 5 + [0] * 995,  # Only 0.5% fraud
        ... })
        >>> stats = generate_statistics(df, label_col="is_fraud")
        >>> detector = ClassImbalanceDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues)
        1
        >>> issues[0].metric_value
        0.005  # 0.5% positive class
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Class Imbalance"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect extreme class imbalance in training data.

        Args:
            statistics: Dataset statistics with label_col and label_rate
            serving_statistics: Unused (imbalance is a training-only issue)

        Returns:
            List with single Issue if positive rate below threshold,
            empty list otherwise or if no label column.
        """
        # Cannot detect imbalance without label column
        if statistics.label_col is None or statistics.label_rate is None:
            return []

        # Get thresholds from config or use defaults
        thresholds = self.config.get("thresholds") or DEFAULT_THRESHOLDS["class_imbalance"]
        min_positive_rate = thresholds["min_positive_rate"]
        target_ratio = thresholds.get("target_ratio", 0.1)  # Optional

        positive_rate = statistics.label_rate

        # Check if below minimum threshold
        if positive_rate >= min_positive_rate:
            # Not imbalanced enough to be an issue
            return []

        # Determine severity (only HIGH for v0.1)
        severity = IssueSeverity.HIGH

        # Calculate how far from target ratio
        ratio_gap = target_ratio - positive_rate

        # Create dataset-level issue (feature=None, but mention label_col in description)
        issue = Issue(
            type=IssueType.CLASS_IMBALANCE,
            severity=severity,
            feature=None,  # Dataset-level issue
            metric_value=positive_rate,
            threshold=min_positive_rate,
            ne_direction="↑",  # Imbalance increases error on minority class
            auc_direction="↓",  # Low minority samples reduce discriminative power
            description=f"Positive class rate is {positive_rate:.2%} (target: ~{target_ratio:.0%})",
            affected_samples=int(statistics.n_rows * positive_rate),  # Number of positive samples
        )

        return [issue]
