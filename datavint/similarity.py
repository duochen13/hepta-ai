"""
Experiment Similarity Module

Computes similarity between experiments for near-duplicate detection.

Week 3-4 implementation:
- Feature extraction from datasets (columns, types, statistics)
- Cosine similarity between feature vectors
- Configurable similarity threshold (default: 0.95 = 95%)
"""

import json
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine


def extract_features(df: pd.DataFrame) -> Dict:
    """
    Extract features from a DataFrame for similarity comparison.

    Features extracted:
    - Column names (sorted)
    - Column types
    - Row count
    - Column count
    - Basic statistics (mean, std, min, max) for numeric columns
    - Cardinality for categorical columns

    Args:
        df: DataFrame to extract features from

    Returns:
        Dictionary of features
    """
    features = {
        'columns': sorted(df.columns.tolist()),
        'column_count': len(df.columns),
        'row_count': len(df),
        'dtypes': {},
        'numeric_stats': {},
        'categorical_cardinality': {}
    }

    # Extract column types
    for col in df.columns:
        dtype = str(df[col].dtype)
        features['dtypes'][col] = dtype

    # Extract numeric statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in df.columns:
            try:
                features['numeric_stats'][col] = {
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max())
                }
            except Exception:
                # Skip columns that can't be computed
                pass

    # Extract categorical cardinality
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        if col in df.columns:
            features['categorical_cardinality'][col] = int(df[col].nunique())

    return features


def features_to_vector(features: Dict) -> np.ndarray:
    """
    Convert feature dictionary to fixed-length vector for cosine similarity.

    Strategy:
    - Normalize all values to [0, 1] range
    - Create fixed-length vector from features
    - Use column name hashing for position-independent comparison

    Args:
        features: Feature dictionary from extract_features()

    Returns:
        NumPy array representing the feature vector
    """
    vector_parts = []

    # 1. Row count (log-normalized)
    row_count = features['row_count']
    if row_count > 0:
        row_count_norm = np.log10(row_count + 1) / 10.0  # Normalize to ~[0, 1]
    else:
        row_count_norm = 0
    vector_parts.append(row_count_norm)

    # 2. Column count (normalized)
    col_count = features['column_count']
    col_count_norm = min(col_count / 100.0, 1.0)  # Cap at 100 columns
    vector_parts.append(col_count_norm)

    # 3. Column names (sorted hash sum)
    # Use sum of hash values (modulo) for position-independent comparison
    column_hash_sum = sum(hash(col) % 10000 for col in features['columns']) / 100000.0
    vector_parts.append(column_hash_sum)

    # 4. Numeric statistics (aggregated)
    if features['numeric_stats']:
        means = [stats['mean'] for stats in features['numeric_stats'].values()]
        stds = [stats['std'] for stats in features['numeric_stats'].values()]

        # Normalize to avoid extreme values
        mean_avg = np.mean(means) if means else 0
        std_avg = np.mean(stds) if stds else 0

        # Clip to reasonable range
        mean_avg_norm = np.clip(mean_avg / 1000.0, -1, 1)
        std_avg_norm = np.clip(std_avg / 1000.0, 0, 1)

        vector_parts.extend([mean_avg_norm, std_avg_norm])
    else:
        vector_parts.extend([0, 0])

    # 5. Categorical cardinality (aggregated)
    if features['categorical_cardinality']:
        cardinalities = list(features['categorical_cardinality'].values())
        cardinality_avg = np.mean(cardinalities) if cardinalities else 0
        cardinality_avg_norm = min(np.log10(cardinality_avg + 1) / 5.0, 1.0)
        vector_parts.append(cardinality_avg_norm)
    else:
        vector_parts.append(0)

    # 6. Data type distribution
    if features['dtypes']:
        # Count types
        type_counts = {}
        for dtype in features['dtypes'].values():
            type_counts[dtype] = type_counts.get(dtype, 0) + 1

        # Normalize by total columns
        total_cols = len(features['dtypes'])
        numeric_ratio = sum(1 for dt in features['dtypes'].values()
                           if 'int' in dt or 'float' in dt) / total_cols
        object_ratio = sum(1 for dt in features['dtypes'].values()
                          if 'object' in dt or 'category' in dt) / total_cols

        vector_parts.extend([numeric_ratio, object_ratio])
    else:
        vector_parts.extend([0, 0])

    return np.array(vector_parts)


def compute_similarity(features1: Dict, features2: Dict) -> float:
    """
    Compute similarity between two experiments using cosine similarity.

    Args:
        features1: Features from first experiment
        features2: Features from second experiment

    Returns:
        Similarity score [0, 1] where 1 = identical, 0 = completely different
    """
    # Convert features to vectors
    vec1 = features_to_vector(features1)
    vec2 = features_to_vector(features2)

    # Compute cosine similarity
    # scipy.spatial.distance.cosine returns distance (1 - similarity)
    # So we convert: similarity = 1 - distance
    try:
        distance = cosine(vec1, vec2)
        similarity = 1 - distance
        return max(0, min(1, similarity))  # Clamp to [0, 1]
    except Exception:
        # If vectors are zero or invalid, return 0 similarity
        return 0.0


def find_similar_experiments(
    target_features: Dict,
    candidate_features_list: List[Tuple[int, Dict]],
    threshold: float = 0.95
) -> List[Tuple[int, float]]:
    """
    Find experiments similar to target above threshold.

    Args:
        target_features: Features of the experiment to compare against
        candidate_features_list: List of (experiment_id, features) tuples
        threshold: Minimum similarity score [0, 1] to be considered similar

    Returns:
        List of (experiment_id, similarity_score) tuples, sorted by similarity (descending)
    """
    similar = []

    for exp_id, candidate_features in candidate_features_list:
        similarity = compute_similarity(target_features, candidate_features)
        if similarity >= threshold:
            similar.append((exp_id, similarity))

    # Sort by similarity (descending)
    similar.sort(key=lambda x: x[1], reverse=True)

    return similar


def compute_column_overlap(features1: Dict, features2: Dict) -> float:
    """
    Compute column name overlap between two experiments.

    Args:
        features1: Features from first experiment
        features2: Features from second experiment

    Returns:
        Jaccard similarity of column names [0, 1]
    """
    cols1 = set(features1['columns'])
    cols2 = set(features2['columns'])

    if not cols1 and not cols2:
        return 1.0

    intersection = len(cols1 & cols2)
    union = len(cols1 | cols2)

    return intersection / union if union > 0 else 0.0


def compute_shape_similarity(features1: Dict, features2: Dict) -> float:
    """
    Compute shape similarity (row count, column count) between experiments.

    Args:
        features1: Features from first experiment
        features2: Features from second experiment

    Returns:
        Shape similarity score [0, 1]
    """
    # Row count similarity (log scale)
    rows1 = features1['row_count']
    rows2 = features2['row_count']

    if rows1 == 0 or rows2 == 0:
        row_sim = 0.0
    else:
        log_ratio = abs(np.log10(rows1 / rows2))
        row_sim = max(0, 1 - log_ratio / 2.0)  # Allow 2 orders of magnitude difference

    # Column count similarity
    cols1 = features1['column_count']
    cols2 = features2['column_count']

    if cols1 == 0 or cols2 == 0:
        col_sim = 0.0
    else:
        col_sim = min(cols1, cols2) / max(cols1, cols2)

    # Average of row and column similarity
    return (row_sim + col_sim) / 2.0
