"""
DataVint Experiment Tracking

Provides experiment versioning for ML training pipelines:
- Content-based data versioning (SHA256 hashing)
- Model run tracking with metrics and hyperparameters
- Lineage tracking (which data version was used for which model run)
- SQLite metadata store for persistence

Usage:
    >>> import datavint as dv
    >>> import pandas as pd
    >>>
    >>> with dv.experiment("learning_rate_sweep") as exp:
    ...     # Register data version
    ...     df = pd.read_csv("data.csv")
    ...     data_id = exp.log_data(df, message="fix user coverage")
    ...
    ...     # Train model
    ...     model.fit(X_train, y_train)
    ...     metrics = {"NE": 0.867, "CTR": 0.0058}
    ...
    ...     # Log model run
    ...     exp.log_run(
    ...         data_commit_id=data_id,
    ...         metrics=metrics,
    ...         params={"lr": 0.005, "sample_rate": 0.6},
    ...         message="best config"
    ...     )
"""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


class ExperimentContext:
    """
    Context manager for tracking experiment lineage.

    Tracks:
    - Data commits (dataset versions with content hashes)
    - Model runs (training experiments with metrics)
    - Connections (which data was used for which models)
    """

    def __init__(self, experiment_id: str, db_path: Optional[Path] = None):
        """
        Initialize experiment context.

        Args:
            experiment_id: Unique identifier for this experiment
            db_path: Path to SQLite database (default: .datavint/metadata.db)
        """
        self.experiment_id = experiment_id
        self.db_path = db_path or Path.home() / ".datavint" / "metadata.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._current_data_commit_id: Optional[str] = None

    def __enter__(self):
        """Enter experiment context - create database and tables."""
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit experiment context - close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self):
        """Create SQLite tables for metadata storage."""
        cursor = self.conn.cursor()

        # Data commits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_commits (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                hash TEXT NOT NULL,
                message TEXT,
                row_count INTEGER,
                column_count INTEGER,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Model runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_runs (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                data_commit_id TEXT NOT NULL,
                message TEXT,
                metrics TEXT,
                params TEXT,
                timestamp TEXT NOT NULL,
                best INTEGER DEFAULT 0,
                sweep_id INTEGER,
                sweep_name TEXT,
                FOREIGN KEY (data_commit_id) REFERENCES data_commits(id)
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_commits_experiment
            ON data_commits(experiment_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_runs_experiment
            ON model_runs(experiment_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_runs_data_commit
            ON model_runs(data_commit_id)
        """)

        self.conn.commit()

    def _compute_dataframe_hash(self, df: pd.DataFrame) -> str:
        """
        Compute content-based hash for a DataFrame.

        Uses SHA256 on the binary representation of the DataFrame.
        This ensures the same data always gets the same hash.

        Args:
            df: DataFrame to hash

        Returns:
            Hexadecimal hash string (first 7 characters)
        """
        # Convert DataFrame to bytes for hashing
        # Sort columns first for deterministic ordering
        df_sorted = df[sorted(df.columns)]
        json_str = df_sorted.to_json(orient='split')
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        # Return first 7 chars (like Git short SHAs)
        return hash_obj.hexdigest()[:7]

    def log_data(
        self,
        df: pd.DataFrame,
        message: Optional[str] = None,
        commit_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a data version (data commit).

        Computes content-based hash and stores metadata in database.
        If the same data (by hash) already exists, returns existing ID.

        Args:
            df: DataFrame to register
            message: Description of this data version
            commit_id: Optional custom ID (auto-generated if not provided)
            metadata: Additional metadata to store

        Returns:
            Data commit ID (e.g., "D0", "D1")

        Example:
            >>> df = pd.read_csv("data.csv")
            >>> data_id = exp.log_data(df, message="dedup interactions")
            >>> print(data_id)
            D0
        """
        # Compute content hash
        content_hash = self._compute_dataframe_hash(df)

        # Check if this data version already exists
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM data_commits WHERE experiment_id = ? AND hash = ?",
            (self.experiment_id, content_hash)
        )
        existing = cursor.fetchone()
        if existing:
            commit_id = existing[0]
            self._current_data_commit_id = commit_id
            return commit_id

        # Generate ID if not provided
        if commit_id is None:
            cursor.execute(
                "SELECT COUNT(*) FROM data_commits WHERE experiment_id = ?",
                (self.experiment_id,)
            )
            count = cursor.fetchone()[0]
            commit_id = f"D{count}"

        # Insert new data commit
        cursor.execute("""
            INSERT INTO data_commits
            (id, experiment_id, hash, message, row_count, column_count, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            commit_id,
            self.experiment_id,
            content_hash,
            message,
            len(df),
            len(df.columns),
            datetime.now().isoformat(),
            json.dumps(metadata) if metadata else None
        ))

        self.conn.commit()
        self._current_data_commit_id = commit_id
        return commit_id

    def log_run(
        self,
        metrics: Dict[str, float],
        data_commit_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        run_id: Optional[str] = None,
        best: bool = False,
        sweep_id: Optional[int] = None,
        sweep_name: Optional[str] = None
    ) -> str:
        """
        Log a model training run.

        Args:
            metrics: Model performance metrics (e.g., {"NE": 0.867, "CTR": 0.0058})
            data_commit_id: Data version used (defaults to last logged data)
            params: Hyperparameters used (e.g., {"lr": 0.005})
            message: Description of this run
            run_id: Optional custom ID (auto-generated if not provided)
            best: Whether this is the best model overall
            sweep_id: Optional sweep/group ID for hyperparameter sweeps
            sweep_name: Optional sweep description

        Returns:
            Model run ID (e.g., "M0", "M1", "M2.1")

        Example:
            >>> exp.log_run(
            ...     metrics={"NE": 0.867, "CTR": 0.0058},
            ...     params={"lr": 0.005, "sample_rate": 0.6},
            ...     message="best config",
            ...     best=True
            ... )
            M2.2
        """
        # Use last logged data commit if not specified
        if data_commit_id is None:
            if self._current_data_commit_id is None:
                raise ValueError(
                    "data_commit_id not specified and no data has been logged yet. "
                    "Call log_data() first or provide data_commit_id explicitly."
                )
            data_commit_id = self._current_data_commit_id

        # Generate ID if not provided
        cursor = self.conn.cursor()
        if run_id is None:
            cursor.execute(
                "SELECT COUNT(*) FROM model_runs WHERE experiment_id = ?",
                (self.experiment_id,)
            )
            count = cursor.fetchone()[0]
            run_id = f"M{count}"

        # Insert model run
        cursor.execute("""
            INSERT INTO model_runs
            (id, experiment_id, data_commit_id, message, metrics, params,
             timestamp, best, sweep_id, sweep_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            self.experiment_id,
            data_commit_id,
            message,
            json.dumps(metrics),
            json.dumps(params) if params else None,
            datetime.now().isoformat(),
            1 if best else 0,
            sweep_id,
            sweep_name
        ))

        self.conn.commit()
        return run_id


@contextmanager
def experiment(experiment_id: str, db_path: Optional[Path] = None):
    """
    Create an experiment tracking context.

    This context manager handles experiment lineage tracking including:
    - Data versioning with content-based hashing
    - Model run tracking with metrics and hyperparameters
    - Automatic database management

    Args:
        experiment_id: Unique identifier for this experiment
        db_path: Path to SQLite database (default: ~/.datavint/metadata.db)

    Yields:
        ExperimentContext: Context manager for logging data and runs

    Example:
        >>> import datavint as dv
        >>>
        >>> with dv.experiment("learning_rate_sweep") as exp:
        ...     # Log data version
        ...     df = pd.read_csv("data.csv")
        ...     data_id = exp.log_data(df, message="dedup interactions")
        ...
        ...     # Train and log runs
        ...     for lr in [0.001, 0.005, 0.01]:
        ...         model.fit(X, y, lr=lr)
        ...         metrics = evaluate(model)
        ...         exp.log_run(
        ...             metrics=metrics,
        ...             params={"lr": lr},
        ...             message=f"lr={lr}"
        ...         )
    """
    ctx = ExperimentContext(experiment_id, db_path)
    with ctx:
        yield ctx
