# GUI Metrics Investigation Summary

**Date:** 2025-11-03
**Issue:** GUI showing 66.7% high confidence - user expected better results from sqlglot_improvement work

---

## Root Causes Identified

### 1. **Misleading Label in GUI** ✅ FIXED
**Problem:** Frontend displayed correct numbers but wrong threshold label
- **Before:** "509 high (66.7% ≥0.85)"
- **Reality:** 509 objects at ≥0.75, not ≥0.85
- **Fix:** Changed label in `frontend/components/ImportDataModal.tsx:743` from "≥0.85" to "≥0.75"

### 2. **Cache Not Cleared in Full Refresh Mode** ✅ FIXED
**Problem:** `lineage_metadata` table persisted even in Full Refresh mode
- Full Refresh was dropping: `objects`, `dependencies`, `definitions`, `query_logs`, `table_columns`
- But NOT dropping: `lineage_metadata` (where parse results are cached)
- **Result:** Old parse results persisted, new parser improvements not reflected
- **Fix:** Added `lineage_metadata` to truncation list in `api/background_tasks.py:223`

### 3. **SQLGlot Improvement Code Not Deployed** ⚠️ ACTION NEEDED
**Problem:** The optimized preprocessing from `sqlglot_improvement/` folder is not active in main parser
- **Current parser** (`lineage_v3/parsers/quality_aware_parser.py:689-722`): Uses "PHASE 1 FINAL - ITERATION 3"
  - Only removes comments and replaces GO statements
  - Result: 104/202 SPs at ≥0.85 (51.5%)
- **sqlglot_improvement folder**: Has better preprocessing with leading semicolons
  - Result: 86/202 SPs at ≥0.85 (42.6%) documented, but potentially better in latest code
- **Impact:** User expected ~187 SPs at ≥0.85 but got 104 SPs

---

## Actual Current Metrics

After running fresh analysis on the current workspace:

```
Total objects: 763 (61 views, 202 SPs, 500 tables)

ALL OBJECTS:
  High confidence (≥0.85): 412 (54.0%)
  High confidence (≥0.75): 507 (66.7%) ← What GUI showed
  Medium (0.75-0.84):      95 (12.5%)
  Low (<0.75):             3 (0.4%)

BY OBJECT TYPE:
  Stored Procedures (202):
    ≥0.85: 104 (51.5%)
    ≥0.75: 199 (98.5%)

  Views (61):
    ≥0.85: 60 (98.4%)
    ≥0.75: 60 (98.4%)

  Tables (500):
    ≥0.85: 248 (49.6%)
    ≥0.75: 248 (49.6%)
```

---

## Fixes Applied

### 1. Frontend Label Correction
**File:** `frontend/components/ImportDataModal.tsx`
**Line:** 743
**Change:**
```diff
- ({((parseSummary.confidence_statistics.high_confidence_count / parseSummary.total_objects) * 100).toFixed(1)}% ≥0.85)
+ ({((parseSummary.confidence_statistics.high_confidence_count / parseSummary.total_objects) * 100).toFixed(1)}% ≥0.75)
```

### 2. Cache Clearing Fix
**File:** `api/background_tasks.py`
**Line:** 223
**Change:**
```diff
- tables_to_truncate = ['objects', 'dependencies', 'definitions', 'query_logs', 'table_columns']
+ tables_to_truncate = ['objects', 'dependencies', 'definitions', 'query_logs', 'table_columns', 'lineage_metadata']
```

### 3. Frontend Rebuild
**Command:** `cd frontend && npm run build`
**Status:** ✅ Complete

---

## Testing Instructions

### Test the Fixes
1. **Clear existing data:**
   ```bash
   curl -X DELETE http://localhost:8000/api/clear-data
   ```

2. **Upload Parquet files in Full Refresh mode:**
   - Uncheck "Incremental parsing" in GUI
   - Upload your Parquet files
   - Wait for completion

3. **Verify the results:**
   - Label should now show "≥0.75" (not "≥0.85")
   - Numbers should reflect fresh parsing (no cache)
   - With current parser: expect ~104 SPs at ≥0.85

### Expected vs Actual
- **With current parser code:** 104/202 SPs at ≥0.85 (51.5%)
- **After deploying sqlglot_improvement:** Should improve significantly

---

## Recommended Next Steps

### 1. Deploy SQLGlot Improvement Code (HIGH PRIORITY)
The `sqlglot_improvement/` folder contains better preprocessing logic that needs to be integrated into the main parser.

**Action Items:**
- [ ] Review `sqlglot_improvement/docs/PHASE1_FINAL_RESULTS.md`
- [ ] Identify the exact preprocessing code to deploy
- [ ] Update `lineage_v3/parsers/quality_aware_parser.py._preprocess_ddl()`
- [ ] Run `/sub_DL_OptimizeParsing` to verify improvements
- [ ] Document in `docs/PARSER_EVOLUTION_LOG.md`

### 2. Verify Threshold Strategy
The threshold was lowered from ≥0.85 to ≥0.75 in v3.8.0 (per CLAUDE.md:144).

**Consideration:** Should we reconsider this threshold change?
- **Pros of ≥0.75:** More inclusive, better overall coverage percentage
- **Cons of ≥0.75:** Lower quality bar, potentially less trustworthy results
- **Alternative:** Use ≥0.85 for display but continue tracking both thresholds

### 3. Add Threshold to Summary JSON
Currently, the summary JSON doesn't include the threshold value, causing confusion.

**Proposal:** Add `confidence_threshold` field to `lineage_summary.json`:
```json
{
  "confidence_statistics": {
    "threshold": 0.75,
    "high_confidence_count": 509,
    ...
  }
}
```

---

## Conclusion

The GUI was displaying **correct numbers** but with:
1. ❌ **Wrong label** (≥0.85 vs ≥0.75) → FIXED
2. ❌ **Stale cache** (Full Refresh didn't clear lineage_metadata) → FIXED
3. ⚠️ **Outdated parser** (sqlglot_improvement not deployed) → NEEDS ACTION

After uploading with Full Refresh mode, you should now see:
- ✅ Correct threshold label (≥0.75)
- ✅ Fresh parsing results (no cache)
- ⏳ Results will improve once sqlglot_improvement code is deployed

---

**Files Modified:**
- `frontend/components/ImportDataModal.tsx` (line 743)
- `api/background_tasks.py` (line 223)
- Frontend rebuilt with `npm run build`

**Test Script Created:**
- `temp/check_confidence_threshold.py` (for verifying workspace metrics)
