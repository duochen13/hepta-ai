"""
Base detector interface.

All detectors inherit from BaseDetector and implement the detect() method.
Detectors operate on DatasetStatistics, not raw DataFrames, for separation
of concerns and performance.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..types import DatasetStatistics, Issue


class BaseDetector(ABC):
    """
    Abstract base class for all data quality detectors.

    Detectors implement a single responsibility: given DatasetStatistics,
    identify specific types of data quality issues.

    Design principles:
    1. Operate on statistics, not raw data (separation of concerns)
    2. Return structured Issue objects with severity and metrics
    3. Support both single-dataset and train-test scenarios
    4. Configurable thresholds via config dict

    Example:
        >>> class MyDetector(BaseDetector):
        ...     @property
        ...     def name(self) -> str:
        ...         return "My Custom Detector"
        ...
        ...     def detect(self, statistics, serving_statistics=None):
        ...         issues = []
        ...         # Detection logic here
        ...         return issues
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize detector with optional configuration.

        Args:
            config: Optional configuration dict for thresholds and settings.
                   If None, uses defaults from datavint.config.

        Example:
            >>> detector = MissingValuesDetector(config={"high": 0.6, "medium": 0.3})
        """
        self.config = config or {}

    @abstractmethod
    def detect(
        self,
        statistics: DatasetStatistics,
        serving_statistics: Optional[DatasetStatistics] = None,
    ) -> List[Issue]:
        """
        Detect data quality issues from statistics.

        Args:
            statistics: Statistics from primary dataset (typically training data)
            serving_statistics: Optional statistics from serving/test data.
                              Used for train-test skew detection.

        Returns:
            List of detected issues. Empty list if no issues found.

        Raises:
            ValueError: If statistics are invalid or incompatible

        Example:
            >>> train_stats = generate_statistics("train.csv")
            >>> test_stats = generate_statistics("test.csv")
            >>> detector = TrainTestSkewDetector()
            >>> issues = detector.detect(train_stats, serving_statistics=test_stats)
            >>> len(issues)
            3  # Found 3 features with skew
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name of the detector.

        Returns:
            Detector name (e.g., "Missing Values", "Train-Test Skew")

        Example:
            >>> detector = MissingValuesDetector()
            >>> detector.name
            'Missing Values'
        """
        pass
