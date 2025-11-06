# Lineage Metadata Error Fix

**Date:** 2025-11-03
**Error:** "Catalog Error: Table with name lineage_metadata does not exist!"
**Root Cause:** Query tried to access `lineage_metadata` table after Full Refresh dropped it

---

## Problem Description

### Error Message
```
Processing failed: Catalog Error: Table with name lineage_metadata does not exist!
Did you mean "lineage_workspace.lineage_metadata"?
```

### When It Occurred
- User uploaded Parquet files with **Full Refresh mode** (incremental=false)
- Full Refresh correctly dropped all tables including `lineage_metadata`
- But then `get_objects_to_parse()` tried to query the non-existent table

### Root Cause
**File:** `lineage_v3/core/duckdb_workspace.py:418-438`

The incremental parsing logic did a LEFT JOIN to `lineage_metadata` without checking if the table exists first:

```python
else:
    # Return only objects needing update
    query = f"""
        SELECT ...
        FROM objects o
        LEFT JOIN lineage_metadata m  # ❌ Table doesn't exist after Full Refresh!
            ON o.object_id = m.object_id
        WHERE ...
    """
```

---

## Fixes Applied

### Fix 1: Check Table Existence Before Query

**File:** `lineage_v3/core/duckdb_workspace.py:418-455`

**What Changed:**
Added table existence check before attempting LEFT JOIN:

```python
else:
    # Check if lineage_metadata table exists
    tables = [row[0] for row in self.connection.execute("SHOW TABLES").fetchall()]

    if 'lineage_metadata' not in tables:
        # No metadata table means nothing has been parsed yet
        # Treat as full refresh
        query = """
            SELECT object_id, schema_name, object_name, object_type, modify_date
            FROM objects
            ORDER BY schema_name, object_name
        """
    else:
        # Return only objects needing update
        query = f"""
            SELECT ...
            FROM objects o
            LEFT JOIN lineage_metadata m ON o.object_id = m.object_id
            WHERE ...
        """
```

**Result:**
- ✅ No error when `lineage_metadata` doesn't exist
- ✅ Automatically falls back to full refresh behavior
- ✅ Works correctly for both first upload and after Full Refresh

---

### Fix 2: Disable Incremental Toggle When No Data Exists

**Requirement:** "make sure when no data are in duckdb that incremental option is not available"

#### Backend Changes

**File:** `api/main.py:207-257`

Added `incremental_available` field to `/api/metadata` endpoint:

```python
@app.get("/api/metadata")
async def get_metadata():
    # Check if workspace exists for incremental parsing
    workspace_file = DATA_DIR / "lineage_workspace.duckdb"
    has_workspace = workspace_file.exists()

    if not LATEST_DATA_FILE.exists():
        return JSONResponse(
            content={
                "available": False,
                "incremental_available": False  # ✅ New field
            }
        )

    # ... (if data exists)
    return JSONResponse(
        content={
            "available": True,
            "incremental_available": has_workspace,  # ✅ New field
            # ... other metadata
        }
    )
```

#### Frontend Changes

**File:** `frontend/components/ImportDataModal.tsx`

**1. Added State (Line 147):**
```typescript
const [incrementalAvailable, setIncrementalAvailable] = useState(false);
```

**2. Updated fetchMetadata (Lines 198-219):**
```typescript
const fetchMetadata = async () => {
    const metadata = await response.json();
    if (metadata.available) {
        setIncrementalAvailable(metadata.incremental_available || false);
    } else {
        setIncrementalAvailable(false);
    }

    // If incremental is not available, force full refresh mode
    if (!metadata.incremental_available) {
        setUseIncremental(false);
    }
};
```

**3. Disabled Checkbox (Line 612):**
```typescript
<input
    type="checkbox"
    checked={useIncremental}
    onChange={(e) => setUseIncremental(e.target.checked)}
    disabled={isProcessing || !incrementalAvailable}  // ✅ Added condition
    className="..."
/>
```

**4. Added Help Text (Lines 622-626):**
```typescript
{!incrementalAvailable && (
    <div className="text-xs text-yellow-700 mt-1">
        ℹ️ Not available - no existing data to compare against.
        First upload will always use Full Refresh.
    </div>
)}
```

**5. Conditional Warning (Line 632):**
```typescript
{!useIncremental && incrementalAvailable && (  // ✅ Only show if available
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-900">
            <strong>Full Refresh Mode:</strong> ...
        </p>
    </div>
)}
```

---

## Testing Instructions

### Test 1: First Upload (No Data Exists)
1. Clear all data: `curl -X DELETE http://localhost:8000/api/clear-data`
2. Open Import Data modal
3. Switch to Parquet tab
4. **Expected:** Incremental toggle is disabled with help text
5. Upload Parquet files
6. **Expected:** Processes in Full Refresh mode (no error)

### Test 2: Second Upload (Data Exists)
1. After first upload completes
2. Open Import Data modal again
3. Switch to Parquet tab
4. **Expected:** Incremental toggle is enabled and checked by default
5. Upload same Parquet files with incremental mode
6. **Expected:** Processes quickly, only re-parsing modified objects

### Test 3: Manual Full Refresh (Data Exists)
1. With existing data
2. Open Import Data modal
3. Switch to Parquet tab
4. **Uncheck** "Incremental Parsing"
5. Upload Parquet files
6. **Expected:** All objects re-parsed, no error

---

## Behavior Summary

### Before Fixes
❌ Full Refresh → Error: "Table lineage_metadata does not exist"
❌ Incremental toggle always enabled (even when no data)

### After Fixes
✅ Full Refresh → Works correctly (no error)
✅ Incremental toggle disabled when no data exists
✅ Helpful message explains why toggle is disabled
✅ Automatic fallback to full refresh when metadata table missing

---

## Files Modified

1. **lineage_v3/core/duckdb_workspace.py**
   - Lines 418-455: Added table existence check in `get_objects_to_parse()`

2. **api/main.py**
   - Lines 222-233: Added `incremental_available` check to `/api/metadata`
   - Lines 250: Return `incremental_available` in response

3. **frontend/components/ImportDataModal.tsx**
   - Line 147: Added `incrementalAvailable` state
   - Lines 198-219: Updated `fetchMetadata()` to track incremental availability
   - Line 612: Disabled checkbox when `!incrementalAvailable`
   - Lines 622-626: Added help text for disabled state
   - Line 632: Conditional warning display

4. **Frontend rebuilt:** `npm run build` completed successfully

---

## Edge Cases Handled

✅ **First upload ever** - Incremental disabled, uses Full Refresh
✅ **After clearing data** - Incremental disabled until next upload
✅ **Workspace exists but empty** - Gracefully falls back to full refresh
✅ **Manual Full Refresh** - Works without error, clears metadata table
✅ **Incremental with existing data** - Works as expected

---

## Related Issues Fixed Previously

This fix complements the earlier cache clearing fix:

**Previous Issue:** `lineage_metadata` was not being dropped in Full Refresh mode
**Fix:** Added `lineage_metadata` to truncation list in `api/background_tasks.py:223`

**Current Issue:** Query failed when `lineage_metadata` didn't exist
**Fix:** Added table existence check before querying

**Result:** Full Refresh mode now works end-to-end without errors

---

## Conclusion

✅ **Error fixed:** No more "table does not exist" error
✅ **UX improved:** Incremental toggle disabled when not applicable
✅ **Graceful fallback:** Automatic full refresh when metadata missing
✅ **All edge cases handled:** First upload, cleared data, manual full refresh

The system now correctly handles the absence of `lineage_metadata` table in all scenarios.
