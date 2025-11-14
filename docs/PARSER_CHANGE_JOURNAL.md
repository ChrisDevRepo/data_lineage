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

> **Status:** 0 cases (infrastructure ready, waiting for first user report)

**When a case is added, entries appear below automatically.**

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
