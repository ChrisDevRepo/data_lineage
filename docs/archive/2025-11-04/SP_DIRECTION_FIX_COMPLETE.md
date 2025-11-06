# SP-to-SP Lineage Direction Fix - COMPLETED

## Issue Summary

When stored procedures use `EXECUTE` or `EXEC` to call other stored procedures, the parser was incorrectly treating these calls as **inputs** (incoming arrows) instead of **outputs** (outgoing arrows) in the GUI.

### Example Problem

**Before Fix:**
```
spLoadFactTables:
  inputs: [spLoadFactOrders, spLoadFactInvoices, ...]  ← WRONG!
  outputs: []
```
GUI showed **incoming arrows** to `spLoadFactTables` from the SPs it calls.

**After Fix:**
```
spLoadFactTables:
  inputs: []
  outputs: [spLoadFactOrders, spLoadFactInvoices, ...]  ← CORRECT!
```
GUI now shows **outgoing arrows** from `spLoadFactTables` to the SPs it calls.

---

## Root Causes (Two Bugs Fixed)

### Bug #1: Parser Direction
**File:** `lineage_v3/parsers/quality_aware_parser.py:228`

The regex parser correctly detected EXEC/EXECUTE statements and identified the called SPs, but then added them to `input_ids` instead of `output_ids`.

**Fix:**
```python
# Before
input_ids.extend(sp_ids)  # WRONG - made SPs appear as inputs

# After
output_ids.extend(sp_ids)  # CORRECT - SPs are outputs/targets
```

**Rationale:** When `SP_A` executes `SP_B`, the relationship is `SP_A → SP_B`, meaning `SP_B` is a target/output of `SP_A`, not an input.

### Bug #2: Bidirectional Graph Reverse Lookup
**File:** `lineage_v3/main.py:458-474`

The bidirectional graph building logic was applying reverse lookups to **all objects**, including Stored Procedures. This caused SP-to-SP relationships to be duplicated in both directions.

**Problem:**
- Reverse lookup is designed for Tables/Views (which don't have their own DDL)
- Stored Procedures have their own parsed dependencies
- Applying reverse lookup to SPs created duplicate/incorrect relationships

**Fix:**
Added a check to skip Stored Procedures during reverse lookup:
```python
# Check if this is a Table or View (not a Stored Procedure)
obj_type = db.query("SELECT object_type FROM objects WHERE object_id = ?", [table_id])

# Skip Stored Procedures - they have their own dependencies from parsing
if obj_type == 'Stored Procedure':
    continue
```

**Evidence of Fix:**
- Before: "Updated 483 Tables/Views with reverse dependencies" (included SPs!)
- After: "Updated 282 Tables/Views with reverse dependencies" (excludes SPs correctly)

---

## Verification

### Test Case: spLoadFactTables

**DDL:**
```sql
CREATE PROC [CONSUMPTION_FINANCE].[spLoadFactTables] AS
begin
exec CONSUMPTION_FINANCE.spLoadGLCognosData;
exec CONSUMPTION_FINANCE.spLoadFactGLCOGNOS;
exec CONSUMPTION_FINANCE.spLoadFactGLSAP;
exec CONSUMPTION_FINANCE.spLoadFactAgingSAP;
exec CONSUMPTION_POWERBI.spLoadFactLaborCostForEarnedValue_1;
exec CONSUMPTION_POWERBI.spLoadFactLaborCostForEarnedValue_2;
exec CONSUMPTION_POWERBI.spLoadFactAggregatedLaborCost;
end
```

**Before Fix (from latest_frontend_lineage.json):**
```json
{
  "name": "spLoadFactTables",
  "inputs": [7 stored procedure IDs],  ← WRONG
  "outputs": []
}
```

**After Fix (verified in new latest_frontend_lineage.json):**
```json
{
  "name": "spLoadFactTables",
  "inputs": [],                        ← CORRECT
  "outputs": [7 stored procedure IDs]  ← CORRECT
}
```

### Verification of Called SP

**spLoadFactLaborCostForEarnedValue_1** (one of the called SPs):
- **Before:** Would have had `spLoadFactTables` as an input (incorrect reverse lookup)
- **After:** Shows only its own parsed dependencies (3 table inputs, 1 table output)
- Does NOT show `spLoadFactTables` as an input (correct!)

---

## Impact

### Scope
- **Affects:** All 151 SP-to-SP relationships tracked in the system
- **Visual Impact:** Arrow direction in GUI is now correct
- **Semantic Impact:** Call hierarchy properly represented
- **Examples:** spLoadFactTables, spLoadDimTables, spLoadArAnalyticsMetricsETL

### Confidence Metrics
- No change to confidence scores (still 97.0% SP confidence, 95.5% overall)
- Confidence is based on dependency counts, not direction
- All 202 SPs remain at high confidence (≥0.85)

---

## Files Changed

### 1. lineage_v3/parsers/quality_aware_parser.py
**Changes:**
- Line 16: Version updated to v4.0.3
- Lines 20-26: Added v4.0.3 changelog entry
- Line 43: Updated v4.0.1 note to reference correction in v4.0.3
- Lines 225-228: Changed `input_ids.extend(sp_ids)` → `output_ids.extend(sp_ids)`

### 2. lineage_v3/main.py
**Changes:**
- Lines 459-460: Added comment clarifying SPs should be excluded
- Lines 463-474: Added object type check to skip Stored Procedures in reverse lookup

### 3. CLAUDE.md
**Changes:**
- Line 183: Updated version to v4.0.3 (SP-to-SP Direction Fix)

### 4. data/latest_frontend_lineage.json
**Changes:**
- Regenerated with correct SP-to-SP directions
- File size increased from 218K to 2.2M (includes DDL text)

---

## Steps Performed

1. ✅ Identified issue: SP calls were in wrong direction
2. ✅ Fixed parser: Changed sp_ids from inputs → outputs
3. ✅ Fixed bidirectional graph: Excluded SPs from reverse lookup
4. ✅ Updated version to v4.0.3 with changelog
5. ✅ Deleted DuckDB workspace to ensure clean state
6. ✅ Re-ran parser with full refresh
7. ✅ Verified fix in JSON output
8. ✅ Restarted frontend and backend servers
9. ✅ Updated documentation

---

## Testing in GUI

To verify the fix works in the GUI:

1. Open: http://localhost:3000
2. Import the data (already loaded at startup)
3. Search for: `spLoadFactTables`
4. Verify:
   - No incoming arrows (inputs are empty)
   - 7 outgoing arrows to the SPs it calls
   - Each arrow should point FROM spLoadFactTables TO the called SP

5. Click on one of the called SPs (e.g., `spLoadFactLaborCostForEarnedValue_1`)
6. Verify:
   - Does NOT show an incoming arrow from spLoadFactTables
   - Shows its own table dependencies correctly

---

## Server Status

✅ **Backend:** http://localhost:8000 (PID: 2552)
✅ **Frontend:** http://localhost:3000 (PID: 2590)

**Logs:**
- Backend: `tail -f /tmp/backend.log`
- Frontend: `tail -f /tmp/frontend.log`

**Stop Services:**
```bash
./stop-app.sh
# or
kill 2552 2590
```

---

## Summary

**Status:** ✅ **COMPLETED**

Both bugs have been fixed:
1. Parser now correctly identifies SP calls as outputs (not inputs)
2. Bidirectional graph no longer corrupts SP dependencies with reverse lookup

The lineage data has been regenerated and the servers restarted. You can now view the corrected SP-to-SP relationships in the GUI, where arrows will point in the correct direction (from caller to callee).

**Impact:** 151 SP-to-SP relationships now display correctly with proper directional flow.

---

**Date:** 2025-11-04
**Version:** v4.0.3 (SP-to-SP Direction Fix)
