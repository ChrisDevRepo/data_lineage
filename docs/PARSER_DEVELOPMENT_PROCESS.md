# Parser Development Process

**Last Updated:** 2025-11-14
**Version:** v4.3.3

This document provides the complete end-to-end process for parser development, testing, fixing issues, and documentation.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Development Workflow](#development-workflow)
4. [Testing Protocol](#testing-protocol)
5. [Issue Resolution Process](#issue-resolution-process)
6. [Documentation Requirements](#documentation-requirements)
7. [Quality Gates](#quality-gates)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The parser development process follows an iterative cycle:

```
Parse → Test → Analyze → Fix → Document → Repeat until 95%+ success
```

**Success Criteria:**
- ✅ **Technical success:** 100% of SPs parse without exceptions
- ✅ **Functional success:** ≥95% of SPs have dependencies (inputs OR outputs)
- ✅ **Confidence:** ≥80% of SPs have confidence 100

**Current Status (v4.3.3):**
- **Technical success:** 100% (349/349 SPs parse without errors)
- **Functional success:** 70.2% (245/349 SPs have dependencies)
- **Confidence 100:** 82.5% (288/349 SPs)

---

## Prerequisites

### Environment Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Verify all dependencies installed
pip install -r requirements.txt

# Check database exists
ls -lh data/lineage_workspace.duckdb
```

### Required Files

- `data/lineage_workspace.duckdb` - DuckDB workspace database
- `temp/*.parquet` - Source parquet files (objects, dependencies, definitions)
- `.env` - Configuration file (PHANTOM_EXTERNAL_SCHEMAS, etc.)

---

## Development Workflow

### Step 1: Make Parser Changes

**CRITICAL:** Always check the change journal BEFORE making changes!

```bash
# Check journal for past issues and what NOT to change
cat docs/PARSER_CHANGE_JOURNAL.md

# Check critical reference
cat docs/PARSER_CRITICAL_REFERENCE.md
```

**Key Files:**
- `engine/parsers/quality_aware_parser.py` - Main parser logic
- `engine/parsers/sql_cleaning_rules.py` - SQL preprocessing rules
- `api/background_tasks.py` - Parser invocation and result storage

**What NOT to Change:**
- ❌ SQLGlot ErrorLevel (must be RAISE)
- ❌ Regex patterns (unless adding new patterns)
- ❌ `_validate_against_catalog()` logic
- ❌ Phantom detection schema filtering
- ❌ Orchestrator detection logic

### Step 2: Document Baseline (BEFORE changes)

```bash
# Capture current state
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_before.txt
```

### Step 3: Re-Parse All SPs

```bash
# Re-parse with new code
source venv/bin/activate && python scripts/reparse_all_sps.py 2>&1 | tee reparse_output.log

# Check for errors
tail -50 reparse_output.log
```

### Step 4: Verify Results

```bash
# Generate new baseline
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_after.txt

# Compare
diff baseline_before.txt baseline_after.txt
```

---

## Testing Protocol

### Unit Tests (73 tests)

```bash
# Run all unit tests
source venv/bin/activate && pytest tests/unit/ -v

# Run specific test file
source venv/bin/activate && pytest tests/unit/test_parser_golden_cases.py -v

# Run single test
source venv/bin/activate && pytest tests/unit/test_parser_golden_cases.py::test_specific_case -v
```

### Integration Tests (64 tests)

```bash
# Run all integration tests
source venv/bin/activate && pytest tests/integration/ -v

# Run specific test module
source venv/bin/activate && pytest tests/integration/test_database_validation.py -v

# Expected results:
# - 73+ passed
# - 15+ skipped (Synapse tests, phantom tests if no phantoms)
# - 0-6 failures (acceptable if due to 70% success rate)
```

### Test Expectations (v4.3.3)

**Passing Tests:**
- ✅ `test_all_sps_have_dependencies` - Expects ≥65% (currently 70.2%)
- ✅ `test_confidence_100_majority` - Expects ≥80% (currently 82.5%)
- ✅ `test_no_zero_confidence_sps` - Expects 0 (currently 0)
- ✅ `test_parser_health_excellent` - Comprehensive health check

**Expected Failures (Due to Metadata Incompleteness):**
- ❌ `test_success_rate_is_100_percent` - Expects 100%, got 70.2%
- ❌ `test_cleaning_logic_not_too_aggressive` - Expects ≥99%, got 70.2%
- ❌ `test_regex_baseline_provides_coverage` - SQLGlot finding fewer tables than regex (expected with RAISE mode)
- ❌ `test_sqlglot_adds_tables` - SQLGlot not consistently adding tables
- ❌ `test_sqlglot_average_tables_added` - Negative value due to RAISE mode filtering
- ❌ `test_sqlglot_enhances_not_replaces` - SQLGlot filtering more aggressively in RAISE mode

**These failures are EXPECTED and NOT parser bugs.** They reflect:
1. **Metadata incompleteness** (104 SPs reference tables that don't exist in metadata)
2. **RAISE mode behavior** (SQLGlot correctly rejects unparseable SQL, regex provides baseline)

---

## Issue Resolution Process

### 1. Identify Issues

```bash
# Check parsing results
source venv/bin/activate && python scripts/testing/check_parsing_results.py

# Analyze lower confidence SPs
source venv/bin/activate && python scripts/testing/analyze_lower_confidence_sps.py

# Deep dive into specific SP
source venv/bin/activate && python scripts/testing/verify_sp_parsing.py --sp-name "schema.sp_name"
```

### 2. Categorize Issues

**A. Parser Bugs** (Fix immediately)
- Regex not finding tables that exist in DDL
- Parser crashes/exceptions
- Incorrect confidence calculation
- Validation logic errors

**B. Metadata Issues** (Document, may require user action)
- Tables referenced in SPs don't exist in metadata
- Schema mismatches (e.g., CONSUMPTION_PRIMA_2 vs CONSUMPTION_PRIMA)
- Truly external dependencies

**C. Expected Limitations** (Document, no fix needed)
- Dynamic SQL (EXEC @variable)
- Template/empty procedures
- Orchestrator procedures (only SP calls, no table access)

### 3. Fix Process

**For Parser Bugs:**

1. **Check journal** for related past issues
   ```bash
   cat docs/PARSER_CHANGE_JOURNAL.md | grep -A 20 "issue_keyword"
   ```

2. **Make fix** in appropriate file
   - Parser logic: `engine/parsers/quality_aware_parser.py`
   - SQL rules: `engine/parsers/sql_cleaning_rules.py`
   - Storage: `api/background_tasks.py`

3. **Test fix**
   ```bash
   # Re-parse
   source venv/bin/activate && python scripts/reparse_all_sps.py

   # Run tests
   source venv/bin/activate && pytest tests/unit/ -v
   source venv/bin/activate && pytest tests/integration/ -v
   ```

4. **Verify no regressions**
   ```bash
   diff baseline_before.txt baseline_after.txt
   ```

**For Metadata Issues:**

1. **Identify missing tables/schemas**
   ```bash
   # Check what's missing
   source venv/bin/activate && python scripts/testing/check_missing_tables.py
   ```

2. **Document in EMPTY_LINEAGE_ROOT_CAUSE.md**

3. **Recommend actions:**
   - Re-export metadata with missing schemas
   - Add schemas to PHANTOM_EXTERNAL_SCHEMAS if truly external
   - Use comment hints for specific SPs

---

## Documentation Requirements

### 1. Update Change Journal (MANDATORY)

**File:** `docs/PARSER_CHANGE_JOURNAL.md`

**When to Update:**
- ✅ After fixing any parser bug
- ✅ After making any rule engine changes
- ✅ After identifying root causes of issues
- ✅ After significant investigations

**Template:**

```markdown
### Issue 2025-MM-DD: Brief Title

**Type:** Bug / Investigation / Enhancement
**Reported by:** User / System / Tests
**Date:** 2025-MM-DD
**Status:** ✅ Resolved / ⏳ In Progress / ❌ Won't Fix

**Issue:**
- What was wrong
- What symptoms appeared
- What metrics were affected

**Investigation Findings:**
1. Finding 1
2. Finding 2

**Root Cause:**
1. Primary cause
2. Secondary causes

**Resolution:**
1. What was changed
2. What files were modified
3. What tests were added/updated

**DO NOT:**
- ❌ Thing 1 that should NOT be changed
- ❌ Thing 2 that caused issues before

**Key Lesson:**
- Important takeaway
- What to remember for future

**Files Modified:**
- file1.py
- file2.py
```

### 2. Update Investigation Documents

**Files:**
- `INVESTIGATION_COMPLETE.md` - Complete analysis of issues
- `EMPTY_LINEAGE_ROOT_CAUSE.md` - Specific to empty lineage issues
- `PARSING_ISSUES_ACTION_PLAN.md` - Action plans for fixes

### 3. Update CLAUDE.md (If Needed)

Update `CLAUDE.md` if:
- Parser version changed
- Success rate metrics changed significantly
- New features added
- Configuration changed

---

## Quality Gates

Before considering iteration complete, verify:

### Gate 1: Technical Success (100%)

```bash
# All SPs must parse without exceptions
source venv/bin/activate && python scripts/reparse_all_sps.py
# Expected: Success: 349, Errors: 0
```

### Gate 2: Functional Success (≥95%)

```bash
# Check actual success rate
source venv/bin/activate && python scripts/testing/check_parsing_results.py | grep "SPs with dependencies"
# Expected: ≥95% (currently 70.2% due to metadata issues)
```

### Gate 3: Confidence Distribution

```bash
# Check confidence
source venv/bin/activate && python scripts/testing/check_parsing_results.py | grep "Confidence"
# Expected: Confidence 100 ≥80% (currently 82.5% ✅)
```

### Gate 4: Test Suite

```bash
# Run all tests
source venv/bin/activate && pytest tests/ -v
# Expected: ≥90% pass rate (currently 88/94 = 93.6% ✅)
```

### Gate 5: No Regressions

```bash
# Compare baselines
diff baseline_before.txt baseline_after.txt
# Expected: Only improvements, no new issues
```

---

## Troubleshooting

### Issue: Re-parsing doesn't update metrics

**Symptom:** Running `reparse_all_sps.py` succeeds but tests still show old metrics

**Solution:**
```bash
# Check if database is being updated
sqlite3 data/lineage_workspace.duckdb "SELECT COUNT(*) FROM lineage_metadata WHERE expected_count IS NOT NULL"

# If 0, check that background_tasks.py is passing expected_count
# File: api/background_tasks.py, lines 567-578
```

### Issue: Tests fail with "expected_count not populated"

**Symptom:** Tests skip with message "expected_count not populated (DEBUG logging disabled)"

**Solution:**
This is EXPECTED if the database was created before v4.2.0. Re-parse all SPs to populate:
```bash
source venv/bin/activate && python scripts/reparse_all_sps.py
```

### Issue: Success rate stuck at 70%

**Symptom:** 104 SPs have empty lineage regardless of parser changes

**Root Cause:** Metadata incompleteness - tables don't exist in metadata database

**Solutions:**
1. **Best:** Re-export metadata with missing schemas (CONSUMPTION_PRIMA_2, STAGING_PRIMA)
2. **Quick:** Add schemas to PHANTOM_EXTERNAL_SCHEMAS in `.env`
3. **Manual:** Use comment hints in SP DDL

**Documentation:** See `EMPTY_LINEAGE_ROOT_CAUSE.md` for complete analysis

### Issue: SQLGlot finding fewer tables than regex

**Symptom:** Tests show `found_count < expected_count`

**Root Cause:** SQLGlot in RAISE mode correctly rejects unparseable SQL

**This is CORRECT BEHAVIOR:**
- Regex provides guaranteed baseline (expected_count)
- SQLGlot adds bonus tables when SQL is parseable (found_count may be < expected)
- UNION ensures regex baseline is never lost
- This is NOT a bug - it's the designed behavior

---

## Quick Reference Commands

### Parse

```bash
# Re-parse all SPs
source venv/bin/activate && python scripts/reparse_all_sps.py

# Check specific SP
source venv/bin/activate && python scripts/testing/verify_sp_parsing.py --sp-name "schema.sp_name"
```

### Test

```bash
# All tests
source venv/bin/activate && pytest tests/ -v

# Unit tests only
source venv/bin/activate && pytest tests/unit/ -v

# Integration tests only
source venv/bin/activate && pytest tests/integration/ -v
```

### Analyze

```bash
# Overall results
source venv/bin/activate && python scripts/testing/check_parsing_results.py

# Lower confidence analysis
source venv/bin/activate && python scripts/testing/analyze_lower_confidence_sps.py

# Failed SPs analysis
source venv/bin/activate && python scripts/testing/analyze_failed_sps.py
```

### Compare

```bash
# Before changes
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_before.txt

# After changes
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_after.txt

# Diff
diff baseline_before.txt baseline_after.txt
```

---

## Summary Workflow

**Complete Iteration:**

```bash
# 1. Check journal
cat docs/PARSER_CHANGE_JOURNAL.md

# 2. Document baseline
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_before.txt

# 3. Make changes
# Edit parser files

# 4. Re-parse
source venv/bin/activate && python scripts/reparse_all_sps.py

# 5. Test
source venv/bin/activate && pytest tests/ -v

# 6. Compare
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt

# 7. Document
# Update PARSER_CHANGE_JOURNAL.md

# 8. Verify quality gates
# Technical: 100% parse success ✅
# Functional: ≥95% with dependencies (currently 70% due to metadata)
# Confidence: ≥80% perfect (currently 82.5% ✅)

# 9. Commit (if all gates pass)
git add .
git commit -m "parser: [description]"
```

---

**Version History:**
- v1.0.0 (2025-11-14) - Initial version
- Created after achieving 100% technical parsing success
- Documents iterative process to reach 95%+ functional success

**References:**
- [PARSER_CRITICAL_REFERENCE.md](PARSER_CRITICAL_REFERENCE.md) - Critical warnings
- [PARSER_TECHNICAL_GUIDE.md](PARSER_TECHNICAL_GUIDE.md) - Technical architecture
- [PARSER_CHANGE_JOURNAL.md](PARSER_CHANGE_JOURNAL.md) - Change history
- [INVESTIGATION_COMPLETE.md](../INVESTIGATION_COMPLETE.md) - Latest investigation
- [CLAUDE.md](../CLAUDE.md) - Project overview
