# GitHub Actions Workflows

Comprehensive CI/CD pipelines for Data Lineage Visualizer v4.3.3.

## Overview

| Workflow | Trigger | Purpose | Duration |
|----------|---------|---------|----------|
| **CI Validation** | Push to main/develop/claude/*, PRs | Full CI pipeline (backend, frontend, E2E) | ~20 min |
| **PR Validation** | PR opened/updated | PR quality checks, parser warnings | ~5 min |
| **Parser Validation** | Parser file changes | Comprehensive parser regression testing | ~20 min |

---

## Workflow Details

### 1. CI Validation (`ci-validation.yml`)

**Purpose:** Main CI pipeline for all code changes

**Triggers:**
- Push to `main`, `develop`, `claude/**` branches
- Pull requests to `main`, `develop`

**Jobs:**

1. **Backend Tests** (15 min)
   - Python unit tests with coverage
   - Integration tests (64 tests, skip without data)
   - Coverage upload to Codecov

2. **User-Verified Test Cases** (10 min)
   - Golden test cases for parser regression prevention
   - Runs if `tests/unit/test_parser_golden_cases.py` exists

3. **Parser Baseline** (20 min, conditional)
   - Runs only if parser files changed
   - Compares parsing results between branches
   - Detects regressions in success rate

4. **Frontend Tests** (15 min)
   - TypeScript type checking
   - Unit tests (when configured)

5. **Frontend E2E** (20 min)
   - Playwright E2E tests (90+ tests)
   - Chromium browser only in CI
   - Uploads reports on failure

6. **Code Quality** (10 min)
   - Ruff linting (non-blocking)
   - MyPy type checking (non-blocking)

7. **Documentation Validation** (5 min)
   - Checks for outdated config references
   - Validates version consistency

8. **CI Success Summary**
   - Required for PR merge
   - Aggregates all job results

**Status Badge:**
```markdown
[![CI Status](https://github.com/USER/REPO/workflows/CI%20Validation/badge.svg)](https://github.com/USER/REPO/actions/workflows/ci-validation.yml)
```

---

### 2. PR Validation (`pr-validation.yml`)

**Purpose:** Fast PR quality checks and warnings

**Triggers:**
- Pull request opened, synchronized, reopened

**Jobs:**

1. **PR Checks** (5 min)
   - ✅ Conventional commits format validation
   - ⚠️ Parser change warnings (MANDATORY journal check)
   - ℹ️ Documentation update reminders

2. **Baseline Comparison** (20 min, conditional)
   - Runs only if parser files modified
   - Compares PR vs main branch parsing results
   - **BLOCKS MERGE** if regression detected
   - Uploads comparison artifacts (14 days)

3. **Auto Label** (1 min)
   - Automatically suggests PR labels
   - Based on changed files (parser, frontend, backend, docs, testing)

**Parser Change Warning:**
When parser files modified, shows:
```
⚠️  Parser files modified in this PR

📋 MANDATORY Requirements:
  1. ⚠️  MUST check docs/PARSER_CHANGE_JOURNAL.md BEFORE changes
  2. ✅ User-verified test cases will validate no regressions
  3. ✅ Parser validation workflow will run comprehensive checks
  4. ✅ Integration tests (64 tests) will validate expectations
  5. ⚠️  Review parser changes carefully (ErrorLevel, RAISE mode)
```

---

### 3. Parser Validation (`parser-validation.yml`) ⭐ NEW

**Purpose:** Comprehensive validation for parser changes

**Triggers:**
- Pull requests modifying parser files
- Push to `claude/**` branches with parser changes

**Monitored Files:**
- `lineage_v3/parsers/quality_aware_parser.py`
- `lineage_v3/parsers/sql_cleaning_rules.py`
- `lineage_v3/rules/**/*.yaml`
- `tests/unit/test_parser_golden_cases.py`

**Jobs:**

1. **Pre-flight Checks** (5 min)
   - ⚠️ Warns if journal not consulted
   - Lists modified parser files
   - Validates critical documentation exists

2. **User-Verified Test Cases** (10 min)
   - Runs golden cases: `test_parser_golden_cases.py`
   - **BLOCKS MERGE** if any case fails (regression!)

3. **Parser Unit Tests** (15 min)
   - Runs all parser unit tests with coverage
   - Uploads coverage report
   - **BLOCKS MERGE** if tests fail

4. **Parser Integration Tests** (20 min)
   - Runs 64 pytest integration tests
   - Tests validate parser v4.3.3 expectations:
     - ✅ 100% success rate
     - ✅ 80%+ perfect confidence (100)
     - ✅ Valid confidence distribution
     - ✅ Phantom detection working
   - Tests skip gracefully without workspace database
   - **BLOCKS MERGE** if tests fail

5. **Baseline Comparison** (15 min, PRs only)
   - Compares confidence distribution
   - **BLOCKS MERGE** if confidence 100% drops >1%
   - Uploads baseline artifacts (30 days)

6. **Parser Validation Summary**
   - Required for PR merge
   - Aggregates all validation results

**What Gets Validated:**

| Validation | Tests | Blocks Merge | Duration |
|------------|-------|--------------|----------|
| Unit tests | All parser tests | ✅ Yes | 15 min |
| Golden cases | User-verified SPs | ✅ Yes | 10 min |
| Integration tests | 64 comprehensive tests | ✅ Yes | 20 min |
| Baseline comparison | Confidence distribution | ✅ Yes | 15 min |

---

## Integration Tests (NEW)

**Location:** `tests/integration/`
**Count:** 64 tests
**Coverage:** 6 validation modules

### Test Modules

1. **test_database_validation.py** (13 tests)
   - Overall statistics (100% success rate)
   - Confidence distribution
   - Average dependencies
   - Specific test SPs
   - Top SPs by dependency count

2. **test_sp_parsing_details.py** (8 tests)
   - Detailed SP parsing results
   - Phantom object detection
   - Expected dependencies validation
   - Table name verification

3. **test_confidence_analysis.py** (11 tests)
   - Confidence 85/75 analysis
   - Completeness ranges
   - Pattern analysis for lower confidence
   - Cleaning logic assessment

4. **test_sqlglot_performance.py** (14 tests)
   - SQLGlot enhancement impact
   - Completeness analysis
   - Tables added by SQLGlot
   - Phantom detection

5. **test_failure_analysis.py** (8 tests)
   - Failure categorization
   - Root cause analysis
   - Pattern matching
   - Cleaning logic validation

6. **test_sp_deep_debugging.py** (10 tests)
   - Regex extraction validation
   - SQLGlot WARN/RAISE mode behavior
   - Problematic pattern detection
   - Debugging workflow validation

### Integration Test Behavior

**With Workspace Database:**
```bash
$ pytest tests/integration/ -v
============================== test session starts ===============================
collected 64 items

test_database_validation.py::test_all_sps_have_dependencies PASSED       [  1%]
test_database_validation.py::test_confidence_values_are_valid PASSED     [  3%]
...
============================== 64 passed in 12.34s ===============================
```

**Without Workspace Database (CI):**
```bash
$ pytest tests/integration/ -v
============================== test session starts ===============================
collected 64 items

test_database_validation.py::test_all_sps_have_dependencies SKIPPED      [  1%]
test_database_validation.py::test_confidence_values_are_valid SKIPPED    [  3%]
...
============================== 64 skipped in 0.22s ===============================
```

**Key Points:**
- ✅ Tests skip gracefully without data (normal in CI)
- ✅ No test failures, just skips
- ✅ For full validation, run locally with real data
- ✅ CI still validates using unit tests + golden cases

---

## Workflow Status

### Current Status

| Workflow | Status | Last Run | Notes |
|----------|--------|----------|-------|
| CI Validation | ✅ Active | Every push | Full pipeline |
| PR Validation | ✅ Active | Every PR | Fast checks |
| Parser Validation | ⭐ NEW | Parser changes | Comprehensive |

### Required for Merge

**All PRs:**
- ✅ CI Validation must pass
- ✅ PR Validation must pass (or show warnings)

**Parser Changes:**
- ✅ Parser Validation must pass (all 5 jobs)
- ✅ User-verified cases must pass (if available)
- ✅ No baseline regression (confidence maintained)

---

## Local Testing

### Run All Tests Locally

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires workspace database)
pytest tests/integration/ -v

# Specific module
pytest tests/integration/test_database_validation.py -v

# With coverage
pytest tests/ -v --cov=lineage_v3 --cov=api --cov-report=term
```

### Run Parser Validation Steps Locally

```bash
# 1. Check journal (manual)
cat docs/PARSER_CHANGE_JOURNAL.md

# 2. Run user-verified cases
pytest tests/unit/test_parser_golden_cases.py -v

# 3. Run parser unit tests
pytest tests/unit/ -k parser -v

# 4. Run integration tests
pytest tests/integration/ -v

# 5. Compare baseline (requires workspace)
python scripts/testing/check_parsing_results.py > baseline_before.txt
# ... make changes ...
python scripts/testing/check_parsing_results.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt
```

---

## Troubleshooting

### Integration Tests Skipping

**Symptom:** All 64 integration tests skip in CI
**Cause:** No workspace database (`data/lineage_workspace.duckdb`)
**Expected:** This is normal without real production data
**Solution:** Tests validate with unit tests + golden cases instead

### Parser Validation Failing

**Symptom:** Parser validation workflow fails
**Common causes:**
1. User-verified golden cases failing → Regression detected!
2. Baseline confidence decreased → Parser quality degraded
3. Unit tests failing → Code logic error

**Solution:**
1. Review failed job logs
2. Run tests locally to debug
3. Check `docs/PARSER_CHANGE_JOURNAL.md` for known issues

### Baseline Comparison Fails

**Symptom:** "REGRESSION DETECTED" in baseline job
**Cause:** Confidence 100% percentage decreased by >1%
**Impact:** **Blocks PR merge**
**Solution:**
1. Review parser changes carefully
2. Check if regression is expected (new SQL patterns)
3. Update journal if fixing known issue
4. If expected, document why quality decreased

---

## Adding New Workflows

### Workflow Template

```yaml
name: My Custom Workflow

on:
  push:
    branches: [ main ]

jobs:
  my-job:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python 3.10
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        cache: 'pip'

    - name: Run custom validation
      run: |
        echo "Running validation..."
```

### Best Practices

1. **Timeouts:** Always set realistic `timeout-minutes`
2. **Caching:** Use `cache: 'pip'` for Python, `cache: 'npm'` for Node.js
3. **Artifacts:** Upload important results with `retention-days`
4. **Conditional:** Use `if:` for optional jobs
5. **Dependencies:** Use `needs:` for job ordering
6. **Status:** Add summary job for PR merge requirements

---

## References

- **Parser Documentation:** `docs/PARSER_CRITICAL_REFERENCE.md`
- **Change Journal:** `docs/PARSER_CHANGE_JOURNAL.md`
- **Technical Guide:** `docs/PARSER_TECHNICAL_GUIDE.md`
- **Integration Tests:** `tests/integration/README.md` (if exists)
- **GitHub Actions Docs:** https://docs.github.com/en/actions

---

**Last Updated:** 2025-11-14
**Version:** v4.3.3
**Integration Tests:** 64 tests across 6 modules
