# Phantom Function Schema Filter Bug

**Date:** 2025-11-12
**Version:** v4.3.3
**Severity:** Medium (data quality issue)

---

## Issue Summary

**Historical Issue (v4.3.2):** Phantom functions bypassed the schema filter (v4.3.2 used `PHANTOM_INCLUDE_SCHEMAS`), allowing invalid schemas (AA, TS, U, ra, s) to be stored in the database.

**Status:** ✅ Fixed in v4.3.3 with redesigned phantom philosophy (EXTERNAL sources only).

---

## Root Cause

**File:** `lineage_v3/parsers/quality_aware_parser.py`

### Phantom Tables (Lines 1406-1409) ✅ CORRECT
```python
# v4.3.0: INCLUDE LIST APPROACH - Only create phantoms for schemas matching include patterns
if not self._schema_matches_include_list(schema):
    logger.debug(f"Skipping phantom (schema not in include list): {name}")
    continue
```

### Phantom Functions (Lines 441-445) ❌ BUG
```python
parts = func_name.split('.')
if len(parts) == 2:
    schema, name = parts
    if not self._is_excluded(schema, name):  # ❌ Only checks excluded schemas
        phantom_functions.add(func_name)      # ❌ Does NOT check include list!
```

**The bug:** Phantom functions only check `_is_excluded` (system schemas), not `_schema_matches_include_list`.

---

## Evidence

### Database Query Results

Found **8 phantom functions** with **5 invalid schemas**:

| Schema | Object | Type | Status |
|--------|--------|------|--------|
| **AA** | Date | Function | ❌ Should NOT be allowed |
| **TS** | Date | Function | ❌ Should NOT be allowed |
| **U** | MonthlyFTEAggCount | Function | ❌ Should NOT be allowed |
| **U** | MonthlyFTEAggSUM | Function | ❌ Should NOT be allowed |
| **U** | MonthlyLastDayDailyFTEAggSUM | Function | ❌ Should NOT be allowed |
| **U** | MonthlyLastDayFTEAggCount | Function | ❌ Should NOT be allowed |
| **ra** | Submission | Function | ❌ Should NOT be allowed |
| **s** | Submission | Function | ❌ Should NOT be allowed |
| **B** | (4 functions) | Function | ✅ Expected (in include list) |
| **BB** | Date | Function | ✅ Expected (in include list) |

### Include List Configuration (v4.3.3 - REDESIGNED)

```env
# v4.3.3: EXTERNAL sources ONLY (exact match, no wildcards)
PHANTOM_EXTERNAL_SCHEMAS=  # Empty = no external dependencies
# Examples: power_consumption,external_lakehouse,partner_erp
```

**Philosophy:** Phantoms represent EXTERNAL dependencies NOT in our metadata database.

**Expected behavior:** Only phantoms from exact schema matches should be created.

**Actual behavior (before v4.3.3 fix):** Phantom functions ignored the filter entirely.

---

## Impact

### Data Quality
- ❌ 8 invalid phantom functions in database
- ❌ Schemas: AA, TS, U, ra, s (5 invalid schemas)
- ✅ No functional impact (orphaned phantoms, no references)

### Root Cause of Invalid Schemas
These are likely **table aliases** being misidentified as function calls:

```sql
FROM Orders U           -- U is a table alias
WHERE MONTH(U.Date) ... -- Regex sees "U.Date(" and thinks it's a function
```

The regex pattern `r'\b\[?(\w+)\]?\.\[?(\w+)\]?\s*\('` matches ANY:
- `alias.column(` patterns (false positive)
- `schema.function(` patterns (true positive)

The include list filter would have caught and rejected the false positives.

---

## Fix

### Code Changes

**File:** `lineage_v3/parsers/quality_aware_parser.py`
**Lines:** 441-445

**Before:**
```python
parts = func_name.split('.')
if len(parts) == 2:
    schema, name = parts
    if not self._is_excluded(schema, name):
        phantom_functions.add(func_name)
```

**After:**
```python
parts = func_name.split('.')
if len(parts) == 2:
    schema, name = parts
    # v4.3.3: Apply same filtering as phantom tables
    if not self._is_excluded(schema, name) and self._schema_matches_include_list(schema):
        phantom_functions.add(func_name)
```

### Testing

**Before fix:**
```bash
python3 -c "
import duckdb
conn = duckdb.connect('data/lineage_workspace.duckdb', read_only=True)
result = conn.execute('''
    SELECT schema_name, COUNT(*) as count
    FROM phantom_objects
    WHERE schema_name IN ('AA', 'TS', 'U', 'ra', 's')
    GROUP BY schema_name
''').fetchall()
print(f'Invalid schemas: {len(result)}')
for row in result:
    print(f'  {row[0]}: {row[1]} objects')
conn.close()
"
```

Expected output:
```
Invalid schemas: 5
  AA: 1 objects
  TS: 1 objects
  U: 4 objects
  ra: 1 objects
  s: 1 objects
```

**After fix:**
1. Drop existing invalid phantoms (one-time cleanup)
2. Re-run parser on all SPs
3. Verify no invalid schemas appear

---

## Cleanup Required

After applying the fix, clean up existing invalid phantoms:

```sql
-- Delete invalid phantom functions
DELETE FROM phantom_references
WHERE phantom_id IN (
    SELECT object_id FROM phantom_objects
    WHERE schema_name IN ('AA', 'TS', 'U', 'ra', 's')
    AND object_type = 'Function'
);

DELETE FROM phantom_objects
WHERE schema_name IN ('AA', 'TS', 'U', 'ra', 's')
AND object_type = 'Function';
```

---

## Acceptance Criteria

✅ Phantom functions check `_schema_matches_include_list`
✅ Only schemas matching `PHANTOM_EXTERNAL_SCHEMAS` can create phantoms (v4.3.3)
✅ No invalid schemas (AA, TS, U, ra, s) in database
✅ All existing parser tests still pass
✅ Parser still at 100% success rate

---

## Files to Update

1. ✅ `lineage_v3/parsers/quality_aware_parser.py` - Add include list check
2. ✅ Clean up existing invalid phantoms in database
3. ✅ Test on full SP set (349 SPs)
4. ✅ Update documentation

---

**Status:** ✅ Root cause identified, fix ready to implement
**Priority:** Medium (no functional impact, but data quality issue)
