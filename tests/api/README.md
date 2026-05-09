# API Tests

This directory contains unit tests and integration tests for the DataVint API.

## Test Files

### Unit Tests (no server required)

These tests run standalone without requiring the backend server:

- **`test_skill_simple.py`** - Tests individual skill execution
  - Creates test dataset
  - Executes `check-completeness` skill
  - Verifies output format and content

- **`test_routing_layer.py`** - Tests routing decision logic
  - Tests command matching (`/check-completeness`)
  - Tests pattern matching ("check missing values")
  - Tests keyword matching ("imbalance")
  - Tests LLM fallback for unmatched queries
  - Reports routing metrics (70% skill, 30% LLM)

- **`test_profile_missing_values.py`** - Tests `vint.profile()` compatibility
  - Tests the exact pattern used in LLM-generated code
  - Verifies issue serialization for API responses
  - Validates missing value detection accuracy

### Integration Test (requires running server)

- **`test_e2e_chatbox.py`** - End-to-end chatbox flow test
  - Requires backend server running on http://localhost:8000
  - Tests full flow: CSV upload → routing → execution → response
  - Covers skill routing, LLM routing, and slash commands
  - Tests metrics endpoint

## Running Tests

### Quick Run (all unit tests)

```bash
cd /Users/duochen/Desktop/career/datavint

# Run all unit tests
for test in tests/api/test_*.py; do
    [ "$(basename $test)" != "test_e2e_chatbox.py" ] && python3 "$test"
done
```

### Individual Tests

```bash
# Simple skill test
python3 tests/api/test_skill_simple.py

# Routing layer test
python3 tests/api/test_routing_layer.py

# Profile compatibility test
python3 tests/api/test_profile_missing_values.py
```

### E2E Integration Test

```bash
# Terminal 1: Start backend server
uvicorn server.api.main:app --reload

# Terminal 2: Run E2E test
python3 tests/api/test_e2e_chatbox.py
```

## Pre-commit Hook

The `.git/hooks/pre-commit` hook automatically runs all tests before allowing commits.

If tests fail:
```
❌ COMMIT BLOCKED: Tests failed
```

To bypass (not recommended):
```bash
git commit --no-verify
```

## Expected Output

### Unit Tests
```
✅ test_skill_simple.py passed
✅ test_routing_layer.py passed
✅ test_profile_missing_values.py passed
```

### E2E Test
```
✅ Server is running!
✅ TEST 1 PASSED - Skill Routing
✅ TEST 2 PASSED - LLM Routing
✅ TEST 3 PASSED - Slash Command
✅ TEST 4 PASSED - Metrics Endpoint
✅ ALL TESTS PASSED (4/4)
```

## Test Coverage

### Routing Coverage
- ✅ Command match (`/check-completeness`, `/check-imbalance`)
- ✅ Pattern match ("check missing values", "find imbalance")
- ✅ Keyword match ("completeness", "cardinality")
- ✅ LLM fallback (unmatched queries)

### Skill Coverage
- ✅ `check-completeness` - Missing values analysis
- ✅ `check-imbalance` - Class distribution analysis
- ✅ `check-cardinality` - High cardinality detection
- ⏳ `check-distinctness` - Placeholder
- ⏳ `check-entropy` - Placeholder
- ⏳ `check-uniqueness` - Placeholder

### DataVint SDK Coverage
- ✅ `vint.profile()` on datasets with missing values
- ✅ Boolean dtype handling (NumPy 2.0+ compatibility)
- ✅ Issue serialization (`issue.to_dict()`)
- ✅ Statistics serialization (`stats.to_dict()`)

## Troubleshooting

### Server not running (E2E test)
```
❌ ERROR: Backend server not running!

To start the server:
  cd /Users/duochen/Desktop/career/datavint
  uvicorn server.api.main:app --reload
```

### NumPy boolean error
If you see `numpy boolean subtract` error:
- Fixed in `datavint/statistics.py:204` (boolean dtype check)
- Update to latest commit

### Import errors
```
ModuleNotFoundError: No module named 'server'
```
Tests include Python path setup - should auto-resolve. If not:
```bash
export PYTHONPATH=/Users/duochen/Desktop/career/datavint:$PYTHONPATH
```

## CI/CD Integration

These tests run automatically on:
- **Pre-commit** - All unit tests run before commit
- **Manual E2E** - Run before deploying to production

Future: Add to GitHub Actions workflow
