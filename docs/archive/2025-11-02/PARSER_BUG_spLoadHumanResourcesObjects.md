# Parser Bug Report: spLoadHumanResourcesObjects

**Date:** 2025-11-02
**Parser Version:** v3.8.0
**Reported By:** User
**Symptom:** SP shows "no connection" in GUI (0 inputs, 0 outputs)

---

## Problem Summary

The stored procedure `CONSUMPTION_PRIMA.spLoadHumanResourcesObjects` is incorrectly parsed with:
- **Inputs:** 1 (self-reference, WRONG)
- **Outputs:** 0 (WRONG - should have ~20 table outputs)
- **Confidence:** 0.50 (low)
- **Primary Source:** parser

**Expected Result:**
- **Inputs:** Multiple tables from STAGING_PRIMA and CONSUMPTION_PRIMA schemas
- **Outputs:** Multiple tables in CONSUMPTION_PRIMA schema (~20 tables)
- **Confidence:** ≥0.85 (successful parse)

---

## SP Characteristics

| Metric | Value |
|--------|-------|
| Schema | CONSUMPTION_PRIMA |
| Name | spLoadHumanResourcesObjects |
| Object ID | 1235104157 |
| DDL Size | 35,609 characters |
| DDL Lines | 667 lines |
| Complexity | High (large ETL procedure) |

---

## Parser Output Analysis

### Incorrect Internal Lineage
```json
{
  "id": 1235104157,
  "name": "spLoadHumanResourcesObjects",
  "schema": "CONSUMPTION_PRIMA",
  "object_type": "Stored Procedure",
  "inputs": [1235104157],  ← WRONG: Self-reference
  "outputs": [],            ← WRONG: Should have ~20 tables
  "provenance": {
    "primary_source": "parser",
    "confidence": 0.5       ← LOW: Parser failed
  }
}
```

### Self-Reference Bug
The SP has itself (object_id 1235104157) as an input. This is clearly incorrect - a stored procedure cannot depend on itself in a lineage graph.

**Root Cause:** Parser is incorrectly extracting the SP name from a DECLARE statement:
```sql
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_PRIMA].[spLoadHumanResourcesObjects]'
```

This is a variable assignment for logging purposes, NOT a dependency.

---

## Actual Dependencies in DDL

### Inputs (Source Tables)
The SP reads from tables in these schemas:
1. **STAGING_PRIMA.HREmployees** (line 175)
2. Other staging tables (not fully enumerated in preview)

Example SELECT statements:
```sql
SET @RowsInHrContractsTargetBegin = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrContracts)
SET @RowsInHrDepartmentsTargetBegin = (SELECT COUNT(1) FROM CONSUMPTION_PRIMA.HrDepartments)
-- ... 18 more SELECT COUNT statements from CONSUMPTION_PRIMA tables
```

### Outputs (Target Tables)
The SP writes to **at least 20 tables** in CONSUMPTION_PRIMA schema:

| Table Name | Operation | Evidence |
|------------|-----------|----------|
| HrContracts | TRUNCATE + INSERT | Line 175-178 |
| HrDepartments | INSERT | Line 137 |
| HrManningTable | INSERT | Line 138 |
| HrOffices | INSERT | Line 139 |
| HrPositions | INSERT | Line 140 |
| HrEmployeeTransfers | INSERT | Line 142 |
| HrTrainings | INSERT | Line 143 |
| HrResignations | INSERT | Line 144 |
| HrQuizMaster | INSERT | Line 146 |
| HrQuizSessions | INSERT | Line 147 |
| HrTrainingEmployees | INSERT | Line 148 |
| HrTrainingEmployeesTimesheet | INSERT | Line 149 |
| HrTrainingMatrix | INSERT | Line 150 |
| HrTrainingTitles | INSERT | Line 151 |
| HrTutorials | INSERT | Line 152 |
| HrEmployeeLeaveStatistics | INSERT | Line 167 |
| HrEmployeeWorkdays | INSERT | Line 168 |
| HrLeaveTracker | INSERT | Line 169 |
| HrManagement | INSERT | Line 170 |
| HrScormSessions | INSERT | Line 171 |

**Example DML:**
```sql
IF ((SELECT Count(1) FROM [STAGING_PRIMA].HREmployees) > 0 )
    TRUNCATE TABLE CONSUMPTION_PRIMA.[HrContracts]
    INSERT INTO CONSUMPTION_PRIMA.[HrContracts]
    (
        [CONTRACT_ID], [EMPLOYEE_ID], [CONTRACT_TYPE_ID], ...
    )
    FROM ...
```

### EXEC Statements (Filtered Utility SPs)
The SP calls `spLastRowCount` 20 times:
```sql
EXEC [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrContractsRecordCount output
EXEC [CONSUMPTION_PRIMAREPORTING_2].[spLastRowCount] @Count = @AffectedHrDepartmentsRecordCount output
-- ... 18 more EXEC calls
```

**Parser Behavior:** These are correctly **filtered out** (spLastRowCount is in EXCLUDED_UTILITY_SPS)

---

## Why Parser Failed

### Hypothesis 1: Large SP Size
- 35KB DDL, 667 lines
- SQLGlot parser may timeout or fail on large/complex SQL
- Regex fallback returns 0.50 confidence but extracts incorrect dependencies

### Hypothesis 2: Complex SQL Patterns
- Multiple nested IF statements
- TRUNCATE + INSERT combinations
- Variable assignments that look like dependencies
- Try/Catch blocks with logging

### Hypothesis 3: Parser Bugs
1. **Self-Reference Bug:**
   - Parser extracts SP name from DECLARE statement
   - Should ignore string literals in variable assignments

2. **Missing Table Extraction:**
   - Parser fails to extract table names from INSERT/TRUNCATE statements
   - May be related to IF block handling
   - May be related to multi-line INSERT statements

### Hypothesis 4: Preprocessing Issues
The parser has preprocessing logic to:
- Remove code after COMMIT statements
- Remove error handling blocks
- Clean up comments

Large/complex SPs might:
- Be over-aggressively stripped
- Have SQL removed that contains actual table references
- Fail to parse after preprocessing

---

## Parser Code Locations to Investigate

### 1. Self-Reference Extraction (`lineage_v3/parsers/quality_aware_parser.py`)

Search for:
- DECLARE statement handling
- String literal extraction
- Variable assignment parsing

**Fix:** Add filter to exclude string literals in DECLARE statements from dependency extraction

### 2. Table Extraction (`lineage_v3/parsers/quality_aware_parser.py`)

Search for:
- INSERT statement handling
- TRUNCATE statement handling
- Multi-line DML parsing

**Fix:** Ensure INSERT INTO ... FROM patterns are correctly extracted

### 3. Preprocessing Logic (`lineage_v3/parsers/quality_aware_parser.py`)

Search for:
- `_preprocess_ddl()` method
- COMMIT statement removal
- TRY/CATCH block handling

**Fix:** Verify large SPs aren't being over-stripped

---

## Impact Assessment

### User Impact
- **High:** User sees "no connection" in GUI for this SP
- **Confusing:** SP clearly has dependencies but parser shows none
- **Data Quality:** Lineage graph is incomplete for HR data flow

### Scope
- **Single SP:** Only affects spLoadHumanResourcesObjects currently
- **Pattern Risk:** Other large ETL SPs may have same issue
- **Confidence:** Low confidence (0.50) correctly flags issue for AI disambiguation

### Workaround
- **Short-term:** AI disambiguation (Phase 5) can handle this SP
- **Long-term:** Fix parser to handle large ETL procedures

---

## Recommended Fixes

### Priority 1: Fix Self-Reference Bug
```python
# In quality_aware_parser.py
def _extract_dependencies(self, ddl: str):
    # ... existing code ...

    # EXCLUDE: String literals in DECLARE statements
    # Pattern: DECLARE @var = '[schema].[object]'
    ddl = re.sub(r"DECLARE\s+@\w+.*?=\s*'[^']+'", "", ddl, flags=re.IGNORECASE)

    # Now extract dependencies
    # ...
```

### Priority 2: Debug Table Extraction Failure
1. Add detailed logging for INSERT/TRUNCATE extraction
2. Test parser on spLoadHumanResourcesObjects DDL in isolation
3. Compare SQLGlot AST output vs expected tables
4. Fix table extraction logic for complex INSERT patterns

### Priority 3: Add Large SP Handling
```python
# In quality_aware_parser.py
DDL_SIZE_THRESHOLD = 30000  # 30KB

def parse(self, ddl: str):
    if len(ddl) > DDL_SIZE_THRESHOLD:
        logger.warning(f"Large SP detected ({len(ddl)} chars), using AI disambiguation")
        return self._parse_with_ai(ddl)  # Skip SQLGlot for large SPs
```

---

## Testing Plan

### 1. Unit Test: Self-Reference Bug
```python
def test_no_self_reference_in_declare():
    ddl = """
    CREATE PROC [dbo].[spTest] AS
    BEGIN
        DECLARE @procname VARCHAR(100) = '[dbo].[spTest]'
        SELECT * FROM [dbo].[RealTable]
    END
    """
    result = parser.parse(ddl)

    # Should NOT include spTest as dependency
    assert 'spTest' not in result['inputs']

    # SHOULD include RealTable
    assert 'RealTable' in result['inputs']
```

### 2. Integration Test: spLoadHumanResourcesObjects
```python
def test_spLoadHumanResourcesObjects():
    # Load actual DDL from database
    ddl = get_ddl('CONSUMPTION_PRIMA', 'spLoadHumanResourcesObjects')

    result = parser.parse(ddl)

    # Expected outputs
    expected_outputs = [
        'HrContracts', 'HrDepartments', 'HrManningTable',
        'HrOffices', 'HrPositions', 'HrEmployeeTransfers',
        # ... 14 more tables
    ]

    assert len(result['outputs']) >= 15  # At least 15 output tables
    assert result['confidence'] >= 0.85  # High confidence parse
    assert result['object_id'] not in result['inputs']  # No self-reference
```

### 3. Regression Test: Full Smoke Test
```bash
# Re-run smoke test after fix
python smoke_test_sp.py

# Verify:
# - spLoadHumanResourcesObjects has >0 inputs
# - spLoadHumanResourcesObjects has >15 outputs
# - Confidence >= 0.85
# - No self-reference in inputs
```

---

## Related Issues

### Orphaned Metadata Records
While investigating, found 3 records in `lineage_metadata` without matching `objects` entries:
- Object IDs: 60954293, 1394350465, 1378350408
- **Fix:** Add JOIN to objects table in summary_formatter.py

### Cache Bug
User reported stale confidence counts in GUI:
- **Fix:** Added cache-control headers and cache-busting parameter
- **Status:** ✅ Fixed (see CACHE_BUG_FIX_SUMMARY.md)

---

## Next Steps

1. **Immediate:** Document this bug in parser evolution log
2. **Short-term:** Add to backlog for parser enhancement sprint
3. **Medium-term:** Implement fixes (Priority 1 & 2)
4. **Long-term:** Add AI disambiguation fallback for large SPs

---

## Appendix: Full DDL Location

**File:** `spLoadHumanResourcesObjects_DDL.sql` (667 lines, 35KB)

**Key Sections:**
- Lines 1-100: Variable declarations (logging setup)
- Lines 136-171: Source table row counts (SELECT COUNT from tables)
- Lines 175+: Main ETL logic (TRUNCATE + INSERT statements)

**EXEC Calls:** 20x `spLastRowCount` (correctly filtered)

---

**Author:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-02
**Version:** v3.8.0
**Status:** 🔍 INVESTIGATION COMPLETE - FIX PENDING
