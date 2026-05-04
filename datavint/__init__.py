"""
DataVint: Data Quality Detection for ML

A lightweight SDK for detecting data quality issues in ML datasets.

Public API:
    - profile_dataset: Quick dataset overview before quality checks
    - compare_datasets: Compare train vs test datasets side-by-side
    - generate_statistics: Compute dataset statistics
    - detect_issues: Run all detectors on statistics
    - display_issues: Pretty-print detected issues
    - DatasetStatistics: Statistics dataclass
    - Issue: Issue dataclass
"""

from .profiling import profile_dataset, compare_datasets
from .statistics import generate_statistics
from .issues import detect_issues, display_issues
from .types import DatasetStatistics, Issue, IssueSeverity, IssueType

__version__ = "0.1.0"

__all__ = [
    "profile_dataset",
    "compare_datasets",
    "generate_statistics",
    "detect_issues",
    "display_issues",
    "DatasetStatistics",
    "Issue",
    "IssueSeverity",
    "IssueType",
]
