# Phantom Object Issues - Critical Findings

**Date:** 2025-11-12
**Severity:** High
**Issues Found:** 2 critical problems

---

## Issue 1: B and BB Schemas in Include List ❌

### Problem

**Schemas B and BB appear as phantom objects** but should NOT be allowed.

**Current Configuration:**
```bash
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B
```

**Found in Database:**
- `B.MonthlyFTEAggCount` (Function)
- `B.MonthlyFTEAggSUM` (Function)
- `B.MonthlyLastDayDailyFTEAggSUM` (Function)
- `B.MonthlyLastDayFTEAggCount` (Function)
- `BB.Date` (Function)

### Root Cause

**These are false positives from table aliases:**

```sql
-- SQL pattern that triggers false detection:
FROM Orders B           -- B is a table alias, NOT a schema
WHERE MONTH(B.Date)     -- Regex sees "B.Date(" as B.MonthlyFTE...

-- Another example:
FROM Budget BB          -- BB is a table alias
WHERE BB.Date > ...     -- Regex sees "BB.Date(" as function call
```

**Why they're detected:**
1. Regex pattern: `r'\b\[?(\w+)\]?\.\[?(\w+)\]?\s*\('` matches `B.Date(`
2. Parser thinks "B" is a schema, "Date" is a function
3. Include list has "B" and "BB" as valid schemas
4. Phantom created for non-existent "B.Date" function

### Solution

**Remove B and BB from include list:**

**Before:**
```bash
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B
```

**After:**
```bash
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*
```

**Impact:**
- Will prevent future false positives
- Need to clean up existing 5 B/BB phantoms

---

## Issue 2: All 382 Phantoms Have NO References ❌

### Problem

**ALL phantom objects (100%) have ZERO references.**

**Database Status:**
```
phantom_objects table: 382 rows
phantom_references table: 0 rows  ⚠️ EMPTY!
```

**Examples:**
- `CONSUMPTION_ClinOpsFinance.CadenceBudgetData` - 0 references
- `CONSUMPTION_PRIMA_2.spLoadDimCompany` - 0 references
- `STAGING_PRIMA.tblCompany` - 0 references
- ALL 382 phantoms - 0 references

### Why This is Critical

**Phantoms are detected FROM references:**

```python
# Parser logic:
1. Parse SP_A: "SELECT * FROM PhantomTable"
2. PhantomTable not in catalog → create phantom
3. Track reference: SP_A → PhantomTable  ← THIS SHOULD HAPPEN
4. Result: phantom_references should have 1 row
```

**If phantom has no references, it means:**
- No SP uses it (impossible - why was it created?)
- OR references were deleted
- OR phantom tracking failed

### Investigation Results

**Phantom creation timestamp:**
```
Earliest: 2025-11-12 18:23:46
Latest:   2025-11-12 18:24:02
Duration: ~16 seconds (full parse run)
```

**Reference tracking:**
```sql
SELECT COUNT(*) FROM phantom_references;
-- Result: 0
```

**Code verification:**
- ✅ `_track_phantom_references()` function exists
- ✅ Function is called after creating phantoms (lines 433, 459)
- ✅ UPSERT query looks correct
- ❌ But phantom_references table is empty

### Root Cause Hypotheses

**Theory 1: Database transaction rollback**
- Phantoms committed, references rolled back
- Check: Were there any errors during parsing?

**Theory 2: Workspace connection issue**
- phantom_objects created in one connection
- phantom_references inserted in another (read-only?)
- Check: Is workspace in read-only mode?

**Theory 3: Schema migration**
- phantom_references table created after phantoms
- Old phantoms exist, new table empty
- Check: Was database reset/migrated?

**Theory 4: Parsing mode issue**
- Parser created phantoms but didn't call _track_phantom_references
- Check: Were phantoms created by old parser version?

### How to Reproduce

**Test phantom tracking:**

```python
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

workspace = DuckDBWorkspace('data/lineage_workspace.duckdb')
parser = QualityAwareParser(workspace=workspace)

# Parse one SP
result = parser.parse_object(object_id=715842)  # Sample SP

# Check phantom_references
import duckdb
conn = duckdb.connect('data/lineage_workspace.duckdb', read_only=True)
refs = conn.execute('SELECT COUNT(*) FROM phantom_references').fetchone()[0]
print(f'Phantom references: {refs}')
conn.close()
```

**Expected:** refs > 0 if SP has phantom dependencies
**Actual:** ?

---

## Issue 3: Orphaned Phantoms Cannot Exist

### The Logical Impossibility

**Phantom detection logic:**

```python
# Step 1: Parse SQL
sources = regex_scan(ddl)  # e.g., {'STAGING.Table1', 'STAGING.Table2'}

# Step 2: Check catalog
catalog_sources = validate_against_catalog(sources)
# Result: {'STAGING.Table1'}  ← Found in catalog
# Missing: {'STAGING.Table2'}  ← NOT in catalog = phantom

# Step 3: Create phantom for 'STAGING.Table2'
phantom_id = create_phantom('STAGING.Table2')

# Step 4: Track reference
track_phantom_references(sp_id, phantom_id, 'input')  ← SHOULD HAPPEN

# Result:
# - phantom_objects: 1 row (STAGING.Table2)
# - phantom_references: 1 row (current_sp → STAGING.Table2)
```

**Current state violates this logic:**
- 382 phantoms exist
- 0 references exist
- **Impossibility:** Can't detect phantom without parsing SP that references it

**This means:**
- Phantoms were created correctly during parsing
- References were either never inserted OR were deleted later

---

## Recommended Actions

### Immediate Actions

**1. Check Parser Logs**
```bash
# Did parsing succeed?
grep -i "error\|fail" parser.log

# Were references tracked?
grep -i "phantom" parser.log | grep -i "reference"
```

**2. Test Phantom Tracking**
```python
# Re-parse ONE SP that should have phantoms
result = parser.parse_object(715842)

# Verify phantom_references populated
SELECT COUNT(*) FROM phantom_references WHERE referencing_sp_id = 715842;
```

**3. Remove B and BB from Include List**
```bash
# .env
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*
# Remove: ,BB,B
```

**4. Clean Up Invalid Phantoms**
```sql
-- Delete B and BB phantoms (false positives)
DELETE FROM phantom_references
WHERE phantom_id IN (
    SELECT object_id FROM phantom_objects
    WHERE schema_name IN ('B', 'BB')
);

DELETE FROM phantom_objects
WHERE schema_name IN ('B', 'BB');
```

### Investigation Actions

**1. Check Database Mode**
```python
workspace = DuckDBWorkspace('data/lineage_workspace.duckdb')
print(f'Read-only: {workspace.read_only}')
```

**2. Check Recent Parsing**
```sql
-- When was last parse?
SELECT MAX(last_parsed_at) FROM lineage_metadata;

-- How many SPs parsed?
SELECT COUNT(*) FROM lineage_metadata WHERE last_parsed_at > '2025-11-12';
```

**3. Enable Debug Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Re-parse with debug output
result = parser.parse_object(715842)
# Look for: "Tracked phantom reference: SP X -> Phantom Y"
```

### Long-term Fixes

**1. Add Phantom Reference Validation**
```python
# After parsing, verify references were tracked
phantoms_created = len(phantom_ids_map)
refs_tracked = workspace.query(
    'SELECT COUNT(*) FROM phantom_references WHERE referencing_sp_id = ?',
    [sp_id]
)[0][0]

if phantoms_created > 0 and refs_tracked == 0:
    logger.error(f"SP {sp_id}: Created {phantoms_created} phantoms but tracked 0 references!")
```

**2. Add Orphan Detection**
```python
# Periodic cleanup
orphaned = workspace.query('''
    SELECT p.object_id, p.schema_name, p.object_name
    FROM phantom_objects p
    LEFT JOIN phantom_references r ON p.object_id = r.phantom_id
    WHERE r.phantom_id IS NULL
''')

if orphaned:
    logger.warning(f"Found {len(orphaned)} orphaned phantoms - this should not happen!")
```

**3. Stricter Include List**
```bash
# Only allow multi-character schemas
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*

# Exclude all single-letter schemas (likely aliases)
PHANTOM_MIN_SCHEMA_LENGTH=3  # New config option
```

---

## Summary

### Issues Found

1. ❌ **B and BB schemas** - False positives from table aliases
2. ❌ **382 orphaned phantoms** - All phantoms have no references
3. ❌ **phantom_references table empty** - Tracking logic failed

### Impact

- **Data Quality:** 5 false positive phantoms (B, BB schemas)
- **Functionality:** Phantom impact analysis broken (no references)
- **User Experience:** Confusing phantom objects with no connections

### Root Cause

**B and BB issue:**
- Single-letter schemas in include list match table aliases
- Solution: Remove from include list

**Orphaned phantoms issue:**
- Unknown - need investigation
- Possible causes: Transaction rollback, read-only mode, schema migration
- Solution: Debug phantom tracking, add validation

### Next Steps

1. ✅ Remove B and BB from include list
2. ✅ Clean up 5 B/BB phantoms
3. ⏳ Investigate why phantom_references is empty
4. ⏳ Test phantom tracking on sample SP
5. ⏳ Add validation to prevent orphaned phantoms

---

**Status:** ⚠️ Critical issues identified, fixes needed
**Priority:** High
**Risk:** Medium (data quality issue, no functional breakage)
