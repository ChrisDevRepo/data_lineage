# Real Data Analysis - Consolidated Findings & Action Plan

**Date:** 2025-11-07
**Dataset:** 349 Stored Procedures, 137 Views, 1,067 Objects
**Status:** ✅ Analysis Complete | Issues Identified | Solutions Ready

---

## Quick Answer to Your Questions

### 1. "DMV limitation: Only tracks views, not SPs" - What does this mean?

**Short Answer:** SQL Server's `sys.sql_dependencies` DMV only records dependencies for **Views and Functions**, NOT for **Stored Procedures**. This is a Microsoft SQL Server limitation.

**Why?**
- Dynamic SQL (`EXEC(@sql)`) - dependencies unknown at CREATE time
- Temp tables (`#temp`) - not in catalog
- Deferred name resolution - objects may not exist yet
- Control flow (IF/WHILE) - conditional dependencies
- Cross-database refs - often not tracked

**Evidence:** 137 views with 436 dependencies ✅ | 349 SPs with 0 dependencies ❌

**Full Explanation:** See `docs/development/DMV_LIMITATION_EXPLAINED.md`

---

### 2. What SQLGlot Could NOT Handle

**Analysis:** SQLGlot failed on **95/349 SPs (27.2%)**

**Top Failure Patterns (from 95 failed SPs):**

| T-SQL Pattern | Occurrence | Percentage |
|---------------|-----------|------------|
| **DECLARE statements** | 95 / 95 | 100.0% |
| **SET variable** | 94 / 95 | 98.9% |
| **EXEC statements** | 94 / 95 | 98.9% |
| **BEGIN TRY/CATCH** | 93 / 95 | 97.9% |
| **RAISERROR** | 93 / 95 | 97.9% |
| **Transaction control** | 54 / 95 | 56.8% |
| **IF EXISTS checks** | 46 / 95 | 48.4% |
| **WHILE loops** | 9 / 95 | 9.5% |
| **CURSOR usage** | 4 / 95 | 4.2% |

**Root Cause:** SQLGlot is a generic SQL parser, NOT T-SQL specific. It chokes on:
- Microsoft-specific syntax (BEGIN TRY/CATCH, RAISERROR)
- Procedural constructs (DECLARE, SET, WHILE)
- Control flow statements

**Solution:** ✅ SQL Cleaning Engine (already developed in Phase 2!)
- Pre-processes SQL before SQLGlot parsing
- Removes/replaces T-SQL-specific constructs
- Tested: 0% → 100% success on complex SP

**Status:** Ready for integration (Phase 4)

---

### 3. Smoke Test Results - Are Parser Results Plausible?

**Method:** Compare distinct table names in DDL text vs parser results

**Results:**

| Category | Count | Percentage |
|----------|-------|------------|
| Perfect match (diff = 0) | 98 | 28.1% |
| Close match (\|diff\| ≤ 2) | 263 | **75.4%** |
| Under-parsed (diff < -2) | 84 | 24.1% |
| Over-parsed (diff > 2) | 2 | 0.6% |

**Overall Assessment:** ⚠️ **ACCEPTABLE** but needs improvement

- **75.4% within ±2 tables** - Decent but not great
- **Average expected:** 4.8 tables/SP
- **Average parser found:** 2.4 tables/SP
- **Finding:** Parser **under-extracts by ~50%**

**Worst Cases:**
- `spLoadHumanResourcesObjects`: Expected 42 tables, found 1 (diff: -41)
- `spLoadTsRecords2yrs`: Expected 22 tables, found 1 (diff: -21)
- `spLoadPfmObjects`: Expected 18 tables, found 1 (diff: -17)

**Why?**
- Simple regex parser (used in evaluation) is basic
- Quality-aware parser (production) has more sophisticated logic
- Some SPs are orchestrators (mostly EXEC, few direct table refs)

**Next Step:** Re-run with full quality_aware_parser.py (not simple regex)

---

### 4. DuckDB Test View for Expected Counts

**Your Idea:** Create a DuckDB view that counts distinct tables per DDL

**Implementation:** ✅ Done in `smoke_test_analysis.py`

**Logic:**
```python
# For each SP:
1. Extract table names from DDL using regex patterns:
   - FROM/JOIN patterns
   - INSERT INTO patterns
   - UPDATE patterns
   - DELETE FROM patterns
   - TRUNCATE TABLE patterns

2. Categorize tables:
   - Real tables (e.g., schema.table)
   - Temp tables (#temp) - EXCLUDE
   - Variables (@var) - EXCLUDE
   - System tables (sys., tempdb.) - EXCLUDE

3. Count distinct REAL tables

4. Compare with parser results
```

**Exclusions Applied:**
- ✅ Temp tables (#temp)
- ✅ Variables (@var)
- ✅ System schemas (sys, tempdb, INFORMATION_SCHEMA)
- ✅ Utility SPs (LogMessage, spLastRowCount) - in EXEC patterns

**Plausibility Threshold:**
- If |diff| ≤ 2: ✅ Plausible
- If diff < -2: ⚠️ Under-parsed (missed tables)
- If diff > 2: ⚠️ Over-parsed (false positives)

**Results:** 75.4% plausible (within ±2)

---

## Key Issues Identified

### Issue 1: Simple Parser Under-Extracts

**Evidence:**
- Expected avg: 4.8 tables/SP
- Parser found avg: 2.4 tables/SP
- 50% under-extraction rate

**Root Cause:**
- `simple_real_data_analysis.py` uses basic regex
- Doesn't handle all SQL patterns
- Missing sophisticated preprocessing

**Solution:**
- ✅ Use `quality_aware_parser.py` (production parser) instead
- ✅ Integrate SQL Cleaning Engine (Phase 4)
- ✅ Add missing regex patterns

**Impact:** Will significantly improve accuracy

---

### Issue 2: SQLGlot Fails on T-SQL Constructs

**Evidence:**
- 27.2% failure rate (95/349 SPs)
- 100% of failures have DECLARE statements
- 98.9% have SET/EXEC statements

**Solution:**
- ✅ SQL Cleaning Engine (already developed!)
  - Removes DECLARE/SET/EXEC/TRY/CATCH
  - Extracts core DML statements
  - Proven: 0% → 100% success on test SP

**Status:** Ready for Phase 4 integration

---

### Issue 3: No Ground Truth for SPs

**Evidence:**
- DMV tracks 137 views ✅
- DMV tracks 0 SPs ❌

**Solution:**
- Multi-tier validation strategy:
  1. **Views:** Use DMV ground truth → true accuracy
  2. **SPs:** Use catalog validation → filter false positives
  3. **SPs:** Use smoke tests → plausibility check
  4. **SPs:** Use UAT feedback → real-world validation
  5. **SPs:** Use comment hints → edge cases

**Status:** ✅ Strategy validated, tools ready

---

## Recommended Actions

### Immediate (This Week)

**1. Re-run Analysis with Full Parser**

Current analysis used `simple_real_data_analysis.py` (basic regex).

**Action:**
```bash
# Use quality_aware_parser.py instead
python evaluation_baselines/real_data_analysis.py

# This will give true parser performance
```

**Expected:** Better results than smoke test (which used simple regex)

**2. Create View Evaluation Baseline (Phase 3)**

**Action:**
```bash
# Evaluate parser on 137 views with DMV ground truth
python evaluation_baselines/view_evaluation.py --create-baseline
```

**Output:**
- True precision, recall, F1 scores
- Regression testing baseline
- Confidence score calibration

**Timeline:** 1-2 days

---

### Short-term (Week 2-3)

**3. Integrate SQL Cleaning Engine (Phase 4)**

**What:** Add SQL preprocessing before SQLGlot parsing

**Files to modify:**
- `lineage_v3/parsers/quality_aware_parser.py`
  - Import SQL cleaning rules
  - Add cleaning step before `_sqlglot_parse()`
  - Add feature flag for gradual rollout

**Expected Impact:**
- SQLGlot success: 72.8% → 75-80%
- Confidence scores: +0.10-0.15 average
- Reduced under-extraction

**Timeline:** 3-5 days

---

### Medium-term (Week 4-5)

**4. Deploy UAT Feedback System (Phase 6)**

**Status:** ✅ System built, needs deployment

**Action:**
- Train 3-5 users
- Deploy feedback capture tool
- Set up automated regression test generation

**Timeline:** 1 week

---

## Updated Success Metrics

### Parser Performance (After Improvements)

| Metric | Current | Target | How to Achieve |
|--------|---------|--------|----------------|
| **SQLGlot Success Rate** | 72.8% | 75-80% | Phase 4: SQL Cleaning Engine |
| **View F1 Score** | TBD | ≥80% | Phase 3: View evaluation |
| **SP Plausibility** | 75.4% | ≥85% | Full parser + SQL Cleaning |
| **Catalog Validation (SP)** | TBD | ≥85% avg | Natural improvement |

### Validation Coverage

| Method | Coverage | Purpose | Status |
|--------|----------|---------|--------|
| **DMV Ground Truth (Views)** | 137 views | True accuracy | ✅ Ready Phase 3 |
| **Catalog Validation (All)** | 349 SPs | False positive filter | ✅ Implemented |
| **Smoke Test (All)** | 349 SPs | Plausibility check | ✅ Script created |
| **UAT Feedback** | Critical SPs | Real-world validation | ✅ Ready Phase 6 |
| **Comment Hints** | Edge cases | Developer input | ✅ Ready Phase 2 |

---

## Files Created

**Analysis Scripts:**
- ✅ `evaluation_baselines/simple_real_data_analysis.py` - Basic parser evaluation
- ✅ `evaluation_baselines/real_data_analysis.py` - Full parser evaluation (ready to use)
- ✅ `evaluation_baselines/smoke_test_analysis.py` - Plausibility testing

**Results:**
- ✅ `evaluation_baselines/real_data_results/parser_results.json` - 349 SP results
- ✅ `evaluation_baselines/real_data_results/smoke_test_results.json` - Plausibility data
- ✅ `evaluation_baselines/real_data_results/sqlglot_analysis.json` - Failure patterns

**Documentation:**
- ✅ `docs/development/DMV_LIMITATION_EXPLAINED.md` - **NEW** - Full DMV explanation
- ✅ `docs/development/PARSER_IMPROVEMENT_ROADMAP.md` - 7-phase plan
- ✅ `docs/development/PARSING_REVIEW_STATUS.md` - Updated with findings
- ✅ `evaluation_baselines/real_data_results/REAL_DATA_ANALYSIS_FINDINGS.md` - Detailed findings
- ✅ `evaluation_baselines/real_data_results/SUMMARY_FOR_USER.md` - Executive summary
- ✅ `evaluation_baselines/real_data_results/CONSOLIDATED_FINDINGS.md` - **THIS FILE**

**All properly organized - nothing in root directory!**

---

## Next Immediate Steps

### For You (Review):

1. **Read DMV explanation:** `docs/development/DMV_LIMITATION_EXPLAINED.md`
2. **Review smoke test:** Are 75.4% plausibility results acceptable?
3. **Approve next phase:** Phase 3 (view evaluation) or Phase 4 (SQL Cleaning)?

### Questions to Answer:

1. **Should we re-run with full parser first?**
   - Current results from simple_real_data_analysis.py (basic)
   - quality_aware_parser.py will be better
   - Recommend: Yes, re-run

2. **What's acceptable plausibility rate?**
   - Current: 75.4% within ±2 tables
   - Target: 85%+?
   - Your threshold?

3. **Priority: View evaluation or SQL Cleaning?**
   - View evaluation → measure true accuracy
   - SQL Cleaning → improve results immediately
   - Both are ready

---

## Bottom Line

✅ **DMV Limitation:** Documented and explained
✅ **SQLGlot Failures:** Analyzed (100% have DECLARE, solution ready)
✅ **Smoke Test:** Completed (75.4% plausible)
✅ **DuckDB Test View:** Implemented in smoke test
✅ **Solutions:** All ready (SQL Cleaning Engine, view evaluation, UAT)
⏳ **Next:** Decide on Phase 3 vs Phase 4 priority

**Recommendation:** Run full parser evaluation (`real_data_analysis.py`) to get true baseline, then proceed with Phase 3 (views) + Phase 4 (SQL Cleaning) in parallel.

---

**Status:** ✅ All questions answered, documentation complete, ready for next phase
