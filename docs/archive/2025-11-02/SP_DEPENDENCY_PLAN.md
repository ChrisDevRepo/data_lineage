# SP-to-SP Dependency Tracking Implementation Plan

**Issue:** Parser currently removes ALL EXEC statements, missing SP-to-SP dependencies
**Example:** `spLoadDateRange` calls `spLoadDateRangeDetails` via EXEC - currently NOT tracked

**Date:** 2025-11-02
**Priority:** HIGH (63 missing dependencies)

---

## Problem Analysis

### Current Behavior
```python
# lineage_v3/parsers/quality_aware_parser.py:114
(r'\bEXEC\s+\[?[^\]]+\]?\.\[?[^\]]+\]?[^;]*;?', '', 0),  # Removes ALL EXEC
```

**Impact:**
- 63 SP-to-SP dependencies MISSING from lineage graph
- Example: `CONSUMPTION_ClinOpsFinance.spLoadDateRange` → `spLoadDateRangeDetails`

### Data Analysis Results

```
EXEC Statement Classification (764 total):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Logging calls (LogMessage, etc.):      460
Utility calls (spLastRowCount, etc.):  222
Resolvable SP-to-SP:                    63 ⭐ MISSING
Unresolvable (external DB):             19
```

**Key Insight:**
- 100% of EXEC statements are SP calls (no dynamic SQL)
- Regex can reliably detect: `EXEC [schema].[sp_name]`
- SQLGlot can NOT parse EXEC (T-SQL specific)

---

## Solution Design

### 1. Detection Strategy

**Pattern:**
```regex
\bEXEC(?:UTE)?\s+\[?(\w+)\]?\.\[?(\w+)\]?
```

**Examples:**
```sql
EXEC [dbo].[spProcessOrders]                          -- Match
EXEC CONSUMPTION_FINANCE.spLoadDimAccount            -- Match
exec  [ADMIN].[sp_SetProcessSetRunSucceeded]         -- Match (case-insensitive)
EXEC [dbo].[LogMessage] @msg = 'test'                -- Match (but filter later)
EXEC (@dynamicSQL)                                    -- NO MATCH (dynamic SQL)
```

### 2. Filtering Strategy

**Exclude utility/logging SPs (noise):**
```python
EXCLUDED_UTILITY_SPS = {
    # Logging
    'logmessage', 'logerror', 'loginfo', 'logwarning',

    # Utility
    'splastrowcount',
}
```

**Validation:**
- Check if called SP exists in `objects` catalog
- Skip if SP not found (external database)

### 3. Classification

**SP-to-SP calls are INPUTS (dependencies):**
```
spLoadDateRange (caller)
  ├─ INPUT: DimDate table (FROM clause)
  ├─ INPUT: spLoadDateRangeDetails (EXEC call)  ← NEW
  └─ OUTPUT: FactDateRange table (INSERT clause)
```

**NOT outputs** (SP doesn't write TO another SP)

---

## Implementation

### Step 1: Update Preprocessing (quality_aware_parser.py:114)

**BEFORE:**
```python
# Remove EXEC commands (stored procedure calls)
(r'\bEXEC\s+\[?[^\]]+\]?\.\[?[^\]]+\]?[^;]*;?', '', 0),
```

**AFTER:**
```python
# Remove only logging/utility EXEC calls (keep SP-to-SP calls for lineage)
# Pattern: EXEC [schema].[sp_name] where sp_name is logging/utility
(r'\bEXEC(?:UTE)?\s+\[?[^\]]+\]?\.\[?(LogMessage|LogError|LogInfo|spLastRowCount)\]?[^;]*;?',
 '', re.IGNORECASE),
```

### Step 2: Add EXEC SP Pattern to Regex Scan (quality_aware_parser.py:349)

**Location:** `_regex_scan()` method, SOURCE patterns section

**Add new pattern:**
```python
# SP-TO-SP patterns (SP calls other SP via EXEC)
# Pattern: EXEC [schema].[sp_name]
# These are INPUT dependencies (caller depends on callee)
exec_sp_patterns = [
    r'\bEXEC(?:UTE)?\s+\[?(\w+)\]?\.\[?(\w+)\]?',  # EXEC [schema].[sp_name]
]
```

**Validation logic:**
```python
for pattern in exec_sp_patterns:
    matches = re.findall(pattern, ddl, re.IGNORECASE)
    for schema, sp_name in matches:
        # Filter out logging/utility SPs
        if sp_name.lower() in EXCLUDED_UTILITY_SPS:
            continue

        # Filter non-persistent objects
        if self._is_excluded(schema, sp_name):
            continue

        if self._is_non_persistent(schema, sp_name, non_persistent):
            continue

        sources.add(f"{schema}.{sp_name}")  # SP dependency = input
```

### Step 3: Add Excluded Utility SPs Constant (quality_aware_parser.py:72)

**Location:** After `EXCLUDED_SCHEMAS` constant

```python
# Utility/logging SPs to exclude from lineage (noise)
EXCLUDED_UTILITY_SPS = {
    # Logging (administrative, not data lineage)
    'logmessage', 'logerror', 'loginfo', 'logwarning',

    # Utility (helper functions, not data dependencies)
    'splastrowcount',
}
```

### Step 4: SQLGlot AST - Skip

**Reason:** SQLGlot doesn't parse EXEC statements reliably (T-SQL specific)

**No changes needed** - regex extraction is sufficient and more reliable

---

## Testing Strategy

### Before Changes
```bash
# Create baseline
/sub_DL_OptimizeParsing init --name baseline_20251102_before_exec_fix

# Run evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_20251102_before_exec_fix
```

**Expected Results:**
- spLoadDateRange: Missing 2-3 dependencies

### After Changes
```bash
# Reload parquet (optional if DDL unchanged)
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# Run evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_20251102_before_exec_fix
```

**Expected Results:**
- spLoadDateRange: +2-3 dependencies (SP calls detected)
- Overall: +63 dependencies across all SPs
- No regressions (confidence scores same or higher)

### Validation Queries
```python
# Check spLoadDateRange specifically
query = """
SELECT inputs, outputs
FROM lineage_metadata
WHERE object_id = (
    SELECT object_id FROM objects
    WHERE object_name = 'spLoadDateRange'
)
"""
```

---

## Pass Criteria

✅ **Success:**
- 63 SP-to-SP dependencies detected
- Logging/utility calls filtered (682 excluded)
- No regressions in confidence scores
- External SPs skipped (19 unresolvable)

❌ **Failure:**
- False positives (logging calls in lineage)
- Regressions (high-confidence SPs drop)
- Missing valid SP dependencies

---

## Rollback Plan

If issues detected:
1. Revert quality_aware_parser.py changes
2. Re-run parser: `python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh`
3. Document issue in PARSER_EVOLUTION_LOG.md

---

## Impact Assessment

**Benefits:**
- +63 dependencies (more complete lineage)
- Captures orchestration patterns (master SP → worker SPs)
- Better visualization of ETL workflows

**Risks:**
- Low (regex pattern well-tested)
- Minimal code changes (3 locations)
- Easily reversible

**Cost:**
- Development: 1 hour
- Testing: /sub_DL_OptimizeParsing run (~5 minutes)
- Zero AI cost (regex only)

---

## Example: spLoadDateRange

**Before:**
```json
{
  "object_id": 12345,
  "object_name": "spLoadDateRange",
  "inputs": [101, 102],  // Just tables
  "outputs": [201],
  "confidence": 0.85
}
```

**After:**
```json
{
  "object_id": 12345,
  "object_name": "spLoadDateRange",
  "inputs": [
    101,  // DimDate table
    102,  // ConfigTable
    301,  // spLoadDateRangeDetails (NEW!)
    302   // spLoadDateRangeMonthClose_Config (NEW!)
  ],
  "outputs": [201],
  "confidence": 0.85
}
```

---

## Notes

- **Regex vs SQLGlot:** Regex more reliable for EXEC (T-SQL specific)
- **AI not needed:** Pattern is deterministic
- **Performance:** Negligible impact (regex already runs)
- **Maintenance:** Add to EXCLUDED_UTILITY_SPS as needed

---

## Related Documentation

- [PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
- [PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
- [quality_aware_parser.py](lineage_v3/parsers/quality_aware_parser.py)
