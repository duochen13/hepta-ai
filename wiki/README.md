# DataVint Documentation

Documentation for DataVint data quality detection SDK.

## 📚 Directory Structure

```
docs/
├── README.md                    # This file
├── api/                         # Public API reference
│   └── profiling.md            # Profiling API documentation
├── features/                    # Feature specs & implementation notes
│   └── data-profiling.md       # Data profiling feature summary
└── changelog/                   # Product design & architecture decisions
    └── 2026-04-27-datavint-design.md  # Main product design spec
```

## 🚀 Quick Links

### For Users

- **[Getting Started](../notebooks/GETTING_STARTED.md)** - 3-minute setup guide
- **[Profiling API Reference](api/profiling.md)** - Complete API docs for profiling features
- **[Detectors API Reference](api/detectors.md)** - Complete API docs for issue detection
- **[Quickstart Notebook](../notebooks/quickstart.ipynb)** - 5-minute interactive tutorial

### For Developers

- **[Product Design Spec](changelog/2026-04-27-datavint-design.md)** - Complete product vision and architecture
- **[Data Profiling Feature](features/data-profiling.md)** - Implementation details and design decisions

## 📖 Documentation by Topic

### Data Profiling

**What:** Quick dataset overview before running quality checks

**Docs:**
- [API Reference](api/profiling.md) - Function signatures and examples
- [Feature Summary](features/data-profiling.md) - Implementation details
- [Jupyter Notebooks](../notebooks/) - Interactive tutorials

**Quick example:**
```python
import datavint as dv

# Quick profile
dv.profile_dataset("train.csv", label_col="click")

# Compare train vs test
dv.compare_datasets("train.csv", "test.csv", label_col="click")
```

### Statistics Generation (v0.1)

**What:** Detailed per-feature statistics for quality detection

**Docs:**
- Coming soon: `docs/api/statistics.md`

**Quick example:**
```python
stats = dv.generate_statistics("train.csv", label_col="click")
print(f"Rows: {stats.n_rows:,}")
print(f"Duplicate rate: {stats.duplicate_rate:.1%}")
```

### Issue Detection (v0.1)

**What:** Automated detection of 6 quality issue types

**Docs:**
- [API Reference](api/detectors.md) - Complete detector documentation
- [Feature Summary](features/issue-detection.md) - Implementation details (coming soon)

**Quick example:**
```python
issues = dv.detect_issues(statistics=train_stats, serving_statistics=test_stats)
dv.display_issues(issues)
```

### Manifest Generation (v0.2+)

**What:** Automatic data cleaning manifests

**Status:** Coming in v0.2

## 🗂️ Other Resources

### Notebooks
- [quickstart.ipynb](../notebooks/quickstart.ipynb) - 5-minute intro
- [data_profiling_demo.ipynb](../notebooks/data_profiling_demo.ipynb) - Complete guide
- [Notebooks README](../notebooks/README.md) - Notebook guide

### Examples
- [demo_profiling.py](../examples/demo_profiling.py) - Python examples
- [quick_profile.py](../examples/quick_profile.py) - Simple workflow

### Tests
- [tests/](../tests/) - Unit and integration tests

## 📝 Documentation Standards

### For API Docs (`docs/api/`)

**Should include:**
- Function signatures with type hints
- Parameter descriptions
- Return value descriptions
- Usage examples
- Common use cases
- Error handling notes

**Format:** Markdown with code blocks

### For Feature Docs (`docs/features/`)

**Should include:**
- Feature overview
- Design decisions and rationale
- Implementation details
- Performance characteristics
- Testing status
- Future enhancements

**Format:** Markdown with code blocks

### For Changelog & Design Specs (`docs/changelog/`)

**Should include:**
- Product vision
- User personas
- Technical architecture
- MVP scope
- Roadmap
- Competitive analysis
- Architecture decision records

**Format:** Markdown (comprehensive, timestamped)

## 🔄 Keeping Docs Updated

**When adding a new feature:**
1. Add API reference to `docs/api/`
2. Add feature summary to `docs/features/`
3. Update this README with quick links
4. Add examples to `examples/`
5. Create notebook if needed

**When changing existing API:**
1. Update API reference docs
2. Update examples
3. Update notebooks
4. Add migration guide if breaking change

## 🤝 Contributing to Docs

**Guidelines:**
- Keep docs concise and example-driven
- Use consistent formatting (see existing docs)
- Test all code examples before committing
- Add links between related docs

## 📧 Questions?

- Check [notebooks/GETTING_STARTED.md](../notebooks/GETTING_STARTED.md) for setup help
- See [examples/](../examples/) for working code
- Read [changelog/2026-04-27-datavint-design.md](changelog/2026-04-27-datavint-design.md) for architecture details
