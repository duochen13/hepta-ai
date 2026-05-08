"""
DataVint: Data Quality Detection & Optimization for ML

A lightweight SDK for detecting and fixing data quality issues in ML datasets.

Public API (v0.2):
    Detection:
    - profile_dataset: Quick dataset overview before quality checks
    - compare_datasets: Compare train vs test datasets side-by-side
    - generate_statistics: Compute dataset statistics
    - detect_issues: Run all detectors on statistics
    - display_issues: Pretty-print detected issues

    Optimization (NEW in v0.2):
    - generate_manifest: Generate data quality manifest from statistics
    - generate_manifest_from_path: Single-pass manifest generation from CSV
    - Manifest: Data quality manifest (row_mask, sample_weights, feature_fixes)

    Convenience API (for Code Playground):
    - load_demo_dataset: Load pre-configured demo datasets
    - profile: Simplified one-call profiling (stats + issues)

    Configuration:
    - config: Global configuration for detection thresholds

    Types:
    - DatasetStatistics: Statistics dataclass
    - Issue: Issue dataclass
    - DataVintError: Base exception for all DataVint errors
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Union

from .profiling import profile_dataset, compare_datasets
from .statistics import generate_statistics
from .issues import detect_issues, display_issues
from .manifest import Manifest, generate_manifest, generate_manifest_from_path
from .types import DatasetStatistics, Issue, IssueSeverity, IssueType, DataVintError
from .config import config

__version__ = "0.2.0"

# Demo datasets registry
DEMO_DATASETS = {
    'titanic': 'raw_data/titanic/titanic.csv'
}


def load_demo_dataset(name: str) -> pd.DataFrame:
    """
    Load a pre-configured demo dataset.

    Args:
        name: Name of the demo dataset ('titanic')

    Returns:
        pandas DataFrame with the loaded dataset

    Raises:
        ValueError: If dataset name is not recognized
        FileNotFoundError: If dataset file doesn't exist

    Example:
        >>> import datavint as vint
        >>> df = vint.load_demo_dataset('titanic')
        >>> print(df.shape)
        (891, 12)
    """
    if name not in DEMO_DATASETS:
        available = ', '.join(DEMO_DATASETS.keys())
        raise ValueError(f"Unknown dataset: '{name}'. Available: {available}")

    # Get absolute path relative to project root
    project_root = Path(__file__).parent.parent
    dataset_relative_path = DEMO_DATASETS[name]

    # Try multiple possible locations for datasets
    # 1. Standard location: project_root/raw_data/...
    dataset_path = project_root / dataset_relative_path

    # 2. Railway deployment: server/raw_data/... (when Railway root is /server)
    #    In Railway, cwd might be /app/server, so check ../server/raw_data
    if not dataset_path.exists():
        import os
        cwd = Path(os.getcwd())
        # If we're in /app/server, datasets are at /app/server/raw_data
        alt_path = cwd / dataset_relative_path
        if alt_path.exists():
            dataset_path = alt_path

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    return pd.read_csv(dataset_path)


def profile(df: pd.DataFrame, return_dict: bool = False) -> Union[Tuple[DatasetStatistics, List[Issue]], Dict]:
    """
    Simplified one-call profiling: generate statistics and detect issues.

    This is a convenience wrapper that combines generate_statistics() and detect_issues()
    into a single call for quick data quality checks.

    Args:
        df: Input DataFrame to profile
        return_dict: If True, return dict for JSON serialization (for API endpoints)

    Returns:
        If return_dict=False: Tuple of (statistics, issues)
        If return_dict=True: Dict with 'statistics' and 'issues' keys

    Example:
        >>> import datavint as vint
        >>> df = vint.load_demo_dataset('titanic')
        >>> stats, issues = vint.profile(df)
        >>> print(f"Found {len(issues)} data quality issues")
        Found 15 data quality issues
    """
    # Generate statistics
    stats = generate_statistics(df)

    # Detect issues
    issues = detect_issues(stats)

    if return_dict:
        return {
            'statistics': stats.to_dict(),
            'issues': [issue.to_dict() for issue in issues],
            'summary': {
                'num_rows': stats.n_rows,
                'num_columns': stats.n_cols,
                'num_issues': len(issues),
                'severity_counts': {
                    'high': sum(1 for i in issues if i.severity == IssueSeverity.HIGH),
                    'medium': sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM),
                    'low': sum(1 for i in issues if i.severity == IssueSeverity.LOW),
                }
            }
        }

    return stats, issues


__all__ = [
    # Detection (v0.1)
    "profile_dataset",
    "compare_datasets",
    "generate_statistics",
    "detect_issues",
    "display_issues",
    # Optimization (v0.2)
    "Manifest",
    "generate_manifest",
    "generate_manifest_from_path",
    # Convenience API (Code Playground)
    "load_demo_dataset",
    "profile",
    # Configuration
    "config",
    # Types
    "DatasetStatistics",
    "Issue",
    "IssueSeverity",
    "IssueType",
    "DataVintError",
]
