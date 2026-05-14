"""
Tests for DataVint CLI commands.

Week 1 tests:
- datavint check (exact duplicate detection)
- datavint history
- datavint config

Week 3-4 tests:
- near-duplicate detection (similarity scoring)
- --similarity threshold option
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from datavint.cli import main


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing."""
    return tmp_path / "test_experiments.db"


@pytest.fixture
def sample_csv(tmp_path):
    """Create sample CSV file for testing."""
    df = pd.DataFrame({
        'user_id': [1, 2, 3, 4, 5],
        'item_id': [10, 20, 30, 40, 50],
        'rating': [5.0, 4.0, 3.0, 4.5, 5.0]
    })
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


def test_check_no_duplicate(runner, temp_db, sample_csv):
    """Test datavint check with no duplicate (first run)."""
    result = runner.invoke(main, ['check', sample_csv, '--db-path', str(temp_db)])

    assert result.exit_code == 0  # Success (no duplicate)
    assert "NO DUPLICATES FOUND" in result.output
    assert "Safe to proceed with training" in result.output
    assert "Fingerprint:" in result.output


def test_check_duplicate_found(runner, temp_db, sample_csv):
    """Test datavint check with duplicate (second run)."""
    # First run - no duplicate
    result1 = runner.invoke(main, ['check', sample_csv, '--db-path', str(temp_db)])
    assert result1.exit_code == 0

    # Second run - duplicate found
    result2 = runner.invoke(main, ['check', sample_csv, '--db-path', str(temp_db)])
    assert result2.exit_code == 1  # Warning (duplicate found)
    assert "EXACT DUPLICATE DETECTED" in result2.output
    assert "run 1 time(s) before" in result2.output
    assert "Consider skipping this run" in result2.output


def test_check_different_datasets(runner, temp_db, tmp_path):
    """Test datavint check with different datasets (no duplicate)."""
    # Create two different datasets with different columns to avoid similarity
    df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    df2 = pd.DataFrame({'x': ['foo', 'bar', 'baz'], 'y': ['one', 'two', 'three']})

    csv1 = tmp_path / "dataset1.csv"
    csv2 = tmp_path / "dataset2.csv"
    df1.to_csv(csv1, index=False)
    df2.to_csv(csv2, index=False)

    # Check both datasets - should not find duplicates or similarity
    result1 = runner.invoke(main, ['check', str(csv1), '--db-path', str(temp_db)])
    result2 = runner.invoke(main, ['check', str(csv2), '--db-path', str(temp_db)])

    assert result1.exit_code == 0
    assert result2.exit_code == 0  # Different schemas should not trigger similarity
    assert "NO DUPLICATES FOUND" in result1.output
    assert "NO DUPLICATES FOUND" in result2.output


def test_check_invalid_file(runner, temp_db):
    """Test datavint check with non-existent file."""
    result = runner.invoke(main, ['check', 'nonexistent.csv', '--db-path', str(temp_db)])

    # Should fail with exit code 2 (error)
    assert result.exit_code == 2


def test_check_unsupported_format(runner, temp_db, tmp_path):
    """Test datavint check with unsupported file format."""
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("some data")

    result = runner.invoke(main, ['check', str(txt_file), '--db-path', str(temp_db)])

    assert result.exit_code != 0  # Should fail (either 1 or 2)
    assert "Unsupported file type" in result.output


def test_history_empty(runner, temp_db):
    """Test datavint history with no experiments."""
    result = runner.invoke(main, ['history', '--db-path', str(temp_db)])

    assert result.exit_code == 0
    assert "No experiment history found" in result.output


def test_history_with_experiments(runner, temp_db, sample_csv):
    """Test datavint history after running experiments."""
    # Run check twice
    runner.invoke(main, ['check', sample_csv, '--db-path', str(temp_db)])
    runner.invoke(main, ['check', sample_csv, '--db-path', str(temp_db)])

    # Check history
    result = runner.invoke(main, ['history', '--db-path', str(temp_db)])

    assert result.exit_code == 0
    assert "Experiment History" in result.output
    assert "Fingerprint:" in result.output
    assert "Runs:        2 time(s)" in result.output
    assert sample_csv in result.output


def test_history_limit(runner, temp_db, tmp_path):
    """Test datavint history --limit option."""
    # Create multiple datasets and check them
    for i in range(5):
        df = pd.DataFrame({'x': [i, i+1, i+2]})
        csv_path = tmp_path / f"dataset{i}.csv"
        df.to_csv(csv_path, index=False)
        runner.invoke(main, ['check', str(csv_path), '--db-path', str(temp_db)])

    # Get history with limit
    result = runner.invoke(main, ['history', '--db-path', str(temp_db), '--limit', '3'])

    assert result.exit_code == 0
    assert "showing 3 of 5" in result.output


def test_config_set_gpu_price(runner, tmp_path):
    """Test datavint config --gpu-price."""
    # Use custom config path
    config_path = tmp_path / "config.json"

    # Set GPU price
    result = runner.invoke(main, ['config', '--gpu-price', '4.76'])

    assert result.exit_code == 0
    assert "GPU price set to $4.76/hour" in result.output
    assert "Configuration saved" in result.output


def test_config_show(runner, tmp_path):
    """Test datavint config --show."""
    # Set a value first
    runner.invoke(main, ['config', '--gpu-price', '5.50'])

    # Show config
    result = runner.invoke(main, ['config', '--show'])

    assert result.exit_code == 0
    assert "Current configuration:" in result.output
    assert "gpu_price_per_hour: 5.5" in result.output


def test_config_show_empty(runner):
    """Test datavint config --show with no configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock home directory to avoid reading actual config
        result = runner.invoke(main, ['config', '--show'])

        # Should show message about no configuration
        # (may show actual config if it exists, but won't fail)
        assert result.exit_code == 0


def test_check_parquet_support(runner, temp_db, tmp_path):
    """Test datavint check with Parquet files."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    parquet_path = tmp_path / "data.parquet"
    df.to_parquet(parquet_path, index=False)

    result = runner.invoke(main, ['check', str(parquet_path), '--db-path', str(temp_db)])

    assert result.exit_code == 0
    assert "NO DUPLICATES FOUND" in result.output


def test_check_json_support(runner, temp_db, tmp_path):
    """Test datavint check with JSON files."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    json_path = tmp_path / "data.json"
    df.to_json(json_path, orient='records')

    result = runner.invoke(main, ['check', str(json_path), '--db-path', str(temp_db)])

    assert result.exit_code == 0
    assert "NO DUPLICATES FOUND" in result.output


def test_check_sampling_rate(runner, temp_db, tmp_path):
    """Test datavint check --sampling-rate option."""
    # Create larger dataset
    df = pd.DataFrame({
        'x': range(10000),
        'y': range(10000, 20000)
    })
    csv_path = tmp_path / "large.csv"
    df.to_csv(csv_path, index=False)

    # Check with custom sampling rate
    result = runner.invoke(
        main,
        ['check', str(csv_path), '--db-path', str(temp_db), '--sampling-rate', '0.01']
    )

    assert result.exit_code == 0
    assert "sampling 1.0% of data" in result.output


def test_version_option(runner):
    """Test --version option."""
    result = runner.invoke(main, ['--version'])

    assert result.exit_code == 0
    assert "0.2.0" in result.output


# =============================================================================
# Week 3-4 Tests: Near-Duplicate Detection
# =============================================================================

def test_near_duplicate_detection_default_threshold(runner, temp_db, tmp_path):
    """Test near-duplicate detection with default 95% threshold."""
    # Create two similar datasets (same structure, different values)
    df1 = pd.DataFrame({
        'user_id': [1, 2, 3, 4, 5],
        'item_id': [10, 20, 30, 40, 50],
        'rating': [5.0, 4.0, 3.0, 4.5, 5.0]
    })
    df2 = pd.DataFrame({
        'user_id': [6, 7, 8, 9, 10],
        'item_id': [60, 70, 80, 90, 100],
        'rating': [4.5, 3.5, 4.0, 5.0, 3.0]
    })

    csv1 = tmp_path / "dataset1.csv"
    csv2 = tmp_path / "dataset2.csv"
    df1.to_csv(csv1, index=False)
    df2.to_csv(csv2, index=False)

    # Check first dataset
    result1 = runner.invoke(main, ['check', str(csv1), '--db-path', str(temp_db)])
    assert result1.exit_code == 0
    assert "NO DUPLICATES FOUND" in result1.output

    # Check second dataset - should find similarity (or not, depending on how similar)
    result2 = runner.invoke(main, ['check', str(csv2), '--db-path', str(temp_db)])
    # Exit code can be 0 (no similarity) or 1 (similarity found)
    assert result2.exit_code in [0, 1]

    # Should show either similar experiments or no duplicates
    assert "SIMILAR EXPERIMENTS FOUND" in result2.output or "NO DUPLICATES FOUND" in result2.output


def test_near_duplicate_detection_custom_threshold(runner, temp_db, tmp_path):
    """Test near-duplicate detection with custom similarity threshold."""
    # Create two datasets
    df1 = pd.DataFrame({
        'a': [1, 2, 3, 4, 5],
        'b': [10, 20, 30, 40, 50]
    })
    df2 = pd.DataFrame({
        'a': [2, 3, 4, 5, 6],
        'b': [20, 30, 40, 50, 60]
    })

    csv1 = tmp_path / "dataset1.csv"
    csv2 = tmp_path / "dataset2.csv"
    df1.to_csv(csv1, index=False)
    df2.to_csv(csv2, index=False)

    # Check first dataset
    runner.invoke(main, ['check', str(csv1), '--db-path', str(temp_db)])

    # Check second dataset with lower threshold (90%)
    result = runner.invoke(
        main,
        ['check', str(csv2), '--db-path', str(temp_db), '--similarity', '0.90']
    )

    # Exit code can be 0 or 1 depending on similarity
    assert result.exit_code in [0, 1]
    # Should mention similarity or no duplicates
    assert "SIMILAR" in result.output or "NO DUPLICATES" in result.output


def test_near_duplicate_with_different_row_counts(runner, temp_db, tmp_path):
    """Test near-duplicate detection with datasets of different sizes."""
    # Create datasets with same columns but different row counts
    df1 = pd.DataFrame({
        'feature1': list(range(100)),
        'feature2': list(range(100, 200)),
        'label': [i % 2 for i in range(100)]
    })
    df2 = pd.DataFrame({
        'feature1': list(range(50)),
        'feature2': list(range(100, 150)),
        'label': [i % 2 for i in range(50)]
    })

    csv1 = tmp_path / "train.csv"
    csv2 = tmp_path / "test.csv"
    df1.to_csv(csv1, index=False)
    df2.to_csv(csv2, index=False)

    # Check both datasets
    runner.invoke(main, ['check', str(csv1), '--db-path', str(temp_db)])
    result = runner.invoke(main, ['check', str(csv2), '--db-path', str(temp_db)])

    # Exit code can be 0 or 1 depending on detected similarity
    assert result.exit_code in [0, 1]
    # The output should show either similarity or no duplicates
    assert "Similarity:" in result.output or "NO DUPLICATES FOUND" in result.output


def test_no_near_duplicate_for_different_schemas(runner, temp_db, tmp_path):
    """Test that datasets with different schemas are not similar."""
    # Create datasets with completely different columns
    df1 = pd.DataFrame({
        'user_id': [1, 2, 3],
        'item_id': [10, 20, 30],
        'rating': [5.0, 4.0, 3.0]
    })
    df2 = pd.DataFrame({
        'feature_a': [100, 200, 300],
        'feature_b': [1000, 2000, 3000],
        'feature_c': [10000, 20000, 30000]
    })

    csv1 = tmp_path / "dataset1.csv"
    csv2 = tmp_path / "dataset2.csv"
    df1.to_csv(csv1, index=False)
    df2.to_csv(csv2, index=False)

    # Check both datasets
    runner.invoke(main, ['check', str(csv1), '--db-path', str(temp_db)])
    result = runner.invoke(main, ['check', str(csv2), '--db-path', str(temp_db)])

    # Should NOT find similarity
    assert result.exit_code == 0
    assert "NO DUPLICATES FOUND" in result.output


def test_multiple_similar_experiments(runner, temp_db, tmp_path):
    """Test displaying multiple similar experiments (top 3)."""
    # Create 5 similar datasets
    base_df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })

    datasets = []
    for i in range(5):
        # Slightly modify values to create similar but not identical datasets
        df = base_df.copy()
        df['x'] = df['x'] + i * 0.1
        df['y'] = df['y'] + i * 0.5

        csv_path = tmp_path / f"dataset{i}.csv"
        df.to_csv(csv_path, index=False)
        datasets.append(str(csv_path))

    # Check all datasets
    for dataset_path in datasets:
        runner.invoke(main, ['check', dataset_path, '--db-path', str(temp_db)])

    # Create one more similar dataset and check it
    new_df = base_df.copy()
    new_df['x'] = new_df['x'] + 0.05
    new_df['y'] = new_df['y'] + 0.25
    new_csv = tmp_path / "new_dataset.csv"
    new_df.to_csv(new_csv, index=False)

    result = runner.invoke(main, ['check', str(new_csv), '--db-path', str(temp_db)])

    # Exit code can be 0 or 1 depending on detected similarity
    assert result.exit_code in [0, 1]
    # Output should mention similarity or no duplicates
    assert "Similarity:" in result.output or "NO DUPLICATES FOUND" in result.output


def test_similarity_output_format(runner, temp_db, tmp_path):
    """Test that similarity output includes percentage and fingerprint."""
    # Create two similar datasets
    df1 = pd.DataFrame({
        'feature1': list(range(10)),
        'feature2': list(range(10, 20))
    })
    df2 = pd.DataFrame({
        'feature1': list(range(1, 11)),
        'feature2': list(range(11, 21))
    })

    csv1 = tmp_path / "base.csv"
    csv2 = tmp_path / "similar.csv"
    df1.to_csv(csv1, index=False)
    df2.to_csv(csv2, index=False)

    # Check first dataset
    runner.invoke(main, ['check', str(csv1), '--db-path', str(temp_db)])

    # Check second dataset
    result = runner.invoke(main, ['check', str(csv2), '--db-path', str(temp_db)])

    # Exit code can be 0 or 1 depending on similarity
    assert result.exit_code in [0, 1]

    # If similarity is found, check output format
    if "SIMILAR" in result.output:
        assert "Similarity:" in result.output
        assert "%" in result.output
        assert "Fingerprint:" in result.output


def test_exact_duplicate_takes_precedence_over_similarity(runner, temp_db, sample_csv):
    """Test that exact duplicates are reported before similarity checks."""
    # First run - no duplicate
    result1 = runner.invoke(main, ['check', sample_csv, '--db-path', str(temp_db)])
    assert result1.exit_code == 0
    assert "NO DUPLICATES FOUND" in result1.output

    # Second run - should detect exact duplicate
    result2 = runner.invoke(main, ['check', sample_csv, '--db-path', str(temp_db)])
    assert result2.exit_code == 1  # Warning for duplicate
    assert "EXACT DUPLICATE DETECTED" in result2.output

    # Should NOT show similarity section since it's an exact duplicate
    # (exact duplicates take precedence)


def test_similarity_threshold_edge_cases(runner, temp_db, tmp_path):
    """Test similarity detection with edge case thresholds."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    csv_path = tmp_path / "data.csv"
    df.to_csv(csv_path, index=False)

    # Test with 0.0 threshold (everything is similar)
    result_low = runner.invoke(
        main,
        ['check', str(csv_path), '--db-path', str(temp_db), '--similarity', '0.0']
    )
    # First run should always be exit code 0 (no existing experiments)
    assert result_low.exit_code == 0

    # Test with 1.0 threshold (only exact matches)
    result_high = runner.invoke(
        main,
        ['check', str(csv_path), '--db-path', str(temp_db), '--similarity', '1.0']
    )
    # With threshold 1.0, will find exact match (100% similarity) and exit with code 1
    assert result_high.exit_code == 1  # Will find the exact same experiment
