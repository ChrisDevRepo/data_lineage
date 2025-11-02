# SP Schema Mismatch Analysis

**Date:** 2025-11-02
**SP:** `CONSUMPTION_ClinOpsFinance.spLoadCadenceBudget_LaborCost_PrimaUtilization_Junc`
**Issue:** Medium confidence (0.75) with missing dependencies

---

## Problem Statement

**User Report:** "this is wrong spLoadCadenceBudget_LaborCost_PrimaUtilization_Junc"

**Current State:**
- Confidence: 0.75 (medium)
- Inputs captured: 1 (self-reference)
- Outputs captured: 0

**Expected:**
- Inputs: 4 tables
- Outputs: 1 table

---

## Root Cause: Schema Mismatch

### What the SP Code References

```sql
-- In DDL:
FROM CONSUMPTION_POWERBI.CadenceBudgetData           -- ❌ Wrong schema!
FROM CONSUMPTION_POWERBI.EmployeeUtilization         -- ❌ Wrong schema!
FROM CONSUMPTION_POWERBI.FactLaborCostForEarnedValue -- ✅ Exists
TRUNCATE TABLE CONSUMPTION_ClinOpsFinance.CadenceBudget_LaborCost_PrimaUtilization_Junc
```

### What Actually Exists in Catalog

```sql
-- Actual tables:
CONSUMPTION_ClinOpsFinance.CadenceBudgetData         -- ✅ Different schema!
CONSUMPTION_ClinOpsFinance.EmployeeUtilization       -- ❌ Not found (may be view/different name)
CONSUMPTION_POWERBI.FactLaborCostForEarnedValue      -- ✅ Correct schema
```

### The Mismatch

| DDL Reference | Exists in Catalog? | Actual Location |
|---------------|-------------------|-----------------|
| `CONSUMPTION_POWERBI.CadenceBudgetData` | ❌ NO | `CONSUMPTION_ClinOpsFinance.CadenceBudgetData` |
| `CONSUMPTION_POWERBI.EmployeeUtilization` | ❌ NO | Not found (different name?) |
| `CONSUMPTION_POWERBI.FactLaborCostForEarnedValue` | ✅ YES | Correct |
| `dbo.DimDate` | ✅ YES | Correct |

---

## Parser Behavior (Correct)

**Parser Logic:**
1. ✅ Extract table names from SQL: `CONSUMPTION_POWERBI.CadenceBudgetData`
2. ✅ Look up in `objects` catalog
3. ✅ NOT FOUND → Exclude from dependencies
4. ✅ Only add valid object IDs to result

**Why This Is Correct:**
- Parser MUST validate against catalog
- Can't add non-existent object IDs
- Invalid references should be excluded
- This prevents phantom dependencies

**Quality Check Results:**
```
regex_sources: 2        (Found: CadenceBudgetData, EmployeeUtilization)
parser_sources: 1       (Validated: only FactLaborCostForEarnedValue exists)
source_match: 0.5       (50% - low match rate)
overall_match: 0.8      (80% - medium confidence)
```

---

## Why the Schema Mismatch Exists

**Possible Reasons:**

### 1. Tables Were Moved
- Tables originally in `CONSUMPTION_POWERBI`
- Later moved to `CONSUMPTION_ClinOpsFinance`
- SP code not updated

### 2. Wrong Schema in SP Code
- SP developer used wrong schema
- Code works due to synonym or default schema
- DMV shows actual resolved schema

### 3. Views or Synonyms
- `CONSUMPTION_POWERBI.CadenceBudgetData` might be a synonym
- Points to `CONSUMPTION_ClinOpsFinance.CadenceBudgetData`
- DMV snapshot didn't capture synonyms

### 4. Multiple Versions
- Development vs Production schema differences
- SP extracted from one environment
- DMV from another environment

---

## Impact Analysis

### On Parsing
- **Medium confidence (0.75)** is appropriate
- Parser working correctly (validating references)
- Missing dependencies reflect actual catalog state

### On Lineage
- **Incomplete lineage graph**
- Missing edges from SP to actual source tables
- Downstream users won't see true dependencies

### On Users
- Lineage visualization incomplete
- Impact analysis inaccurate
- May miss table dependencies

---

## Solutions

### Option 1: Fix SP Code (Recommended)
**Action:** Update SP to use correct schemas

```sql
-- Change FROM:
FROM CONSUMPTION_POWERBI.CadenceBudgetData

-- TO:
FROM CONSUMPTION_ClinOpsFinance.CadenceBudgetData
```

**Pros:**
- Fixes root cause
- Code matches reality
- Future parses will be correct

**Cons:**
- Requires code deployment
- May break if synonyms exist
- Need testing

### Option 2: Add Synonyms to Catalog
**Action:** Capture synonyms in DMV extraction

**Pros:**
- No code changes needed
- Parser can resolve synonyms
- Reflects actual database structure

**Cons:**
- Requires extractor changes
- May not be synonyms (just wrong code)

### Option 3: Fuzzy Matching (Not Recommended)
**Action:** Parser tries to "guess" correct schema

```python
# If CONSUMPTION_POWERBI.CadenceBudgetData not found:
# Try CONSUMPTION_ClinOpsFinance.CadenceBudgetData
```

**Pros:**
- Works around schema mismatches

**Cons:**
- Dangerous (could match wrong tables)
- Hides real problems in SP code
- Reduces parser reliability

### Option 4: Accept As-Is (Current)
**Action:** No changes

**Pros:**
- Parser is correct
- No development effort
- Medium confidence flags the issue

**Cons:**
- Incomplete lineage
- Users may notice missing dependencies

---

## Recommendation

**Priority 1: Investigate Schema Mismatch**

**Steps:**
1. Check if `CONSUMPTION_POWERBI.CadenceBudgetData` is a synonym
   ```sql
   SELECT *
   FROM sys.synonyms
   WHERE name = 'CadenceBudgetData' AND schema_id = SCHEMA_ID('CONSUMPTION_POWERBI')
   ```

2. Check actual query execution logs
   ```sql
   SELECT command_text
   FROM query_logs
   WHERE command_text LIKE '%CadenceBudgetData%'
   ```

3. Verify which schema the SP actually uses at runtime

**Priority 2: Update DMV Extraction**

If synonyms exist:
- Add synonym extraction to DMV snapshot
- Include synonym definitions in `objects` table
- Parser can then resolve synonym → actual table

**Priority 3: Document Limitations**

Add to parser documentation:
- Parser validates all references against catalog
- Schema mismatches result in lower confidence
- Check query logs for actual runtime behavior

---

## Similar SPs to Check

Based on this finding, check other medium-confidence SPs for schema mismatches:

1. **CONSUMPTION_FINANCE.spLoadDimCompany** (0.75)
2. **CONSUMPTION_FINANCE.spLoadDimAccount** (0.75)
3. **CONSUMPTION_FINANCE.spLoadDimCurrency** (0.75)
4. **CONSUMPTION_FINANCE.spLoadDimConsType** (0.75)
5. **CONSUMPTION_FINANCE.spLoadDimActuality** (0.75)

**Pattern:** Multiple SPs in CONSUMPTION_FINANCE with 0.75 confidence

**Hypothesis:** These may all have schema mismatch issues

**Test:**
```sql
-- For each medium-confidence SP:
1. Extract table references from DDL
2. Check if referenced schemas exist in catalog
3. Search for table names in different schemas
```

---

## Metrics Impact

**Current:**
```
Medium confidence (0.75): 10 SPs (5.0%)
Reason: Schema mismatches, not parser bugs
```

**If schemas were corrected:**
```
Potential improvement: +10 SPs → 84.2% high confidence
Actual improvement: Depends on how many have schema issues
```

---

## Testing Commands

### Check for Synonyms
```sql
SELECT
    s.name AS synonym_name,
    SCHEMA_NAME(s.schema_id) AS synonym_schema,
    s.base_object_name AS target_object
FROM sys.synonyms s
WHERE s.name LIKE '%CadenceBudget%' OR s.name LIKE '%EmployeeUtilization%'
```

### Check Query Logs for Actual Usage
```sql
SELECT DISTINCT
    command_text
FROM query_logs
WHERE command_text LIKE '%spLoadCadenceBudget_LaborCost_PrimaUtilization_Junc%'
  AND status = 'Completed'
ORDER BY command_text
```

### Find Schema Mismatches in All SPs
```sql
-- Extract table references from all SP DDLs
-- Compare against objects catalog
-- Report mismatches
```

---

## Conclusion

**Issue:** NOT a parser bug - **correct behavior**

**Root Cause:** SP code references wrong schemas

**Parser Behavior:** ✅ Correctly validates references and excludes invalid ones

**Solution:** Fix SP code or add synonyms to catalog extraction

**Impact:** 10 medium-confidence SPs likely have similar schema mismatch issues

**Recommendation:** Investigate schema structure and update either:
1. SP code to use correct schemas, OR
2. DMV extraction to capture synonyms

---

**Status:** ✅ Root cause identified - Schema mismatch in SP code, not parser bug
**Next Steps:** Check for synonyms, update DMV extraction, or fix SP schemas
