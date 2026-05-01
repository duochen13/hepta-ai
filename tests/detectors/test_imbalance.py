"""
Test suite for ClassImbalanceDetector.

Validates that:
1. Extreme imbalance (<1% positive) is flagged as HIGH severity
2. Moderate imbalance (1-10%) is not flagged in v0.1
3. Balanced datasets are not flagged
4. Returns empty list if no label_col provided
"""

import pytest
import pandas as pd

from heptaai.statistics import generate_statistics
from heptaai.detectors.imbalance import ClassImbalanceDetector
from heptaai.types import IssueSeverity, IssueType


class TestClassImbalanceDetector:
    """Test ClassImbalanceDetector behavior."""

    def test_no_label_col(self):
        """No issues when no label column provided."""
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"],
        })
        stats = generate_statistics(df)  # No label_col
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        assert len(issues) == 0, "Should return empty list without label_col"

    def test_balanced_dataset(self):
        """No issues when dataset is balanced (50-50)."""
        df = pd.DataFrame({
            "feature": range(100),
            "label": [0, 1] * 50,  # 50% positive
        })
        stats = generate_statistics(df, label_col="label")
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        assert len(issues) == 0, "Should not flag balanced dataset"

    def test_extreme_imbalance(self):
        """Extreme imbalance (<1%) should be flagged as HIGH."""
        df = pd.DataFrame({
            "feature": range(1000),
            "is_fraud": [1] * 5 + [0] * 995,  # 0.5% positive
        })
        stats = generate_statistics(df, label_col="is_fraud")
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1, "Should detect extreme imbalance"

        issue = issues[0]
        assert issue.type == IssueType.CLASS_IMBALANCE
        assert issue.severity == IssueSeverity.HIGH
        assert issue.feature is None  # Dataset-level issue
        assert issue.metric_value == 0.005  # 0.5% positive
        assert issue.threshold == 0.01  # Default threshold
        assert issue.ne_direction == "↑"
        assert issue.auc_direction == "↓"
        assert "0.50%" in issue.description  # Description shows rate
        assert issue.affected_samples == 5  # Number of positive samples

    def test_exactly_at_threshold(self):
        """Positive rate exactly at 1% should not be flagged."""
        df = pd.DataFrame({
            "feature": range(1000),
            "label": [1] * 10 + [0] * 990,  # Exactly 1.0%
        })
        stats = generate_statistics(df, label_col="label")
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        # 1% is NOT < 1%, so should not be flagged
        assert len(issues) == 0, "Should not flag exactly at threshold"

    def test_moderate_imbalance_not_flagged(self):
        """Moderate imbalance (1-10%) should not be flagged in v0.1."""
        df = pd.DataFrame({
            "feature": range(1000),
            "label": [1] * 50 + [0] * 950,  # 5% positive
        })
        stats = generate_statistics(df, label_col="label")
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        assert len(issues) == 0, "Should not flag moderate imbalance (5%) in v0.1"

    def test_very_small_positive_class(self):
        """Very small positive class (0.1%) should be HIGH severity."""
        df = pd.DataFrame({
            "feature": range(10000),
            "rare_event": [1] * 10 + [0] * 9990,  # 0.1% positive
        })
        stats = generate_statistics(df, label_col="rare_event")
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert issues[0].metric_value == 0.001  # 0.1%
        assert issues[0].severity == IssueSeverity.HIGH

    def test_custom_threshold(self):
        """Custom threshold should override default."""
        df = pd.DataFrame({
            "feature": range(1000),
            "label": [1] * 20 + [0] * 980,  # 2% positive
        })
        stats = generate_statistics(df, label_col="label")

        # Custom threshold: 5% minimum
        detector = ClassImbalanceDetector(
            config={"thresholds": {"min_positive_rate": 0.05}}
        )
        issues = detector.detect(stats)

        # 2% is < 5%, so should be flagged
        assert len(issues) == 1
        assert issues[0].threshold == 0.05

    def test_description_includes_target_ratio(self):
        """Description should mention target ratio."""
        df = pd.DataFrame({
            "feature": range(1000),
            "label": [1] * 5 + [0] * 995,  # 0.5%
        })
        stats = generate_statistics(df, label_col="label")
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert "target:" in issues[0].description.lower()
        assert "10%" in issues[0].description  # Default target is 10%

    def test_serving_statistics_ignored(self):
        """serving_statistics parameter should be ignored (training-only issue)."""
        df_train = pd.DataFrame({
            "feature": range(1000),
            "label": [1] * 5 + [0] * 995,  # 0.5% imbalance
        })
        df_test = pd.DataFrame({
            "feature": range(1000),
            "label": [1] * 500 + [0] * 500,  # 50% balanced
        })

        train_stats = generate_statistics(df_train, label_col="label")
        test_stats = generate_statistics(df_test, label_col="label")

        detector = ClassImbalanceDetector()

        # Should only check train_stats, not test_stats
        issues = detector.detect(train_stats, serving_statistics=test_stats)
        assert len(issues) == 1
        assert issues[0].metric_value == 0.005  # From train_stats

    def test_dataset_level_issue(self):
        """Imbalance issue should be dataset-level (feature=None)."""
        df = pd.DataFrame({
            "col1": range(1000),
            "col2": ["a"] * 1000,
            "label": [1] * 5 + [0] * 995,
        })
        stats = generate_statistics(df, label_col="label")
        detector = ClassImbalanceDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert issues[0].feature is None, "Imbalance should be dataset-level"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
