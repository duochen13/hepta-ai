"""
Performance metrics for model validation.

Computes standard ML metrics to measure impact of data quality fixes.
"""

from typing import Dict
import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
    mean_squared_error,
    log_loss,
)


def compute_normalized_entropy(y_true: np.ndarray, y_pred_proba: np.ndarray) -> float:
    """
    Compute Normalized Entropy (NE).

    NE measures label distribution uniformity when conditioned on predictions.
    Lower NE = less noise, better signal.

    Args:
        y_true: True labels (binary: 0 or 1)
        y_pred_proba: Predicted probabilities for positive class

    Returns:
        Normalized entropy [0, 1]
            0 = perfect prediction (no noise)
            1 = random prediction (maximum noise)

    Formula:
        NE = H(Y|X) / H(Y)
        where H(Y|X) is conditional entropy and H(Y) is label entropy
    """
    # Compute label entropy H(Y)
    pos_rate = np.mean(y_true)
    if pos_rate == 0 or pos_rate == 1:
        return 0.0  # No entropy if all labels are the same

    label_entropy = -pos_rate * np.log2(pos_rate) - (1 - pos_rate) * np.log2(1 - pos_rate)

    # Compute conditional entropy H(Y|X)
    # Approximate by binning predictions
    bins = np.linspace(0, 1, 11)  # 10 bins
    bin_indices = np.digitize(y_pred_proba, bins) - 1
    bin_indices = np.clip(bin_indices, 0, 9)

    conditional_entropy = 0.0
    for bin_idx in range(10):
        mask = bin_indices == bin_idx
        if not mask.any():
            continue

        bin_size = mask.sum()
        bin_prob = bin_size / len(y_true)
        bin_labels = y_true[mask]

        # Entropy within this bin
        bin_pos_rate = np.mean(bin_labels)
        if bin_pos_rate > 0 and bin_pos_rate < 1:
            bin_entropy = -bin_pos_rate * np.log2(bin_pos_rate) - (1 - bin_pos_rate) * np.log2(1 - bin_pos_rate)
        else:
            bin_entropy = 0.0

        conditional_entropy += bin_prob * bin_entropy

    # Normalize by label entropy
    normalized_entropy = conditional_entropy / label_entropy if label_entropy > 0 else 0.0

    return normalized_entropy


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: np.ndarray,
    metric_names: list = None,
) -> Dict[str, float]:
    """
    Compute comprehensive performance metrics.

    Args:
        y_true: True labels (binary: 0 or 1)
        y_pred: Predicted labels (binary: 0 or 1)
        y_pred_proba: Predicted probabilities for positive class
        metric_names: List of metrics to compute. If None, compute all.
                     Options: ["auc", "f1", "precision", "recall", "rmse", "ne", "log_loss"]

    Returns:
        Dictionary of metric name -> value

    Example:
        >>> metrics = compute_metrics(y_true, y_pred, y_pred_proba)
        >>> print(f"AUC: {metrics['auc']:.3f}")
        >>> print(f"F1: {metrics['f1']:.3f}")
        >>> print(f"NE: {metrics['ne']:.3f}")
    """
    if metric_names is None:
        metric_names = ["auc", "f1", "precision", "recall", "rmse", "ne", "log_loss"]

    metrics = {}

    # AUC (primary metric)
    if "auc" in metric_names:
        try:
            metrics["auc"] = roc_auc_score(y_true, y_pred_proba)
        except ValueError:
            # Fails if only one class in y_true
            metrics["auc"] = 0.0

    # F1 Score
    if "f1" in metric_names:
        metrics["f1"] = f1_score(y_true, y_pred, zero_division=0.0)

    # Precision
    if "precision" in metric_names:
        metrics["precision"] = precision_score(y_true, y_pred, zero_division=0.0)

    # Recall
    if "recall" in metric_names:
        metrics["recall"] = recall_score(y_true, y_pred, zero_division=0.0)

    # RMSE (for probability calibration)
    if "rmse" in metric_names:
        metrics["rmse"] = np.sqrt(mean_squared_error(y_true, y_pred_proba))

    # Normalized Entropy (DataVint's focus metric)
    if "ne" in metric_names:
        metrics["ne"] = compute_normalized_entropy(y_true, y_pred_proba)

    # Log Loss (calibration metric)
    if "log_loss" in metric_names:
        try:
            # Clip to avoid log(0)
            y_pred_proba_clipped = np.clip(y_pred_proba, 1e-15, 1 - 1e-15)
            metrics["log_loss"] = log_loss(y_true, y_pred_proba_clipped)
        except ValueError:
            metrics["log_loss"] = np.inf

    return metrics


def compare_metrics(
    metrics_before: Dict[str, float],
    metrics_after: Dict[str, float],
) -> str:
    """
    Generate human-readable comparison of metrics.

    Args:
        metrics_before: Metrics before data quality fixes
        metrics_after: Metrics after data quality fixes

    Returns:
        Formatted comparison string

    Example:
        >>> print(compare_metrics(baseline, improved))
        Metrics Before → After:
          AUC   : 0.762 → 0.824 (↑+8.1%)
          F1    : 0.145 → 0.287 (↑+97.9%)
          NE    : 0.523 → 0.412 (↓-21.2%)
    """
    lines = []
    lines.append("Metrics Before → After:")

    for metric in metrics_before.keys():
        before = metrics_before[metric]
        after = metrics_after[metric]
        delta = after - before
        pct = (delta / before) * 100 if before != 0 else 0

        # For NE and RMSE, lower is better
        if metric in ["ne", "rmse", "log_loss"]:
            arrow = "↓" if delta < 0 else "↑"
            improvement = "✅" if delta < 0 else "⚠️"
        else:
            arrow = "↑" if delta > 0 else "↓"
            improvement = "✅" if delta > 0 else "⚠️"

        lines.append(
            f"  {metric.upper():10s}: {before:.3f} → {after:.3f} "
            f"({arrow}{pct:+.1f}%) {improvement}"
        )

    return "\n".join(lines)
