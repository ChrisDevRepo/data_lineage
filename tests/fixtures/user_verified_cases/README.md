# User-Verified Test Cases

## Purpose

This directory contains **user-reported parsing corrections** that serve as regression tests to prevent repeating the same mistakes.

**Philosophy:** When a user reports incorrect parsing results and provides the correct expected data, we store it here as a verified test case. This creates a growing library of known-good examples that validates parser behavior.

---

## Process

### 1. User Reports Issue

User notices incorrect parsing results for a stored procedure:

```
SP: spLoadFactTables
Issue: Missing FactLaborCost in inputs
Expected Inputs: DimDate, DimProject, FactLaborCost
Actual Inputs: DimDate, DimProject  ❌ Missing FactLaborCost
```

### 2. Create Verified Case File

Create a new YAML file: `case_XXX_descriptive_name.yaml`

**Naming Convention:**
- `case_001_sp_load_fact_tables.yaml`
- `case_002_phantom_wildcard_issue.yaml`
- `case_003_if_exists_false_positive.yaml`

### 3. Case File Format

```yaml
# User-Verified Test Case
# Auto-loaded by tests/unit/test_user_verified_cases.py

sp_name: "spLoadFactTables"
reported_date: "2025-11-14"
reported_by: "john@company.com"
issue: "Missing FactLaborCost table in inputs"
root_cause: "IF EXISTS pattern removing table reference"
fix_version: "v4.1.3"
fix_description: "Added IF EXISTS removal to preprocessing patterns"

# Expected parsing results (verified by user)
expected_inputs:
  - "dbo.DimDate"
  - "dbo.DimProject"
  - "dbo.FactLaborCost"  # This was missing before fix

expected_outputs:
  - "dbo.FactLaborCostForEarnedValue"

expected_confidence: 100

# Optional: Provide DDL snippet for test reproducibility
ddl_snippet: |
  CREATE PROCEDURE spLoadFactTables
  AS
  BEGIN
      -- Check if target exists
      IF EXISTS (SELECT 1 FROM FactLaborCost)  -- This was causing issue
          DELETE FROM FactLaborCost;

      -- Load data
      INSERT INTO FactLaborCostForEarnedValue
      SELECT * FROM FactLaborCost
      JOIN DimDate ON ...
      JOIN DimProject ON ...
  END

# What NOT to change (prevents regression)
do_not_change:
  - "IF EXISTS removal pattern (line 150-165 in quality_aware_parser.py)"
  - "Keep preprocessing before regex scan"
```

### 4. Run Tests

```bash
# All user-verified cases
pytest tests/unit/test_user_verified_cases.py -v

# Specific case
pytest tests/unit/test_user_verified_cases.py::test_case_001 -v

# With detailed output
pytest tests/unit/test_user_verified_cases.py -vv
```

### 5. Automatic Change Journal

When you add a verified case, it automatically updates the change journal:

**File:** `docs/PARSER_CHANGE_JOURNAL.md`

Entry auto-generated:
```markdown
## 2025-11-14 - Missing Table in spLoadFactTables
**Case:** case_001_sp_load_fact_tables.yaml
**Reported By:** john@company.com
**Issue:** FactLaborCost not detected as input
**Root Cause:** IF EXISTS pattern removing table reference
**Fix:** v4.1.3 - Added IF EXISTS removal pattern
**DO NOT:** Remove IF EXISTS pattern (regression)
```

---

## Example Cases

### Case 001: IF EXISTS False Positive

**File:** `case_001_if_exists_false_positive.yaml`

**Problem:** `IF EXISTS (SELECT 1 FROM Table)` checks were treated as data dependencies

**Solution:** Remove IF EXISTS patterns during preprocessing

**Test:** Ensures FactLaborCost appears only as output, not input

---

### Case 002: Phantom Schema Wildcards

**File:** `case_002_phantom_wildcard_issue.yaml`

**Problem:** Wildcard matching (`CONSUMPTION*`) creating false phantoms

**Solution:** v4.3.3 - Changed to exact match only (`PHANTOM_EXTERNAL_SCHEMAS`)

**Test:** Ensures no false phantoms for internal schemas

---

## File Structure

```
tests/fixtures/user_verified_cases/
├── README.md (this file)
├── case_001_if_exists_false_positive.yaml
├── case_002_phantom_wildcard_issue.yaml
├── case_003_declare_set_removal.yaml
└── verified_cases_index.json (auto-generated catalog)
```

---

## Test Implementation

**File:** `tests/unit/test_user_verified_cases.py`

```python
import pytest
import yaml
from pathlib import Path
from engine.parsers import QualityAwareParser

@pytest.fixture
def load_verified_cases():
    """Load all verified test cases from YAML files."""
    cases_dir = Path("tests/fixtures/user_verified_cases")
    cases = []

    for case_file in cases_dir.glob("case_*.yaml"):
        with open(case_file) as f:
            case_data = yaml.safe_load(f)
            case_data['_file'] = case_file.name
            cases.append(case_data)

    return cases

@pytest.mark.parametrize("case", load_verified_cases(), ids=lambda c: c['_file'])
def test_user_verified_case(case, duckdb_workspace):
    """Test that parser produces user-verified results."""

    # Parse the stored procedure
    parser = QualityAwareParser(duckdb_workspace)
    result = parser.parse_by_name(case['sp_name'])

    # Validate inputs match expected
    assert set(result['inputs']) == set(case['expected_inputs']), \
        f"Inputs mismatch for {case['sp_name']}: {case['issue']}"

    # Validate outputs match expected
    assert set(result['outputs']) == set(case['expected_outputs']), \
        f"Outputs mismatch for {case['sp_name']}"

    # Validate confidence
    assert result['confidence'] == case['expected_confidence'], \
        f"Confidence mismatch for {case['sp_name']}"
```

---

## Benefits

✅ **Prevents Regression**
- Every user-reported issue becomes a permanent test
- Parser changes validated against known-good examples
- CI/CD fails if any verified case breaks

✅ **User-Driven Quality**
- Users are the ultimate judges of correctness
- Their corrections become automated tests
- Quality improves based on real-world feedback

✅ **Built-in Change Journal**
- Every case documents why a change was made
- Prevents repeating the same mistake
- Historical context preserved

✅ **Traceability**
- Who reported: `reported_by` field
- When reported: `reported_date` field
- Why changed: `issue` and `root_cause` fields
- What NOT to change: `do_not_change` field

---

## Adding Your First Case

1. **Identify Issue:** User reports incorrect parsing
2. **Get Correct Data:** User provides expected inputs/outputs
3. **Create YAML:** Copy template above, fill in details
4. **Run Test:** `pytest tests/unit/test_user_verified_cases.py -v`
5. **Commit:** Include case file in commit with fix

**Template:**

```bash
cp tests/fixtures/user_verified_cases/case_template.yaml \
   tests/fixtures/user_verified_cases/case_004_your_issue.yaml

# Edit case_004_your_issue.yaml with your data
# Run tests
pytest tests/unit/test_user_verified_cases.py::test_case_004 -v
```

---

## Integration with CI/CD

GitHub Actions automatically runs verified cases on every PR:

```yaml
# .github/workflows/ci-validation.yml
user-verified-cases:
  runs-on: ubuntu-latest
  steps:
    - name: Run user-verified test cases
      run: pytest tests/unit/test_user_verified_cases.py -v --tb=short
```

**Status Badge:** Shows how many verified cases pass

**PR Checks:** Blocks merge if any verified case fails

---

**Last Updated:** 2025-11-14
**Cases:** 0 (infrastructure ready, add first case when user reports issue)
