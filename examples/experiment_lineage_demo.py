"""
DataVint Experiment Tracking with Lineage Visualization Demo

This script demonstrates:
1. Data versioning with content-based hashing
2. Model run tracking with metrics and hyperparameters
3. Lineage visualization in bipartite graph

After running this script, view the lineage at:
http://localhost:5173/experiments/titanic_survival
"""

import pandas as pd
import numpy as np
import datavint as dv
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score
from pathlib import Path
import sqlite3


def main():
    print("🔬 DataVint Experiment Tracking & Lineage Demo\n")

    # ========================================================================
    # Step 1: Load Titanic Dataset
    # ========================================================================
    print("📊 Loading Titanic dataset...")
    df = pd.read_csv("raw_data/titanic/titanic.csv")

    print(f"   Dataset shape: {df.shape}")
    print(f"   Survival rate: {df['Survived'].mean():.2%}\n")

    # ========================================================================
    # Step 2: Track Data Versions and Model Runs
    # ========================================================================
    with dv.experiment("titanic_survival") as exp:

        # === Data Version 1: Raw data with missing values ===
        print("=" * 70)
        print("DATA VERSION D0: Raw data with missing values")
        print("=" * 70)
        data_v0_id = exp.log_data(df, message="raw titanic data")
        print(f"✓ Logged data commit: {data_v0_id}")
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        print(f"  Missing Age: {df['Age'].isna().sum()} rows")
        print(f"  Missing Fare: {df['Fare'].isna().sum()} rows\n")

        # === Sweep 1: Different max_depth values on D0 ===
        print("🌲 Sweep 1: Testing different max_depth values on D0\n")

        # Select numeric features for training
        features = ['Pclass', 'Age', 'SibSp', 'Parch', 'Fare']
        df_numeric = df[features + ['Survived']].dropna()

        X = df_numeric[features]
        y = df_numeric['Survived']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        for depth in [3, 5, 10]:
            # Train model
            model = XGBClassifier(
                max_depth=depth,
                n_estimators=10,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)

            # Log run
            run_id = exp.log_run(
                data_commit_id=data_v0_id,
                metrics={
                    "accuracy": round(accuracy, 3),
                    "precision": round(precision, 3)
                },
                params={"max_depth": depth, "n_estimators": 10, "learning_rate": 0.1},
                message=f"max_depth={depth}",
                sweep_id=1,
                sweep_name="Max Depth (from D0)"
            )
            print(f"  {run_id}: depth={depth:2d} → "
                  f"accuracy={accuracy:.3f}, precision={precision:.3f}")

        print()

        # === Data Version 2: Imputed missing values ===
        print("=" * 70)
        print("DATA VERSION D1: Imputed missing values")
        print("=" * 70)
        df_imputed = df.copy()
        df_imputed['Age'].fillna(df_imputed['Age'].median(), inplace=True)
        df_imputed['Fare'].fillna(df_imputed['Fare'].median(), inplace=True)

        data_v1_id = exp.log_data(df_imputed, message="age/fare imputed")
        print(f"✓ Logged data commit: {data_v1_id}")
        print(f"  Rows: {len(df_imputed)}, Columns: {len(df_imputed.columns)}")
        print(f"  Missing Age: {df_imputed['Age'].isna().sum()} rows (was {df['Age'].isna().sum()})")
        print(f"  Missing Fare: {df_imputed['Fare'].isna().sum()} rows (was {df['Fare'].isna().sum()})\n")

        # === Sweep 2: Different learning rates on D1 ===
        print("🌲 Sweep 2: Testing different learning rates on D1\n")

        X_v1 = df_imputed[features]
        y_v1 = df_imputed['Survived']
        X_train_v1, X_test_v1, y_train_v1, y_test_v1 = train_test_split(
            X_v1, y_v1, test_size=0.2, random_state=42
        )

        best_accuracy = 0
        best_run_id = None

        for lr in [0.01, 0.1, 0.3]:
            # Train model
            model = XGBClassifier(
                max_depth=5,
                n_estimators=50,
                learning_rate=lr,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train_v1, y_train_v1)

            # Evaluate
            y_pred = model.predict(X_test_v1)
            accuracy = accuracy_score(y_test_v1, y_pred)
            precision = precision_score(y_test_v1, y_pred)

            # Log run
            is_best = accuracy > best_accuracy
            run_id = exp.log_run(
                data_commit_id=data_v1_id,
                metrics={
                    "accuracy": round(accuracy, 3),
                    "precision": round(precision, 3)
                },
                params={"max_depth": 5, "n_estimators": 50, "learning_rate": lr},
                message=f"learning_rate={lr}",
                sweep_id=2,
                sweep_name="Learning Rate (from D1, depth=5)",
                best=is_best
            )

            status = "⭐ BEST" if is_best else ""
            print(f"  {run_id}: lr={lr:0.2f} → "
                  f"accuracy={accuracy:.3f}, precision={precision:.3f} {status}")

            if is_best:
                best_accuracy = accuracy
                best_run_id = run_id

    print()
    print("=" * 70)
    print("✅ Experiment tracking complete!")
    print("=" * 70)
    print(f"📁 Metadata stored in: ~/.datavint/metadata.db")
    print(f"🏆 Best model: {best_run_id} (accuracy={best_accuracy:.3f})\n")

    # ========================================================================
    # Step 3: Display Lineage Summary
    # ========================================================================
    print_lineage_summary()

    # ========================================================================
    # Step 4: Instructions for Visualization
    # ========================================================================
    print("\n" + "=" * 70)
    print("📊 VIEW LINEAGE IN BIPARTITE GRAPH")
    print("=" * 70)
    print("\n1. Start the server (if not running):")
    print("   cd server && python main.py")
    print("\n2. Start the frontend (if not running):")
    print("   cd client && npm run dev")
    print("\n3. Open in browser:")
    print("   http://localhost:5175/playground/titanic_survival")
    print("\n   You'll see:")
    print("   • Top: Data commits (D0, D1)")
    print("   • Bottom: Model runs (M0-M5) grouped by sweep")
    print("   • Lines: Connections showing data → model lineage")
    print("   • Hover: Highlight lineage relationships")
    print()


def print_lineage_summary():
    """Print a summary of the tracked lineage from the database."""
    db_path = Path.home() / ".datavint" / "metadata.db"

    if not db_path.exists():
        print("⚠️  Database not found")
        return

    conn = sqlite3.connect(str(db_path))

    print("\n📊 LINEAGE SUMMARY (from database)")
    print("=" * 70)

    # Data commits
    print("\nData Commits:")
    commits_df = pd.read_sql_query("""
        SELECT id, message, row_count, column_count, hash
        FROM data_commits
        WHERE experiment_id = 'titanic_survival'
        ORDER BY timestamp
    """, conn)

    for _, row in commits_df.iterrows():
        print(f"  {row['id']}: {row['message']}")
        print(f"      {row['row_count']} rows × {row['column_count']} cols, "
              f"hash={row['hash'][:7]}")

    # Model runs
    print("\nModel Runs:")
    runs_df = pd.read_sql_query("""
        SELECT id, data_commit_id, message, metrics, sweep_id, sweep_name, best
        FROM model_runs
        WHERE experiment_id = 'titanic_survival'
        ORDER BY timestamp
    """, conn)

    current_sweep = None
    for _, row in runs_df.iterrows():
        # Print sweep header
        if row['sweep_id'] != current_sweep:
            current_sweep = row['sweep_id']
            print(f"\n  Sweep {row['sweep_id']}: {row['sweep_name']}")

        # Parse metrics
        import json
        metrics = json.loads(row['metrics'])
        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())

        best_marker = "⭐" if row['best'] else " "
        print(f"    {best_marker} {row['id']} (from {row['data_commit_id']}): "
              f"{row['message']} → {metrics_str}")

    conn.close()


if __name__ == "__main__":
    main()
