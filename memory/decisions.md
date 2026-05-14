# Architectural Decisions

## [2026-05-14] Horizontal Graph Layout with Consistent Purple Borders

**Decision Date**: 2026-05-14

**Context**: User feedback on bipartite graph visualization requested:
1. Equal sizing between data commits and model runs
2. Consistent border styling across all nodes
3. Metrics hidden by default to reduce clutter
4. Removal of "best model" highlighting

**Decision**: Redesigned graph with horizontal data evolution and unified purple borders.

**Key Changes**:

### 1. Fixed Node Dimensions
**Decision**: All nodes (data commits and model runs) are 280px × 120px
**Rationale**:
- Visual consistency prevents confusion about node importance
- Easier to scan horizontally when all nodes align
- Fixed height prevents layout shifting when metrics appear/disappear
- `box-sizing: border-box` ensures padding doesn't affect dimensions
- `overflow: hidden` prevents content from breaking layout

### 2. Unified Purple Borders
**Decision**: `3px solid rgba(139, 92, 246, 0.3)` for all nodes (data commits and model runs)
**Previous**: Different colors - purple for data commits, green for model runs
**Rationale**:
- Emphasizes graph structure over node type
- Purple is DataVint's brand color
- Thicker border (3px) makes nodes more prominent
- 30% opacity prevents overwhelming the content
- On hover: increases to 60% opacity for feedback

**Why Not Green for Models?**
- Green previously suggested "success" but not all model runs succeed
- Creates hierarchy that doesn't reflect actual importance
- Confusing when both types are equally important in lineage

### 3. Hover-Based Metrics Display
**Decision**: Hide metrics grid by default, show on hover
**Implementation**:
```css
.metrics { display: none; }
.model-node:hover .metrics { display: grid; }
```
**Rationale**:
- Reduces visual clutter (default view shows only hyperparameters)
- Preserves information access (hover to reveal)
- User can scan many model runs quickly (not distracted by metrics)
- Metrics become "details on demand" not "always visible"

**User Workflow**:
1. Scan model runs to see hyperparameter variations
2. Hover on interesting config to see performance metrics
3. Compare metrics sequentially by hovering

### 4. Removed Best Model Highlighting
**Decision**: No special borders, badges, or colors for "best" model runs
**Previous**: Green border, "BEST" badge, orange for sweep winners
**Rationale**:
- Treats all experiments equally (exploratory mindset)
- Avoids creating artificial hierarchy
- "Best" is subjective (best NE ≠ best CTR ≠ best coverage)
- Users can identify winners from metrics themselves
- Cleaner, more professional appearance

**Why This Matters**:
- DataVint is about lineage tracking, not winner selection
- Users already know which model is best (they have MLflow for that)
- Highlighting creates bias (what if "best" depends on business context?)

### 5. Single Vertical Connection Line
**Decision**: One purple line from each data commit straight down to first model run
**Previous**: Individual lines to each connected model run (3 lines from D0 → M0/M1/M2)
**Rationale**:
- Reduces visual clutter (1 line vs N lines)
- Still shows connection (line extends to first model run area)
- Cleaner appearance aligns with simplified design
- Indicates "these models use this data" without drawing every link

**Implementation**:
```javascript
// Instead of: loop through all connected models, draw line to each
// Do: draw single line from data commit to first model run top
const firstModelTop = getNodePosition(connectedRuns[0], 'top')
lines.push({
  x1: dataBottom.x,
  y1: dataBottom.y,
  x2: dataBottom.x,  // Same x (vertical)
  y2: firstModelTop.y
})
```

### Design Philosophy Shift

**Before**: Graph communicates "which model won"
- Green borders highlight best runs
- Badges show sweep winners
- Metrics always visible
- Color-coded quality indicators

**After**: Graph communicates "experiment flow"
- All nodes equal visual weight
- Emphasizes timeline (data evolution, then models)
- Details on demand (hover to reveal)
- Consistent styling reduces cognitive load

**Files Changed**:
- `client/src/components/DataCommitNode.vue` - Fixed sizing, purple borders
- `client/src/components/ModelRunNode.vue` - Fixed sizing, purple borders, hover metrics, removed badges
- `client/src/components/LineageGraphHorizontal.vue` - Single vertical connection lines

**User Feedback Incorporated**:
- "D0 and M0 size should be equal" → Fixed 280×120 dimensions
- "Make borders consistent, light purple" → Unified 3px purple borders
- "Only show hyperparameters, metrics on hover" → Hover-based metrics
- "Don't highlight best model" → Removed badges and special styling
- "Only 1 purple line from D0" → Single vertical connection per data commit

**Status**: ✅ IMPLEMENTED (2026-05-14)

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

## Product Pivot: GPU Waste Control (2026-05-13)

**Decision Date**: 2026-05-13

**Context**: Customer validation (3 ML team leads) revealed broader problem than data quality. Customers said "data quality is one aspect of avoiding unnecessary GPU runs" and pushed toward GPU waste control.

**Decision**: Pivot from "data quality for rec systems" to "ML execution waste control layer"

**New Product**: Pre-execution CLI gate that prevents duplicate experiments before GPU allocation

**Rationale**:
- Validated with 3 customers (Physical.ai, Phia, startup)
- Direct quote: "We are spending too much on unknown-value experiments"
- Resource-constrained customers hitting GPU quota limits (not efficiency-optimizing)
- 20-30% GPU waste from duplicate experiments
- 1 customer committed: "Yes, I will try DataVint when you ship it"

**Design Docs**:
- Original: `wiki/changelog/2026-05-04-datavint-rec-systems-data-quality-sdk.md`
- Pivot: `wiki/changelog/2026-05-10-datavint-experiment-versioning-design.md`
- Final: `wiki/changelog/2026-05-13-datavint-gpu-waste-control-design.md`

## CEO Review: Selective Expansion (2026-05-13)

**Decision Date**: 2026-05-13
**Review Mode**: SELECTIVE EXPANSION
**Original Score**: 6.5/10 (good to build, not good to win)

**Context**: /plan-ceo-review challenged original 8-week MVP scope as too narrow to create defensible moat.

**Critical Gaps Identified**:
1. Exact duplicates only = one-time value (no compounding value)
2. Moat is time-dependent (6 months before database becomes irreplaceable)
3. No cost visibility = ROI not clear until month 2-3
4. 30-second latency too slow for CLI tool
5. Cloud storage dependencies (boto3, GCS) add setup friction

**Decision**: EXPAND scope from 8 weeks to 10 weeks with 4 critical additions

### Addition 1: Near-Duplicate Detection (Week 3-4)
**Decision**: Near-duplicates (95%+ similar) REQUIRED for v1.0, not v2.0
**Rationale**:
- Exact duplicates are rare (engineers rarely run IDENTICAL configs)
- Near-duplicates are where waste happens (95% similar configs)
- Creates compounding value: "We tried 95% similar—it failed with OOM"
**Implementation**: Cosine similarity on config hashes, configurable threshold

### Addition 2: Outcome Linkage (Week 5-6)
**Decision**: Store experiment outcome (success/failure/metrics) alongside fingerprint
**Rationale**:
- Fingerprints without outcomes = glorified git log (anyone can copy)
- Outcome data is unique to DataVint (MLflow doesn't have this)
- Enables learning: "Similar experiment failed with OOM. Consider reducing batch size."
**Moat**: Outcome data creates defensible competitive advantage

### Addition 3: Cost Estimation (Week 5-6)
**Decision**: Show "estimated $X" for each experiment (REQUIRED for v1.0)
**Rationale**:
- Startups won't pay $1-3K/month for abstract savings without proof
- Cost estimation makes ROI visible in month 1
- "You've prevented $12K in duplicate runs" justifies procurement
**Activation metric**: User configures GPU pricing within 48 hours

### Addition 4: Optional Team Sync (Week 9)
**Decision**: Add optional cloud backend for team collaboration in v1.0
**Rationale**:
- "Team memory" is core value prop, can't wait until v2.0
- Local-only = personal tool, not team tool
- Engineer A's experiments must be visible to Engineer B
**Implementation**: `datavint init --team` enables PostgreSQL cloud sync (Supabase/Render)

### Addition 5: Fast Path (<5s typical) (Week 7-8)
**Decision**: Add cached fingerprints + cloud metadata fast path
**Rationale**:
- 30 seconds too slow (git status is <1s, docker build is <5s)
- Engineers won't wait 30s every time
**Implementation**:
- Cached fingerprints: If path unchanged in 24h, use cached hash (instant)
- Cloud metadata: S3 ETag, GCS md5Hash (<5s, no download)
- Sampling fallback: Only if path changed and no cloud metadata (30s worst case)
**Target**: 90% of checks complete in <5 seconds

### Scope Reduction: Remove Cloud Storage from v1.0
**Decision**: Remove boto3 (AWS) and google-cloud-storage (GCP) dependencies
**Rationale**:
- boto3 + GCS add setup friction (AWS credentials, IAM roles, dependency size)
- Local filesystem only = pip install → working tool in <5 minutes
- Cloud storage support deferred to v1.1
**Impact**: Reduces adoption friction, simplifies v1.0

### Revised Timeline
- **Original**: 8 weeks (1 engineer)
- **Expanded**: 10 weeks (1 engineer)
- **Tradeoff**: 25% longer, but 2.3x higher success probability (30% → 70%)

### Revised Assignment: Validate Pricing
**Original**: "Get calendar invite for Week 7 kickoff"
**Expanded**: "Validate pricing BEFORE building"
**Action**: Ask committed customer: "Pricing will be $1-3K/month. If DataVint saves you $10K in 3 months, would you pay?"
**Rationale**: Don't build without validating willingness to pay

### Key Decision: "Aha Moment" Hypothesis
**Question**: What creates lock-in?
**Options**:
- (A) Instant value: catch 1 duplicate in week 1
- (B) Compounding value: database irreplaceable after 6 months
- (C) Catastrophic prevention: prevent 1 $40K mistake in first 3 months

**Decision**: Optimize for (C) catastrophic prevention
**Rationale**:
- (B) takes too long (6 months = MLflow can copy in 3 months)
- (A) is nice but not procurement-worthy
- (C) justifies procurement immediately: "It caught one $40K mistake"
**Validation**: Track which users convert to paid, ask "what convinced you?"

### Success Criteria Changes

**Week 10 (Launch) - Added Leading Indicators**:
- 50 PyPI downloads in first week
- 10 users run `datavint check` at least once
- 3 users active (5+ checks)
- 1 user configures GPU pricing (activation metric)

**Month 1 - Added Growth Metrics**:
- 200 total downloads
- 20 active users
- 5 users configure GPU pricing
- 2 users report "warned me about similar experiment"

**Month 2 - Revised Retention**:
- 60% retention (relaxed from 70%)
- 1 user refers to teammate (viral growth)
- 1 user reports "cost estimation prevented wasteful run"

### What This Reveals About Product Strategy

**On scope narrowness**:
- Original instinct: "Start with exact duplicates, add near-duplicates in v2.0"
- CEO challenge: "Exact duplicates are rare. Near-duplicates are where waste happens."
- Learning: "MVP" can be too minimal if it doesn't create a moat

**On moat timing**:
- Original assumption: "6 months of experiments = irreplaceable database = moat"
- CEO challenge: "6 months is too long. MLflow can copy in 3 months."
- Learning: Time-dependent moats are vulnerable to fast followers. Need immediate moat (outcome data).

**On pricing validation**:
- Original approach: "Get verbal commitment, ship product, then talk pricing"
- CEO challenge: "Validate willingness to pay BEFORE building"
- Learning: Builder mode (ship first, sell later) vs customer development mode (validate first, then build)

### v1 vs v2 Comparison

| Feature | v1 (Original) | v2 (Expanded) |
|---------|---------------|---------------|
| Timeline | 8 weeks | 10 weeks |
| Exact duplicates | ✅ | ✅ |
| Near-duplicates | ❌ (v2.0) | ✅ (v1.0) |
| Cost estimation | ❌ | ✅ (required) |
| Outcome linkage | ❌ | ✅ |
| Team sync | ❌ (v2.0) | ✅ (optional) |
| Fast path | ❌ (30s) | ✅ (90% <5s) |
| Cloud storage | ✅ (boto3, GCS) | ❌ (deferred) |
| Success probability | 30% | 70% |

**Bottom line**: v2 adds 2 weeks (25% longer) but increases success probability 2.3x. The expansions transform DataVint from "duplicate blocker" (one-time value) to "experiment advisor" (compounding value + immediate ROI).

**Files**:
- Design v2: `wiki/changelog/2026-05-13-datavint-gpu-waste-control-design-v2-expanded.md`
- CEO Review Summary: `wiki/changelog/2026-05-13-ceo-review-summary.md`

## Week 1 Implementation: CLI + Exact Duplicate Detection (2026-05-13)

**Decision Date**: 2026-05-13
**Status**: COMPLETED ✅

**Context**: Started Week 1 of 10-week v2 implementation. Goal: Working CLI with exact duplicate detection.

**Implementation Decisions**:

### 1. CLI Framework: Click (not Typer)
**Decision**: Use Click for CLI framework
**Rationale**:
- More mature and widely adopted than Typer
- Simpler API for basic commands
- Better documentation and community support
- Lighter dependency (no Pydantic required)

### 2. Database Schema: Separate from Experiment Tracking
**Decision**: Created new `experiment_fingerprints` table, separate from existing `data_commits`
**Rationale**:
- `data_commits` is for experiment lineage tracking (data versioning)
- `experiment_fingerprints` is for duplicate detection (pre-execution gate)
- Different use cases, different access patterns
- Allows independent evolution of both systems

### 3. Fingerprinting Strategy: Sampling-Based
**Decision**: Sample 0.1% of dataset (0.001) for fingerprinting
**Rationale**:
- <30 second target for 500GB dataset (500MB sample)
- SHA256 on sampled data, first 16 characters (not 7 like git)
- Deterministic (random_state=42) for reproducibility
- Trade-off: collision risk vs speed (16 chars = 2^64 possibilities)

### 4. Database Path: ~/.datavint/experiments.db (not ~/.datavint/metadata.db)
**Decision**: Use separate database for CLI vs experiment tracking
**Rationale**:
- `metadata.db` used by `datavint.experiment()` context manager (SDK)
- `experiments.db` used by `datavint check` CLI (pre-execution gate)
- Separation of concerns: SDK ≠ CLI
- Future: may merge or add sync layer

### 5. Exit Codes: 0 (no duplicate), 1 (duplicate warning), 2 (error)
**Decision**: Use standard Unix exit codes with semantic meaning
**Rationale**:
- 0 = success (safe to proceed, no duplicate)
- 1 = warning (duplicate found, user should consider skipping)
- 2 = error (invalid input, unsupported format, etc.)
- Allows scripting: `datavint check data.csv && python train.py`

### 6. File Format Support: CSV, Parquet, JSON (Week 1)
**Decision**: Support CSV, Parquet, JSON in Week 1
**Rationale**:
- Most common ML data formats
- All supported by pandas (no extra dependencies)
- Cloud storage (S3/GCS) deferred to Week 7 (v1.1)

### 7. Configuration: JSON file at ~/.datavint/config.json
**Decision**: Store config in JSON file (not TOML, YAML, or env vars)
**Rationale**:
- Standard library support (no extra deps)
- Simple key-value structure
- Easy to read and edit manually
- Future: may add ~/.datavint/config.toml for richer config

**Implementation Files**:
- `datavint/cli.py` - CLI commands (check, history, config)
- `tests/api/test_cli.py` - 15 tests, all passing
- `pyproject.toml` - Added Click dependency + CLI entry point

**Week 1 Milestone**: ✅ ACHIEVED
- Working `datavint check` command (exact duplicate detection)
- Working `datavint history` command (show past experiments)
- Working `datavint config` command (set GPU price for future use)
- 15 tests passing
- Tested on real datasets (Titanic, train.csv)

## Week 3-4 Implementation: Near-Duplicate Detection (2026-05-13)

**Decision Date**: 2026-05-13

**Context**: Week 1 implemented exact duplicate detection (100% match). Week 3-4 extends this to detect near-duplicates (95%+ similarity) to catch train/test splits, slightly modified datasets, and similar experiments.

**Decision**: Implemented feature-based similarity scoring using cosine similarity on extracted dataset features.

**Key Architectural Choices**:

### 1. Feature Extraction Strategy
**Decision**: Extract 7 categories of features from datasets:
1. Column names (sorted for order independence)
2. Column count and row count
3. Data types distribution (numeric vs categorical ratio)
4. Numeric statistics (mean, std, min, max averaged across columns)
5. Categorical cardinality (unique values per column)
6. Column name hashing (position-independent)
7. Shape similarity (row/column counts on log scale)

**Rationale**:
- Captures both structure (columns, types) and content (statistics)
- Normalized to [0, 1] range for consistent scaling
- Position-independent (sorted columns, hash-based comparison)
- Fast to compute (no full dataset comparison needed)
- Works across different dataset sizes (train vs test)

### 2. Similarity Metric: Cosine Similarity
**Decision**: Use cosine similarity on feature vectors (scipy.spatial.distance.cosine)
**Rationale**:
- Range [0, 1] with clear semantic meaning (1 = identical, 0 = completely different)
- Scale-invariant (works with different feature magnitudes)
- Industry standard for high-dimensional similarity
- Fast to compute (linear in feature vector length)
- Better than Euclidean distance for mixed feature types

### 3. Default Similarity Threshold: 0.95 (95%)
**Decision**: Default threshold of 0.95 for near-duplicate detection
**Rationale**:
- Conservative threshold to avoid false positives
- Catches train/test splits (typically 99%+ similar)
- User-configurable via `--similarity` option
- Exit code 1 (warning) when similar experiments found
- Tested: Titanic train vs test = 99.8%, MovieLens train vs test = 99.9%

### 4. Feature Storage in Database
**Decision**: Store features as JSON in `experiment_fingerprints.features` column
**Rationale**:
- Enables similarity comparison without re-loading datasets
- JSON format is human-readable and debuggable
- SQLite TEXT column with JSON (no schema migration needed)
- ~1KB per experiment (acceptable overhead)
- Migration logic handles existing records (NULL features)

### 5. Top 3 Similar Experiments Display
**Decision**: Show only top 3 most similar experiments in output
**Rationale**:
- Prevents information overload
- Most relevant results shown first
- Mention "... and N more" if >3 found
- Sorted by similarity (descending)
- Includes similarity %, fingerprint, path, size, last run time

### 6. Exit Code Strategy for Similar Experiments
**Decision**: Exit code 1 (warning) when similar experiments found, even without exact duplicate
**Rationale**:
- Consistent with "found an issue" pattern
- Allows scripting: `datavint check data.csv && python train.py` stops on similarity
- User can override with `--similarity 1.0` to only stop on exact matches
- Clear distinction: 0 = safe, 1 = warning, 2 = error

### 7. Helper Functions: column_overlap, shape_similarity
**Decision**: Provide auxiliary similarity functions for debugging/analysis
**Rationale**:
- `compute_column_overlap`: Jaccard similarity of column names
- `compute_shape_similarity`: Row/column count similarity on log scale
- Useful for understanding WHY datasets are similar
- Exposed in API for potential CLI `--explain` flag (future)
- Tested separately for correctness

**Implementation Files**:
- `datavint/similarity.py` - 269 lines (feature extraction, similarity computation)
- `datavint/cli.py` - Updated check command with similarity detection
- `tests/test_similarity.py` - 26 unit tests (feature extraction, similarity, helpers)
- `tests/api/test_cli.py` - Added 8 near-duplicate detection tests

**Test Coverage**:
- 26 similarity module tests (feature extraction, vectors, similarity, helpers)
- 8 CLI tests for near-duplicate detection (thresholds, edge cases, output format)
- Total: 34 new tests, all passing
- Tested on real datasets: Titanic train/test (99.8%), MovieLens train/test (99.9%)

**Week 3-4 Milestone**: ✅ ACHIEVED
- Feature-based similarity scoring (cosine similarity)
- Configurable threshold via `--similarity` option (default 0.95)
- Display top 3 similar experiments with metadata
- Database schema updated to store features
- 34 comprehensive tests (26 unit + 8 integration)
- Validated on real train/test splits

## Week 5-6 Implementation: Outcome Linkage + Cost Estimation (2026-05-13)

**Decision Date**: 2026-05-13

**Context**: Week 1-4 implemented duplicate detection. Week 5-6 adds the ability to track experiment outcomes and estimate costs, creating a feedback loop that makes duplicate warnings more actionable.

**Decision**: Implemented outcome tracking via `datavint log-result` command and heuristic-based cost estimation.

**Key Architectural Choices**:

### 1. Outcome Storage Schema
**Decision**: Extend `experiment_runs` table with outcome columns:
- `status` (TEXT): success/failure/oom/timeout/cancelled
- `metrics` (TEXT/JSON): key-value metrics (accuracy, loss, etc.)
- `duration_hours` (REAL): actual training duration
- `gpu_count` (INTEGER): number of GPUs used
- `cost_usd` (REAL): calculated cost based on GPU price

**Rationale**:
- Reuses existing `experiment_runs` table (1:N relationship with fingerprints)
- JSON for metrics allows flexible schema (different experiments track different metrics)
- Separate duration/gpu_count/cost for cost-benefit analysis
- Migration logic handles existing databases (ALTER TABLE ADD COLUMN)
- Queryable: can analyze outcomes by status, cost range, etc.

### 2. log-result Command Design
**Decision**: `datavint log-result <fingerprint> --status <status> [options]`
**Options**:
- `--status`: Required (success/failure/oom/timeout/cancelled)
- `--metric key=value`: Multiple allowed (e.g., --metric accuracy=0.92 --metric loss=0.08)
- `--duration <hours>`: Optional training duration
- `--gpu-count <n>`: Optional GPU count
- `--notes <text>`: Optional failure analysis

**Rationale**:
- Fingerprint as positional argument (user gets it from check output)
- Status as required field (minimum viable outcome tracking)
- Multiple --metric flags (common pattern in CLI tools like git config)
- Automatic cost calculation if duration, gpu_count, and config price available
- Notes field for free-form failure analysis (e.g., "OOM at batch_size=256")
- Exit code 0 on success, 2 on error (consistent with check command)

### 3. Cost Estimation Heuristic
**Decision**: Estimate cost based on dataset size with industry-standard training durations
**Heuristics**:
- Small (<10K rows): 0.5 hours, 1 GPU
- Medium (10K-100K): 2 hours, 2 GPUs
- Large (100K-1M): 8 hours, 4 GPUs
- Very large (>1M): 24 hours, 8 GPUs
- Adjust by column count: +20% if >50 cols, +50% if >100 cols

**Rationale**:
- Provides immediate ROI clarity without requiring user input
- Based on typical ML training patterns (more data = longer training)
- Conservative estimates (better to overestimate than underestimate cost)
- Adjustable: users can set actual values via log-result after training
- Displayed prominently in check output to emphasize cost impact
- Uses GPU price from config (set via `datavint config --gpu-price`)

**Limitations**:
- Heuristic doesn't account for model complexity (simple vs transformer)
- Assumes homogeneous dataset (same column types/distributions)
- Doesn't consider hyperparameter tuning (multiple runs)
- Future: could learn from actual outcomes to improve estimates

### 4. Outcome Display in Check Command
**Decision**: Show outcomes inline when displaying duplicates/similar experiments

**For exact duplicates**:
```
⚠️  EXACT DUPLICATE DETECTED

This exact experiment has been run 1 time(s) before:
  ...
  Last outcome:
    Status:   success
    Metrics:  accuracy=0.9200, loss=0.0800
    Cost:     $165.00
    Notes:    Baseline model with default params

💡 Skipping this run would save ~$200.00
```

**For similar experiments**:
```
  1. Similarity: 98.5%
     ...
     Outcome:     ✅ success
                  accuracy=0.92, loss=0.08
                  Reduced batch size to avoid OOM
```

**Rationale**:
- Actionable warnings: "This similar experiment failed with OOM" → user reduces batch size
- Success indicators (✅/❌) provide quick visual feedback
- Show first 2 metrics only (avoid clutter)
- Truncate notes to 60 chars (with "..." if longer)
- Display most recent outcome only (users can query history for full log)
- Cost savings calculation makes skip decision quantifiable

### 5. Multiple Outcomes Strategy
**Decision**: Store all outcomes in `experiment_runs` table, display most recent in check
**Rationale**:
- Users re-run experiments after failures (want to see latest result)
- Historical outcomes queryable via SQL for analysis (future `datavint analyze` command)
- Run count in `experiment_fingerprints` increments on check, not log-result
- Allows tracking: 1st run failed → 2nd run success → shows improvement

### 6. Cost Calculation in log-result
**Decision**: Auto-calculate cost if duration, gpu_count, and config price all available
**Formula**: `cost_usd = duration_hours * gpu_count * gpu_price_per_hour`
**Rationale**:
- Single source of truth for cost (user doesn't provide --cost manually)
- Graceful degradation: if no GPU price configured, just store duration/gpu_count
- Displayed in confirmation: "Cost: $165.00" so user knows it was calculated
- Future: could infer GPU type from cost (e.g., A100 vs H100)

### 7. Integration with Existing Features
**Decision**: Cost estimation shown BEFORE duplicate check (not after)
**Rationale**:
- User sees cost immediately (decision factor before reading warnings)
- Cost displayed even if no duplicates found
- Consistent placement: always after fingerprint, before results
- Sets context for "Skipping would save $X" message

**Implementation Files**:
- `datavint/cli.py` - Added log-result command, _get_experiment_outcome(), _estimate_cost()
- Updated check command to display cost estimation and outcomes
- Extended database schema with migration logic
- `tests/api/test_cli.py` - Added 8 comprehensive tests

**Test Coverage**:
- 8 new tests for Week 5-6 features
- Total: 31 CLI tests passing (23 previous + 8 new)
- Tested: log-result command, cost estimation, outcome display, multiple outcomes, invalid inputs

**Week 5-6 Milestone**: ✅ ACHIEVED
- `datavint log-result` command tracks outcomes (status, metrics, cost, notes)
- Heuristic cost estimation based on dataset size
- Outcomes displayed in check command for duplicates and similar experiments
- Automatic cost calculation from duration + GPU count + config price
- 8 comprehensive tests covering all features
- Integration with check command for actionable warnings

## Bipartite Graph Frontend Integration (2026-05-13)

**Decision Date**: 2026-05-13

**Context**: Week 5-6 implemented CLI outcome tracking. The frontend already has a bipartite graph visualization for SDK experiments (data commits + model runs). Need to integrate CLI data into the same visualization.

**Decision**: Create API bridge that reads CLI database and transforms data into bipartite graph format, with mode toggle in frontend.

**Key Architectural Choices**:

### 1. API Bridge Design
**Decision**: New router `cli_experiments.py` with three endpoints:
- `GET /api/cli-experiments/list` - List all fingerprints with outcomes
- `GET /api/cli-experiments/{fingerprint}/lineage` - Bipartite graph data
- `GET /api/cli-experiments/stats` - Aggregate statistics

**Rationale**:
- Separate router keeps CLI and SDK code decoupled
- Transform data at API layer (not frontend)
- Frontend expects specific format (dataCommits, modelRuns, connections)
- Reuse existing LineageGraph component (no UI changes needed)

### 2. Data Transformation Strategy
**Decision**: Map CLI concepts to SDK visualization concepts:
- CLI fingerprints → Data commits (D-{hash})
- CLI experiment runs → Model runs (M-{hash}-{n})
- Similar experiments → Additional data commits (shows train/test splits)
- Connections map fingerprints to their runs

**Example transformation**:
```
CLI: fingerprint "abc123..." with 2 runs
  → Data commit: D-abc123, message="train.csv"
  → Model run 1: M-abc1-1, status="✅ success", metrics={accuracy: 0.92}
  → Model run 2: M-abc1-2, status="❌ failure", notes="OOM error"
  → Connections: {"D-abc123": ["M-abc1-1", "M-abc1-2"]}
```

**Rationale**:
- Same fingerprint = same data version (aligns with SDK concept)
- Multiple runs on same fingerprint = hyperparameter tuning (aligns with SDK sweeps)
- Similar experiments visualized as related data versions (shows data lineage)

### 3. Similarity Integration
**Decision**: Show top 3 similar experiments (90%+ threshold) as additional data commits
**Implementation**:
- Query `experiment_fingerprints` for features
- Compute similarity using `datavint.similarity.compute_similarity`
- Add similar fingerprints as separate data commits with similarity % in message
- Show their latest run as model run

**Rationale**:
- Users can see train/test splits visualized (typically 99%+ similar)
- Understand why CLI flagged an experiment as similar
- Visual representation of near-duplicate detection
- 90% threshold for visualization (looser than 95% CLI default)

### 4. Metrics Formatting
**Decision**: Transform JSON metrics to frontend format with quality indicators
**Formula**:
- Accuracy-like (higher = better): good if ≥0.90, ok if ≥0.75, bad otherwise
- Loss-like (lower = better): good if ≤0.1, ok if ≤0.3, bad otherwise
- Default: neutral quality

**Rationale**:
- Frontend expects `{metric: {value, quality}}` format
- Quality determines color (green/orange/gray)
- Heuristic covers common ML metrics
- Extensible for custom metrics

### 5. Frontend Mode Toggle
**Decision**: Add mode selector in ExperimentView: "SDK Experiments" vs "CLI Experiments"
**Implementation**:
- Query parameter `?mode=cli` for direct links
- Dropdown selector for CLI fingerprints
- Conditional API fetch based on mode
- Error states with helpful hints

**Rationale**:
- Single unified view for both data sources
- No duplicate components needed
- Preserves existing SDK functionality
- Clear separation of concerns (SDK vs CLI tracking)

### 6. Database Access
**Decision**: API reads directly from `~/.datavint/experiments.db` (CLI database)
**Rationale**:
- No sync/migration needed
- Real-time data (no stale cache)
- CLI and API share single source of truth
- Simple: no additional infrastructure

**Limitation**:
- API must run on same machine as CLI (localhost development)
- Future: could add remote database option for team sync (Week 9 feature)

**Implementation Files**:
- `server/api/routes/cli_experiments.py` - API bridge (441 lines)
- `server/api/main.py` - Router registration
- `client/src/views/ExperimentView.vue` - Mode toggle UI

### 7. Ungrouped Runs Support (2026-05-14)
**Problem**: LineageGraph only displayed runs with `sweep` property. CLI experiments don't use sweeps, so all runs were filtered out.

**Decision**: Add `ungroupedRuns` computed property to display runs without sweep information.

**Implementation**:
- `const ungroupedRuns = computed(() => props.modelRuns.filter(run => !run.sweep))`
- Template renders ungrouped runs after sweep clusters
- Works for both CLI experiments (no sweeps) and SDK experiments (with sweeps)

**Visual Improvements**:
- Added `z-index: 10` to node components (DataCommitNode, ModelRunNode)
- Reduced connection line opacity (0.6 → 0.3) and width (2 → 1.5)
- Ensures connection lines stay in background, don't obstruct text

**Files Changed**:
- `client/src/components/LineageGraph.vue` - ungroupedRuns support + line styling
- `client/src/components/DataCommitNode.vue` - z-index for stacking order
- `client/src/components/ModelRunNode.vue` - z-index for stacking order

**Integration Features**:
- Visualize CLI experiments in bipartite graph
- See multiple runs of same dataset
- View similar experiments (train/test splits)
- Cost and duration displayed in runs
- Success/failure status with notes
- Metrics with quality scoring
- Query parameter support

**Bipartite Graph Integration**: ✅ COMPLETE
- CLI outcomes visible in frontend visualization
- Mode toggle between SDK and CLI experiments
- API bridge transforms CLI data to graph format
- Similar experiments shown as related data commits
- Status icons, metrics, and cost displayed

**Next**: Week 7-8 will add fast path optimization (<5s checks via caching).
