"""
Test experiment tracking functionality.

Tests the experiment() context manager, data versioning, and model run tracking.
"""

import pandas as pd
import pytest
import sqlite3
from pathlib import Path
import tempfile
import json

import datavint as dv


def test_experiment_context_creation():
    """Test that experiment context can be created and database is initialized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        with dv.experiment("test_exp", db_path=db_path) as exp:
            assert exp.experiment_id == "test_exp"
            assert exp.conn is not None
            assert db_path.exists()

        # Verify tables were created
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check data_commits table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_commits'")
        assert cursor.fetchone() is not None

        # Check model_runs table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_runs'")
        assert cursor.fetchone() is not None

        conn.close()


def test_log_data_creates_commit():
    """Test that logging data creates a data commit with correct metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'feature_a': [0.5, 0.6, 0.7],
            'label': [0, 1, 0]
        })

        with dv.experiment("test_exp", db_path=db_path) as exp:
            commit_id = exp.log_data(df, message="test data")

            assert commit_id == "D0"  # First commit
            assert exp._current_data_commit_id == "D0"

        # Verify data commit in database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_commits WHERE id = ?", ("D0",))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "test_exp"  # experiment_id
        assert row[3] == "test data"  # message
        assert row[4] == 3  # row_count
        assert row[5] == 3  # column_count

        conn.close()


def test_log_data_deduplication():
    """Test that logging the same data twice returns the same commit ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'feature_a': [0.5, 0.6, 0.7]
        })

        with dv.experiment("test_exp", db_path=db_path) as exp:
            commit_id_1 = exp.log_data(df, message="first log")
            commit_id_2 = exp.log_data(df, message="second log")  # Same data

            # Should return the same ID for identical data
            assert commit_id_1 == commit_id_2

        # Verify only one commit exists
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM data_commits WHERE experiment_id = ?", ("test_exp",))
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()


def test_log_run_creates_model_run():
    """Test that logging a run creates a model run with metrics and params."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        df = pd.DataFrame({'user_id': [1, 2, 3], 'label': [0, 1, 0]})

        with dv.experiment("test_exp", db_path=db_path) as exp:
            data_id = exp.log_data(df, message="training data")

            run_id = exp.log_run(
                metrics={"NE": 0.867, "CTR": 0.0058},
                params={"lr": 0.005, "sample_rate": 0.6},
                message="best config",
                best=True
            )

            assert run_id == "M0"  # First run

        # Verify model run in database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM model_runs WHERE id = ?", ("M0",))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "test_exp"  # experiment_id
        assert row[2] == data_id  # data_commit_id
        assert row[3] == "best config"  # message

        # Check metrics
        metrics = json.loads(row[4])
        assert metrics["NE"] == 0.867
        assert metrics["CTR"] == 0.0058

        # Check params
        params = json.loads(row[5])
        assert params["lr"] == 0.005
        assert params["sample_rate"] == 0.6

        assert row[7] == 1  # best flag

        conn.close()


def test_multiple_runs_with_same_data():
    """Test logging multiple model runs using the same data version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        df = pd.DataFrame({'user_id': [1, 2, 3], 'label': [0, 1, 0]})

        with dv.experiment("lr_sweep", db_path=db_path) as exp:
            data_id = exp.log_data(df, message="dedup interactions")

            # Log multiple runs with different hyperparameters
            learning_rates = [0.001, 0.005, 0.01, 0.02]
            run_ids = []

            for lr in learning_rates:
                run_id = exp.log_run(
                    data_commit_id=data_id,
                    metrics={"NE": 0.8 + lr * 10},  # Mock metrics
                    params={"lr": lr},
                    message=f"lr={lr}",
                    sweep_id=1,
                    sweep_name="Learning Rate Sweep"
                )
                run_ids.append(run_id)

            assert len(run_ids) == 4
            assert run_ids == ["M0", "M1", "M2", "M3"]

        # Verify all runs reference the same data commit
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT data_commit_id FROM model_runs WHERE experiment_id = ?", ("lr_sweep",))
        data_commits = [row[0] for row in cursor.fetchall()]

        assert len(data_commits) == 4
        assert all(dc == data_id for dc in data_commits)

        conn.close()


def test_auto_use_last_data_commit():
    """Test that log_run() automatically uses the last logged data commit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        df = pd.DataFrame({'user_id': [1, 2, 3], 'label': [0, 1, 0]})

        with dv.experiment("test_exp", db_path=db_path) as exp:
            data_id = exp.log_data(df, message="training data")

            # Don't specify data_commit_id - should use D0 automatically
            run_id = exp.log_run(
                metrics={"accuracy": 0.95},
                message="test run"
            )

            assert run_id == "M0"

        # Verify the run is linked to the data commit
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT data_commit_id FROM model_runs WHERE id = ?", ("M0",))
        linked_data_id = cursor.fetchone()[0]

        assert linked_data_id == data_id
        conn.close()


def test_log_run_without_data_raises_error():
    """Test that logging a run without data raises an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        with dv.experiment("test_exp", db_path=db_path) as exp:
            with pytest.raises(ValueError, match="no data has been logged yet"):
                exp.log_run(metrics={"accuracy": 0.95})


def test_content_based_hashing():
    """Test that identical data gets the same hash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df2 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})  # Identical
        df3 = pd.DataFrame({'a': [1, 2, 4], 'b': [4, 5, 6]})  # Different

        with dv.experiment("test_exp", db_path=db_path) as exp:
            hash1 = exp._compute_dataframe_hash(df1)
            hash2 = exp._compute_dataframe_hash(df2)
            hash3 = exp._compute_dataframe_hash(df3)

            assert hash1 == hash2  # Same data = same hash
            assert hash1 != hash3  # Different data = different hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
