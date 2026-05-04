"""
Validation module for measuring DataVint's impact on model performance.

⚠️ MVP LIMITATION: This module assumes datasets < 10GB that fit in memory.
   For production-scale data (>10GB), use manifest-based approach (v0.2+).

Components:
- data_fixer: Apply simple fixes based on detected issues
- model_trainer: Train and evaluate ML models
- metrics: Compute performance metrics (AUC, F1, NE, RMSE)

Typical workflow:
    1. Train baseline model on raw data → metrics_before
    2. Run DataVint detection → find issues
    3. Apply fixes → cleaned dataset
    4. Train on clean data → metrics_after
    5. Compare metrics → prove value
"""

from .data_fixer import fix_dataset, FixReport
from .model_trainer import train_and_evaluate
from .metrics import compute_metrics

__all__ = [
    "fix_dataset",
    "FixReport",
    "train_and_evaluate",
    "compute_metrics",
]
