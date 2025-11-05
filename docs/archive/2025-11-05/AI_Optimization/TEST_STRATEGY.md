# AI Inference Test Strategy

**Created:** 2025-11-03
**Purpose:** Establish baseline test cases to validate AI inference quality and prevent regressions

---

## Test Case #1: GLCognosData_Test (BASELINE - VALID MATCH)

### Table
`CONSUMPTION_FINANCE.GLCognosData_Test`

### Expected SP Match
`CONSUMPTION_FINANCE.spLoadGLCognosData_Test`

### Relationship Type
- **OUTPUT procedure** (SP writes TO table)
- SP performs TRUNCATE + INSERT INTO operations

### SQL Evidence
```sql
-- Line 1969
truncate table [CONSUMPTION_FINANCE].[GLCognosData_Test];

-- Line 1973
insert into [CONSUMPTION_FINANCE].[GLCognosData_Test]
select ... (2000+ line SP)
```

### Full Lineage Pattern
```
INPUTS (SP reads FROM):
  ← staging_finance_cognos.v_ccr2powerbi_facts

OUTPUTS (SP writes TO):
  → consumption_finance.glcognosdata_test  ← TARGET TABLE
  → staging_finance_cognos.glcognosdata_hc100500_test (intermediate/staging)
```

### Expected Database Storage
From **TABLE perspective** (`GLCognosData_Test`):
- `table.inputs = [spLoadGLCognosData_Test]` ← SP provides data TO table
- `table.outputs = []` ← No SPs read FROM table

### Validation Criteria
- ✅ SP name appears in `table.inputs`
- ✅ Target table name appears in SP SQL code (TRUNCATE + INSERT)
- ✅ Confidence ≥ 0.90
- ✅ No false positives (other unrelated SPs)

### Status
**✅ PASSING** (Iteration 7 result confirmed valid)

---

## Test Case #2: dbo.test1 (FALSE POSITIVE - INVALID)

### Table
`dbo.test1`

### Expected SP Match
**NONE** (test table, no ETL processes)

### Relationship Type
N/A - This should return empty results

### SQL Evidence
**NONE** - No SPs reference this table in their SQL code

### Iteration 7 Problem
AI matched this table to 7 UNRELATED SPs:
- dbo.spLastRowCount
- CONSUMPTION_FINANCE.spLoadAggregatedTotalLinesInvoiced
- CONSUMPTION_FINANCE.spLoadDimCompanyKoncern
- CONSUMPTION_FINANCE.spLoadFactSAPSalesInterestSummary
- CONSUMPTION_FINANCE.spLoadSAP_Sales_Summary_AverageDaysToPayPerQuarterMetrics
- CONSUMPTION_PRIMA.spLoadStudyArms
- CONSUMPTION_PRIMA.spLoadGlobalAccounts

**None of these SPs reference "test1" in their SQL code!**

### Expected Database Storage
- `table.inputs = []`
- `table.outputs = []`
- `confidence = 0.0`

### Validation Criteria
- ✅ Both inputs and outputs are empty
- ✅ Confidence = 0.0
- ✅ Reasoning explains no match found

### Status
**❌ FAILING** (Iteration 7 has false positives)

---

## Test Case #3: FactAgingSAP (BASELINE - VALID MATCH)

### Table
`CONSUMPTION_FINANCE.FactAgingSAP`

### Expected SP Match
`CONSUMPTION_FINANCE.spLoadFactAgingSAP`

### Relationship Type
- **OUTPUT procedure** (SP writes TO table)

### SQL Evidence
```sql
TRUNCATE TABLE [CONSUMPTION_FINANCE].[FactAgingSAP];
INSERT INTO [CONSUMPTION_FINANCE].[FactAgingSAP]
```

Multiple explicit references (Lines 26, 52, 58, 153)

### Expected Database Storage
- `table.inputs = [spLoadFactAgingSAP]`
- `table.outputs = []`
- `confidence ≥ 0.85`

### Status
**✅ PASSING** (Iteration 7 result confirmed valid)

---

## Test Automation Script

### Location
`/home/chris/sandbox/AI_Optimization/validate_baseline.py`

### Usage
```bash
/home/chris/sandbox/venv/bin/python AI_Optimization/validate_baseline.py
```

### What It Validates
1. Extracts table operations from SP DDL (TRUNCATE, INSERT, FROM, JOIN)
2. Categorizes into INPUT tables (reads FROM) and OUTPUT tables (writes TO)
3. Compares with AI inference results from database
4. Validates storage semantics (table.inputs vs table.outputs)

---

## Pass/Fail Criteria

### For Each Test Case:
1. **Object Match**: SP correctly identified (or correctly rejected)
2. **SQL Evidence**: Table name appears in SP code at expected operation
3. **Storage Correctness**: SP stored in correct column (inputs vs outputs)
4. **Confidence**: Appropriate confidence level (≥0.85 for matches, 0.0 for rejections)
5. **No False Positives**: Only matched SPs actually reference the table

### Overall System Metrics:
- **Precision:** ≥95% (false positive rate ≤5%)
- **Recall:** ≥80% (capture most valid relationships)
- **Hallucination Rate:** 0% (no SPs matched without SQL evidence)

---

## Regression Testing Workflow

### Before Making Changes:
1. Run validation on all 3 baseline test cases
2. Record results as baseline metrics

### After Making Changes:
1. Re-run validation on all 3 baseline test cases
2. Compare against baseline metrics
3. **BLOCK** deployment if:
   - Any baseline test case fails
   - Precision drops below 95%
   - Hallucination rate > 0%

### Example Validation Command:
```bash
# Run all test cases
for table in GLCognosData_Test test1 FactAgingSAP; do
    echo "Testing: $table"
    /home/chris/sandbox/venv/bin/python AI_Optimization/validate_baseline.py $table
done
```

---

## Current Status (Iteration 7)

| Test Case | Object Match | SQL Evidence | Storage | Confidence | Status |
|-----------|--------------|--------------|---------|------------|--------|
| GLCognosData_Test | ✅ | ✅ | ✅ | 0.95 | **PASS** |
| dbo.test1 | ❌ | ❌ | ❌ | 0.80 | **FAIL** (7 false positives) |
| FactAgingSAP | ✅ | ✅ | ✅ | 0.85 | **PASS** |

**Overall: FAIL** - Precision 7.8% (target ≥95%)

---

## Next Steps

1. **Fix AI Hallucination Problem**
   - Investigate why AI returns SPs without SQL evidence
   - Review few-shot examples for problematic patterns
   - Consider adding negative examples (test tables that should match nothing)

2. **Add More Test Cases**
   - Edge cases: pluralization, prefixes, similar names
   - More negative cases: backup tables, temp tables, lookups

3. **Automate Regression Tests**
   - Run on every parser change
   - Block commits if tests fail
   - Track metrics over time

4. **Expand Validation**
   - Sample 20-50 random matches per iteration
   - Calculate actual precision/recall
   - Monitor hallucination patterns

---

## Appendix: Semantic Clarification

### From TABLE Perspective:
- **table.inputs** = SPs that write TO this table (provide data IN)
- **table.outputs** = SPs that read FROM this table (consume data OUT)

### From SP Perspective:
- **SP outputs** = Tables the SP writes TO
- **SP inputs** = Tables the SP reads FROM

### Mapping (Critical!):
When storing table dependencies:
- `table.inputs = ai_result.targets` (SPs that write to table)
- `table.outputs = ai_result.sources` (SPs that read from table)

This mapping is **CORRECT** in Iteration 7 code (main.py:557-558)
