# Cache Mechanisms Audit

**Date:** 2025-11-03
**Purpose:** Document all caching and cache-clearing mechanisms to ensure proper cleanup

---

## Summary

✅ **All cache clearing mechanisms are now properly implemented**
- Full Refresh mode clears all necessary caches
- No redundant or missing cache clearing

---

## Cache Storage Locations

### 1. **DuckDB Workspace Database** (`data/lineage_workspace.duckdb`)
**What:** Persistent database containing all parsed lineage data
**Tables:**
- `objects` - Object metadata from Parquet
- `dependencies` - DMV dependencies from Parquet
- `definitions` - DDL definitions from Parquet
- `query_logs` - Query execution logs from Parquet (optional)
- `table_columns` - Table column metadata from Parquet (optional)
- `lineage_metadata` - **CACHE TABLE** - Parsed results with confidence scores

**WAL File:** `lineage_workspace.duckdb.wal` (created temporarily during writes)

### 2. **Frontend JSON File** (`data/latest_frontend_lineage.json`)
**What:** Cached frontend-formatted lineage data
**Purpose:** Serves `/api/latest-data` endpoint for persistence across restarts

### 3. **Job Directories** (`/tmp/jobs/{job_id}/`)
**What:** Temporary processing files for each upload job
**Contents:**
- `status.json` - Job progress
- `result.json` - Final results
- Uploaded Parquet files
- Generated lineage JSON files

**Lifetime:** Deleted after job completion (on `/api/result/{job_id}` call)

### 4. **HTTP Cache Headers** (API responses)
**What:** Browser cache control for API responses
**Where:** `api/main.py:599-601`
**Purpose:** Prevent browser from caching result data

---

## Cache Clearing Mechanisms

### 1. **Full Refresh Mode** (Upload with `incremental=False`)

**Location:** `api/background_tasks.py:220-238`

**What gets cleared:**
```python
tables_to_truncate = [
    'objects',
    'dependencies',
    'definitions',
    'query_logs',
    'table_columns',
    'lineage_metadata'  # ✅ FIXED - Was missing before
]
```

**Also clears:**
- `data/latest_frontend_lineage.json` (persistent frontend data)

**What DOES NOT get cleared:**
- DuckDB workspace file itself (reused with empty tables)
- WAL file (DuckDB manages automatically)

**Trigger:** User uploads Parquet files with "Incremental parsing" unchecked

---

### 2. **Incremental Mode** (Upload with `incremental=True`)

**Location:** `api/background_tasks.py:238`

**What gets cleared:** NOTHING
- All tables persist
- `lineage_metadata` cache is reused
- Only modified/new/low-confidence objects are re-parsed

**Logic:** `duckdb_workspace.py:376-444` (`get_objects_to_parse()`)

Objects are re-parsed if:
```sql
WHERE
    -- Object not in metadata (never parsed)
    m.object_id IS NULL
    -- OR object modified since last parse
    OR o.modify_date > m.last_parsed_modify_date
    -- OR confidence below threshold (default 0.85)
    OR m.confidence < {confidence_threshold}
```

---

### 3. **Clear All Data API** (`DELETE /api/clear-data`)

**Location:** `api/main.py:695-758`

**What gets cleared:**
1. ✅ DuckDB workspace file (`lineage_workspace.duckdb`)
2. ✅ DuckDB WAL file (`lineage_workspace.duckdb.wal`)
3. ✅ All job directories in `/tmp/jobs/`
4. ✅ Frontend JSON file (`latest_frontend_lineage.json`)
5. ✅ In-memory job tracking (`active_jobs` dict)

**Result:** Complete clean slate (equivalent to fresh install)

**Trigger:** User manually calls API or uses "Clear Data" button in GUI

---

### 4. **Job Cleanup** (Automatic after result retrieval)

**Location:** `api/main.py:609-618`

**What gets cleared:**
- Specific job directory in `/tmp/jobs/{job_id}/`
- In-memory tracking for that job

**Trigger:** Automatic after `/api/result/{job_id}` is called (frontend fetches results)

---

## DuckDB-Specific Behavior

### WAL (Write-Ahead Log) File
**File:** `lineage_workspace.duckdb.wal`

**When created:**
- Automatically by DuckDB during write operations
- Ensures ACID transactions

**When deleted:**
- Automatically by DuckDB when no longer needed (checkpoint)
- Manually by `/api/clear-data` endpoint

**Important:** Do NOT need to manually manage WAL file in normal operations

### Table Creation with `CREATE OR REPLACE`
**Location:** `duckdb_workspace.py:345-367`

**Behavior:**
- `CREATE OR REPLACE TABLE` automatically drops and recreates tables
- Used when loading Parquet files
- No need for explicit `DROP TABLE` before this

---

## Potential Issues (RESOLVED)

### ❌ **ISSUE 1: lineage_metadata Not Cleared in Full Refresh** → ✅ FIXED

**Problem:** Full Refresh mode was NOT clearing `lineage_metadata` table
- Comment said "lineage_metadata will be rebuilt"
- But table was not in `tables_to_truncate` list
- Result: Parse cache persisted, parser improvements not reflected

**Fix:** Added `lineage_metadata` to truncation list (`api/background_tasks.py:223`)

**Impact:**
- Before: Old parse results persist even in Full Refresh
- After: Fresh re-parsing on every Full Refresh

---

## Cache Clearing Decision Tree

```
User uploads Parquet files
    ├─ Incremental Mode (default)
    │   ├─ Load new data into existing tables
    │   ├─ Keep lineage_metadata cache
    │   ├─ Re-parse only: new, modified, or low-confidence objects
    │   └─ 50-90% faster for typical updates
    │
    └─ Full Refresh Mode
        ├─ DROP all tables (including lineage_metadata)
        ├─ Load fresh data
        ├─ Re-parse ALL objects
        ├─ Use when:
        │   ├─ Parser logic changed
        │   ├─ Confidence thresholds changed
        │   ├─ Testing parser improvements
        │   └─ Want guaranteed fresh results
        └─ Result: Complete re-parsing (slower but clean)
```

---

## Verification Commands

### Check Current Cache State
```bash
# DuckDB workspace
ls -lh data/lineage_workspace.duckdb*

# Frontend JSON
ls -lh data/latest_frontend_lineage.json

# Job directories
ls -la /tmp/jobs/

# Check lineage_metadata row count
python3 -c "
import duckdb
conn = duckdb.connect('data/lineage_workspace.duckdb')
result = conn.execute('SELECT COUNT(*) FROM lineage_metadata').fetchone()
print(f'Cached objects: {result[0]}')
conn.close()
"
```

### Clear All Caches
```bash
# Via API
curl -X DELETE http://localhost:8000/api/clear-data

# Manual (if API down)
rm -f data/lineage_workspace.duckdb*
rm -f data/latest_frontend_lineage.json
rm -rf /tmp/jobs/*
```

---

## Recommendations

### ✅ Current State: GOOD
All necessary cache clearing is implemented correctly:
1. ✅ Full Refresh clears all tables including `lineage_metadata`
2. ✅ Incremental mode properly reuses cache
3. ✅ Clear All Data endpoint clears everything
4. ✅ No redundant cache clearing

### Future Enhancements (Optional)

**1. Add Cache Statistics to GUI**
Show users:
- Last parse date
- Number of cached objects
- Cache size (MB)

**2. Add "Clear Cache Only" Option**
Allow users to clear just `lineage_metadata` without re-uploading Parquet files
- Useful for testing parser changes
- Faster than full data re-upload

**3. Add Cache Age Warning**
Warn user if cached data is older than uploaded Parquet files
- Detect timestamp mismatch
- Suggest Full Refresh

---

## Files Modified (2025-11-03)

1. **api/background_tasks.py:223** - Added `lineage_metadata` to truncation list
2. **frontend/components/ImportDataModal.tsx:743** - Fixed threshold label (≥0.85 → ≥0.75)

---

## Conclusion

✅ **All cache mechanisms are properly documented and implemented**
✅ **No additional cache clearing needed**
✅ **Full Refresh mode now correctly clears all caches**

The caching system is working as designed:
- **Incremental mode:** Fast, preserves cache
- **Full Refresh mode:** Slow, clears everything
- **Clear All Data:** Nuclear option, complete reset

No redundant or missing cache clearing mechanisms found.
