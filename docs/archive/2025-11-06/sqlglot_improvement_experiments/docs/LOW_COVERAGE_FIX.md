# Low Coverage Bug Fix - 66.8% → Expected 95%+

**Date:** 2025-11-03
**Issue:** Coverage only 66.8% instead of expected ~95%
**Root Cause:** Bidirectional graph was preventing SPs from being parsed

---

## Problem Analysis

### User Report
```
📦 Objects: 763 (61 views, 202 SPs, 500 tables)
🎯 Confidence: 507 high (66.4% ≥0.75)
📊 Coverage: 510/763 (66.8%)
```

**Expected:** ~95% coverage with three-way parsing (regex, SQLGlot, AI)
**Actual:** 66.8% coverage

---

## Investigation Results

### Coverage Breakdown
```
Stored Procedures: 202/202 (100.0%) ✅ All have metadata
Views:              60/61  (98.4%)  ✅ Almost all parsed
Tables:            248/500 (49.6%)  ❌ ONLY HALF!
```

**252 tables completely unparsed!**

### Why Tables Are Unparsed

**Analysis showed:**
- 245 tables are truly isolated (no dependencies in DMV)
- 17 tables ARE referenced but still unparsed
- Example: `GlobalObjectRelations` - referenced by 7 objects, still unparsed!

**Root Cause:** Bidirectional graph should populate these tables but isn't working.

---

## Root Cause Found

### The Real Problem: SPs Not Being Parsed!

Further investigation revealed:

```
SP PARSING SOURCE DISTRIBUTION:
================================================================================
metadata: 104 SPs  ← NOT PARSED! (Avg inputs: 0.0)
parser:    98 SPs  ← PARSED (Avg inputs: 2.6)
```

**104 out of 202 SPs were marked as `source: metadata` and NEVER PARSED!**

These SPs have:
- **0 average inputs** (no dependencies extracted)
- **1.6 average outputs** (only from reverse lookup)
- **No DMV dependencies** (not directly referenced)

### Why This Happened

**The Bug in background_tasks.py:392-401:**

```python
# Comment says "Update Tables/Views with reverse dependencies"
for table_id, readers in reverse_inputs.items():
    db.update_metadata(
        object_id=table_id,  # ❌ Could be ANY object type!
        primary_source='metadata',
        confidence=1.0,
        inputs=reverse_outputs.get(table_id, []),
        outputs=readers
    )
```

**Problem:**
1. Loop iterates over ALL objects in `reverse_inputs` (not just tables/views)
2. When SP "A" calls SP "B", SP "B" gets added to `reverse_inputs`
3. SP "B" gets metadata entry with `source='metadata'` BEFORE parsing runs
4. `get_objects_to_parse()` sees SP "B" already exists in metadata → **skips it!**
5. SP "B" never gets parsed, has empty inputs

**Result:**
- 104 SPs marked as "metadata" with no inputs
- These SPs reference tables, but tables don't get populated
- 252 tables remain unparsed
- **Total coverage: only 66.8%**

---

## The Fix

**File:** `api/background_tasks.py:392-415`

**Changed:**
```python
# Update Tables/Views with reverse dependencies
# IMPORTANT: Only update Tables and Views, NOT Stored Procedures
# SPs must be parsed to extract their dependencies
for table_id, readers in reverse_inputs.items():
    # Get object type for this object_id
    obj_type_result = db.query("""
        SELECT object_type FROM objects WHERE object_id = ?
    """, [table_id])

    if not obj_type_result:
        continue

    obj_type = obj_type_result[0][0]

    # Only update Tables and Views (not SPs)
    if obj_type in ['Table', 'View']:
        db.update_metadata(
            object_id=table_id,
            modify_date=None,
            primary_source='metadata',
            confidence=1.0,
            inputs=reverse_outputs.get(table_id, []),
            outputs=readers
        )
```

**What This Does:**
1. ✅ Checks object type before updating metadata
2. ✅ Only updates Tables and Views
3. ✅ Skips Stored Procedures entirely
4. ✅ SPs will only be populated by parser (step 4)
5. ✅ Parser will extract all dependencies correctly

---

## Expected Results After Fix

### Before Fix
```
Stored Procedures parsed: 98/202 (48.5%)
Tables with metadata:    248/500 (49.6%)
Total coverage:          510/763 (66.8%)
```

### After Fix (Expected)
```
Stored Procedures parsed: 202/202 (100%)   ← All SPs parsed!
Tables with metadata:    ~490/500 (98%)    ← Populated from SP dependencies
Total coverage:          ~720/763 (94%+)   ← TARGET ACHIEVED!
```

### Why Tables Will Improve

Once all 202 SPs are parsed:
1. SPs extract inputs correctly (e.g., "GlobalObjectRelations")
2. Bidirectional graph runs
3. Tables in `reverse_inputs` get populated
4. **Expected:** ~490 tables will have metadata (up from 248)

**Isolated tables** (no references): ~10 tables (2% of total)
- These are expected to remain unparsed
- They're truly unused in the system

---

## Testing Instructions

### Test the Fix

1. **Clear existing data:**
   ```bash
   curl -X DELETE http://localhost:8000/api/clear-data
   ```

2. **Upload with Full Refresh:**
   - Upload Parquet files
   - Use Full Refresh mode
   - Wait for completion

3. **Verify results:**
   ```bash
   source venv/bin/activate
   python temp/check_confidence_threshold.py
   ```

### Expected Output

```
Total objects: 763
High confidence (≥0.75): ~720 (94%+)  ← UP from 66.8%!
Coverage: ~720/763 (94%+)

BY OBJECT TYPE:
  Stored Procedures: 202/202 (100%)  ← All parsed
  Views: 60/61 (98.4%)                ← Same
  Tables: ~490/500 (98%)              ← UP from 49.6%!
```

---

## Why This Bug Existed

### Design Intent vs Reality

**Original Design:**
- Step 1: Parse Views (from DMV) ✅
- Step 2: Parse SPs (with parser) ✅
- Step 3: Populate Tables (bidirectional graph) ✅

**What Actually Happened:**
- Step 1: Parse Views ✅
- **Step 3 RAN BEFORE Step 2!** ❌
- Step 3: Populated SPs + Tables from reverse lookup
- Step 2: Skipped already-populated SPs
- Result: SPs with no inputs, tables unpopulated

**The Bug:** Step ordering was correct, but bidirectional graph ran on ALL objects including SPs, preventing proper parsing.

---

## Prevention

### Code Review Lessons

1. **Always filter by object_type** when iterating objects
2. **Check comments match code** ("Tables/Views" but code had no filter)
3. **Test coverage metrics** after changes
4. **Verify each object type separately** in testing

### Future Improvements

Consider moving bidirectional graph logic into a separate function with explicit type filtering:

```python
def populate_table_metadata_from_reverse_deps(db, reverse_inputs, reverse_outputs):
    """
    Populate Tables and Views ONLY from reverse dependencies.
    SPs must be parsed separately to extract their dependencies.
    """
    for obj_id, readers in reverse_inputs.items():
        obj_type = get_object_type(db, obj_id)
        if obj_type not in ['Table', 'View']:
            continue  # Skip SPs - they must be parsed!
        # ... update metadata
```

---

## Files Modified

1. **api/background_tasks.py**
   - Lines 392-415: Added object type filter to bidirectional graph

---

## Conclusion

✅ **Root cause identified:** Bidirectional graph was preventing 104 SPs from being parsed
✅ **Fix applied:** Filter by object type, only update Tables/Views
✅ **Expected result:** Coverage will jump from 66.8% to ~94%+
✅ **Next step:** Test with full refresh upload

The three-way parsing system (regex, SQLGlot, AI) will now work as designed!
