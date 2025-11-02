# Missing Outputs Bug Analysis

**Date:** 2025-11-02
**Reporter:** User
**Issue:** Tables with dependencies showing as "isolated" when they shouldn't be
**Example:** `CONSUMPTION_POWERBI.AverageFTE_Monthly`

---

## Executive Summary

**🚨 CRITICAL PARSER BUG DISCOVERED**

**Symptom:** Tables appear "isolated" (no dependencies) when full-text search of DDL shows they ARE referenced

**Root Cause:** Parser missing outputs from `SELECT...INTO` statements

**Impact:**
- Isolated table count artificially HIGH (includes tables that ARE used)
- Lineage graph INCOMPLETE (missing SP → Table edges)
- Test 3 currently PASSES but with FALSE data

---

## Bug Discovery Process

### Step 1: User Observation
```
User: "why has AverageFTE_Monthly no dependencies check fulltext search in ddl"
```

### Step 2: Initial Investigation
**Query:** Find `AverageFTE_Monthly` in database
```sql
SELECT object_id, schema_name, object_name, object_type
FROM objects
WHERE object_name LIKE '%AverageFTE_Monthly%'
```

**Results:** Found 4 tables with this pattern:
1. `CONSUMPTION_POWERBI.AverageFTE_Monthly` (ID: 1298634819)
2. `CONSUMPTION_ClinOpsFinance.EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail` (ID: 705432232)
3. `CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation` (ID: 625431947)
4. `CONSUMPTION_ClinOpsFinance.EmployeeAverageFTE_Monthly_Utilization_Hours` (ID: 689432175)

**Lineage Check:** ❌ ALL 4 tables have NO dependencies in `lineage_metadata` or `dependencies` tables

### Step 3: Full-Text DDL Search
**Query:** Search ALL SP/View definitions for "AverageFTE_Monthly"
```sql
SELECT o.object_id, o.schema_name, o.object_name, o.object_type
FROM definitions d
JOIN objects o ON d.object_id = o.object_id
WHERE LOWER(d.definition) LIKE '%averagefte_monthly%'
```

**Result:** Found 1 SP that references these tables:
- **SP:** `CONSUMPTION_ClinOpsFinance.spLoadEmployeeContractUtilization_Aggregations` (ID: 2003157877)

### Step 4: DDL Analysis
**SP creates 3 tables using `SELECT...INTO`:**

**Table 1:** (Line 326)
```sql
SELECT <columns>
INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
FROM [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_RankDetailAggregation BP
FULL OUTER JOIN AverageFTE_Monthly_RankDetail_Currency U  -- CTE, not table reference
ON ...
```

**Table 2:** (Line 503)
```sql
SELECT <columns>
INTO [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours]
FROM [CONSUMPTION_ClinOpsFinance].[Employee_Utilization_Hours] H
FULL OUTER JOIN FTE_Contract FTE  -- CTE, not table reference
ON ...
```

**Table 3:** (Line 543)
```sql
SELECT <columns>
INTO [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail]
FROM [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours] EFUH
JOIN [CONSUMPTION_ClinOpsFinance].DateRanges_PM DR
ON ...
```

### Step 5: Parser Results Check
**SP Lineage Metadata:**
```
Confidence: 0.85 (HIGH)
Inputs:  [81666934, 1693780241, ...]  -- 17 inputs captured
Outputs: [593431833, 577431776]       -- Only 2 outputs captured!
```

**Expected Outputs:** 5 tables (3 created + 2 existing)
**Actual Outputs:** 2 tables
**Missing Outputs:** 3 tables ❌

**Missing Tables:**
1. `BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation` (ID: 625431947)
2. `EmployeeAverageFTE_Monthly_Utilization_Hours` (ID: 689432175)
3. `EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail` (ID: 705432232)

---

## Root Cause Analysis

### Hypothesis 1: CTE Confusion ❌
**Theory:** Parser confuses CTE names with table names

**Evidence Against:**
- `AverageFTE_Monthly_RankDetail_Currency` is a CTE (line 293)
- `FTE_Contract` is a CTE (line 465)
- Parser should NOT capture these as outputs
- But parser also NOT capturing the actual `SELECT...INTO` tables

**Conclusion:** CTEs are correctly excluded, but so are real outputs

### Hypothesis 2: Pattern Mismatch ✅ (LIKELY)
**Theory:** Regex/SQLGlot patterns don't match `SELECT...INTO` with complex context

**Evidence:**
```sql
-- Pattern that MIGHT work:
SELECT * INTO Table FROM Source

-- Pattern in actual DDL (might NOT match):
SELECT
  EFUH.[EMPLOYEE_ID]
  ,DR.Rank
  ,EFUH.[BOMDateID]
  ... (many more columns)
INTO [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours_RankDetail]
FROM [CONSUMPTION_ClinOpsFinance].[EmployeeAverageFTE_Monthly_Utilization_Hours] EFUH
```

**Key Differences:**
1. Multi-line SELECT with many columns
2. INTO appears AFTER column list, not immediately after SELECT
3. Brackets around schema/table names
4. Multiple JOINs following

### Hypothesis 3: DROP TABLE Confusion ❌
**Theory:** Parser sees `DROP TABLE` and excludes from outputs

**Evidence:**
```sql
IF OBJECT_ID('...BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation') IS NOT NULL
DROP TABLE [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation;

-- Then later:
SELECT ... INTO [CONSUMPTION_ClinOpsFinance].BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
```

**Conclusion:** Unlikely - parser should look for INSERT/SELECT INTO for outputs, not DROP

---

## Parser Code Investigation

### Current Regex Pattern
**File:** `lineage_v3/parsers/quality_aware_parser.py`

**Line 430-452 (Target extraction):**
```python
# INTO pattern
r'\\bINTO\\s+\\[?(\\w+)\\]?\\.\\[?(\\w+)\\]?'  # INTO [schema].[table]
```

**Potential Issues:**
1. Pattern expects `INTO` followed immediately by schema.table
2. May not handle multi-line `SELECT ... INTO` with columns in between
3. May not handle brackets correctly

### SQLGlot Parsing
**Line 454-550 (SQLGlot extraction):**
```python
try:
    parsed = sqlglot.parse_one(preprocessed_ddl, dialect="tsql")
    # Extract targets from INSERT/MERGE/UPDATE statements
except Exception:
    # Fallback to empty
```

**Potential Issues:**
1. SQLGlot may fail to parse `SELECT...INTO` syntax
2. T-SQL dialect may not fully support this pattern
3. Complex DDL with CTEs may confuse parser

---

## Impact Assessment

### Scope
**Query:** Find all SPs with `SELECT...INTO` that might be affected
```sql
SELECT COUNT(*)
FROM definitions
WHERE LOWER(definition) LIKE '%select%into%'
  AND object_type = 'Stored Procedure'
```

**Estimated Impact:** 50-100 SPs (10-20% of total)

### Current Metrics Affected
**Isolated Tables:**
- Current count: 223
- False positives: Unknown (need to check all)
- Actual isolated: Likely 150-180

**SP Confidence:**
- Current high confidence: 163/202 (80.7%)
- Some SPs may have incomplete outputs but still high confidence
- This means confidence score DOESN'T catch this bug

**Lineage Graph:**
- Missing SP → Table edges
- Tables appear isolated when they're actually populated by SPs
- Downstream impact analysis INCOMPLETE

---

## Why Test 3 Didn't Catch This

### Current Test 3 Logic
```python
# Get isolated tables
isolated_tables = conn.execute('''
    SELECT object_id, schema_name, object_name
    FROM objects
    WHERE object_type = 'Table'
    AND object_id NOT IN (
        SELECT DISTINCT referenced_object_id FROM dependencies
        UNION
        SELECT DISTINCT CAST(json_extract(...) AS INTEGER)
        FROM lineage_metadata, json_each(inputs_item.value)
        UNION
        SELECT DISTINCT CAST(json_extract(...) AS INTEGER)
        FROM lineage_metadata, json_each(outputs_item.value)
    )
''')
```

**Why It Passes:**
- Test checks if table appears in `dependencies` OR `lineage_metadata.inputs/outputs`
- If table is NOT in either, it's marked as "isolated"
- Test ASSUMES: If parser captured it, it's in lineage_metadata
- Test DOESN'T VERIFY: Did parser capture ALL tables mentioned in DDL?

**The Gap:**
- Test verifies: "Isolated tables are actually isolated"
- Test DOESN'T verify: "Non-isolated tables are captured"
- Missing: Cross-check DDL full-text search vs captured outputs

---

## Proposed New Test: Test 5 - DDL Full-Text Validation

### Purpose
Verify that all table references in DDL are captured in lineage_metadata

### Logic
```python
def test_ddl_fulltext_validation(conn: duckdb.DuckDBPyConnection) -> Tuple[int, int, bool]:
    """
    Test 5: DDL Full-Text Validation

    For each SP/View:
    1. Get definition text
    2. Full-text search for table references (SELECT...INTO, INSERT INTO, UPDATE, MERGE)
    3. Resolve table names to object_ids
    4. Compare against lineage_metadata.outputs
    5. Report missing outputs
    """

    # Get all SPs/Views with definitions
    objects_with_ddl = conn.execute('''
        SELECT o.object_id, o.schema_name, o.object_name, o.object_type, d.definition
        FROM objects o
        JOIN definitions d ON o.object_id = d.object_id
        WHERE o.object_type IN ('Stored Procedure', 'View')
    ''').fetchall()

    missing_outputs = []

    for obj_id, schema, name, obj_type, ddl in objects_with_ddl:
        # Extract table references from DDL using regex
        into_pattern = r'\bINTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
        insert_pattern = r'\bINSERT\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
        update_pattern = r'\bUPDATE\s+\[?(\w+)\]?\.\[?(\w+)\]?'
        merge_pattern = r'\bMERGE\s+\[?(\w+)\]?\.\[?(\w+)\]?'

        into_matches = re.findall(into_pattern, ddl, re.IGNORECASE)
        insert_matches = re.findall(insert_pattern, ddl, re.IGNORECASE)
        update_matches = re.findall(update_pattern, ddl, re.IGNORECASE)
        merge_matches = re.findall(merge_pattern, ddl, re.IGNORECASE)

        all_targets = set(into_matches + insert_matches + update_matches + merge_matches)

        # Resolve to object_ids
        expected_output_ids = set()
        for tgt_schema, tgt_table in all_targets:
            result = conn.execute('''
                SELECT object_id FROM objects
                WHERE LOWER(schema_name) = LOWER(?)
                  AND LOWER(object_name) = LOWER(?)
            ''', [tgt_schema, tgt_table]).fetchone()

            if result:
                expected_output_ids.add(result[0])

        # Get actual outputs from lineage_metadata
        lineage = conn.execute('''
            SELECT outputs FROM lineage_metadata WHERE object_id = ?
        ''', [obj_id]).fetchone()

        if lineage and lineage[0]:
            actual_outputs = set(json.loads(lineage[0]))
        else:
            actual_outputs = set()

        # Find missing
        missing = expected_output_ids - actual_outputs

        if missing:
            missing_outputs.append({
                'object_id': obj_id,
                'name': f'{schema}.{name}',
                'type': obj_type,
                'expected_outputs': len(expected_output_ids),
                'actual_outputs': len(actual_outputs),
                'missing_count': len(missing),
                'missing_ids': list(missing)
            })

    # Report
    total_objects = len(objects_with_ddl)
    failed_objects = len(missing_outputs)
    passed = (failed_objects == 0)

    print(f"\n{'='*60}")
    print(f"Test 5: DDL Full-Text Validation")
    print(f"{'='*60}")
    print(f"Total objects checked: {total_objects}")
    print(f"Objects with missing outputs: {failed_objects}")

    if missing_outputs:
        print(f"\n❌ FAILED - Missing outputs detected:\n")
        for obj in missing_outputs[:10]:  # Show first 10
            print(f"  {obj['name']} ({obj['type']})")
            print(f"    Expected: {obj['expected_outputs']}, Actual: {obj['actual_outputs']}, Missing: {obj['missing_count']}")
    else:
        print(f"\n✅ PASSED - All DDL table references captured")

    return total_objects, failed_objects, passed
```

### Expected Results
**Before Fix:**
- Total objects: ~471 (202 SPs + 269 Views)
- Failed objects: 50-100 (estimated)
- Status: ❌ FAILED

**After Fix:**
- Total objects: ~471
- Failed objects: 0
- Status: ✅ PASSED

---

## Proposed Solution

### Option 1: Fix Regex Pattern (Quick Win - 2 hours)

**Update regex to handle multi-line SELECT...INTO:**
```python
# Current (broken):
r'\bINTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'

# Proposed (fixed):
r'\bSELECT\s+.*?\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'  # Greedy match
```

**Issues:**
- May be too greedy (match too much)
- Need to handle CRLF/LF line endings
- Need to handle comments between SELECT and INTO

### Option 2: Dedicated SELECT...INTO Parser (Better - 4 hours)

**Add dedicated method:**
```python
def _extract_select_into_targets(self, ddl: str) -> Set[str]:
    """
    Extract table targets from SELECT...INTO statements.

    Handles:
    - Multi-line SELECT with column lists
    - Brackets around schema/table names
    - CTEs (exclude from results)
    """
    targets = set()

    # Preprocess: Remove CTEs to avoid false positives
    ddl_no_ctes = self._remove_ctes(ddl)

    # Pattern: SELECT ... INTO [schema].[table]
    # Use DOTALL to match across newlines
    pattern = r'\bSELECT\s+.+?\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
    matches = re.findall(pattern, ddl_no_ctes, re.IGNORECASE | re.DOTALL)

    for schema, table in matches:
        targets.add(f"{schema}.{table}")

    return targets

def _remove_ctes(self, ddl: str) -> str:
    """Remove CTE definitions to avoid confusion."""
    # Pattern: WITH <cte_name> AS (...)
    cte_pattern = r'\bWITH\s+(\w+)\s+AS\s*\([^)]+\)'
    return re.sub(cte_pattern, '', ddl, flags=re.IGNORECASE | re.DOTALL)
```

**Advantages:**
- More robust
- Handles edge cases
- Easier to test/debug

### Option 3: SQLGlot Enhancement (Best - 6-8 hours)

**Improve SQLGlot preprocessing:**
```python
def _preprocess_for_sqlglot(self, ddl: str) -> str:
    """Enhanced preprocessing for SELECT...INTO."""

    # 1. Extract SELECT...INTO statements separately
    select_into_pattern = r'(SELECT\s+.+?\s+INTO\s+\[?\w+\]?\.\[?\w+\]?.*?FROM.*?(?=;|$))'
    select_into_stmts = re.findall(select_into_pattern, ddl, re.IGNORECASE | re.DOTALL)

    # 2. Convert to INSERT...SELECT for SQLGlot compatibility
    converted_stmts = []
    for stmt in select_into_stmts:
        # Extract INTO target
        match = re.search(r'INTO\s+(\[?\w+\]?\.\[?\w+\]?)', stmt, re.IGNORECASE)
        if match:
            target = match.group(1)
            # Convert: SELECT cols INTO target FROM source
            # To: INSERT INTO target SELECT cols FROM source
            converted = stmt.replace(f'INTO {target}', '')
            converted = f'INSERT INTO {target} {converted}'
            converted_stmts.append(converted)

    # 3. Replace original statements with converted ones
    preprocessed = ddl
    for original, converted in zip(select_into_stmts, converted_stmts):
        preprocessed = preprocessed.replace(original, converted)

    return preprocessed
```

**Advantages:**
- Leverages SQLGlot's robust parsing
- Handles complex syntax
- More maintainable

**Disadvantages:**
- More complex implementation
- May introduce new edge cases

---

## Recommendation

**Immediate Action (Today - 4 hours):**
1. ✅ Create Test 5 (DDL Full-Text Validation)
2. ✅ Run test to quantify scope
3. ✅ Implement Option 2 (Dedicated SELECT...INTO Parser)
4. ✅ Re-run full parse and validate

**Short-term (This Week - 6 hours):**
5. ✅ Implement Option 3 (SQLGlot Enhancement)
6. ✅ Run `/sub_DL_OptimizeParsing` to validate no regressions
7. ✅ Update parser evolution log

**Medium-term (Next Week - 4 hours):**
8. ✅ Review all "isolated" tables with new logic
9. ✅ Update isolated table metrics
10. ✅ Update documentation

---

## Expected Impact

### Before Fix
```
High confidence: 163/202 (80.7%)
Isolated tables: 223
SP → Table edges: ~584 (incomplete)
```

### After Fix
```
High confidence: 165-170/202 (82-84%)  -- Some SPs will improve
Isolated tables: 150-180 (reduced by ~40-70)
SP → Table edges: ~650-700 (complete)
```

**Quality Improvement:** +40-70 table dependencies discovered

---

## Why This Bug Existed

### Root Causes
1. **Test 3 design flaw:** Only checks if isolated tables are truly isolated, doesn't verify non-isolated tables are captured
2. **Confidence score limitation:** High confidence doesn't mean ALL dependencies captured, just that methods agree
3. **SELECT...INTO edge case:** Less common pattern in codebase, so not prioritized in initial regex design
4. **No full-text validation:** Never cross-checked DDL text against parsed results

### Prevention
1. ✅ Add Test 5 (DDL full-text validation)
2. ✅ Expand `/sub_DL_OptimizeParsing` to include output validation
3. ✅ Add test case for SELECT...INTO patterns
4. ✅ Document SELECT...INTO as critical pattern

---

## Files to Modify

1. **test_isolated_objects.py**
   - Add Test 5: DDL Full-Text Validation

2. **lineage_v3/parsers/quality_aware_parser.py**
   - Add `_extract_select_into_targets()` method
   - Update `_extract_targets_regex()` to call new method
   - Add unit tests for SELECT...INTO patterns

3. **docs/PARSING_USER_GUIDE.md**
   - Document SELECT...INTO pattern handling
   - Add examples

4. **docs/PARSER_EVOLUTION_LOG.md**
   - Document bug discovery and fix

---

## Conclusion

**Status:** 🚨 CRITICAL BUG CONFIRMED

**Impact:** Medium-High (affects 50-100 SPs, ~40-70 missing table dependencies)

**Urgency:** High (isolated table metrics are incorrect)

**Complexity:** Medium (4-8 hours to fix)

**Next Steps:**
1. Create Test 5
2. Quantify exact scope
3. Implement fix (Option 2 or 3)
4. Validate with full parse
5. Update metrics and documentation

---

**Discovered By:** User observation + Claude analysis
**Date:** 2025-11-02
**Parser Version:** v3.7.0
**Affected Scope:** SELECT...INTO statements (~50-100 SPs)

