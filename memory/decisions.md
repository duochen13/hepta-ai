# Architectural Decisions

## [2026-05-11] Sequential Hyperparameter Tuning: Local Optima Risk (Future Consideration)

**Observation:** Mock data shows sequential sweeps (Sweep 1: lr → pick best → Sweep 2: sample_rate with fixed lr). This pattern can miss global optimum.

**The Problem:**
```
Sweep 1: Test lr=[0.001, 0.005, 0.01, 0.02] with sample_rate=0.5 (default)
         Pick best: lr=0.005 (NE=0.712 at sample_rate=0.5)

Sweep 2: Test sample_rate=[0.4, 0.6, 0.8] with lr=0.005 (fixed)
         Pick best: sample_rate=0.6 (NE=0.701 at lr=0.005)

Issue: Best lr at sample_rate=0.5 may not be best lr at sample_rate=0.6
Maybe: lr=0.008, sample_rate=0.6 → NE=0.690 (better, but never tested!)
```

**Why Hyperparameters Interact:**
The optimal value of parameter A depends on the value of parameter B. Sequential optimization (greedy) can get stuck in local optima.

**Counter-Arguments (Why Sequential is Still Valid):**
1. **Computational Cost:** Grid search is O(n^d). Example: 4 lr × 4 sample_rate × 3 batch_size = 48 runs vs ~11 sequential runs
2. **Practical Effectiveness:** Sequential often gets "good enough" results (maybe 98% of global optimum)
3. **Domain Knowledge:** ML engineers know which params interact strongly (joint optimize) vs weakly (sequential optimize)
4. **Diminishing Returns:** Global optimum may only improve by 0.5% but cost 5x compute

**Alternatives:**
- **Random Search:** Sample (lr, sample_rate) pairs randomly
- **Bayesian Optimization:** Model hyperparameter response surface, recommend next trial
- **Grid Search on Subsets:** Do 2D grid on strongly interacting params only
- **User Education:** Warn about interaction risks without forcing an approach

**DataVint Feature Idea (v2.0 - Not v1.0):**
Don't prescribe optimization strategy, but **warn users** when detecting sequential patterns:

```
⚠️ Sequential Sweep Pattern Detected

You're optimizing sample_rate with lr fixed at 0.005 (best from Sweep 1).

Risk: The best lr may differ at different sample_rates due to parameter interaction.

Suggestions:
• Grid search: Test lr × sample_rate combinations (more expensive)
• Random search: Sample parameter pairs randomly
• Continue: Proceed with sequential optimization (faster, usually good enough)

Learn more: [link to doc about hyperparameter interaction]
```

**Decision for v1.0:**
- ✓ Keep mock data showing sequential pattern (realistic, common in practice)
- ✓ Don't implement warning yet (need real user feedback first)
- ✓ Document this as v2.0 consideration
- ✓ Focus v1.0 on visualization and lineage tracking, not optimization advice
- ⚠️ Don't make users feel DataVint is opinionated about "the right way" to tune

**Challenge to This Concern:**
User's intuition is correct about the risk, but:
1. Most ML engineers already know this trade-off
2. Sequential is industry standard for initial exploration
3. Warning might be noise for experienced users
4. Better to provide tools than prescribe methods

**Status:** Documented for future consideration, not blocking v1.0

**Files:**
- `server/api/routes/experiments_mock.py` - Mock data shows sequential sweeps
- Future: Sweep pattern detection logic

## Session Management

- Using gstack `/context-save` and `/context-restore` for session continuity
- Checkpoint mode: explicit (not continuous auto-commits)
- Skill routing: not yet configured in CLAUDE.md

## Data Validation Architecture

- Following TFDV (TensorFlow Data Validation) functional API design
- Schema detector split into modular components:
  - Type detection
  - Range detection
  - Separate orchestration layer

## Enriched Statistical Detectors (v0.2)

**Decision Date**: 2026-05-08

**Context**: Issue #9 requested advanced statistical metrics inspired by Amazon Deequ and Great Expectations. Needed to enrich data profiling beyond basic quality checks.

**Decision**: Implemented 6 new detectors focusing on statistical distribution and information theory:
1. **ClassImbalanceDetector** - Label distribution analysis (requires `label_col` parameter)
2. **CompletenessDetector** - Missing value analysis (completeness = 1 - null_rate)
3. **CardinalityDetector** - High cardinality detection for categorical features
4. **EntropyDetector** - Information content analysis using Shannon entropy
5. **UniquenessDetector** - Duplicate value detection (unique = appears exactly once)
6. **DistinctnessDetector** - Distinct value analysis (distinct = any unique value)

**Rationale**:
- Prioritized single-column metrics over multi-column (correlation, mutual information) for v0.2
- Deferred probabilistic algorithms (HyperLogLog) to future releases
- Focused on metrics most valuable for recommendation systems (target domain)
- Maintained two-phase architecture: compute statistics once, run detectors on cached results

**Integration Points**:
- Python API: `vint.profile(df, label_col='label')`
- Chatbox: Natural language queries via LLM code generation
- Claude Skills: 6 new skills in `.claude/skills/` with rich formatting
- Skill routing: Automatic invocation via CLAUDE.md rules

**Deferred**:
- Multi-column metrics (MutualInformation, Correlation)
- Probabilistic algorithms (ApproxCountDistinct, ApproxQuantiles)
- Constraint-based metrics (Compliance, PatternMatch)

## Experiment Versioning Architecture (2026-05-11)

**Decision Date**: 2026-05-11

**Context**: Need to track ML experiment lineage including data versions and model runs for recommendation systems.

**Decision**: Implemented experiment tracking with content-based data versioning:

**Components**:
1. **SDK**: `datavint.experiment()` context manager with SQLite storage
2. **Backend**: FastAPI routes at `/api/experiments/:id/lineage`
3. **Frontend**: Bipartite graph dashboard (Vue 3 + SVG)

**Key Architectural Choices**:

### 1. Content-Based Data Versioning
- **Decision**: SHA256 hash of DataFrame content (sorted columns)
- **Rationale**:
  - Automatic deduplication (same data → same ID)
  - Detects data changes automatically
  - No manual version management needed
- **Implementation**: First 7 chars of SHA256 (git-style short hash)

### 2. SQLite Metadata Store
- **Decision**: Local SQLite database at `~/.datavint/metadata.db`
- **Rationale**:
  - Zero-config persistence
  - Easy to query with SQL
  - Portable across environments
  - No server dependencies
- **Schema**:
  - `data_commits`: id, experiment_id, hash, message, row_count, timestamp
  - `model_runs`: id, experiment_id, data_commit_id, metrics, params, best, sweep_id

### 3. Bipartite Graph Visualization
- **Decision**: Two-column layout with SVG Bezier curves
- **Rationale**:
  - Clear data → model lineage flow
  - Sweep clustering shows hyperparameter groups
  - Hover interactions reveal connections
- **Colors**:
  - Default lines: Light green (--accent-light-green)
  - Active: Purple (--accent-purple)
  - Best model: Bright green (--accent-green)

### 4. Winner Selection Logic
- **Decision**: Lowest NE (Normalized Entropy) = best performance
- **Rationale**: User's recommendation system domain uses this metric
- **Implementation**:
  - Overall best: Lowest NE across all runs
  - Sweep winner: Lowest NE within that sweep

### 5. Mock Data Strategy
- **Decision**: Frontend works with mock data, falls back gracefully
- **Rationale**:
  - Frontend development unblocked by backend delays
  - Easy to develop/test UI in isolation
  - Seamless transition when backend ready
- **Implementation**: try/catch with loadMockData() fallback

**Integration Points**:
- SDK: `datavint.experiment()` context manager
- API: `GET /api/experiments/:id/lineage`
- Dashboard: http://localhost:5173/experiments/:id
- Demo: `python3 examples/experiment_tracking_demo.py`

**Deferred to Future**:
- MLflow integration (read local mlflow.db)
- Real-time monitoring dashboard
- Automatic model comparison reports
- Slack/PagerDuty alerts for quality regressions
