# Action Plan - Path to 95%+ Coverage
## Data Lineage Parser Optimization

**Date:** 2025-11-03
**Current Status:** 66.8% coverage (510/763 objects)
**Target:** 95%+ coverage (~720/763 objects)
**Timeline:** 3-4 hours of focused work

---

## Executive Summary

Today's investigation revealed **THREE CRITICAL ISSUES** preventing high coverage:

1. ✅ **FIXED:** Cache not cleared in Full Refresh mode
2. ✅ **FIXED:** Bidirectional graph preventing SP parsing (104 SPs affected)
3. ⚠️ **NOT DEPLOYED:** Optimized preprocessing from this folder

**Impact:** After deploying fixes + optimized preprocessing, expect **95%+ coverage**.

---

## Current State Analysis

### Coverage Breakdown (Before Fixes)
```
Stored Procedures: 202/202 metadata entries
  - 98 actually PARSED (source: parser)
  - 104 NOT PARSED (source: metadata, 0 inputs)
Views:             60/61 (98.4%)
Tables:           248/500 (49.6%)
TOTAL:            510/763 (66.8%)
```

### Root Causes Identified

#### Issue #1: Bidirectional Graph Bug ✅ FIXED
**File:** `api/background_tasks.py:392-415`
**Problem:** SPs were populated by reverse lookup BEFORE parsing could run
**Fix Applied:** Added object type filter - only Tables/Views get reverse lookup
**Impact:** All 202 SPs will now be parsed properly
**Expected Gain:** +104 SPs with dependencies → +~240 tables populated → **+~210 objects coverage**

#### Issue #2: Cache Not Cleared ✅ FIXED
**File:** `api/background_tasks.py:231-233`
**Problem:** `lineage_metadata` table not dropped in Full Refresh
**Fix Applied:** Added `lineage_metadata` to truncation list + recreate schema
**Impact:** Full Refresh now truly fresh

#### Issue #3: Optimal Preprocessing Not Deployed ⚠️ ACTION NEEDED
**Location:** `quality_aware_parser.py:689-722`
**Current:** Basic comment removal (PHASE 1 ITERATION 3)
**Available:** Better preprocessing in this folder
**Impact:** Would improve from current 51.5% SP confidence (≥0.85) to ~92%

---

## Action Items

### PRIORITY 1: Test Current Fixes (15 minutes)

**Goal:** Verify bidirectional graph fix works

**Steps:**
1. Clear all data:
   ```bash
   curl -X DELETE http://localhost:8000/api/clear-data
   ```

2. Upload Parquet files with Full Refresh mode

3. Check results:
   ```bash
   source venv/bin/activate
   python temp/check_confidence_threshold.py
   ```

**Expected Results:**
```
Stored Procedures: 202/202 parsed (source: parser)
  - Avg inputs: 2.5+ (not 0!)
  - High confidence (≥0.85): ~104 SPs (51.5%)
  - High confidence (≥0.75): ~199 SPs (98.5%)

Tables: ~490/500 (98%)
  - Up from 248 (49.6%)

TOTAL COVERAGE: ~720/763 (94%+)
  - Up from 510 (66.8%)
```

**If this doesn't work:** Investigate why SPs still have source=metadata

---

### PRIORITY 2: Deploy Optimized Preprocessing (30 minutes)

**Goal:** Improve SP parsing quality from 51.5% to ~92% (≥0.85)

#### Step 1: Review Available Preprocessing Options

**Location:** Check `docs/PHASE1_FINAL_RESULTS.md` for best approach

**Options Documented:**
- **Plan A:** Statement removal (78 SPs, 38.6%)
- **Your Approach:** Leading semicolons (86 SPs, 42.6%)
- **PHASE 1 ITERATION 3:** Comment removal (current - 160 SPs, 79.2%?)

**Question:** Which preprocessing is actually best?

**Action:** Read `docs/PHASE1_FINAL_RESULTS.md` carefully to determine optimal approach

#### Step 2: Identify Best Preprocessing Code

**Candidates:**
1. Leading semicolons approach (documented in PHASE1_FINAL_RESULTS.md)
2. Comment removal (currently deployed)
3. Hybrid approach (TBD)

**Find the code:**
```bash
# Check if there's a backup of better preprocessing
ls -la lineage_v3/parsers/*.BACKUP*
grep -n "leading.*semicolon" lineage_v3/parsers/quality_aware_parser.py
```

#### Step 3: Deploy Best Preprocessing

**File to modify:** `lineage_v3/parsers/quality_aware_parser.py:689-722`

**Current code:**
```python
def _preprocess_ddl(self, ddl: str) -> str:
    """
    PHASE 1 FINAL - ITERATION 3: GO + COMMENT REMOVAL
    Result: 160/202 SPs (79.2%) high confidence
    """
    cleaned = ddl
    cleaned = re.sub(r'--[^\n]*', '', cleaned)  # Remove single-line comments
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)  # Remove multi-line
    cleaned = re.sub(r'\bGO\b', ';', cleaned, flags=re.IGNORECASE)  # Replace GO
    return cleaned
```

**Replace with:** (TBD after reviewing docs)

#### Step 4: Test Preprocessing Change

**Use the evaluation framework:**
```bash
# Create baseline BEFORE changes
cd /home/chris/sandbox
/sub_DL_OptimizeParsing init --name baseline_before_preprocessing_update

# Run baseline
/sub_DL_OptimizeParsing run --mode full --baseline baseline_before_preprocessing_update

# Make preprocessing changes to quality_aware_parser.py

# Run evaluation AFTER changes
/sub_DL_OptimizeParsing run --mode full --baseline baseline_before_preprocessing_update

# Compare results
/sub_DL_OptimizeParsing compare --run1 run_YYYYMMDD_HHMMSS --run2 run_YYYYMMDD_HHMMSS
```

**Success Criteria:**
- Zero regressions (no objects ≥0.85 drop below 0.85)
- SP high confidence (≥0.85) increases to ~187/202 (92.6%)

---

### PRIORITY 3: Investigate AI Usage (20 minutes)

**Goal:** Understand if AI fallback is working

**Current Status Unknown:**
- Is AI enabled?
- Is AI being called for low-confidence SPs?
- What are AI results?

**Actions:**

1. **Check AI Configuration:**
   ```bash
   grep -r "AZURE_OPENAI" .env
   curl http://localhost:8000/health | jq '.ai_enabled'
   ```

2. **Check AI Usage in Code:**
   ```bash
   grep -n "ai_disambiguator\|AIDisambiguator" lineage_v3/parsers/quality_aware_parser.py
   ```

3. **Check if AI is called:**
   Look for AI usage in parse flow - are low-confidence SPs sent to AI?

4. **Review AI Spec:**
   ```bash
   cat docs/AI_DISAMBIGUATION_SPEC.md | grep -A 10 "When to Use"
   ```

**Expected Finding:**
- AI is either:
  - Not configured (missing credentials)
  - Not integrated into parse flow
  - Not working properly

**If AI not working:** Document as PRIORITY 4 action item

---

### PRIORITY 4: Document Preprocessing Decision (15 minutes)

**Goal:** Create clear record of which preprocessing is best and why

**Actions:**

1. **Compare All Approaches:**
   Create comparison table:
   ```
   | Approach | SPs (≥0.85) | % | Complexity | Deployed |
   |----------|-------------|---|------------|----------|
   | Baseline | 46 | 22.8% | None | No |
   | Plan A | 78 | 38.6% | Low | No |
   | Leading ; | 86 | 42.6% | Very Low | No |
   | Iteration 3 | 160 | 79.2% | Low | YES (current) |
   ```

2. **Determine if current is actually best:**
   - Reread PHASE1_FINAL_RESULTS.md
   - Check if "160 SPs" claim is validated
   - Compare with actual results (104 SPs currently)

3. **Document conclusion:**
   Update `README.md` in this folder with decision

---

### PRIORITY 5: Clean Up Documentation (15 minutes)

**Goal:** Make this folder the single source of truth for optimization work

**Actions:**

1. **Move today's findings here:**
   ```bash
   mv /home/chris/sandbox/LOW_COVERAGE_FIX.md sqlglot_improvement/docs/
   ```

2. **Update README.md with current status:**
   - Add "Current Status (2025-11-03)" section
   - Reference LOW_COVERAGE_FIX.md
   - Update expected results

3. **Archive old docs:**
   ```bash
   # These are already archived in docs/archive/2025-11-02/
   # Just ensure sqlglot_improvement docs are current
   ```

4. **Create INDEX.md:**
   ```bash
   # Document reading order:
   # 1. ACTION_PLAN_2025_11_03.md (this file)
   # 2. README.md (updated with current status)
   # 3. docs/LOW_COVERAGE_FIX.md (today's findings)
   # 4. docs/PHASE1_FINAL_RESULTS.md (preprocessing options)
   # 5. MASTER_PLAN.md (original strategy)
   ```

---

## Key Questions to Answer

### Question 1: Why the discrepancy?
**Documented:** 160/202 SPs (79.2%) with Iteration 3 preprocessing
**Actual:** 104/202 SPs (51.5%) before today's fix

**Possible Reasons:**
- A) Documented results used different evaluation method
- B) Code was changed after documentation was written
- C) Preprocessing was partially reverted
- D) Bidirectional graph bug was hiding the problem

**Action:** Investigate by comparing quality_aware_parser.py with backup files

### Question 2: What preprocessing is currently deployed?
**Answer:** Found in quality_aware_parser.py:689-722
- Comment removal
- GO replacement
- Marked as "PHASE 1 FINAL - ITERATION 3"

### Question 3: Is there better preprocessing available?
**Answer:** Check docs/PHASE1_FINAL_RESULTS.md and compare approaches

### Question 4: Why aren't we at 95% yet?
**Answer (after today's fixes):**
- Bidirectional graph fix: Should get to ~94%
- Remaining 6%: Truly isolated tables (expected)
- If still low: Preprocessing needs improvement OR AI needs deployment

---

## Success Metrics

### After PRIORITY 1 (Bidirectional Fix Test)
```
✅ All 202 SPs have source='parser' (not 'metadata')
✅ SPs have avg inputs > 2.0 (not 0)
✅ Tables parsed: ~490/500 (up from 248)
✅ Total coverage: ~720/763 (94%+)
```

### After PRIORITY 2 (Preprocessing Deployment)
```
✅ SP confidence (≥0.85): ~187/202 (92.6%)
✅ SP confidence (≥0.75): ~201/202 (99.5%)
✅ Zero regressions from previous baseline
```

### After PRIORITY 3 (AI Investigation)
```
✅ AI status known (enabled/disabled)
✅ AI integration understood
✅ Plan for AI improvement documented (if needed)
```

### Final Target
```
✅ Total coverage: 95%+ (720+/763)
✅ SP parsing: 99%+ high confidence
✅ Table population: 98%+ (490+/500)
✅ Isolated tables identified: ~10-20 (expected)
```

---

## Timeline Estimate

| Priority | Task | Time | Cumulative |
|----------|------|------|------------|
| 1 | Test bidirectional fix | 15 min | 0:15 |
| 2 | Deploy preprocessing | 30 min | 0:45 |
| 3 | Investigate AI | 20 min | 1:05 |
| 4 | Document decision | 15 min | 1:20 |
| 5 | Clean up docs | 15 min | 1:35 |
| **Total** | | **1:35** | |

**Add 30-60 min buffer for unexpected issues = 2-3 hours total**

---

## Files to Modify

### Code Changes
1. ✅ `api/background_tasks.py` (already fixed)
2. ⚠️ `lineage_v3/parsers/quality_aware_parser.py` (preprocessing - TBD)

### Documentation Updates
1. `sqlglot_improvement/README.md` (current status)
2. `sqlglot_improvement/ACTION_PLAN_2025_11_03.md` (this file)
3. `sqlglot_improvement/docs/LOW_COVERAGE_FIX.md` (move from root)
4. `docs/PARSER_EVOLUTION_LOG.md` (record changes)

---

## Critical Decisions Needed

### Decision 1: Which preprocessing to deploy?
**Options:**
- A) Keep current (Iteration 3: comment removal)
- B) Deploy leading semicolons (86 SPs documented)
- C) Test hybrid approach
- D) Do nothing, focus on AI

**Recommendation:** Review PHASE1_FINAL_RESULTS.md first, then decide

**Decision Maker:** You
**Deadline:** After PRIORITY 1 test results

### Decision 2: Should we enable AI?
**Depends on:**
- Current results after bidirectional fix
- Preprocessing improvement results
- Whether we're already at 95% without AI

**Recommendation:** Decide after seeing PRIORITY 1 + 2 results

**Decision Maker:** You
**Deadline:** After PRIORITY 2 complete

---

## Rollback Plan

If changes cause regressions:

1. **Rollback preprocessing:**
   ```bash
   git diff lineage_v3/parsers/quality_aware_parser.py
   git checkout lineage_v3/parsers/quality_aware_parser.py
   ```

2. **Rollback bidirectional fix:**
   ```bash
   git diff api/background_tasks.py
   # Manually revert lines 406-415
   ```

3. **Clear data and re-upload:**
   ```bash
   curl -X DELETE http://localhost:8000/api/clear-data
   # Upload again
   ```

---

## Next Steps After Completion

1. **Update CLAUDE.md** with new baseline metrics
2. **Update Parser Evolution Log** with deployment details
3. **Archive this action plan** to docs/archive/
4. **Create new baseline** for future improvements
5. **Consider Phase 2** (AI integration) if not at 95%

---

## Contact Points

**If stuck:**
- Review LOW_COVERAGE_FIX.md for bidirectional bug details
- Review PHASE1_FINAL_RESULTS.md for preprocessing options
- Review AI_DISAMBIGUATION_SPEC.md for AI integration
- Run `/sub_DL_OptimizeParsing` for systematic evaluation

**Don't:**
- ❌ Make changes without baseline evaluation
- ❌ Skip testing after code changes
- ❌ Deploy multiple changes at once (can't isolate impact)
- ❌ Assume documentation is accurate without validation

---

## Status Tracking

**Last Updated:** 2025-11-03
**Status:** READY TO EXECUTE
**Next Action:** Run PRIORITY 1 test

**Update this section after each priority completes:**

- [ ] PRIORITY 1: Bidirectional fix test
- [ ] PRIORITY 2: Preprocessing deployment
- [ ] PRIORITY 3: AI investigation
- [ ] PRIORITY 4: Document decision
- [ ] PRIORITY 5: Clean up docs
- [ ] Final validation: 95%+ coverage achieved
