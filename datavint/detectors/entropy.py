"""
Entropy detector.

Entropy is a measure of information content in a feature.
- Low entropy indicates near-constant features (low information)
- High entropy (for categorical features) may indicate noise or randomness

Entropy is measured in nats (natural units of information).
"""

from typing import List, Optional
import math

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import config


class EntropyDetector(BaseDetector):
    """
    Detector for features with unusual entropy.

    Low Entropy:
        Features with very low entropy are near-constant and provide little information.
        Example: [a, a, a, a, b] has low entropy (mostly constant)

    High Entropy:
        For categorical features with many categories, very high entropy might indicate
        random/noisy data.
        Example: Uniform distribution across 100 categories has high entropy

    Example:
        >>> from datavint.statistics import generate_statistics
        >>> import pandas as pd
        >>> df = pd.DataFrame({"constant": ["A"] * 99 + ["B"]})  # Low entropy
        >>> stats = generate_statistics(df)
        >>> detector = EntropyDetector()
        >>> issues = detector.detect(stats)
        >>> len(issues)
        1
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Entropy"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect features with unusually low or high entropy.

        Args:
            statistics: Dataset statistics
            serving_statistics: Unused (entropy is single-dataset metric)

        Returns:
            List of issues for features with unusual entropy
        """
        issues = []

        # Get thresholds from config
        thresholds = self.config.get("thresholds", {
            "low_entropy": 0.1,     # <0.1 nats = near-constant
            "high_entropy_ratio": 0.95,  # >95% of max entropy for categorical
            "min_categories": 10,   # Minimum categories to check high entropy
        })

        for feat_name, feat_stats in statistics.features.items():
            # Skip features with all null values
            if feat_stats.completeness is None or feat_stats.completeness == 0.0:
                continue

            if feat_stats.entropy is None:
                continue

            # 1. Check for low entropy (near-constant features)
            if feat_stats.entropy < thresholds["low_entropy"]:
                issues.append(
                    Issue(
                        type=IssueType.LOW_ENTROPY,
                        severity=IssueSeverity.MEDIUM,
                        feature=feat_name,
                        metric_value=feat_stats.entropy,
                        threshold=thresholds["low_entropy"],
                        ne_direction="↓",  # Low entropy = low information
                        auc_direction="↓",  # Low discriminative power
                        description=f"Entropy: {feat_stats.entropy:.3f} (near-constant feature, low information)",
                        affected_samples=feat_stats.count,
                    )
                )

            # 2. Check for high entropy (potentially noisy/random features)
            # Only for categorical features with many categories
            if feat_stats.type == "categorical" and feat_stats.distinct_count:
                if feat_stats.distinct_count > thresholds["min_categories"]:
                    # Maximum entropy for k categories is log(k)
                    max_entropy = math.log(feat_stats.distinct_count)
                    entropy_ratio = feat_stats.entropy / max_entropy

                    if entropy_ratio > thresholds["high_entropy_ratio"]:
                        issues.append(
                            Issue(
                                type=IssueType.HIGH_ENTROPY,
                                severity=IssueSeverity.LOW,
                                feature=feat_name,
                                metric_value=feat_stats.entropy,
                                threshold=thresholds["high_entropy_ratio"] * max_entropy,
                                ne_direction="↑",  # High entropy = high noise
                                auc_direction="?",  # Depends on whether it's signal or noise
                                description=f"Entropy: {feat_stats.entropy:.3f} ({entropy_ratio:.1%} of max, potentially noisy)",
                                affected_samples=feat_stats.count,
                            )
                        )

        return issues
