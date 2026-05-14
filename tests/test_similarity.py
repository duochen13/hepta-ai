"""
Tests for DataVint similarity module.

Week 3-4 tests:
- Feature extraction from DataFrames
- Feature vector conversion
- Cosine similarity computation
- Helper functions (column overlap, shape similarity)
"""

import numpy as np
import pandas as pd
import pytest

from datavint.similarity import (
    extract_features,
    features_to_vector,
    compute_similarity,
    find_similar_experiments,
    compute_column_overlap,
    compute_shape_similarity
)


class TestFeatureExtraction:
    """Tests for extract_features function."""

    def test_extract_features_basic(self):
        """Test basic feature extraction."""
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [4, 5, 6],
            'c': ['x', 'y', 'z']
        })

        features = extract_features(df)

        assert features['column_count'] == 3
        assert features['row_count'] == 3
        assert set(features['columns']) == {'a', 'b', 'c'}
        assert len(features['dtypes']) == 3
        assert len(features['numeric_stats']) == 2  # a, b are numeric
        assert len(features['categorical_cardinality']) == 1  # c is categorical

    def test_extract_features_numeric_only(self):
        """Test feature extraction with only numeric columns."""
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [10.5, 20.5, 30.5, 40.5, 50.5]
        })

        features = extract_features(df)

        assert features['column_count'] == 2
        assert features['row_count'] == 5
        assert 'x' in features['numeric_stats']
        assert 'y' in features['numeric_stats']
        assert len(features['categorical_cardinality']) == 0

        # Check numeric stats
        assert features['numeric_stats']['x']['mean'] == 3.0
        assert features['numeric_stats']['x']['min'] == 1
        assert features['numeric_stats']['x']['max'] == 5

    def test_extract_features_categorical_only(self):
        """Test feature extraction with only categorical columns."""
        df = pd.DataFrame({
            'category1': ['a', 'b', 'c', 'a', 'b'],
            'category2': ['x', 'y', 'x', 'y', 'x']
        })

        features = extract_features(df)

        assert features['column_count'] == 2
        assert features['row_count'] == 5
        assert len(features['numeric_stats']) == 0
        assert len(features['categorical_cardinality']) == 2

        # Check cardinality
        assert features['categorical_cardinality']['category1'] == 3  # a, b, c
        assert features['categorical_cardinality']['category2'] == 2  # x, y

    def test_extract_features_empty_dataframe(self):
        """Test feature extraction with empty DataFrame."""
        df = pd.DataFrame()

        features = extract_features(df)

        assert features['column_count'] == 0
        assert features['row_count'] == 0
        assert len(features['columns']) == 0
        assert len(features['dtypes']) == 0
        assert len(features['numeric_stats']) == 0
        assert len(features['categorical_cardinality']) == 0

    def test_extract_features_with_nulls(self):
        """Test feature extraction with null values."""
        df = pd.DataFrame({
            'a': [1, 2, None, 4, 5],
            'b': ['x', 'y', None, 'z', 'w']
        })

        features = extract_features(df)

        # Should handle nulls gracefully
        assert features['column_count'] == 2
        assert features['row_count'] == 5
        # Numeric stats should be computed on non-null values
        assert 'a' in features['numeric_stats']


class TestFeatureVector:
    """Tests for features_to_vector function."""

    def test_feature_vector_length(self):
        """Test that feature vector has consistent length."""
        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df2 = pd.DataFrame({'x': [10, 20], 'y': [30, 40], 'z': [50, 60]})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        vec1 = features_to_vector(features1)
        vec2 = features_to_vector(features2)

        # Vectors should have same length regardless of dataset
        assert len(vec1) == len(vec2)

    def test_feature_vector_values_in_range(self):
        """Test that feature vector values are normalized."""
        df = pd.DataFrame({
            'a': list(range(1000)),
            'b': list(range(1000, 2000))
        })

        features = extract_features(df)
        vec = features_to_vector(features)

        # Most values should be in [0, 1] range (with some exceptions for means)
        # Check that we don't have extreme values
        assert np.all(np.abs(vec) < 100), "Feature vector has unreasonably large values"

    def test_feature_vector_identical_data(self):
        """Test that identical datasets produce identical vectors."""
        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df2 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        vec1 = features_to_vector(features1)
        vec2 = features_to_vector(features2)

        np.testing.assert_array_almost_equal(vec1, vec2)

    def test_feature_vector_empty_features(self):
        """Test feature vector with empty features."""
        features = {
            'columns': [],
            'column_count': 0,
            'row_count': 0,
            'dtypes': {},
            'numeric_stats': {},
            'categorical_cardinality': {}
        }

        vec = features_to_vector(features)

        # Should produce a vector of zeros or near-zeros
        assert len(vec) > 0
        assert np.all(np.abs(vec) < 1.0)


class TestCosineSimilarity:
    """Tests for compute_similarity function."""

    def test_identical_datasets_similarity(self):
        """Test that identical datasets have 100% similarity."""
        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df2 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        similarity = compute_similarity(features1, features2)

        # Should be very close to 1.0 (100% similar)
        assert similarity > 0.99

    def test_similar_datasets_high_similarity(self):
        """Test that similar datasets have high similarity."""
        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df2 = pd.DataFrame({'a': [2, 3, 4], 'b': [5, 6, 7]})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        similarity = compute_similarity(features1, features2)

        # Should be high similarity (same structure, similar values)
        assert similarity > 0.90

    def test_different_datasets_low_similarity(self):
        """Test that different datasets have low similarity."""
        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df2 = pd.DataFrame({'x': ['a', 'b', 'c'], 'y': ['d', 'e', 'f']})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        similarity = compute_similarity(features1, features2)

        # Should be low similarity (different schema and types)
        assert similarity < 0.80

    def test_similarity_range(self):
        """Test that similarity is always in [0, 1] range."""
        df1 = pd.DataFrame({'a': [1, 2, 3]})
        df2 = pd.DataFrame({'b': [100, 200, 300]})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        similarity = compute_similarity(features1, features2)

        assert 0.0 <= similarity <= 1.0

    def test_similarity_symmetry(self):
        """Test that similarity is symmetric (A→B == B→A)."""
        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df2 = pd.DataFrame({'x': [10, 20, 30], 'y': [40, 50, 60]})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        sim_1_2 = compute_similarity(features1, features2)
        sim_2_1 = compute_similarity(features2, features1)

        assert abs(sim_1_2 - sim_2_1) < 1e-6


class TestFindSimilarExperiments:
    """Tests for find_similar_experiments function."""

    def test_find_similar_above_threshold(self):
        """Test finding experiments above similarity threshold."""
        df_target = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df_similar = pd.DataFrame({'a': [2, 3, 4], 'b': [5, 6, 7]})
        df_different = pd.DataFrame({'x': ['a', 'b', 'c']})

        target_features = extract_features(df_target)
        candidates = [
            (1, extract_features(df_similar)),
            (2, extract_features(df_different))
        ]

        similar = find_similar_experiments(target_features, candidates, threshold=0.90)

        # Should find the similar one but not the different one
        assert len(similar) >= 1
        # Check that returned IDs make sense
        assert all(isinstance(exp_id, int) for exp_id, _ in similar)
        assert all(0.0 <= sim <= 1.0 for _, sim in similar)

    def test_find_similar_sorted_descending(self):
        """Test that results are sorted by similarity (highest first)."""
        df_target = pd.DataFrame({'a': [1, 2, 3]})

        target_features = extract_features(df_target)

        # Create candidates with varying similarity
        candidates = []
        for i in range(5):
            df = pd.DataFrame({'a': [i, i+1, i+2]})
            candidates.append((i, extract_features(df)))

        similar = find_similar_experiments(target_features, candidates, threshold=0.80)

        # Results should be sorted by similarity (descending)
        if len(similar) > 1:
            similarities = [sim for _, sim in similar]
            assert similarities == sorted(similarities, reverse=True)

    def test_find_similar_empty_candidates(self):
        """Test with no candidates."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        features = extract_features(df)

        similar = find_similar_experiments(features, [], threshold=0.95)

        assert similar == []

    def test_find_similar_high_threshold(self):
        """Test with very high threshold (99%)."""
        df1 = pd.DataFrame({'a': [1, 2, 3]})
        df2 = pd.DataFrame({'a': [2, 3, 4]})

        features1 = extract_features(df1)
        features2 = extract_features(df2)

        similar = find_similar_experiments(features1, [(1, features2)], threshold=0.99)

        # With high threshold, may or may not find matches depending on similarity
        assert isinstance(similar, list)


class TestColumnOverlap:
    """Tests for compute_column_overlap function."""

    def test_identical_columns(self):
        """Test column overlap with identical columns."""
        features1 = {'columns': ['a', 'b', 'c']}
        features2 = {'columns': ['a', 'b', 'c']}

        overlap = compute_column_overlap(features1, features2)

        assert overlap == 1.0  # 100% overlap

    def test_no_column_overlap(self):
        """Test column overlap with no common columns."""
        features1 = {'columns': ['a', 'b', 'c']}
        features2 = {'columns': ['x', 'y', 'z']}

        overlap = compute_column_overlap(features1, features2)

        assert overlap == 0.0  # 0% overlap

    def test_partial_column_overlap(self):
        """Test column overlap with partial overlap."""
        features1 = {'columns': ['a', 'b', 'c', 'd']}
        features2 = {'columns': ['b', 'c', 'e', 'f']}

        overlap = compute_column_overlap(features1, features2)

        # Intersection: {b, c} = 2
        # Union: {a, b, c, d, e, f} = 6
        # Jaccard: 2/6 = 0.333...
        assert abs(overlap - (2/6)) < 1e-6

    def test_empty_columns(self):
        """Test column overlap with empty columns."""
        features1 = {'columns': []}
        features2 = {'columns': []}

        overlap = compute_column_overlap(features1, features2)

        assert overlap == 1.0  # Both empty = 100% overlap


class TestShapeSimilarity:
    """Tests for compute_shape_similarity function."""

    def test_identical_shape(self):
        """Test shape similarity with identical shapes."""
        features1 = {'row_count': 100, 'column_count': 10}
        features2 = {'row_count': 100, 'column_count': 10}

        similarity = compute_shape_similarity(features1, features2)

        assert similarity == 1.0  # 100% similar

    def test_similar_shape(self):
        """Test shape similarity with similar shapes."""
        features1 = {'row_count': 100, 'column_count': 10}
        features2 = {'row_count': 150, 'column_count': 12}

        similarity = compute_shape_similarity(features1, features2)

        # Should have high similarity (within same order of magnitude)
        assert similarity > 0.70

    def test_very_different_shape(self):
        """Test shape similarity with very different shapes."""
        features1 = {'row_count': 100, 'column_count': 10}
        features2 = {'row_count': 100000, 'column_count': 2}

        similarity = compute_shape_similarity(features1, features2)

        # Should have low similarity (very different scales)
        assert similarity < 0.50

    def test_zero_rows(self):
        """Test shape similarity with zero rows."""
        features1 = {'row_count': 0, 'column_count': 10}
        features2 = {'row_count': 100, 'column_count': 10}

        similarity = compute_shape_similarity(features1, features2)

        # Should handle zero rows gracefully
        assert 0.0 <= similarity <= 1.0
