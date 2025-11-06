# SP-to-SP Lineage Direction Fix Verification

## Issue Identified

In the regex parser, when we detect `EXECUTE` or `EXEC` statements, we were incorrectly treating the called stored procedures as **inputs** (dependencies) when they should be **outputs** (targets).

## Current Behavior (Before Fix)

```
spLoadFactTables:
  - Inputs: [spLoadFactOrders, spLoadFactInvoices, ...] ← WRONG!
  - Outputs: []
```

In the GUI, this shows **incoming arrows** to `spLoadFactTables` from the SPs it calls.

## Expected Behavior (After Fix)

```
spLoadFactTables:
  - Inputs: []
  - Outputs: [spLoadFactOrders, spLoadFactInvoices, ...] ← CORRECT!
```

In the GUI, this shows **outgoing arrows** from `spLoadFactTables` to the SPs it calls.

## Root Cause

File: `lineage_v3/parsers/quality_aware_parser.py:226-227`

**Before:**
```python
# STEP 5b: Add SP-to-SP lineage (v4.0.1)
# Stored procedures are INPUTS (we read/call them)  ← WRONG COMMENT!
sp_ids = self._resolve_sp_names(regex_sp_calls_valid)
input_ids.extend(sp_ids)  ← WRONG DIRECTION!
```

**After:**
```python
# STEP 5b: Add SP-to-SP lineage (v4.0.1)
# Stored procedures are OUTPUTS (we call/execute them)  ← CORRECT!
# When SP_A executes SP_B: SP_A → SP_B (SP_B is a target/output)
sp_ids = self._resolve_sp_names(regex_sp_calls_valid)
output_ids.extend(sp_ids)  ← CORRECT DIRECTION!
```

## Verification from Existing Data

From `data/latest_frontend_lineage.json`:

```json
{
  "id": "1960777773",
  "name": "spLoadFactTables",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Stored Procedure",
  "description": "Confidence: 0.85 (parser)",
  "data_model_type": "Other",
  "inputs": [
    "14113149",      // spLoadFactLaborCostForEarnedValue_1
    "322603708",     // Other SP
    "765306298",     // Other SP
    "838891072",     // Other SP
    "1845618780",    // Other SP
    "1849810814",    // Other SP
    "1860147480"     // Other SP
  ],
  "outputs": []  // Empty!
}
```

These 7 "inputs" are actually stored procedures that `spLoadFactTables` **executes**, so they should be **outputs**.

## Impact

- **Affects:** 151 SP-to-SP relationships (all orchestrator/utility SPs)
- **Visual Impact:** Arrow direction in GUI will be corrected
- **Semantic Impact:** Call hierarchy will be properly represented
- **Examples:** spLoadFactTables, spLoadDimTables, spLoadArAnalyticsMetricsETL

## Confidence Metrics

This fix does **not** affect confidence scores. The confidence calculation is based on the count of dependencies found, not their direction. All 202 SPs at ≥0.85 confidence remain at high confidence.

## Next Steps

1. ✅ Fix applied to `quality_aware_parser.py:228`
2. ✅ Changelog updated (v4.0.3)
3. ✅ CLAUDE.md updated
4. ⏳ Run full parser to regenerate lineage data
5. ⏳ Verify in GUI that arrows point correctly
6. ⏳ Commit changes

## Code Changes Summary

**File:** `lineage_v3/parsers/quality_aware_parser.py`
- **Line 16:** Version updated to 4.0.3
- **Lines 20-26:** Added v4.0.3 changelog entry
- **Line 43:** Updated v4.0.1 note to reference correction
- **Lines 225-228:** Changed `input_ids.extend(sp_ids)` → `output_ids.extend(sp_ids)`

**File:** `CLAUDE.md`
- **Line 183:** Updated version to v4.0.3 (SP-to-SP Direction Fix)
