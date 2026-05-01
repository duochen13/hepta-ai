"""
Train-test skew detector.

Identifies features where train and test distributions differ significantly,
which can cause model performance degradation in production.
"""

from typing import List, Optional
import numpy as np
from scipy.spatial.distance import jensenshannon

from .base import BaseDetector
from ..types import DatasetStatistics, Issue, IssueType, IssueSeverity
from ..config import DEFAULT_THRESHOLDS


class TrainTestSkewDetector(BaseDetector):
    """
    Detector for distribution shift between training and serving data.

    Train-test skew occurs when the distribution of features in production
    differs from training data. This causes:
    - Model performance degradation
    - Prediction bias
    - Poor generalization

    Uses Jensen-Shannon (JS) divergence to measure distribution differences:
    - For numeric features: Compare histograms (pre-computed during statistics)
    - For categorical features: Compare value count distributions

    Severity levels:
    - HIGH: JS divergence > 0.2 (default threshold)
    - MEDIUM: JS divergence > 0.1 (default threshold)

    Note:
        Requires both training and serving statistics. If serving_statistics
        is None, returns empty list (no skew can be detected).

    Example:
        >>> from heptaai.statistics import generate_statistics
        >>> train_stats = generate_statistics("train.csv")
        >>> test_stats = generate_statistics("test.csv")
        >>> detector = TrainTestSkewDetector()
        >>> issues = detector.detect(train_stats, serving_statistics=test_stats)
        >>> for issue in issues:
        ...     print(f"{issue.feature}: JS={issue.metric_value:.3f}")
        user_country: JS=0.156  # Distribution shifted in test set
    """

    @property
    def name(self) -> str:
        """Detector name."""
        return "Train-Test Skew"

    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect distribution skew between train and serving data.

        Args:
            statistics: Training dataset statistics
            serving_statistics: Serving/test dataset statistics (required!)

        Returns:
            List of issues for features with significant distribution shift.
            Empty list if serving_statistics is None.
        """
        # Cannot detect skew without serving data
        if serving_statistics is None:
            return []

        # Get thresholds from config or use defaults
        thresholds = self.config.get("thresholds") or DEFAULT_THRESHOLDS["train_test_skew"]
        high_threshold = thresholds["js_high"]
        medium_threshold = thresholds["js_medium"]

        issues = []

        # Check each feature present in both datasets
        for feat_name, train_feat in statistics.features.items():
            # Skip if feature not in serving data
            if feat_name not in serving_statistics.features:
                continue

            serving_feat = serving_statistics.features[feat_name]

            # Skip if types don't match (schema issue, not skew)
            if train_feat.type != serving_feat.type:
                continue

            # Compute JS divergence based on feature type
            if train_feat.type == "numeric":
                js_divergence = self._compute_numeric_js(train_feat, serving_feat)
            else:  # categorical
                js_divergence = self._compute_categorical_js(train_feat, serving_feat)

            # Skip if no divergence (identical distributions)
            if js_divergence is None or js_divergence == 0.0:
                continue

            # Determine severity
            if js_divergence > high_threshold:
                severity = IssueSeverity.HIGH
                threshold = high_threshold
            elif js_divergence > medium_threshold:
                severity = IssueSeverity.MEDIUM
                threshold = medium_threshold
            else:
                # Below both thresholds - not an issue
                continue

            # Create issue
            issues.append(
                Issue(
                    type=IssueType.TRAIN_TEST_SKEW,
                    severity=severity,
                    feature=feat_name,
                    metric_value=js_divergence,
                    threshold=threshold,
                    ne_direction="↑",  # Distribution shift increases prediction error
                    auc_direction="↓",  # Shift reduces model discriminative power
                    description=f"Distribution differs between train and test (JS divergence: {js_divergence:.3f})",
                    affected_samples=serving_statistics.n_rows,  # All serving samples affected
                )
            )

        return issues

    def _compute_numeric_js(self, train_feat, serving_feat) -> Optional[float]:
        """
        Compute skew metric for numeric features using statistical moments.

        Since pre-computed histograms use different bin edges for train and test,
        we cannot directly compare them. Instead, we use a normalized difference
        in statistical moments as a proxy for distribution shift.

        Args:
            train_feat: Training feature statistics
            serving_feat: Serving feature statistics

        Returns:
            Normalized difference metric (scaled to [0, 1] range like JS divergence)
            or None if statistics not available

        Note:
            v0.2 will improve this by storing raw data ranges and re-binning
            test data using training bin edges for proper JS divergence.
        """
        # Check if required statistics are available
        if train_feat.mean is None or serving_feat.mean is None:
            return None
        if train_feat.std is None or serving_feat.std is None:
            return None

        # Avoid division by zero
        if train_feat.std == 0:
            # If train std is 0, any difference in test mean is significant
            if serving_feat.mean != train_feat.mean:
                return 1.0  # Maximum skew
            return 0.0

        # Compute normalized mean difference (in units of train std)
        mean_diff = abs(serving_feat.mean - train_feat.mean) / train_feat.std

        # Compute std ratio difference
        std_ratio = abs(serving_feat.std / train_feat.std - 1.0) if train_feat.std > 0 else 0

        # Combine both metrics (weighted average)
        # Mean shift is more important than scale change
        skew_metric = 0.7 * min(mean_diff / 3.0, 1.0) + 0.3 * min(std_ratio, 1.0)

        # Scale to match JS divergence range (0-1, typically 0-0.5 for real data)
        return float(min(skew_metric, 1.0))

    def _compute_categorical_js(self, train_feat, serving_feat) -> Optional[float]:
        """
        Compute JS divergence for categorical features using value counts.

        Args:
            train_feat: Training feature statistics with histogram
            serving_feat: Serving feature statistics with histogram

        Returns:
            JS divergence or None if value counts not available
        """
        # Check if histograms (value counts) are available
        if train_feat.histogram is None or serving_feat.histogram is None:
            return None

        train_value_counts = train_feat.histogram.get("value_counts", {})
        serving_value_counts = serving_feat.histogram.get("value_counts", {})

        # Get all unique values across both datasets
        all_values = sorted(set(train_value_counts.keys()) | set(serving_value_counts.keys()))

        if len(all_values) == 0:
            return None

        # Build count arrays
        train_counts = np.array([train_value_counts.get(v, 0) for v in all_values], dtype=float)
        serving_counts = np.array([serving_value_counts.get(v, 0) for v in all_values], dtype=float)

        # Normalize to probability distributions
        train_dist = train_counts / (train_counts.sum() or 1)
        serving_dist = serving_counts / (serving_counts.sum() or 1)

        # Compute JS divergence
        js_distance = jensenshannon(train_dist, serving_dist)
        js_divergence = float(js_distance ** 2)

        return js_divergence
