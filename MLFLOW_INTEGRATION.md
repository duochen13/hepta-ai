# MLflow Integration Guide

## Overview

DataVint now integrates seamlessly with MLflow, providing **unified experiment tracking** across both platforms:

- **DataVint**: Visual lineage tracking with bipartite graphs (data → model connections)
- **MLflow**: Metrics dashboard, parameter tuning, and run artifacts

## 🚀 Quick Start

### 1. Export DataVint Experiment to MLflow

```python
from datavint.mlflow_integration import MLflowSync

# Export existing experiment
sync = MLflowSync()
sync.export_to_mlflow("test-05-14")

# View in MLflow UI
# Open: http://localhost:5000
```

### 2. View in Both Systems

**DataVint (Bipartite Graph)**
```
http://localhost:5175/playground/test-05-14
```
- Visual lineage: data commits → model runs
- Sweep grouping
- Best model highlighting
- Interactive connections

**MLflow (Metrics Dashboard)**
```
http://localhost:5000
```
- Metric comparisons across runs
- Parameter tuning visualization
- Run artifacts and logs
- Model registry

## 📊 Features

### Exported to MLflow

When you export a DataVint experiment, the following are synced:

**Metrics**
- All metrics logged via `exp.log_run(metrics={...})`
- Example: accuracy, precision, recall, f1, loss, etc.

**Parameters**
- All parameters logged via `exp.log_run(params={...})`
- Example: learning_rate, max_depth, n_estimators, etc.

**Tags (Metadata)**
- `datavint.run_id`: DataVint model run ID (M0, M1, etc.)
- `datavint.experiment_id`: Experiment name
- `datavint.data_commit_id`: Which data version was used (D0, D1, etc.)
- `datavint.data_hash`: Content-based hash of the dataset
- `datavint.data_message`: Data commit description
- `datavint.data_rows`: Number of rows in dataset
- `datavint.data_cols`: Number of columns
- `datavint.sweep_id`: Hyperparameter sweep ID
- `datavint.sweep_name`: Sweep description
- `datavint.best`: Marked if this is a best model
- `datavint.timestamp`: When the run was logged

## 🔄 Bidirectional Sync

### Export: DataVint → MLflow

```python
from datavint.mlflow_integration import MLflowSync

sync = MLflowSync()

# Export specific experiment
run_mapping = sync.export_to_mlflow(
    experiment_id="test-05-14",
    mlflow_experiment_name="test-05-14"  # Optional: custom MLflow name
)

print(f"Exported {len(run_mapping)} runs")
# Returns: {'M0': 'mlflow_run_id_1', 'M1': 'mlflow_run_id_2', ...}
```

### Import: MLflow → DataVint

```python
from datavint.mlflow_integration import MLflowSync

sync = MLflowSync()

# Import MLflow experiment to DataVint
count = sync.import_from_mlflow(
    mlflow_experiment_name="my_mlflow_exp",
    datavint_experiment_id="imported_exp",  # Optional: custom DataVint name
    import_data_commits=True  # Create data commits from tags
)

print(f"Imported {count} runs")
```

### Compare Experiments

```python
from datavint.mlflow_integration import MLflowSync

sync = MLflowSync()

# Compare DataVint and MLflow
stats = sync.compare_experiments("test-05-14")

print(stats)
# Output:
# {
#     'experiment_id': 'test-05-14',
#     'datavint_runs': 9,
#     'mlflow_runs': 9,
#     'synced': True,
#     'mlflow_experiment_name': 'test-05-14'
# }
```

## 📝 Usage Examples

### Example 1: Track Experiment in Both Systems

```python
import datavint as dv
import pandas as pd
import numpy as np
from datavint.mlflow_integration import MLflowSync

# 1. Run your experiment in DataVint
with dv.experiment("my_experiment") as exp:
    # Log data version
    df = pd.DataFrame({'x': np.random.rand(100)})
    data_id = exp.log_data(df, message="training data v1")

    # Train and log runs
    for lr in [0.01, 0.1]:
        # ... train model ...
        metrics = {"accuracy": 0.92, "loss": 0.08}

        exp.log_run(
            metrics=metrics,
            params={"lr": lr},
            message=f"lr={lr}"
        )

# 2. Sync to MLflow
sync = MLflowSync()
sync.export_to_mlflow("my_experiment")

# 3. View in both UIs
# DataVint: http://localhost:5175/playground/my_experiment
# MLflow:   http://localhost:5000
```

### Example 2: Custom MLflow Tracking URI

```python
from datavint.mlflow_integration import MLflowSync

# Use remote MLflow server
sync = MLflowSync(
    mlflow_tracking_uri="http://mlflow-server:5000"
)

sync.export_to_mlflow("my_experiment")
```

### Example 3: Import Existing MLflow Experiments

```python
from datavint.mlflow_integration import MLflowSync

# Import historical MLflow experiments into DataVint
sync = MLflowSync()

# Import from MLflow
count = sync.import_from_mlflow(
    mlflow_experiment_name="legacy_experiment",
    datavint_experiment_id="legacy_imported"
)

# Now view in DataVint bipartite graph
# http://localhost:5175/playground/legacy_imported
```

## 🎯 Use Cases

### 1. Team Collaboration

**Data Scientist A** uses DataVint for visual lineage:
```bash
# View data evolution and model lineage
http://localhost:5175/playground/team_project
```

**Data Scientist B** uses MLflow for metric analysis:
```bash
# Compare runs, analyze parameter impact
http://localhost:5000
```

Both see the **same experiment data**, synced automatically.

### 2. Model Registry

```python
# After finding best model in DataVint
sync = MLflowSync()
sync.export_to_mlflow("production_model")

# Register in MLflow Model Registry
import mlflow
mlflow.register_model(
    f"runs:/best_run_id/model",
    "ProductionChurnModel"
)
```

### 3. Audit Trail

DataVint + MLflow provides complete lineage:
- **DataVint**: Which data version was used
- **MLflow**: What parameters and code version
- **Combined**: Full reproducibility

## 🔧 Configuration

### Custom Database Paths

```python
from pathlib import Path
from datavint.mlflow_integration import MLflowSync

sync = MLflowSync(
    datavint_db=Path("/custom/path/metadata.db"),
    mlflow_tracking_uri="file:///custom/mlruns"
)
```

### MLflow Autolog (Experimental)

```python
from datavint.mlflow_integration import enable_mlflow_autolog
import datavint as dv

# Enable automatic MLflow logging
enable_mlflow_autolog("my_experiment")

with dv.experiment("my_experiment") as exp:
    # All log_run() calls auto-sync to MLflow
    exp.log_run(metrics={"accuracy": 0.92})
```

## 🌐 Viewing Experiments

### DataVint Bipartite Graph

```bash
# Start servers
cd server && python3 -m uvicorn server.api.main:app --port 8080 --reload &
cd client && npm run dev &

# View experiment
open http://localhost:5175/playground/{experiment_id}
```

**Shows:**
- Data commits (left column)
- Model runs (right column, grouped by sweep)
- Connections (Bezier curves)
- Best models (stars)
- Hover interactions

### MLflow UI

```bash
# Start MLflow UI
python3 -m mlflow ui --port 5000

# View experiments
open http://localhost:5000
```

**Shows:**
- All runs in table format
- Metric comparison charts
- Parameter parallel coordinates
- Run artifacts
- Model registry

## 📦 Installation

MLflow integration is included in DataVint. Ensure MLflow is installed:

```bash
pip install mlflow
```

Or add to requirements.txt:
```
mlflow>=2.0.0
```

## 🧪 Demo Script

Run the included demo:

```bash
python3 examples/mlflow_sync_demo.py
```

This will:
1. Export `test-05-14` experiment to MLflow
2. Show comparison statistics
3. Provide links to both UIs

## 🔍 Troubleshooting

### MLflow UI not starting

```bash
# Check if port 5000 is in use
lsof -i :5000

# Use different port
python3 -m mlflow ui --port 5001
```

### Import/Export errors

```python
# Check if experiment exists
from datavint.mlflow_integration import MLflowSync

sync = MLflowSync()
stats = sync.compare_experiments("my_experiment")
print(stats)
```

### Database not found

```bash
# Verify DataVint database exists
ls -la ~/.datavint/metadata.db

# Or run an experiment first
python3 examples/experiment_lineage_demo.py
```

## 📚 API Reference

### MLflowSync Class

```python
class MLflowSync:
    def __init__(
        self,
        datavint_db: Optional[Path] = None,
        mlflow_tracking_uri: Optional[str] = None
    )

    def export_to_mlflow(
        self,
        experiment_id: str,
        mlflow_experiment_name: Optional[str] = None
    ) -> Dict[str, str]

    def import_from_mlflow(
        self,
        mlflow_experiment_name: str,
        datavint_experiment_id: Optional[str] = None,
        import_data_commits: bool = True
    ) -> int

    def compare_experiments(
        self,
        experiment_id: str,
        mlflow_experiment_name: Optional[str] = None
    ) -> Dict[str, Any]
```

### Helper Functions

```python
def enable_mlflow_autolog(experiment_id: str) -> None
```

## 🎨 Architecture

```
┌─────────────────────┐
│  Python Script      │  datavint.experiment()
└──────────┬──────────┘
           │
           ├─────────────────┐
           │                 │
           ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│  DataVint DB     │  │  MLflow Tracking │
│  metadata.db     │◄─┤  (mlruns/)       │
└──────────┬───────┘  └────────┬─────────┘
           │                   │
           │                   │
           ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│  Bipartite Graph │  │  MLflow UI       │
│  (Vue Frontend)  │  │  (Flask)         │
└──────────────────┘  └──────────────────┘
   localhost:5175        localhost:5000
```

## 🚀 Next Steps

1. **Run the demo**: `python3 examples/mlflow_sync_demo.py`
2. **Export your experiments**: `sync.export_to_mlflow("your_exp")`
3. **View in both UIs**: Compare DataVint lineage with MLflow metrics
4. **Share with team**: Unified tracking across tools

## 📖 Related Documentation

- [EXPERIMENT_LINEAGE_SETUP.md](./EXPERIMENT_LINEAGE_SETUP.md) - Complete experiment tracking setup
- [QUICK_START.md](./QUICK_START.md) - 3-step quick start guide
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html) - Official MLflow docs
