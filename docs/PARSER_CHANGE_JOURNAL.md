# Parser Change Journal

**Purpose:** Track parser changes to avoid repeating mistakes

**Source:** Auto-generated from `tests/fixtures/user_verified_cases/*.yaml`

## 🚨 CRITICAL: Check This Journal BEFORE Making Changes

**⚠️ MANDATORY REQUIREMENT:**
- **Rule engine changes** → Check journal for preprocessing/cleaning patterns
- **SQLGlot changes** → Check journal for ErrorLevel/dialect/WARN mode issues
- **Parser logic changes** → Check journal for regression patterns

**Why this matters:**
- Prevents repeating past mistakes (e.g., WARN mode regression)
- Shows what NOT to change (defensive checks, critical patterns)
- Explains root causes (not just symptoms)
- Documents user-verified corrections

**Philosophy:** Every user-reported bug becomes a permanent record with:
- What was wrong (issue)
- Why it happened (root cause)
- What was changed (fix)
- What NOT to change (regression prevention)

---

## How It Works

This journal is **automatically maintained** through user-verified test cases:

1. **User reports issue** → Create `case_XXX_descriptive_name.yaml`
2. **Case file documents** → reported_by, issue, root_cause, fix_version, fix_description, do_not_change
3. **Journal entry auto-generated** → From YAML metadata (zero maintenance)
4. **CI/CD enforces** → Test fails if verified case breaks
5. **Regression prevented** → "DO NOT" section prevents repeating mistakes

**Location:** `tests/fixtures/user_verified_cases/`

**Test File:** `tests/unit/test_user_verified_cases.py`

---

## Active Cases

> **Status:** 1 investigation documented (not a parser bug, data quality issue)

**When a case is added, entries appear below automatically.**

---

### Investigation 2025-11-14: Empty Lineage for 104 SPs

**Type:** Investigation (not a parser bug)
**Reported by:** User
**Date:** 2025-11-14
**Status:** ✅ Resolved - ROOT CAUSE IDENTIFIED

**Issue:**
- 104/349 SPs (29.8%) have empty lineage (0 inputs AND 0 outputs)
- Tests were incorrectly checking `inputs IS NOT NULL` instead of `json_array_length(inputs) > 0`
- Empty JSON arrays `[]` are NOT NULL but have 0 elements
- Actual success rate: 70.2% (not 100% as originally reported)

**Investigation Findings:**
1. **Parser is working correctly** - Regex found 42 tables in test SP
2. **Tables don't exist in metadata database** - Missing from metadata export
3. **Parser correctly filters non-existent tables** - `_validate_against_catalog()` working as designed
4. **Phantom detection correctly skips them** - Schemas not in `PHANTOM_EXTERNAL_SCHEMAS`
5. **ALL 104 SPs have expected_count = None** - Database populated without these fields
6. **3 SPs reference valid tables** but still have empty lineage (due to #5)

**Breakdown of 104 Empty SPs:**
- 94 (90.4%): Wrong schema (tables exist in CONSUMPTION_PRIMA not CONSUMPTION_PRIMA_2)
- 7 (6.7%): Truly external (sys.dm_pdw_sql_requests, ADMIN.Logs)
- 3 (2.9%): Valid tables exist but empty lineage (expected_count = None issue)

**Root Cause:**
1. **Incomplete metadata export** - CONSUMPTION_PRIMA_2 and STAGING_PRIMA schemas have no tables in metadata
2. **Database populated without expected_count/found_count** - All 349 records have NULL values
3. **Orchestrator detection failed** - `is_orchestrator = (expected_count == 0 and ...)` evaluates False when expected_count is None

**Resolution:**
1. ✅ **Updated integration tests** to use `json_array_length()` instead of `IS NOT NULL`
   - test_database_validation.py: 5 assertions fixed
   - test_sqlglot_performance.py: 1 assertion fixed
   - test_confidence_analysis.py: Bulk updated NULL checks
   - test_failure_analysis.py: Bulk updated NULL checks
2. ✅ **Created .env file** with `PHANTOM_EXTERNAL_SCHEMAS=CONSUMPTION_POWERBI`
3. ✅ **Documented findings** in INVESTIGATION_COMPLETE.md, EMPTY_LINEAGE_ROOT_CAUSE.md, PARSING_ISSUES_ACTION_PLAN.md

**Recommended Next Steps:**
1. Re-parse all 349 SPs with current code to populate expected_count/found_count
2. Investigate metadata export to include missing schemas (CONSUMPTION_PRIMA_2, STAGING_PRIMA)
3. Consider adding missing schemas to PHANTOM_EXTERNAL_SCHEMAS if they are truly external

**DO NOT:**
- ❌ Change `_validate_against_catalog()` logic - it's working correctly
- ❌ Remove phantom schema filtering - it's preventing incorrect phantom creation
- ❌ Modify orchestrator detection logic - it works when expected_count is populated
- ❌ Change regex patterns - they're finding tables correctly
- ❌ Assume `IS NOT NULL` checks are sufficient for JSON arrays - always use `json_array_length()`

**Key Lesson:**
- JSON arrays in DuckDB: `[]` is NOT NULL but has length 0
- Always validate test assertions with actual data queries
- Parser correctness depends on metadata completeness
- expected_count and found_count are critical for confidence calculation and orchestrator detection

**Files Modified:**
- tests/integration/test_database_validation.py
- tests/integration/test_sqlglot_performance.py
- tests/integration/test_confidence_analysis.py
- tests/integration/test_failure_analysis.py
- .env (created)
- INVESTIGATION_COMPLETE.md (created)
- EMPTY_LINEAGE_ROOT_CAUSE.md (created)
- PARSING_ISSUES_ACTION_PLAN.md (created)

**Reference:** See INVESTIGATION_COMPLETE.md for complete analysis

---

### Fix 2025-11-14: Missing expected_count/found_count in database

**Type:** Bug Fix
**Reported by:** Investigation
**Date:** 2025-11-14
**Status:** ✅ Resolved

**Issue:**
- Parser calculates `expected_count` and `found_count` (lines 531-534, 573-574 in quality_aware_parser.py)
- Workspace database has the columns (added in migration)
- **But all 349 records had NULL values** - fields were never saved
- This broke orchestrator detection: `is_orchestrator = (expected_count == 0 and ...)` evaluated False when expected_count is None

**Investigation Findings:**
1. Parser correctly returns `expected_count` and `found_count` in result dict
2. `DuckDBWorkspace.update_metadata()` has parameters for these fields (lines 728-740)
3. **`api/background_tasks.py` was NOT passing these parameters** (lines 567-574)
4. Result: Fields calculated but never saved to database

**Root Cause:**
api/background_tasks.py line 567-574 was missing parameters:
```python
# BEFORE (WRONG):
db.update_metadata(
    object_id=sp_dict['object_id'],
    modify_date=sp_dict['modify_date'],
    primary_source=result.get('primary_source', 'parser'),
    confidence=result['confidence'],
    inputs=result.get('inputs', []),
    outputs=result.get('outputs', [])
)

# AFTER (CORRECT):
db.update_metadata(
    object_id=sp_dict['object_id'],
    modify_date=sp_dict['modify_date'],
    primary_source=result.get('primary_source', 'parser'),
    confidence=result['confidence'],
    inputs=result.get('inputs', []),
    outputs=result.get('outputs', []),
    confidence_breakdown=result.get('confidence_breakdown'),
    parse_failure_reason=result.get('parse_failure_reason'),
    expected_count=result.get('expected_count'),  # ← ADDED
    found_count=result.get('found_count')          # ← ADDED
)
```

**Resolution:**
1. ✅ **Fixed api/background_tasks.py** (lines 574-577) - Added missing parameters
2. ✅ **Created scripts/reparse_all_sps.py** - Re-parse all 349 SPs with correct code
3. ✅ **Re-parsed all 349 SPs** - 100% success rate (349/349 parsed without errors)
4. ✅ **Verified population** - All 349 SPs now have expected_count and found_count populated

**Result:**
- **100% technical success** - All 349 SPs parse without errors
- **70.2% functional success** - 245/349 SPs have dependencies (104 have empty lineage due to metadata incompleteness)
- **82.5% perfect confidence** - 288/349 SPs have confidence 100

**DO NOT:**
- ❌ Assume all parser result fields are automatically saved - check background_tasks.py
- ❌ Skip re-parsing after fixing storage logic - old database still has NULL values
- ❌ Expect 100% functional success with incomplete metadata - 104 SPs reference non-existent tables

**Key Lesson:**
- Parser logic (quality_aware_parser.py) and storage logic (background_tasks.py) are separate
- Always verify that ALL parser result fields are passed to `update_metadata()`
- Re-parsing is required after fixing storage logic to populate existing records
- Technical success (100% parse) != Functional success (dependencies present)

**Files Modified:**
- api/background_tasks.py (lines 574-577) - Added expected_count, found_count parameters
- scripts/reparse_all_sps.py (created) - Re-parse script
- docs/PARSER_DEVELOPMENT_PROCESS.md (created) - Complete process documentation

**Impact:**
- Enables completeness validation (found/expected ratio)
- Fixes orchestrator detection (None != 0 issue resolved)
- Allows SQLGlot enhancement tracking (bonus tables beyond regex baseline)
- Provides diagnostic metrics for parser improvement

**Reference:** See docs/PARSER_DEVELOPMENT_PROCESS.md for complete workflow

### Example Format (Template)

```markdown
## YYYY-MM-DD - Brief Issue Description

**Case:** `case_XXX_descriptive_name.yaml`
**SP Name:** `spStoredProcedureName`
**Reported By:** user@company.com
**Version:** vX.X.X

**Issue:**
Brief description of what was wrong (e.g., "Missing FactLaborCost table in inputs")

**Root Cause:**
Technical reason (e.g., "IF EXISTS pattern removing table reference")

**Fix:**
What was changed (e.g., "Added IF EXISTS removal to preprocessing patterns")

**Expected Results:**
- Inputs: schema.Table1, schema.Table2
- Outputs: schema.TargetTable
- Confidence: 100%

**DO NOT:**
- Remove IF EXISTS pattern (line 150-165 in quality_aware_parser.py)
- Change preprocessing order (regression)

**Test Status:** ✅ Verified case passing in CI/CD

**Related:**
- case_002_similar_issue.yaml (if applicable)
```

---

## Journal Entries

<!-- Entries auto-populate when user-verified cases are added -->

### 2025-11-14 - Infrastructure Ready

**Status:** User-verified test case system deployed

**Components:**
- ✅ `tests/fixtures/user_verified_cases/` directory created
- ✅ `tests/fixtures/user_verified_cases/README.md` (500+ lines)
- ✅ `tests/fixtures/user_verified_cases/case_template.yaml` (template)
- ✅ `tests/unit/test_user_verified_cases.py` (automated tests)
- ✅ `.github/workflows/ci-validation.yml` (CI/CD integration)
- ✅ `.git/hooks/pre-commit` (local validation)
- ✅ `scripts/testing/run_baseline_validation.sh` (regression detection)

**Process:**
1. User reports incorrect parsing result
2. Create `case_XXX_issue_name.yaml` from template
3. Fill in: sp_name, issue, root_cause, expected results, do_not_change
4. Run tests: `pytest tests/unit/test_user_verified_cases.py -v`
5. Commit with fix
6. CI/CD prevents future regressions

**Next:** Waiting for first user-reported case

---

## Common Fix Patterns

### Pattern 1: False Positive Dependencies

**Symptoms:**
- Tables appearing in inputs when they shouldn't
- IF EXISTS checks treated as data dependencies
- WHERE clause filters causing phantom dependencies

**Solutions:**
- Add preprocessing pattern to remove false positive syntax
- Update regex to be more specific about data flow
- Add negative lookahead in pattern matching

**Example Cases:** (None yet)

---

### Pattern 2: Missing Dependencies

**Symptoms:**
- Tables not detected in inputs/outputs
- Dynamic SQL not parsed correctly
- Schema-qualified names not captured

**Solutions:**
- Enhance regex pattern coverage
- Add SQLGlot fallback handling
- Update table reference extraction logic

**Example Cases:** (None yet)

---

### Pattern 3: Confidence Score Issues

**Symptoms:**
- Perfect parse showing 85% instead of 100%
- Orchestrator SPs not getting 100% confidence
- False 0% for valid parses

**Solutions:**
- Review expected table count logic
- Check special case handling (orchestrators, empty SPs)
- Validate completeness calculation

**Example Cases:** (None yet)

---

## Adding a New Case

### Step 1: Create Case File

```bash
cp tests/fixtures/user_verified_cases/case_template.yaml \
   tests/fixtures/user_verified_cases/case_001_your_issue.yaml
```

### Step 2: Fill In Details

```yaml
sp_name: "spYourStoredProcedureName"
reported_date: "2025-11-14"
reported_by: "user@company.com"
issue: "Brief description of what was wrong"
root_cause: "Technical reason for the issue"
fix_version: "v4.3.4"
fix_description: "What was changed to fix it"

expected_inputs:
  - "schema.Table1"
  - "schema.Table2"

expected_outputs:
  - "schema.TargetTable"

expected_confidence: 100

do_not_change:
  - "Specific pattern or rule that should not be removed"
```

### Step 3: Run Tests

```bash
pytest tests/unit/test_user_verified_cases.py::test_case_001 -v
```

### Step 4: Update This Journal

Add entry to "Journal Entries" section using the example format above.

### Step 5: Commit

```bash
git add tests/fixtures/user_verified_cases/case_001_your_issue.yaml
git add docs/PARSER_CHANGE_JOURNAL.md
git commit -m "fix(parser): [brief description] (case_001)"
```

---

## Regression Prevention

### DO NOT Remove These Patterns

**Current Protected Patterns:** (Populated from user-verified cases)

- (None yet - will be populated from `do_not_change` fields in case files)

### DO NOT Change These Behaviors

**Current Protected Behaviors:** (Populated from user-verified cases)

- (None yet - will be populated from case documentation)

---

## Metrics

**Total Cases:** 0
**Success Rate:** 100% (349/349 SPs)
**Cases by Confidence:**
- 100% (Perfect): 0 cases
- 85% (Good): 0 cases
- 75% (Acceptable): 0 cases
- 0% (Failed): 0 cases

**Categories:**
- False Positives: 0
- Missing Dependencies: 0
- Confidence Issues: 0
- Other: 0

---

## Historical Context

### v4.3.3 - Simplified Rules + Phantom Fix (2025-11-12)

**Changes:**
- Simplified SQL cleaning: 11 → 5 patterns (55% reduction)
- Fixed phantom function filter to enforce include list
- Removed 8 invalid phantom functions
- Combined 6 conflicting DECLARE/SET patterns into 1

**DO NOT:**
- Split DECLARE/SET pattern back into multiple patterns (creates conflicts)
- Remove `_schema_matches_include_list()` check (phantom bug regression)

**Result:** 100% success maintained, zero regressions

---

### v4.3.2 - Defensive Improvements (2025-11-12)

**Changes:**
- Added empty command node check (prevents WARN mode regression)
- Added performance tracking (logs slow SPs > 1 second)
- Simplified SELECT handling (object-level lineage only)
- Added SQLGlot statistics tracking
- Created user-verified test suite

**DO NOT:**
- Remove empty command node check (critical defensive check)
- Change to WARN mode (causes empty lineage disaster)
- Add column-level SELECT parsing (out of scope, complexity explosion)

**Result:** 100% success maintained, zero regressions

---

### v4.3.1 - RAISE Mode + UNION Strategy (2025-11-10)

**Changes:**
- Changed SQLGlot mode from WARN to RAISE
- Implemented UNION strategy (regex baseline + SQLGlot bonus)
- Simplified post-processing (remove system schemas, temp tables)
- Discrete confidence values: {0, 75, 85, 100}

**DO NOT:**
- Change back to WARN mode (regression to empty lineage)
- Remove regex baseline (guaranteed coverage)
- Use INTERSECTION strategy (loses regex baseline)

**Result:** 349/349 SPs at 100% success (up from 330/349)

---

**Last Updated:** 2025-11-14
**Version:** v4.3.3
**Maintained By:** Automated from user-verified test cases

**See Also:**
- [User-Verified Cases README](../tests/fixtures/user_verified_cases/README.md)
- [Parser Critical Reference](PARSER_CRITICAL_REFERENCE.md)
- [Parser Technical Guide](PARSER_TECHNICAL_GUIDE.md)
