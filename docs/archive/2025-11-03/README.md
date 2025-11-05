# Archive: Confidence Metrics Fix (2025-11-03)

**Date:** November 3, 2025
**Version:** v4.0.3
**Status:** ✅ Completed

## Summary

This directory contains documentation from the confidence metrics fix implementation. The fix addressed inconsistent confidence calculations between the backend parser, evaluation framework, and frontend display.

## Files Archived

### CONFIDENCE_FIX_SUMMARY.md
Quick summary of the three critical bugs found and fixed:
1. Inconsistent calculations between backend and evaluation
2. Missing real-time stats during upload
3. Stale cache issues

### CONFIDENCE_FIX_CHECKLIST.md
Pre-deployment checklist and verification steps for the confidence metrics fix.

## What Was Fixed

### Bug #1: Inconsistent Calculations
- **Backend Parser:** Used match percentages (regex vs SQLGlot comparison)
- **Evaluation Testing:** Used F1 scores (precision × recall)
- **Fix:** Created unified `ConfidenceCalculator` class

### Bug #2: No Real-time Stats
- **Issue:** Backend status updates during upload didn't include confidence stats
- **Fix:** Added live stats calculation and transmission every 10 SPs

### Bug #3: Stale Cache
- **Issue:** Incremental parsing kept old metadata after new parquet upload
- **Fix:** Automatic cache cleanup with `clear_orphaned_metadata()`

## Impact

**Before:**
- ❌ Parser and evaluation had different confidence formulas
- ❌ Frontend showed stale/wrong stats during upload
- ❌ New uploads mixed old cached data
- ❌ 501/763 objects counted (65.7% - missing unreferenced tables)

**After:**
- ✅ Single unified confidence calculator
- ✅ Real-time accurate stats during upload
- ✅ Automatic cache cleanup
- ✅ 763/763 objects counted (100% - all tables included)
- ✅ Verified: 729/763 high confidence (95.5%)

## Related Changes

**Files Modified:**
- `lineage_v3/utils/confidence_calculator.py` (new)
- `api/background_tasks.py` (real-time stats)
- `lineage_v3/core/duckdb_workspace.py` (cache cleanup)
- `lineage_v3/parsers/quality_aware_parser.py` (unified calc)
- `evaluation/score_calculator.py` (unified calc)

## Current Status

✅ All fixes are in production (v4.0.3)
✅ Backward compatible (no migration needed)
✅ Metrics now consistent across all components
