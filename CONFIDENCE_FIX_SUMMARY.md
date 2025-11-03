# Confidence Metrics Fix - Summary

**Date:** 2025-11-03
**Status:** ✅ FIXED

---

## What Was Wrong?

You reported: *"we are using confidence calc differently in backend, testing and frontend. also metrics are cached so when i upload parquet file i get wrong numbers"*

You were **100% correct**. I found **THREE critical bugs**:

---

### Bug #1: Inconsistent Calculations ❌

**Backend Parser:**
- Used match percentages (regex vs SQLGlot comparison)
- Returned bucketed scores: 0.85 / 0.75 / 0.5

**Evaluation Testing:**
- Used F1 scores (precision × recall)
- Returned continuous scores: 0.0 - 1.0 (NOT bucketed!)

**Result:** Incompatible confidence scores → impossible to compare

---

### Bug #2: No Real-time Stats ❌

**Backend status updates** during upload did NOT include confidence stats.

**Frontend expected stats** but backend never sent them.

**Result:** Frontend showed old cached stats or empty stats during upload

---

### Bug #3: Stale Cache ❌

**Incremental parsing** kept old `lineage_metadata` when you uploaded new parquet.

Old objects stayed in cache even if not in new upload.

**Result:** Confidence stats mixed old + new data → **WRONG NUMBERS**

---

## What I Fixed ✅

### Fix #1: Unified Calculator

Created **single source of truth** for ALL confidence calculations:

**New file:** `/lineage_v3/utils/confidence_calculator.py`

**Updated:**
- ✅ Parser → uses unified calculator
- ✅ Evaluation → uses unified calculator
- ✅ Both return consistent bucketed scores (0.85/0.75/0.5)

---

### Fix #2: Real-time Stats

Backend now calculates and sends **live confidence stats** during upload:

**Updated:** `/api/background_tasks.py`

**Stats sent:**
- ✅ Every 10 SPs during parsing
- ✅ After loading DMV dependencies
- ✅ After building graph relationships

---

### Fix #3: Cache Invalidation

Automatic cleanup of orphaned metadata after loading new parquet:

**Updated:** `/lineage_v3/core/duckdb_workspace.py`

**New method:** `clear_orphaned_metadata()`

**Called automatically:**
- ✅ After web upload
- ✅ After CLI upload

---

## How to Verify ✅

### Run Automated Tests

```bash
cd /home/chris/sandbox
python3 test_confidence_fix.py
```

**Expected:**
```
✅ ALL TESTS PASSED!

The unified confidence calculator is working correctly.
All components now use consistent metric calculations.
```

### Manual Test

1. Upload a parquet file
2. Watch for **real-time stats** during processing
3. Verify **final stats match** DuckDB query
4. Re-upload → verify **no orphaned records**

---

## Files Changed

### New Files (3)
```
lineage_v3/utils/confidence_calculator.py  ← Unified calculator
test_confidence_fix.py                      ← Verification tests
docs/CONFIDENCE_METRICS_FIX.md              ← Full documentation
```

### Modified Files (4)
```
api/background_tasks.py                     ← Real-time stats
lineage_v3/core/duckdb_workspace.py        ← Cache cleanup
lineage_v3/parsers/quality_aware_parser.py  ← Uses unified calc
evaluation/score_calculator.py              ← Uses unified calc
```

---

## Impact

**Before:** ❌
- Parser and evaluation had different confidence formulas
- Frontend showed stale/wrong stats during upload
- New uploads mixed old cached data → wrong numbers

**After:** ✅
- Single unified confidence calculator
- Real-time accurate stats during upload
- Automatic cache cleanup → always fresh numbers

---

## Next Steps

### Ready to Use!

All fixes are **backward compatible** - no migration needed.

### What You'll Notice

✅ **Real-time stats** during parquet upload
✅ **Accurate confidence counts** after upload
✅ **No more stale cached numbers**
✅ **Consistent metrics** across all components

---

## Documentation

**Quick Start:** This file
**Full Details:** [docs/CONFIDENCE_METRICS_FIX.md](docs/CONFIDENCE_METRICS_FIX.md)
**API Reference:** [lineage_v3/utils/confidence_calculator.py](lineage_v3/utils/confidence_calculator.py)

---

**Fixed By:** Claude Code Agent
**Tested:** ✅ Verified
**Ready:** ✅ Production
