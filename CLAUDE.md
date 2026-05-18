# NanoML Project Instructions

## Wiki Documentation

**At the start of each session, load the wiki to get all project documentation:**

Run this command to load all documentation:
```bash
./.claude/load-memory.sh
```

This loads:
- Memory files (patterns, decisions, gotchas, tips)
- All wiki documentation (18 markdown files covering architecture, API, guides, deployment, etc.)

The wiki contains:
- `wiki/architecture/` - System architecture
- `wiki/api/` - API reference docs
- `wiki/guides/` - Usage guides
- `wiki/deployment/` - Deployment documentation
- `wiki/features/` - Feature specifications
- `wiki/notebooks/` - Notebook documentation
- `wiki/changelog/` - Design decisions and history

## Memory System

Project knowledge is stored in the `memory/` folder:
- `patterns.md` - Coding patterns and conventions
- `decisions.md` - Architectural decisions
- `gotchas.md` - Common pitfalls
- `tips.md` - Useful commands

Update these files when you learn something new or make important decisions.

## Issue Review Protocol

**Automatically review every GitHub issue after creation.**

When a user creates a GitHub issue (via `gh issue create`), immediately run:
```bash
gh issue view <issue_number>
```

Then provide a comprehensive review covering:

### Review Structure

1. **✅ Strengths** (2-4 points)
   - What's well-defined
   - Clear value propositions
   - Good structure/organization

2. **⚠️ Concerns & Gaps** (3-6 points)
   - Ambiguities requiring clarification
   - Missing technical details
   - Incomplete specifications
   - Broken links or invalid assumptions

3. **🔍 Technical Feasibility Analysis**
   - Implementation estimate (hours/days)
   - Backend/frontend breakdown
   - Dependency requirements
   - Total effort calculation

4. **📝 Recommendations**
   - Explicit decisions needed (e.g., "Choose approach X for MVP")
   - Prerequisites to add
   - Simplifications to consider
   - Related issues to link

5. **✅ Final Verdict**
   - Issue quality score (X/10)
   - Blocking issues identified
   - Recommendation: Approve / Approve with modifications / Needs rework
   - Implementation priority (High/Medium/Low)

### Example Review Format

```markdown
## Issue #X Review: [Title]

### ✅ Strengths
- Clear user value proposition
- Well-structured proposal with mockups
- Security concerns identified upfront

### ⚠️ Concerns & Gaps
**1. Missing Detail X**
Current: [quote from issue]
Problem: [why this is incomplete]
Recommendation: [specific fix]

### 🔍 Technical Feasibility Analysis
**MVP Implementation Estimate:**
- Backend: 2-3 hours
- Frontend: 3-4 hours
- Total: 5-7 hours (1 day)

### 📝 Recommendations
1. Update issue with explicit MVP decision
2. Add prerequisites section
3. Validate demo datasets exist

### ✅ Final Verdict
**Issue Quality:** 8/10
**Blocking Issues:** [list]
**Recommendation:** ✅ Approve with modifications
**Implementation Priority:** Medium-High
```

### Phase 2: Engineering Review (Hybrid Approach)

**After completing the basic issue review, if the issue scores 7/10 or higher:**

1. **Convert issue to plan format:**
   - Extract implementation requirements from the issue
   - Structure as a markdown plan document
   - Save to `/tmp/issue-{number}-plan.md` with sections:
     - Problem Statement
     - Proposed Solution
     - Implementation Steps
     - Technical Considerations
     - Success Criteria

2. **Invoke /plan-eng-review:**
   - Use the Skill tool: `Skill("plan-eng-review")`
   - Point it to the converted plan document
   - Get deep architecture analysis covering:
     - Edge cases and error handling
     - Testing strategy
     - Performance considerations
     - Security implications
     - Maintenance burden

3. **Synthesize results:**
   - Combine issue review + engineering review findings
   - Highlight any critical concerns from engineering review
   - Provide unified implementation recommendations
   - Update issue quality score if engineering review reveals issues

**Skip Phase 2 if:**
- Score < 7/10 (needs issue refinement first)
- Issue is documentation-only
- Issue is a trivial bug fix (< 10 lines of code)
- User explicitly requests to skip engineering review

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore

**Data Quality Analysis Skills:**
- Class imbalance / balanced dataset / class distribution → invoke /check-imbalance
- Completeness / missing values / null values → invoke /check-completeness
- High cardinality / unique values / ID columns → invoke /check-cardinality
- Entropy / information content / constant features → invoke /check-entropy
- Uniqueness / duplicate values / low uniqueness → invoke /check-uniqueness
- Distinctness / distinct values / few distinct → invoke /check-distinctness

---

# Product Design Document

## 🚧 DRAFT DESIGN: NanoML - ML Training Observability & Root-Cause Analysis (v3)

**Generated**: 2026-05-17
**Branch**: main
**Status**: DRAFT - Requires customer validation
**Mode**: Major Pivot - From GPU waste control to observability
**Last Updated**: 2026-05-17
**Full Design**: `wiki/changelog/2026-05-17-nanoml-ml-observability-design-v3.md`

### Executive Summary (100-word version)

When production ML accuracy drops 0.3%, teams waste days asking why. The problem: dual fragmentation. Teams work in silos (data engineers vs ML engineers), and infrastructure is scattered (MLflow, Feast, validators)—any shift breaks models downstream. We're building observability for ML training systems that answers "which data change caused this production regression?" Not another ML platform—an intelligence layer above fragmented infra, tracing user outcome shifts to root-cause training data. Like Datadog for ML decisions, not metrics. Critical as agent-driven workflows amplify cascading failures across fragmented components.

### The Problem: Two-Dimensional Fragmentation

**1. Team Fragmentation**
- Data engineers optimize for pipeline throughput
- ML engineers optimize for model accuracy
- Each team has conflicting goals, different tools, no shared visibility

**2. Infrastructure Fragmentation**
- MLflow for experiments
- Feast for features
- Custom validators for data quality
- Separate systems for each concern
- Any component shift breaks models downstream

**The Cost**: When production accuracy drops, engineers spend 2-5 days on root-cause analysis, wasting 20-30% of engineering time on ML archaeology.

### The Solution

**Product**: Intelligence layer above fragmented ML infrastructure that traces production outcome shifts back to root-cause training data changes.

**Core Value**: "Which training data change caused which production outcome shift?"

**Positioning**:
- NOT another ML platform
- NOT another experiment tracker
- NOT another data quality tool
- **We are**: "Datadog for ML decisions, not ML metrics"

### Target Customer

**ML Team Lead** at ML-focused company (Series A-C)
- Team: 10-50 engineers (data + ML + platform)
- Pain: Spending 20-30% of time debugging production regressions
- Existing stack: MLflow/W&B, Airflow, cloud data warehouse
- Willingness to pay: $5K-$20K/month to save senior engineering time

### Value Proposition

"Stop wasting senior engineering time on ML archaeology. Get root-cause answers in minutes, not days."

**Economics**:
- Current cost: 2-5 days × senior ML engineer ($150K-$250K) = $1,200-$5,000 per incident
- 10-20 incidents/year = $12K-$100K/year in engineering time
- NanoML value: 10x faster root-cause (minutes vs days), 50% fewer incidents reach production
- Pricing: $5K-$15K/month (20-50% of value)

### MVP Roadmap (12 Weeks)

**Phase 1 (Weeks 1-3)**: Foundation
- Data fingerprinting
- Training experiment logging (MLflow integration)
- Production prediction logging
- Graph storage (data → training → production)

**Phase 2 (Weeks 4-6)**: Root-Cause Analysis
- Distribution shift detection
- Feature coverage regression
- Training/serving skew detection
- CLI: `nanoml diagnose --production-metric=ctr --date=2026-05-10`

**Phase 3 (Weeks 7-9)**: Integration & Polish
- MLflow plugin (zero code changes)
- Airflow sensor (block training on data issues)
- Web dashboard
- Slack/PagerDuty integration

**Phase 4 (Weeks 10-12)**: Pilot & Iteration
- Deploy with 1-2 pilot customers
- 5+ successful root-cause diagnoses
- <20% false positive rate

### Differentiation

| Tool | What They Do | Gap |
|------|--------------|-----|
| MLflow / W&B | Passive experiment tracking | No production outcome linkage |
| Monte Carlo / Anomalo | Data pipeline monitoring | Don't understand ML training |
| Datadog / New Relic | Infrastructure metrics | Treat ML models as black boxes |
| LakeFS / DVC | Data versioning | No impact analysis |

**Our Moat**:
1. Cross-layer graph (data → training → production)
2. Outcome causality (trace production shifts to training changes)
3. ML-specific failure mode understanding
4. Compounding value (graph becomes irreplaceable after 3-6 months)

### Success Metrics

**Month 3**: 2 pilot customers, $5K MRR, 20+ successful diagnoses, <20% false positive rate
**Month 6**: 10 customers, $50K MRR, 80% pilot conversion
**Month 12**: $200K ARR, 30 customers, 2 enterprise deals

### Why Pivot from GPU Waste Control?

**Previous**: Pre-execution CLI preventing duplicate experiments

**Reasons**:
1. Broader problem space (observability > duplicate prevention)
2. Stronger moat (compounding graph data vs feature)
3. Better economics (3-5x higher willingness-to-pay for time savings)
4. Customer validation (HF0, Pearx, Point72 emphasize observability)
5. Agent future (unified observability reduces cascading failure risk)

### Next Steps (This Week)

1. **Customer validation**: 3-5 conversations about production regression pain
2. **Technical spike**: Prototype fingerprinting + MLflow plugin (2-3 days)
3. **Competitive analysis**: Deep dive Monte Carlo, Anomalo, Datadog ML
4. **Refine pitch**: 100-word YC description + 3-slide deck

**Decision Point (End of Week)**: Commit to observability pivot OR return to GPU waste control

---

## SUPERSEDED DESIGNS

### Design: NanoML - ML Execution Waste Control Layer (v2)

**Generated**: /plan-ceo-review on 2026-05-13
**Status**: SUPERSEDED (pivoted to observability on 2026-05-17)
**Full Design**: `wiki/changelog/2026-05-13-nanoml-gpu-waste-control-design-v2-expanded.md`

**Why Superseded**: Observability addresses broader problem space with stronger moat and better economics. Root-cause analysis (time savings) has 3-5x higher willingness-to-pay than duplicate prevention (cost savings).

### Design: NanoML - Recommendation Systems Data Quality SDK

**Generated**: /office-hours on 2026-05-04
**Status**: SUPERSEDED (pivoted to GPU waste control on 2026-05-13, then to observability on 2026-05-17)
**Full History**: See `wiki/changelog/` for design evolution

**Pivot History**:
- `2026-05-04`: Rec systems data quality SDK (original design)
- `2026-05-10`: Experiment-level data versioning pivot
- `2026-05-13`: GPU waste control layer (customer-driven pivot)
- `2026-05-13`: v2 expanded (CEO review + selective expansion)
- `2026-05-17`: Observability & root-cause analysis (major pivot)

For full details on all designs, see `wiki/changelog/`.
