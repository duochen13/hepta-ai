"""
Core data structures for DataVint SDK.

This module defines the dataclasses used throughout the SDK:
- FeatureStats: Statistics for a single feature
- DatasetStatistics: Statistics for an entire dataset
- Issue: Detected data quality issue
- IssueSeverity: Severity level enum
- IssueType: Issue type enum
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class IssueSeverity(Enum):
    """Severity level for detected issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueType(Enum):
    """Types of data quality issues detected in v0.1."""
    HIGH_NULL_RATE = "missing_values"
    DUPLICATE_SAMPLES = "duplicates"
    SCHEMA_VIOLATION = "schema_violation"  # Unexpected categories, type mismatches
    OUT_OF_RANGE = "out_of_range"  # Numeric values outside training min/max
    TRAIN_TEST_SKEW = "train_test_skew"
    CLASS_IMBALANCE = "class_imbalance"


@dataclass
class FeatureStats:
    """Statistics for a single feature.

    Attributes:
        name: Feature name
        type: Feature type ("numeric" or "categorical")
        count: Total number of values
        null_count: Number of null/missing values
        null_rate: Fraction of null values (0.0 to 1.0)

        # Numeric-specific fields
        mean: Mean value (numeric only)
        std: Standard deviation (numeric only)
        min: Minimum value (numeric only)
        max: Maximum value (numeric only)
        median: Median value (numeric only)
        p25: 25th percentile (numeric only)
        p75: 75th percentile (numeric only)
        p99: 99th percentile (numeric only)

        # Categorical-specific fields
        unique_count: Number of unique values (categorical only)
        top_values: Top value frequencies as {value: frequency} (categorical only)

        # For skew detection (stored during statistics generation)
        histogram: Histogram data for JS divergence computation
    """
    name: str
    type: str  # "numeric" or "categorical"
    count: int
    null_count: int
    null_rate: float

    # Numeric-specific
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None
    p25: Optional[float] = None
    p75: Optional[float] = None
    p99: Optional[float] = None

    # Categorical-specific
    unique_count: Optional[int] = None
    top_values: Optional[Dict[str, float]] = None  # value -> frequency

    # For skew detection - store histogram bins and counts
    histogram: Optional[Dict[str, Any]] = None


@dataclass
class DatasetStatistics:
    """Statistics for an entire dataset.

    Attributes:
        n_rows: Number of rows
        n_cols: Number of columns
        features: Per-feature statistics (feature_name -> FeatureStats)
        label_col: Name of label column (None for unsupervised)
        label_rate: Positive rate if binary classification
        label_entropy: Global label entropy
        duplicate_count: Number of exact duplicate rows
        duplicate_rate: Fraction of duplicate rows
    """
    n_rows: int
    n_cols: int
    features: Dict[str, FeatureStats]
    label_col: Optional[str] = None
    label_rate: Optional[float] = None  # positive rate if binary
    label_entropy: Optional[float] = None  # global label entropy

    # For duplicate detection - computed during statistics generation
    duplicate_count: int = 0
    duplicate_rate: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "features": {
                name: {
                    "name": stats.name,
                    "type": stats.type,
                    "count": stats.count,
                    "null_count": stats.null_count,
                    "null_rate": stats.null_rate,
                    "mean": stats.mean,
                    "std": stats.std,
                    "min": stats.min,
                    "max": stats.max,
                    "median": stats.median,
                    "p25": stats.p25,
                    "p75": stats.p75,
                    "p99": stats.p99,
                    "unique_count": stats.unique_count,
                    "top_values": stats.top_values,
                }
                for name, stats in self.features.items()
            },
            "label_col": self.label_col,
            "label_rate": self.label_rate,
            "label_entropy": self.label_entropy,
            "duplicate_count": self.duplicate_count,
            "duplicate_rate": self.duplicate_rate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DatasetStatistics':
        """Deserialize from dict."""
        features = {}
        for name, stats_dict in data["features"].items():
            features[name] = FeatureStats(**stats_dict)

        return cls(
            n_rows=data["n_rows"],
            n_cols=data["n_cols"],
            features=features,
            label_col=data.get("label_col"),
            label_rate=data.get("label_rate"),
            label_entropy=data.get("label_entropy"),
            duplicate_count=data.get("duplicate_count", 0),
            duplicate_rate=data.get("duplicate_rate", 0.0),
        )


@dataclass
class Issue:
    """Represents a detected data quality issue.

    Attributes:
        type: Type of issue (from IssueType enum)
        severity: Severity level (HIGH/MEDIUM/LOW)
        feature: Feature name (None for dataset-level issues)
        metric_value: Measured value (e.g., null_rate=0.58, js_divergence=0.31)
        threshold: Threshold used for detection
        ne_direction: Directional impact on Normalized Entropy ("↑", "↓", or None)
        auc_direction: Directional impact on AUC ("↑", "↓", or None)
        description: Human-readable description
        affected_samples: Number of rows affected
    """
    type: IssueType
    severity: IssueSeverity
    feature: Optional[str] = None  # None for dataset-level issues

    # Metrics
    metric_value: float = 0.0  # e.g., null_rate=0.58, js_divergence=0.31
    threshold: float = 0.0  # threshold used for detection

    # Directional impact estimates (not quantitative)
    ne_direction: Optional[str] = None  # "↓", "↑", or None
    auc_direction: Optional[str] = None  # "↓", "↑", or None

    # Human-readable description
    description: str = ""

    # Supporting evidence
    affected_samples: int = 0  # number of rows affected

    def __str__(self) -> str:
        """Format for display_issues()."""
        severity_icon = {
            IssueSeverity.HIGH: "🔴",
            IssueSeverity.MEDIUM: "🟡",
            IssueSeverity.LOW: "⚪",
        }[self.severity]

        feature_str = self.feature if self.feature else "–"

        # Direction string
        directions = []
        if self.ne_direction:
            directions.append(f"NE{self.ne_direction}")
        if self.auc_direction:
            directions.append(f"AUC{self.auc_direction}")
        direction_str = " ".join(directions) if directions else "–"

        return (
            f"{severity_icon} [{self.type.value}] {feature_str}\n"
            f"   {self.description}\n"
            f"   Direction: {direction_str}  Severity: {self.severity.value.upper()}"
        )
