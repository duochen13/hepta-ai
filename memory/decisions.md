# Architectural Decisions

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
