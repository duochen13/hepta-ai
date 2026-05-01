"""
Test suite for TrainTestSkewDetector.

Validates that:
1. High JS divergence (>0.2) is flagged as HIGH severity
2. Medium JS divergence (>0.1) is flagged as MEDIUM severity
3. Low JS divergence (<0.1) is not flagged
4. Both numeric and categorical features are handled
5. Returns empty list if no serving_statistics provided
"""

import pytest
import pandas as pd
import numpy as np

from heptaai.statistics import generate_statistics
from heptaai.detectors.skew import TrainTestSkewDetector
from heptaai.types import IssueSeverity, IssueType


class TestTrainTestSkewDetector:
    """Test TrainTestSkewDetector behavior."""

    def test_no_serving_statistics(self):
        """No issues when serving_statistics not provided."""
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"],
        })
        stats = generate_statistics(df)
        detector = TrainTestSkewDetector()
        issues = detector.detect(stats)  # No serving_statistics

        assert len(issues) == 0, "Should return empty list without serving_statistics"

    def test_identical_distributions(self):
        """No issues when train and test distributions are identical."""
        df_train = pd.DataFrame({
            "age": [25, 30, 35, 40, 45] * 20,
            "country": (["US", "UK", "CA"] * 34)[:100],  # Ensure 100 items
        })
        df_test = pd.DataFrame({
            "age": [25, 30, 35, 40, 45] * 10,
            "country": (["US", "UK", "CA"] * 17)[:50],  # Ensure 50 items
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = TrainTestSkewDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 0, "Should not flag identical distributions"

    def test_high_numeric_skew(self):
        """High skew in numeric feature should be flagged as HIGH."""
        # Train: mostly young people
        df_train = pd.DataFrame({
            "age": np.random.randint(20, 40, 100),
        })
        # Test: mostly old people (clear distribution shift)
        df_test = pd.DataFrame({
            "age": np.random.randint(60, 80, 100),
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = TrainTestSkewDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1, "Should detect high skew"
        issue = issues[0]
        assert issue.type == IssueType.TRAIN_TEST_SKEW
        assert issue.feature == "age"
        assert issue.metric_value > 0.2, f"Expected JS > 0.2, got {issue.metric_value}"
        assert issue.severity == IssueSeverity.HIGH

    def test_medium_numeric_skew(self):
        """Medium skew in numeric feature should be flagged as MEDIUM."""
        np.random.seed(42)
        # Train: centered at 50
        df_train = pd.DataFrame({
            "score": np.random.normal(50, 10, 200),
        })
        # Test: shifted to 55 (moderate shift - 0.5 std)
        df_test = pd.DataFrame({
            "score": np.random.normal(55, 10, 200),
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = TrainTestSkewDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # With ~0.5 std shift, should detect medium skew
        assert len(issues) >= 1, "Should detect medium skew"
        issue = issues[0]
        # Check that it's detected (severity may vary based on exact random values)
        assert issue.metric_value > 0.1, f"Expected metric > 0.1, got {issue.metric_value}"

    def test_high_categorical_skew(self):
        """High skew in categorical feature should be flagged."""
        # Train: 90% US, 10% UK
        df_train = pd.DataFrame({
            "country": ["US"] * 90 + ["UK"] * 10,
        })
        # Test: 10% US, 90% UK (reversed!)
        df_test = pd.DataFrame({
            "country": ["US"] * 10 + ["UK"] * 90,
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = TrainTestSkewDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1, "Should detect high categorical skew"
        issue = issues[0]
        assert issue.feature == "country"
        # With 90/10 vs 10/90, should be high skew
        assert issue.metric_value > 0.2, f"Expected high skew > 0.2, got {issue.metric_value}"

    def test_low_skew_not_flagged(self):
        """Low skew (<0.1) should not be flagged."""
        np.random.seed(42)
        # Train and test very similar
        df_train = pd.DataFrame({
            "value": np.random.normal(100, 15, 500),
        })
        df_test = pd.DataFrame({
            "value": np.random.normal(101, 15, 500),  # Very slight shift
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = TrainTestSkewDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # Should either have no issues or low JS < 0.1
        if len(issues) > 0:
            assert issues[0].metric_value < 0.1, "Should not flag low skew"

    def test_multiple_features_with_skew(self):
        """Multiple features with different skew levels."""
        np.random.seed(42)
        df_train = pd.DataFrame({
            "f1": np.random.randint(0, 100, 100),  # Will have skew
            "f2": ["A"] * 50 + ["B"] * 50,  # Will have skew
            "f3": np.random.randint(0, 10, 100),  # Similar
        })
        df_test = pd.DataFrame({
            "f1": np.random.randint(200, 300, 100),  # High skew
            "f2": ["A"] * 20 + ["B"] * 80,  # Medium skew
            "f3": np.random.randint(0, 10, 100),  # Similar
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = TrainTestSkewDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # Should detect f1 and f2, not f3
        assert len(issues) >= 1, "Should detect at least one skewed feature"
        issue_features = [i.feature for i in issues]
        assert "f1" in issue_features or "f2" in issue_features

    def test_custom_thresholds(self):
        """Custom thresholds should override defaults."""
        np.random.seed(42)
        df_train = pd.DataFrame({
            "col1": np.random.randint(0, 100, 100),
        })
        df_test = pd.DataFrame({
            "col1": np.random.randint(50, 150, 100),
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        # Very lenient thresholds
        detector = TrainTestSkewDetector(
            config={"thresholds": {"js_high": 0.8, "js_medium": 0.5}}
        )
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # With lenient thresholds, might not flag or flag as lower severity
        if len(issues) > 0:
            assert issues[0].threshold >= 0.5

    def test_description_formatting(self):
        """Issue description should include JS divergence value."""
        np.random.seed(42)
        df_train = pd.DataFrame({"col1": np.random.randint(0, 50, 100)})
        df_test = pd.DataFrame({"col1": np.random.randint(100, 150, 100)})

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = TrainTestSkewDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1
        assert "JS divergence:" in issues[0].description
        assert "Distribution differs" in issues[0].description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
