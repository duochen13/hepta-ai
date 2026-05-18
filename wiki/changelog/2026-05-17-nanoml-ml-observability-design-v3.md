# Design: NanoML - ML Training Observability & Root-Cause Analysis (v3)

**Generated**: 2026-05-17
**Status**: DRAFT 🚧
**Mode**: Pivot - Major direction change from GPU waste control to observability
**Previous Design**: GPU Waste Control (v2) - See 2026-05-13-nanoml-gpu-waste-control-design-v2-expanded.md

---

## Executive Summary

### The Problem: Two-Dimensional Fragmentation

Large ML organizations suffer fragmentation on two critical levels:

**1. Team Fragmentation**
- Data engineers build pipelines optimizing for throughput and reliability
- ML engineers tune models optimizing for accuracy and latency
- Platform engineers manage infrastructure optimizing for cost and uptime
- Each team has different goals, different tools, different visibility

**2. Infrastructure Fragmentation**
- MLflow for experiment tracking
- Feast for feature storage
- Custom validators for data quality
- Airflow for orchestration
- Prometheus for infra metrics
- Separate systems for each concern

**The Result: When production accuracy drops 0.3%, engineers waste days asking "Why?"**

Current reality:
- "Is it feature coverage?"
- "Did data distribution shift?"
- "Was there a pipeline bug?"
- "Which training batch caused this?"
- No unified view from data → training → production
- Root-cause analysis requires manual archaeology across 5+ systems

**The Cost**:
- 20-30% of engineering time on debugging production regressions
- Each incident: 2-5 days of senior ML engineer time ($200K+ fully loaded)
- Cascading failures from infrastructure changes (Feast upgrade breaks model)
- Alert fatigue: 40-60% false positives from disconnected monitoring

---

## The Solution: ML Training Observability Layer

**Product**: Intelligence layer above fragmented ML infrastructure that traces production outcome shifts back to root-cause training data changes.

**Positioning**:
- NOT another ML platform
- NOT another experiment tracker
- NOT another data quality tool

**What we are**: "Datadog for ML decisions, not ML metrics"

We answer the question: **"Which training data change caused which production outcome shift?"**

### Core Capabilities

**1. Unified Observability Graph**
```
Data Pipeline → Training Data → Model Training → Production Predictions → User Outcomes
     ↓              ↓                ↓                    ↓                    ↓
  [lineage]    [fingerprints]   [experiments]      [predictions]        [business metrics]
```

**2. Root-Cause Analysis Engine**
- Production regression detected → trace back through the graph
- "Accuracy dropped 0.3% on May 10"
- → "Training batch from May 8 had 15% lower feature coverage"
- → "Pipeline change on May 7 dropped join condition"
- → Root cause identified in minutes, not days

**3. Impact Prediction (Future)**
- Before training: "This data distribution shift will likely decrease accuracy by 0.2-0.4%"
- Before deployment: "This model version shows 12% higher false positive rate on segment X"

---

## Target Customer

**Primary**: ML Team Lead at ML-focused company (Series A to Series C)

**Profile**:
- Company: ML product company or ML-heavy tech company
- Team size: 10-50 engineers (mix of data, ML, platform)
- ML maturity: Multiple models in production, 20+ experiments/month
- Pain: Spending 20-30% of time debugging production regressions
- Infrastructure: Already using MLflow/W&B, Airflow, cloud data warehouse
- Budget authority: Can approve $5K-$20K/month tools that save engineering time

**Secondary**: Platform/Infra team owning ML reliability

**Problem they pay to solve**:
- "Why did our recommendation CTR drop 0.5% after yesterday's deployment?"
- "Which training data caused the fraud model to miss 15% more fraud last week?"
- "Every Feast upgrade breaks something - how do we catch this before production?"

---

## Value Proposition

**Customer-facing**: "Stop wasting senior engineering time on ML archaeology. Get root-cause answers in minutes, not days."

**Economics**:
- Current cost of production regression investigation:
  - 2-5 days × senior ML engineer ($150K-$250K salary) = $1,200-$5,000 per incident
  - Assumes 10-20 incidents/year = $12K-$100K/year in engineering time
  - Plus opportunity cost of delayed features

- NanoML value:
  - 10x faster root-cause analysis (minutes vs days)
  - 50% reduction in incidents reaching production (caught in training)
  - 80% reduction in false positive alerts (context-aware)

**Conservative ROI**:
- Save 200-400 hours/year of senior eng time = $50K-$100K value
- Potential pricing: $5K-$15K/month (20-50% of value capture)

---

## Differentiation: Why Not Existing Tools?

### vs MLflow / Weights & Biases
- **They**: Passive experiment tracking ("what did we run?")
- **We**: Active root-cause analysis ("why did this fail?")
- **Gap**: No connection to production outcomes, no data lineage

### vs Monte Carlo / Anomalo (Data Observability)
- **They**: Data pipeline monitoring (schema, freshness, volume)
- **We**: Training data → production outcome causality
- **Gap**: Don't understand ML training or model behavior

### vs Datadog / New Relic (APM)
- **They**: Infrastructure metrics (latency, errors, throughput)
- **We**: ML decision quality (why predictions changed)
- **Gap**: Treat ML models as black boxes

### vs LakeFS / DVC (Data Versioning)
- **They**: Git for data (traceability)
- **We**: Observability + root-cause (why did this version cause issues?)
- **Gap**: No analysis of impact, just versioning

**Our Moat**:
1. **Cross-layer graph** connecting data → training → production
2. **Outcome causality** tracing production shifts to training changes
3. **Context-aware analysis** understanding ML-specific failure modes
4. **Compounding value** - graph becomes irreplaceable after 3-6 months

---

## MVP Phases (12-Week Timeline)

### Phase 1: Foundation (Weeks 1-3)
**Goal**: Basic observability graph + manual root-cause

**Features**:
- Data fingerprinting (content-addressable hashing)
- Training experiment logging integration (MLflow SDK wrapper)
- Production prediction logging (`nanoml.log_prediction()`)
- SQLite/PostgreSQL storage for graph
- CLI: `nanoml graph show` visualizes data → training → production

**Success Criteria**:
- User can see complete lineage for any production prediction
- Graph connects: dataset version → experiment → model → prediction

### Phase 2: Root-Cause Analysis (Weeks 4-6)
**Goal**: Automated root-cause for common failure modes

**Features**:
- Data distribution shift detection (KL divergence, PSI)
- Feature coverage regression detection
- Training/serving skew detection
- Correlation analysis: production metric drop → training data change
- CLI: `nanoml diagnose --production-metric=ctr --date=2026-05-10`

**Success Criteria**:
- Given production regression, identify root-cause training data issue in <5 min
- Support 5 common failure modes (distribution shift, coverage drop, schema change, label noise, serving skew)

### Phase 3: Integration & Polish (Weeks 7-9)
**Goal**: Make it easy to adopt, integrate with existing tools

**Features**:
- MLflow plugin (auto-capture training data fingerprints)
- Airflow sensor (block training if data quality issues detected)
- Slack/PagerDuty integration for alerts
- Web dashboard (read-only view of graph + diagnoses)
- SDK for common ML frameworks (PyTorch, TensorFlow, scikit-learn)

**Success Criteria**:
- <30 min to integrate into existing ML pipeline
- Zero code changes to training scripts (MLflow plugin auto-instruments)

### Phase 4: Pilot & Iteration (Weeks 10-12)
**Goal**: Deploy with 1-2 pilot customers, iterate based on feedback

**Activities**:
- Deploy to pilot customer production environment
- Monitor adoption metrics (predictions logged, diagnoses run)
- Collect feedback on false positive rate, time-to-root-cause
- Document case studies (before/after)

**Success Criteria**:
- 1 customer using in production for 2+ weeks
- 5+ successful root-cause diagnoses (validated by customer)
- <20% false positive rate on alerts
- Positive NPS from pilot users

---

## Go-to-Market Strategy

### Initial Customer Acquisition (Months 1-3)

**Approach**: Problem-first sales (not product-first)

1. **Identify burning pain**:
   - ML teams that had recent production incidents
   - Companies posting ML reliability/debugging jobs
   - Reddit/HN posts about ML debugging frustrations

2. **Free diagnostic offer**:
   - "We'll help you debug your last production regression for free"
   - Use manual analysis + prototype tool
   - Deliver root-cause report + timeline

3. **Convert to pilot**:
   - "This took us 2 hours. It took you 3 days. Want this automated?"
   - 3-month pilot: $2K/month (founder support included)
   - Success metric: 5+ successful diagnoses

### Pricing Model (Post-Pilot)

**Tier 1: Team ($5K/month)**
- Up to 100 experiments/month
- Up to 1M predictions/month logged
- 5 production models monitored
- Slack/email alerts
- Email support

**Tier 2: Company ($15K/month)**
- Unlimited experiments
- Up to 100M predictions/month
- Unlimited models
- Custom alert rules
- Dedicated Slack channel
- Priority support

**Enterprise: Custom**
- On-prem deployment option
- SSO/SAML
- SLA guarantees
- White-glove onboarding

---

## Key Risks & Mitigation

### Risk 1: "We already have MLflow + Datadog, why do we need this?"

**Mitigation**:
- Lead with the problem, not the solution
- Demo root-cause analysis on their past incident (free diagnostic)
- Show time savings: 3 days → 10 minutes
- Position as "glue" connecting their existing tools

### Risk 2: Privacy concerns (training data)

**Mitigation**:
- Don't require raw data export (use fingerprints only)
- On-prem deployment option for Enterprise
- SOC2 compliance from day 1
- Customer owns all data (we're just the index)

### Risk 3: Too domain-specific (won't generalize)

**Mitigation**:
- Start with one vertical (recommendation systems) where we have expertise
- Learn failure mode patterns from pilot customers
- Build extensible framework for custom failure detectors
- Expand to adjacent verticals (fraud, ranking, search) in 6 months

### Risk 4: Integration friction (hard to adopt)

**Mitigation**:
- MLflow plugin = zero code changes
- SDK auto-detects framework (PyTorch/TF)
- Start with read-only observability (no workflow changes)
- Gradually add "gates" (block training on issues) after trust built

### Risk 5: Databricks/MLflow builds this into their platform

**Mitigation**:
- 6-12 month head start (they move slow)
- Platform-agnostic (works with any tool stack)
- Domain expertise moat (we understand ML failure modes deeply)
- Compounding value (graph data becomes irreplaceable)

---

## Success Metrics

### Month 1 (Post-Launch)
- 50 PyPI/npm downloads
- 5 users complete integration (predictions logged)
- 1 user runs first diagnosis
- 10+ conversations with target customers

### Month 3 (Pilot Stage)
- 2 pilot customers in production
- 20+ successful diagnoses logged
- <20% false positive rate validated
- 1 customer case study published
- $5K MRR (from pilots)

### Month 6 (Early Traction)
- 10 paying customers
- $50K MRR
- 80% pilot → paid conversion
- <10% churn
- 1 customer refers peer
- 200+ diagnoses run (across all customers)

### Month 12 (Product-Market Fit Signal)
- $200K ARR
- 30 paying customers
- 2 enterprise deals ($50K+ ACV)
- 60% of customers report "prevented production incident"
- Feature requests clustered around 2-3 themes (clear roadmap)

---

## Open Questions (Requires Validation)

1. **Data Privacy**: Will customers accept fingerprinting approach, or need full on-prem?
   - **Validation**: Ask in customer discovery calls (next 2 weeks)

2. **Integration Effort**: Is MLflow plugin sufficient, or need direct SDK for each framework?
   - **Validation**: Pilot with 1 PyTorch user, 1 TensorFlow user

3. **Alert Threshold**: What false positive rate is acceptable? <10%? <20%?
   - **Validation**: A/B test with pilot customers

4. **Pricing Sensitivity**: Is $5K/month too high for Series A startups?
   - **Validation**: Survey 10 target customers on willingness-to-pay

5. **Vertical Focus**: Start with recommendations, or be domain-agnostic from day 1?
   - **Validation**: Check if failure modes generalize across domains (literature review + customer interviews)

---

## Pivot Rationale: Why Shift from GPU Waste Control?

**Previous Design (v2)**: Pre-execution CLI gate preventing duplicate ML experiments

**Why Pivot**:

1. **Broader Problem Space**:
   - GPU waste is one symptom of fragmented ML systems
   - Root-cause analysis addresses multiple pain points (not just duplication)
   - Observability has higher ceiling (every ML company needs this vs niche duplicate prevention)

2. **Stronger Moat**:
   - GPU waste control = feature (MLflow could add this)
   - Observability platform = compounding data moat (graph becomes irreplaceable)

3. **Better Economics**:
   - Duplicate prevention: Save $10K-$15K/month waste → $1K-$3K pricing
   - Root-cause analysis: Save 200-400 eng hours/year → $5K-$15K pricing
   - 3-5x higher willingness-to-pay for time savings vs cost savings

4. **Customer Validation**:
   - HF0, Pearx, Point72 references emphasize observability need
   - User feedback: "Why did my model regress?" is more painful than "Did I run this before?"

5. **Agent Future**:
   - Agent-driven ML workflows amplify cascading failure risk
   - Unified observability reduces risk in agent-orchestrated pipelines
   - Better positioned for "ML systems need governed memory for agents"

**Risk**: Larger scope, longer time-to-value

**Mitigation**: Start with narrow MVP (just root-cause), expand over 6-12 months

---

## Next Steps (This Week)

1. **Customer Validation** (3-5 conversations):
   - "Tell me about the last time your production ML model regressed"
   - "How long did it take to find root cause?"
   - "Would you pay $5K/month to reduce that 10x?"

2. **Technical Spike** (2-3 days):
   - Prototype data fingerprinting (murmur3 vs xxhash vs SHA)
   - Prototype MLflow plugin (auto-capture training data metadata)
   - Validate graph storage (SQLite vs PostgreSQL vs graph DB)

3. **Competitive Analysis** (1 day):
   - Deep dive: Monte Carlo, Anomalo, Datadog ML monitoring
   - Document exact gaps (what can't they do?)
   - Build comparison matrix for sales conversations

4. **Refine Pitch** (1 day):
   - Write 100-word YC application description
   - Create 3-slide deck (problem, solution, why now)
   - Record 2-min demo video (mockup UI)

**Decision Point** (End of Week):
- Commit to observability pivot OR return to GPU waste control
- Based on: Customer validation + technical feasibility + founder conviction

---

## Appendix: Related Research & References

**Observability**:
- HF0, Pearx, Point72: "Root-cause analysis for ML training regressions"
- "Observability for training data systems"
- "Datadog for ML decisions, not ML metrics"

**Fragmentation Problem**:
- Two dimensions: Team fragmentation (data vs ML engineers) + Infrastructure fragmentation (MLflow, Feast, etc.)
- "Why it's still so painful to build ML pipelines in 2026? Tools are fragmented and overkill"

**Agent Future**:
- "Future ML systems need governed experiment memory for agents"
- "In the future, agents will not be used in one vertical area, they will advance your ML system connecting different components"
- "Human role will be more like supervisor"

**Market Gaps**:
- Anomalo: Great for data quality monitoring, but doesn't connect to model outcomes
- MLflow: Tracks experiments, but no production outcome linkage
- Datadog: Infrastructure metrics, treats ML as black box
- LakeFS: Data versioning, but no impact analysis

**Customer Pain Quotes** (from research):
- "We rolled our own implementation because nothing I could find came close to what we need"
- "40-60% of on-call time goes to triaging alerts that turn out to be noise"
- "Alert fatigue is the silent killer of data quality programs"
