# Coding Patterns


## [2026-05-11] Pre-push hook enforces memory updates before pushing to main

**Pattern:** Git pre-push hook that ensures memory files are updated before pushing to main branch, maintaining context continuity across sessions.

**Implementation:**
```bash
# .git/hooks/pre-push
# 1. Detects branch being pushed (only enforces on main)
# 2. Gets list of modified files in commits
# 3. Checks if memory/*.md files were modified
# 4. If not modified: warns and offers options
```

**Helper Script:**
```bash
# Quick add dated entries to memory files
./.claude/scripts/update-memory.sh patterns "Your pattern description"
./.claude/scripts/update-memory.sh decisions "Your decision"
./.claude/scripts/update-memory.sh gotchas "Your gotcha"
./.claude/scripts/update-memory.sh tips "Your tip"
```

**Hook Workflow:**
1. User runs `git push` to main
2. Hook checks if memory/ files modified in commits
3. If not modified:
   - **Option [a]**: Abort push - update memory first (recommended)
   - **Option [c]**: Continue anyway (not recommended)
   - **Option [e]**: Edit memory file now, commit it, then push
4. If modified: push proceeds

**Date Format:**
All memory entries use `[YYYY-MM-DD]` format to prevent conflicts with old context:
```markdown
## [2026-05-11] Your Entry Title
```

**Why This Matters:**
- Context is maintained across sessions
- Learnings aren't lost between conversations
- Patterns and decisions are documented
- Future sessions start with full historical context
- Prevents repeating mistakes

**Files:**
- `.git/hooks/pre-push` (git hook)
- `.claude/scripts/update-memory.sh` (helper script)
- `memory/README.md` (documentation)

**Auto-loaded:**
Memory files are loaded at session start via `.claude/load-memory.sh`, ensuring continuity.

## Hybrid Routing Architecture (2026-05-09)

**Pattern:** Route user queries to either pre-defined skills (fast, free, reliable) or LLM code generation (flexible, slower, costly).

**Implementation:**
- `skill_router.py` - Pattern matching (commands, regex, keywords)
- `skill_executor.py` - Execute pre-defined workflows
- `chat.py` - Integrated routing with LLM fallback

**Performance:**
- 70% of queries → Skills (100ms, $0, deterministic)
- 30% of queries → LLM (3s, $0.03, flexible)
- Result: 70% cost reduction, 30x latency improvement for common operations

**When to use:**
- Skills: Common operations users ask repeatedly
- LLM: Novel/complex requests that don't match patterns

**See:** `memory/hybrid-routing.md` for full implementation details

## Validation System

- Data validation follows TFDV-inspired functional API design
- Adaptive histogram binning scales with dataset size
- Schema detection split into type detection + range detection

## Recent Work (v0.1)

- Data profiling implementation complete
- Detector suite and orchestration in place
- Adaptive histogram binning based on dataset size

## Validation Metric Calculation Pattern

### How Impact Delta is Measured

**Pipeline:**
```
1. Train on DIRTY data → metrics_before
2. Detect issues with DataVint
3. Apply fixes (e.g., remove duplicates)
4. Retrain on CLEAN data → metrics_after
5. Compare: delta = metrics_after - metrics_before
```

**Key Principle:**
- **Same test set** for both measurements (ensures fair comparison)
- **Different training sets** (dirty vs clean)
- **Model retrained from scratch** (not fine-tuned)

**Titanic Example:**
```
Before: 712 rows with 72 duplicates → AUC = 0.842
After:  640 rows (duplicates removed) → AUC = 0.845
Delta: +0.0037 (+0.4%)
```

**Why Duplicates Hurt Performance:**
- Create sampling bias in training
- Model overweights repeated patterns
- Underweights unique patterns
- Result: Poor generalization to test set

**File References:**
- Detection: `datavint/issues.py` (detect_issues)
- Fixing: `validation/data_fixer.py` (fix_dataset)
- Training: `validation/model_trainer.py` (train_and_evaluate)
- Metrics: `validation/metrics.py` (compute_metrics)

## Experiment Tracking Pattern (2026-05-11)

**Pattern:** Context manager for ML experiment lineage tracking with content-based data versioning.

**Implementation:**
```python
with dv.experiment("experiment_name") as exp:
    # Log data version (content-based hashing)
    data_id = exp.log_data(df, message="dedup interactions")

    # Train model
    model.fit(X, y)

    # Log run with metrics
    exp.log_run(
        metrics={"NE": 0.685, "CTR": 0.0058},
        params={"lr": 0.005},
        message="best config",
        best=True
    )
```

**Key Features:**
- **Content-based hashing**: SHA256 on sorted DataFrame JSON → automatic deduplication
- **SQLite metadata store**: ~/.datavint/metadata.db (data_commits + model_runs tables)
- **Auto-linking**: log_run() automatically uses last logged data_commit_id
- **Sweep grouping**: Use sweep_id and sweep_name to group related runs

**Files:**
- SDK: `datavint/experiment.py` (ExperimentContext, experiment())
- API: `server/api/routes/experiments.py` (GET /api/experiments/:id/lineage)
- Frontend: `client/src/views/ExperimentView.vue` (bipartite graph)

**Testing:**
- 8 comprehensive tests in `tests/api/test_experiment_tracking.py`
- Demo script: `examples/experiment_tracking_demo.py`

## Bipartite Graph Visualization Pattern (2026-05-11)

**Pattern:** Two-column layout for visualizing data → model lineage connections.

**Implementation:**
- Left column: Data commits (D0, D1) sorted by timestamp
- Right column: Model runs (M0-M3) grouped by sweep
- SVG Bezier curves connecting data to models
- Hover interactions highlight active connections

**Component Structure:**
```
ExperimentView.vue (container)
├── LineageGraph.vue (SVG + layout)
│   ├── DataCommitNode.vue (data version cards)
│   └── ModelRunNode.vue (model run cards with metrics)
└── ChatPanel.vue (experiment queries)
```

**SVG Connection Pattern:**
```javascript
// Bezier curve from data node to model node
const midX = (dataCenter.x + modelCenter.x) / 2
const d = `M ${dataCenter.x} ${dataCenter.y}
           C ${midX} ${dataCenter.y}, ${midX} ${modelCenter.y},
             ${modelCenter.x} ${modelCenter.y}`
```

**Color States:**
- Default: Light green (--accent-light-green)
- Active/Hovered: Purple (--accent-purple)
- Best model: Bright green (--accent-green)

## Mock Data Strategy for Frontend Development (2026-05-11)

**Pattern:** Frontend works with mock data during backend development, seamless transition to real API.

**Implementation:**
```javascript
async function fetchExperimentLineage() {
  try {
    const response = await fetch(`/api/experiments/${experimentId}/lineage`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    dataCommits.value = data.dataCommits
    modelRuns.value = data.modelRuns
    connections.value = data.connections
  } catch (err) {
    // Fall back to mock data for development
    loadMockData()
    error.value = null  // Clear error so graph renders
  }
}
```

**Key Principles:**
- Mock data matches expected API response structure exactly
- Frontend fully functional before backend exists
- Easy transition: implement API endpoint → frontend switches automatically
- Don't block graph rendering on API errors during development

## Automated E2E Testing Hook Pattern (2026-05-11)

**Pattern:** Automated testing hook that runs e2e tests whenever client code changes to ensure /playground page functionality.

**Implementation:**
```bash
# .claude/hooks/client-change-hook.sh
# Detects uncommitted or staged changes in client/
git diff --name-only client/
git diff --cached --name-only client/

# Runs e2e test suite if changes detected
python3 tests/e2e/test_playground_page.py
```

**Hook Integration:**
- Called from user-prompt-submit-hook.sh on every user interaction
- Provides clear visual feedback with formatted output
- Non-blocking: warns but doesn't prevent work if tests fail

**E2E Test Coverage:**
```python
# tests/e2e/test_playground_page.py
1. test_backend_api_running()      # Backend server health
2. test_frontend_running()         # Frontend dev server at /playground/
3. test_experiment_lineage_api()   # API data structure validation
4. test_experiments_list_api()     # Experiments list endpoint
5. Winner logic validation         # Ensures lowest NE = best
```

**When Triggered:**
- Any change to files in client/ directory (uncommitted or staged)
- Lists all modified files before running tests
- Reports pass/fail status with color-coded output

**Test Philosophy:**
- Test-driven development mindset for frontend changes
- Catch breaking changes before commit
- Validate API contract (backend ↔ frontend)
- Ensure critical user flows work (experiment lineage visualization)

**Example Output:**
```
🧪 CLIENT CODE CHANGES DETECTED - RUNNING E2E TESTS
Modified files in client/:
  - client/src/router/index.js
✓ Backend API is running
✓ Frontend is running at /playground/
✓ Winner logic correct: lowest NE (0.685) = best
✅ E2E TESTS PASSED - /playground page working correctly
```
