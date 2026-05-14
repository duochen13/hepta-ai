"""
DataVint API - CLI Experiments Integration

Provides endpoints for retrieving CLI experiment tracking data:
- Experiment fingerprints (datasets checked)
- Experiment outcomes (logged results)
- Cost estimation and ROI analysis
- Integration with bipartite graph visualization

This bridges the CLI database (experiments.db) with the frontend visualization.
"""

from fastapi import APIRouter, HTTPException, Path
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path as PathLib
import sqlite3
import json

router = APIRouter()

# Default CLI database path
DEFAULT_CLI_DB = PathLib.home() / ".datavint" / "experiments.db"


def _get_cli_db_connection(db_path: Optional[PathLib] = None):
    """Get connection to CLI database."""
    path = db_path or DEFAULT_CLI_DB
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"CLI database not found at {path}. Run `datavint check` first."
        )
    return sqlite3.connect(str(path))


def _format_metrics(metrics_json: Optional[str]) -> Dict:
    """
    Format metrics from JSON string to frontend format.

    CLI format: {"accuracy": 0.92, "loss": 0.08}
    Frontend format: {"accuracy": {"value": 0.92, "quality": "good"}, ...}
    """
    if not metrics_json:
        return {}

    try:
        metrics = json.loads(metrics_json)
        formatted = {}

        for key, value in metrics.items():
            # Determine quality based on metric name and value
            quality = "neutral"
            if isinstance(value, (int, float)):
                # For accuracy-like metrics (higher is better)
                if key.lower() in ['accuracy', 'precision', 'recall', 'f1', 'auc']:
                    if value >= 0.90:
                        quality = "good"
                    elif value >= 0.75:
                        quality = "ok"
                    else:
                        quality = "bad"
                # For loss-like metrics (lower is better)
                elif key.lower() in ['loss', 'error', 'mse', 'rmse', 'ne']:
                    if value <= 0.1:
                        quality = "good"
                    elif value <= 0.3:
                        quality = "ok"
                    else:
                        quality = "bad"

            formatted[key] = {
                "value": value if isinstance(value, (int, float)) else str(value),
                "quality": quality
            }

        return formatted
    except (json.JSONDecodeError, Exception):
        return {}


@router.get("/cli-experiments/list")
async def list_cli_experiments(
    limit: int = 50,
    status_filter: Optional[str] = None
):
    """
    List all experiments tracked via CLI.

    Returns fingerprints with their latest outcomes for overview display.

    Args:
        limit: Maximum number of experiments to return (default 50)
        status_filter: Optional filter by status (success/failure/oom/timeout/cancelled)

    Returns:
        List of experiments with fingerprints and latest outcomes
    """
    conn = _get_cli_db_connection()
    cursor = conn.cursor()

    # Query experiments with their latest outcome
    query = """
        SELECT
            f.id,
            f.fingerprint,
            f.dataset_path,
            f.row_count,
            f.column_count,
            f.first_seen,
            f.last_seen,
            f.run_count,
            r.status,
            r.metrics,
            r.duration_hours,
            r.gpu_count,
            r.cost_usd,
            r.notes,
            r.timestamp as outcome_timestamp
        FROM experiment_fingerprints f
        LEFT JOIN (
            SELECT fingerprint_id, status, metrics, duration_hours, gpu_count, cost_usd, notes, timestamp,
                   ROW_NUMBER() OVER (PARTITION BY fingerprint_id ORDER BY timestamp DESC) as rn
            FROM experiment_runs
        ) r ON f.id = r.fingerprint_id AND r.rn = 1
    """

    if status_filter:
        query += " WHERE r.status = ?"
        cursor.execute(query + " ORDER BY f.last_seen DESC LIMIT ?", (status_filter, limit))
    else:
        cursor.execute(query + " ORDER BY f.last_seen DESC LIMIT ?", (limit,))

    rows = cursor.fetchall()
    conn.close()

    experiments = []
    for row in rows:
        exp = {
            "id": row[0],
            "fingerprint": row[1],
            "datasetPath": row[2],
            "rowCount": row[3],
            "columnCount": row[4],
            "firstSeen": row[5],
            "lastSeen": row[6],
            "runCount": row[7],
            "outcome": None
        }

        # Add outcome if exists
        if row[8]:  # status
            exp["outcome"] = {
                "status": row[8],
                "metrics": _format_metrics(row[9]),
                "durationHours": row[10],
                "gpuCount": row[11],
                "costUsd": row[12],
                "notes": row[13],
                "timestamp": row[14]
            }

        experiments.append(exp)

    return {
        "experiments": experiments,
        "total": len(experiments)
    }


@router.get("/cli-experiments/{fingerprint}/lineage")
async def get_cli_experiment_lineage(
    fingerprint: str = Path(..., description="Experiment fingerprint (16-char hash)")
):
    """
    Get experiment lineage data from CLI database in bipartite graph format.

    Transforms CLI data into the format expected by the frontend LineageGraph component:
    - dataCommits: Dataset fingerprints (each fingerprint is a "data version")
    - modelRuns: Experiment outcomes logged via log-result
    - connections: Maps fingerprints to their runs

    This allows visualizing:
    - Same dataset used multiple times (runs on same fingerprint)
    - Similar datasets (via similarity scores)
    - Outcomes across different runs

    Args:
        fingerprint: The 16-character dataset fingerprint

    Returns:
        Dict with dataCommits, modelRuns, connections for bipartite graph
    """
    conn = _get_cli_db_connection()
    cursor = conn.cursor()

    # Get the target fingerprint
    cursor.execute("""
        SELECT id, fingerprint, dataset_path, row_count, column_count,
               first_seen, last_seen, run_count, features
        FROM experiment_fingerprints
        WHERE fingerprint = ?
    """, (fingerprint,))

    target_row = cursor.fetchone()
    if not target_row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Fingerprint '{fingerprint}' not found in CLI database"
        )

    # Parse target data
    target_id = target_row[0]
    target_features = json.loads(target_row[8]) if target_row[8] else None

    # Get all runs for this fingerprint
    cursor.execute("""
        SELECT id, status, metrics, duration_hours, gpu_count, cost_usd, notes, timestamp
        FROM experiment_runs
        WHERE fingerprint_id = ?
        ORDER BY timestamp ASC
    """, (target_id,))

    runs = cursor.fetchall()

    # Get similar fingerprints (if features available)
    similar_fingerprints = []
    if target_features:
        from datavint.similarity import compute_similarity

        cursor.execute("""
            SELECT id, fingerprint, dataset_path, row_count, column_count,
                   first_seen, last_seen, run_count, features
            FROM experiment_fingerprints
            WHERE fingerprint != ? AND features IS NOT NULL
        """, (fingerprint,))

        all_fingerprints = cursor.fetchall()

        for row in all_fingerprints:
            try:
                candidate_features = json.loads(row[8])
                similarity = compute_similarity(target_features, candidate_features)

                if similarity >= 0.90:  # 90% threshold for visualization
                    similar_fingerprints.append((row, similarity))
            except (json.JSONDecodeError, Exception):
                continue

        # Sort by similarity (descending) and limit to top 3
        similar_fingerprints.sort(key=lambda x: x[1], reverse=True)
        similar_fingerprints = similar_fingerprints[:3]

    conn.close()

    # Transform to frontend format
    data_commits = []
    model_runs = []
    connections = {}

    # Add target fingerprint as data commit
    target_commit_id = f"D-{fingerprint[:8]}"
    data_commits.append({
        "id": target_commit_id,
        "message": PathLib(target_row[2]).name,  # Use filename as message
        "hash": target_row[1][:8],  # Short hash
        "rowCount": target_row[3],
        "timestamp": target_row[5],  # first_seen
    })

    # Add runs as model runs
    connections[target_commit_id] = []

    for i, run in enumerate(runs):
        run_id = f"M-{fingerprint[:4]}-{i+1}"
        status_icon = "✅" if run[1] == "success" else "❌"

        model_runs.append({
            "id": run_id,
            "dataCommitId": target_commit_id,
            "message": f"{status_icon} {run[1]}" + (f": {run[6][:30]}..." if run[6] else ""),
            "metrics": _format_metrics(run[2]),
            "timestamp": run[7],
            "best": i == len(runs) - 1 and run[1] == "success",  # Latest success is "best"
        })

        connections[target_commit_id].append(run_id)

    # Add similar fingerprints as additional data commits
    for similar_row, similarity in similar_fingerprints:
        similar_fp = similar_row[1]
        commit_id = f"D-{similar_fp[:8]}"

        data_commits.append({
            "id": commit_id,
            "message": f"{PathLib(similar_row[2]).name} ({similarity*100:.1f}% similar)",
            "hash": similar_fp[:8],
            "rowCount": similar_row[3],
            "timestamp": similar_row[5],
        })

        # Get runs for similar fingerprint
        cursor = _get_cli_db_connection().cursor()
        cursor.execute("""
            SELECT id, status, metrics, timestamp
            FROM experiment_runs
            WHERE fingerprint_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (similar_row[0],))

        similar_run = cursor.fetchone()
        if similar_run:
            run_id = f"M-{similar_fp[:4]}-1"
            status_icon = "✅" if similar_run[1] == "success" else "❌"

            model_runs.append({
                "id": run_id,
                "dataCommitId": commit_id,
                "message": f"{status_icon} {similar_run[1]} (similar dataset)",
                "metrics": _format_metrics(similar_run[2]),
                "timestamp": similar_run[3],
            })

            connections[commit_id] = [run_id]

    return {
        "experimentId": fingerprint,
        "dataCommits": data_commits,
        "modelRuns": model_runs,
        "connections": connections
    }


@router.get("/cli-experiments/stats")
async def get_cli_experiments_stats():
    """
    Get aggregate statistics about CLI-tracked experiments.

    Returns:
        Dict with counts, success rates, total cost, etc.
    """
    conn = _get_cli_db_connection()
    cursor = conn.cursor()

    # Count total fingerprints
    cursor.execute("SELECT COUNT(*) FROM experiment_fingerprints")
    total_fingerprints = cursor.fetchone()[0]

    # Count total runs
    cursor.execute("SELECT COUNT(*) FROM experiment_runs")
    total_runs = cursor.fetchone()[0]

    # Count by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM experiment_runs
        WHERE status IS NOT NULL
        GROUP BY status
    """)
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Sum total cost
    cursor.execute("SELECT SUM(cost_usd) FROM experiment_runs WHERE cost_usd IS NOT NULL")
    total_cost = cursor.fetchone()[0] or 0.0

    # Average duration
    cursor.execute("""
        SELECT AVG(duration_hours)
        FROM experiment_runs
        WHERE duration_hours IS NOT NULL
    """)
    avg_duration = cursor.fetchone()[0] or 0.0

    conn.close()

    return {
        "totalFingerprints": total_fingerprints,
        "totalRuns": total_runs,
        "statusCounts": status_counts,
        "totalCostUsd": round(total_cost, 2),
        "avgDurationHours": round(avg_duration, 2),
        "successRate": round(status_counts.get("success", 0) / max(total_runs, 1) * 100, 1) if total_runs > 0 else 0
    }
