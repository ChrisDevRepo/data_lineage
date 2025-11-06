# SQLGlot Optimization - Coverage Investigation

**Status:** 66.8% coverage (should be 95%+)
**Last Updated:** 2025-11-03

---

## Current Situation

**Problem:** Coverage stuck at 66.8% (510/763 objects) despite fixes
- Expected: 95%+ with 3-way parsing (regex, SQLGlot, AI)
- Actual: Still 66.8% after bidirectional graph fix

**Breakdown:**
- Stored Procedures: 202/202 have metadata
- Views: 60/61 parsed (98.4%)
- Tables: 248/500 parsed (49.6%) ← **PROBLEM**

---

## Investigation Needed

### Today's Findings (2025-11-03)

1. ✅ **Fixed:** Bidirectional graph bug (prevented SP parsing)
2. ✅ **Fixed:** Cache not cleared in Full Refresh
3. ⚠️ **Result:** Coverage still 66.8% - **FIX DIDN'T WORK**

**Critical Question:** Why are we still at 66.8%?

Possible reasons:
- Bidirectional fix not applied correctly?
- Cache still persisting somehow?
- SPs still marked as 'metadata' instead of 'parser'?
- Different underlying issue?

---

## Quick Commands

### Check Current State
```bash
source venv/bin/activate
python temp/check_confidence_threshold.py
```

### Verify SP Sources
```bash
source venv/bin/activate
python3 -c "
from lineage_v3.core import DuckDBWorkspace
with DuckDBWorkspace('data/lineage_workspace.duckdb') as db:
    result = db.query('''
    SELECT primary_source, COUNT(*)
    FROM lineage_metadata lm
    JOIN objects o ON lm.object_id = o.object_id
    WHERE o.object_type = 'Stored Procedure'
    GROUP BY primary_source
    ''')
    for row in result:
        print(f'{row[0]}: {row[1]} SPs')
"
```

---

## Files in This Folder

- **README.md** - This file (current status)
- **ACTION_PLAN_2025_11_03.md** - Detailed investigation & action items
- **docs/LOW_COVERAGE_FIX.md** - Root cause analysis
- **docs/PHASE1_FINAL_RESULTS.md** - Historical preprocessing results
- **scripts/** - Testing utilities

---

## Next Steps

1. **Verify fix was applied:** Check `api/background_tasks.py:406-415`
2. **Test with fresh data:** Clear cache and re-upload
3. **Investigate why still 66.8%:** Check SP parsing sources
4. **Read ACTION_PLAN:** Full details in `ACTION_PLAN_2025_11_03.md`

---

**Last Upload:** Check GUI showed 478 high confidence (62.6% ≥0.75) - **REGRESSION!**
