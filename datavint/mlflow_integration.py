"""
DataVint ↔ MLflow Integration

Bidirectional sync between DataVint experiment tracking and MLflow:
- Export DataVint experiments to MLflow
- Import MLflow runs into DataVint
- Unified tracking across both platforms

Usage:
    >>> import datavint as dv
    >>> from datavint.mlflow_integration import MLflowSync
    >>>
    >>> # Enable MLflow sync
    >>> with dv.experiment("my_experiment", mlflow_tracking=True) as exp:
    ...     data_id = exp.log_data(df)
    ...     exp.log_run(metrics={"accuracy": 0.92})
    >>>
    >>> # Or sync existing experiments
    >>> sync = MLflowSync()
    >>> sync.export_to_mlflow("my_experiment")
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import mlflow
    import mlflow.tracking
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


class MLflowSync:
    """
    Synchronize DataVint experiments with MLflow.

    Provides bidirectional sync between DataVint's experiment tracking
    and MLflow's tracking server.
    """

    def __init__(
        self,
        datavint_db: Optional[Path] = None,
        mlflow_tracking_uri: Optional[str] = None
    ):
        """
        Initialize MLflow sync.

        Args:
            datavint_db: Path to DataVint metadata.db (default: ~/.datavint/metadata.db)
            mlflow_tracking_uri: MLflow tracking URI (default: mlflow default)
        """
        if not MLFLOW_AVAILABLE:
            raise ImportError(
                "MLflow is not installed. Install with: pip install mlflow"
            )

        self.db_path = datavint_db or Path.home() / ".datavint" / "metadata.db"

        if mlflow_tracking_uri:
            mlflow.set_tracking_uri(mlflow_tracking_uri)

        self.client = mlflow.tracking.MlflowClient()

    def export_to_mlflow(
        self,
        experiment_id: str,
        mlflow_experiment_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Export DataVint experiment to MLflow.

        Creates MLflow runs for each model run in the DataVint experiment.
        Data commits are logged as MLflow tags and parameters.

        Args:
            experiment_id: DataVint experiment ID
            mlflow_experiment_name: MLflow experiment name (default: same as experiment_id)

        Returns:
            Dictionary mapping DataVint run IDs to MLflow run IDs

        Example:
            >>> sync = MLflowSync()
            >>> mapping = sync.export_to_mlflow("test-05-14")
            >>> print(f"Exported {len(mapping)} runs to MLflow")
        """
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"DataVint database not found at {self.db_path}"
            )

        # Set MLflow experiment
        mlflow_exp_name = mlflow_experiment_name or experiment_id
        mlflow_experiment = mlflow.set_experiment(mlflow_exp_name)

        # Connect to DataVint database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Get data commits for tagging
        cursor.execute("""
            SELECT id, hash, message, row_count, column_count
            FROM data_commits
            WHERE experiment_id = ?
        """, (experiment_id,))
        data_commits = {row[0]: row for row in cursor.fetchall()}

        # Get all model runs
        cursor.execute("""
            SELECT id, data_commit_id, message, metrics, params,
                   timestamp, best, sweep_id, sweep_name
            FROM model_runs
            WHERE experiment_id = ?
            ORDER BY timestamp ASC
        """, (experiment_id,))
        model_runs = cursor.fetchall()

        if not model_runs:
            conn.close()
            raise ValueError(f"No model runs found for experiment '{experiment_id}'")

        # Export each run to MLflow
        run_mapping = {}

        for run in model_runs:
            (run_id, data_commit_id, message, metrics_json,
             params_json, timestamp, best, sweep_id, sweep_name) = run

            # Parse JSON fields
            metrics = json.loads(metrics_json) if metrics_json else {}
            params = json.loads(params_json) if params_json else {}

            # Start MLflow run
            with mlflow.start_run(
                experiment_id=mlflow_experiment.experiment_id,
                run_name=f"{run_id}: {message}" if message else run_id
            ) as mlflow_run:

                # Log parameters
                if params:
                    mlflow.log_params(params)

                # Log metrics
                if metrics:
                    mlflow.log_metrics(metrics)

                # Log data commit information as tags
                data_commit = data_commits.get(data_commit_id)
                if data_commit:
                    mlflow.set_tags({
                        "datavint.data_commit_id": data_commit_id,
                        "datavint.data_hash": data_commit[1],
                        "datavint.data_message": data_commit[2] or "",
                        "datavint.data_rows": str(data_commit[3]),
                        "datavint.data_cols": str(data_commit[4])
                    })

                # Log DataVint metadata as tags
                mlflow.set_tags({
                    "datavint.run_id": run_id,
                    "datavint.experiment_id": experiment_id,
                    "datavint.timestamp": timestamp,
                })

                # Log sweep information
                if sweep_id is not None:
                    mlflow.set_tags({
                        "datavint.sweep_id": str(sweep_id),
                        "datavint.sweep_name": sweep_name or f"Sweep {sweep_id}"
                    })

                # Mark best models
                if best:
                    mlflow.set_tag("datavint.best", "true")

                run_mapping[run_id] = mlflow_run.info.run_id

        conn.close()

        print(f"✅ Exported {len(run_mapping)} runs to MLflow experiment '{mlflow_exp_name}'")
        print(f"   MLflow UI: {mlflow.get_tracking_uri()}")

        return run_mapping

    def import_from_mlflow(
        self,
        mlflow_experiment_name: str,
        datavint_experiment_id: Optional[str] = None,
        import_data_commits: bool = True
    ) -> int:
        """
        Import MLflow runs into DataVint.

        Creates DataVint model runs from MLflow experiment.
        Optionally creates data commits from MLflow tags.

        Args:
            mlflow_experiment_name: MLflow experiment name to import
            datavint_experiment_id: DataVint experiment ID (default: same as MLflow name)
            import_data_commits: Whether to create data commits from tags

        Returns:
            Number of runs imported

        Example:
            >>> sync = MLflowSync()
            >>> count = sync.import_from_mlflow("my_mlflow_experiment")
            >>> print(f"Imported {count} runs")
        """
        # Get MLflow experiment
        mlflow_experiment = mlflow.get_experiment_by_name(mlflow_experiment_name)
        if not mlflow_experiment:
            raise ValueError(f"MLflow experiment '{mlflow_experiment_name}' not found")

        datavint_exp_id = datavint_experiment_id or mlflow_experiment_name

        # Get all runs from MLflow
        runs = mlflow.search_runs(
            experiment_ids=[mlflow_experiment.experiment_id],
            output_format="list"
        )

        if not runs:
            print(f"No runs found in MLflow experiment '{mlflow_experiment_name}'")
            return 0

        # Connect to DataVint database
        from datavint.experiment import ExperimentContext
        exp = ExperimentContext(datavint_exp_id, self.db_path)

        with exp:
            imported_count = 0

            for mlflow_run in runs:
                # Extract data from MLflow run
                params = mlflow_run.data.params
                metrics = {k: float(v) for k, v in mlflow_run.data.metrics.items()}
                tags = mlflow_run.data.tags

                # Get or create data commit
                data_commit_id = tags.get("datavint.data_commit_id")

                if not data_commit_id and import_data_commits:
                    # Create synthetic data commit from tags
                    import pandas as pd
                    import numpy as np

                    # Create empty DataFrame with metadata
                    row_count = int(tags.get("datavint.data_rows", 0))
                    col_count = int(tags.get("datavint.data_cols", 0))

                    if row_count > 0 and col_count > 0:
                        # Create minimal synthetic DataFrame for hash
                        df = pd.DataFrame(
                            np.zeros((min(row_count, 10), col_count))
                        )
                        data_commit_id = exp.log_data(
                            df,
                            message=tags.get("datavint.data_message", "Imported from MLflow")
                        )

                if not data_commit_id:
                    # Skip runs without data commit info
                    continue

                # Import run
                run_id = tags.get("datavint.run_id", f"M{imported_count}")
                sweep_id = tags.get("datavint.sweep_id")
                sweep_name = tags.get("datavint.sweep_name")
                best = tags.get("datavint.best") == "true"

                exp.log_run(
                    data_commit_id=data_commit_id,
                    metrics=metrics,
                    params=params,
                    message=mlflow_run.info.run_name or "Imported from MLflow",
                    run_id=run_id,
                    best=best,
                    sweep_id=int(sweep_id) if sweep_id else None,
                    sweep_name=sweep_name
                )

                imported_count += 1

        print(f"✅ Imported {imported_count} runs from MLflow to DataVint")
        return imported_count

    def compare_experiments(
        self,
        experiment_id: str,
        mlflow_experiment_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare DataVint and MLflow experiments.

        Shows which runs exist in each system.

        Args:
            experiment_id: DataVint experiment ID
            mlflow_experiment_name: MLflow experiment name (default: same as experiment_id)

        Returns:
            Comparison statistics

        Example:
            >>> sync = MLflowSync()
            >>> stats = sync.compare_experiments("test-05-14")
            >>> print(stats)
        """
        mlflow_exp_name = mlflow_experiment_name or experiment_id

        # Get DataVint runs
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM model_runs WHERE experiment_id = ?",
            (experiment_id,)
        )
        datavint_count = cursor.fetchone()[0]
        conn.close()

        # Get MLflow runs
        mlflow_experiment = mlflow.get_experiment_by_name(mlflow_exp_name)
        mlflow_count = 0
        if mlflow_experiment:
            runs = mlflow.search_runs(
                experiment_ids=[mlflow_experiment.experiment_id],
                output_format="list"
            )
            mlflow_count = len(runs)

        return {
            "experiment_id": experiment_id,
            "datavint_runs": datavint_count,
            "mlflow_runs": mlflow_count,
            "synced": datavint_count == mlflow_count,
            "mlflow_experiment_name": mlflow_exp_name
        }


def enable_mlflow_autolog(experiment_id: str):
    """
    Enable automatic MLflow logging for DataVint experiments.

    This wraps exp.log_run() to automatically sync to MLflow.

    Args:
        experiment_id: DataVint experiment ID

    Example:
        >>> from datavint.mlflow_integration import enable_mlflow_autolog
        >>> import datavint as dv
        >>>
        >>> enable_mlflow_autolog("my_experiment")
        >>>
        >>> with dv.experiment("my_experiment") as exp:
        ...     # This will automatically log to MLflow
        ...     exp.log_run(metrics={"accuracy": 0.92})
    """
    if not MLFLOW_AVAILABLE:
        raise ImportError("MLflow is not installed")

    mlflow.set_experiment(experiment_id)
    mlflow.autolog()

    print(f"✅ MLflow autolog enabled for experiment '{experiment_id}'")
    print(f"   All exp.log_run() calls will sync to MLflow")
