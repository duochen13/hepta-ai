"""
MLflow Integration Demo

Demonstrates how to sync DataVint experiments with MLflow:
1. Export existing DataVint experiment to MLflow
2. View runs in MLflow UI
3. Compare both systems
4. Import MLflow runs back to DataVint (optional)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datavint.mlflow_integration import MLflowSync


def main():
    print("🔄 MLflow Integration Demo\n")

    # ========================================================================
    # Step 1: Export DataVint experiment to MLflow
    # ========================================================================
    print("=" * 70)
    print("STEP 1: Export DataVint → MLflow")
    print("=" * 70)

    sync = MLflowSync()

    # Export the test-05-14 experiment we created earlier
    try:
        print("\n📤 Exporting 'test-05-14' experiment to MLflow...")
        run_mapping = sync.export_to_mlflow("test-05-14")

        print(f"\n✅ Export complete!")
        print(f"   DataVint runs → MLflow runs:")
        for dv_run_id, mlflow_run_id in run_mapping.items():
            print(f"   {dv_run_id} → {mlflow_run_id[:8]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # ========================================================================
    # Step 2: Compare experiments
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 2: Compare DataVint ↔ MLflow")
    print("=" * 70)

    stats = sync.compare_experiments("test-05-14")

    print(f"\n📊 Comparison:")
    print(f"   DataVint runs: {stats['datavint_runs']}")
    print(f"   MLflow runs:   {stats['mlflow_runs']}")
    print(f"   Synced:        {'✅ Yes' if stats['synced'] else '❌ No'}")

    # ========================================================================
    # Step 3: View in MLflow UI
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 3: View in MLflow UI")
    print("=" * 70)

    print("\n🌐 To view your experiments in MLflow UI:")
    print("   1. Start MLflow UI:")
    print("      mlflow ui")
    print()
    print("   2. Open in browser:")
    print("      http://localhost:5000")
    print()
    print("   3. Navigate to experiment:")
    print("      test-05-14")
    print()
    print("   You'll see:")
    print("   • All 9 model runs (M0-M8)")
    print("   • Metrics: accuracy, precision, recall, f1")
    print("   • Parameters: learning_rate, max_depth, n_estimators")
    print("   • Tags: data_commit_id, sweep_id, best models marked")
    print("   • Data lineage information")

    # ========================================================================
    # Step 4: Unified tracking
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 4: Unified Tracking")
    print("=" * 70)

    print("\n📝 Now you have unified tracking:")
    print()
    print("   DataVint (Bipartite Graph):")
    print("   └─ http://localhost:5175/playground/test-05-14")
    print("      • Visual lineage: data → model connections")
    print("      • Sweep grouping")
    print("      • Best model highlighting")
    print()
    print("   MLflow (Metrics Dashboard):")
    print("   └─ http://localhost:5000/#/experiments/.../runs")
    print("      • Metric comparisons")
    print("      • Parameter tuning visualization")
    print("      • Run artifacts")

    # ========================================================================
    # Optional: Import from MLflow
    # ========================================================================
    print("\n" + "=" * 70)
    print("OPTIONAL: Import MLflow → DataVint")
    print("=" * 70)

    print("\n📥 To import MLflow experiments into DataVint:")
    print()
    print("   >>> from datavint.mlflow_integration import MLflowSync")
    print("   >>> sync = MLflowSync()")
    print("   >>> sync.import_from_mlflow('my_mlflow_experiment', 'my_datavint_exp')")
    print()
    print("   This creates:")
    print("   • Data commits from MLflow tags")
    print("   • Model runs with metrics and params")
    print("   • Viewable in bipartite graph")

    print("\n" + "=" * 70)
    print("✅ MLflow Integration Demo Complete")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
