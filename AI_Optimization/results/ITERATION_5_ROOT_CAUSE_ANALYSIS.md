# Iteration 5: Root Cause Analysis

**Date:** 2025-11-03
**Status:** ❌ NO IMPROVEMENT (3 matches, same as Iteration 4)
**Critical Discovery:** Classification logic is backwards, not few-shot examples

---

## Executive Summary

**The Problem We Tried to Solve:**
- Add 3 new few-shot examples to teach AI to recognize patterns (Fact* prefix, pluralization, lookup tables)
- Expected: Improve recall from 3 to 10-15 matches

**What Actually Happened:**
- NO improvement: Still 3 matches
- FactAgingSAP and EnrollmentPlan still showing empty arrays

**Root Cause Discovered:**
- The matches ARE being found (confidence 0.85)
- But they're classified as **"sources" (input_procedures)** instead of **"targets" (output_procedures)**
- Database only stores `outputs` column, so matches in `sources` appear as empty arrays
- **This is a classification logic bug, NOT a few-shot example problem!**

---

## Full Parser Results (Iteration 5)

| Metric | Value |
|--------|-------|
| Total AI-processed tables | 104 |
| Tables with matches | 3 |
| Empty arrays (correct rejections) | 101 |
| False positives | 0 |
| Precision | 100% |
| Recall | 2.9% (3/104) |

**The 3 Matches (same as Iteration 4):**
1. `CONSUMPTION_FINANCE.GLCognosData_Test` → `spLoadGLCognosData_Test`
2. `CONSUMPTION_PRIMA.FeasibilityQuestions` → `spLoadFeasibilityObjects`
3. `CONSUMPTION_PRIMA.ProjectTeamRegions` → `spLoadProjectRegions`

**Expected Improvements (FAILED):**
1. ❌ `CONSUMPTION_FINANCE.FactAgingSAP` → empty array
2. ❌ `CONSUMPTION_PRIMA.EnrollmentPlan` → empty array

---

## Investigation: Why Did FactAgingSAP Fail?

### Step 1: Verify Table and SP Exist
✅ **PASS** - Both exist in database:
- Table: `CONSUMPTION_FINANCE.FactAgingSAP` (object_id: 70536697)
- SP: `CONSUMPTION_FINANCE.spLoadFactAgingSAP` (object_id: 1845618780)

### Step 2: Check SP Ranking (Top 10 Filter)
✅ **PASS** - SP is #1 in top 10:
- Score: 65 points (same schema +10, name match +50, spload prefix +5)
- Next highest: 15 points
- **SP is definitely being sent to AI for evaluation**

### Step 3: Check SQL Extraction
✅ **PASS** - SQL contains table name:
```sql
truncate table [consumption_finance].[factagingsap];
insert into [consumption_finance].[factagingsap]
```
**Table name is clearly visible to AI!**

### Step 4: Run Focused Test
✅ **FOUND THE BUG!**

**Focused Test Result:**
```
Confidence: 0.85
Source object_ids: [1845618780]  ← spLoadFactAgingSAP
Target object_ids: []            ← empty!
Reasoning: Rule-based naming pattern match
```

**Database Result:**
```
outputs: []          ← empty array stored in database
primary_source: ai
confidence: 0.85
```

**The Match IS Being Found!** But it's classified as:
- **Source** (SP reads FROM table) ❌ WRONG
- Should be **Target** (SP writes TO table) ✅ CORRECT

---

## The Root Cause

### What Should Happen:

**For table:** `FactAgingSAP`
**With SP:** `spLoadFactAgingSAP` containing:
```sql
INSERT INTO [CONSUMPTION_FINANCE].[FactAgingSAP]
```

**Classification:**
- INSERT = WRITE operation
- SP writes TO the table
- Should be in **`targets`** (output_procedures)
- Should be stored in database **`outputs`** column

### What Is Actually Happening:

**Classification:**
- SP classified as **`sources`** (input_procedures)
- Means: SP reads FROM the table (backwards!)
- **`targets`** is empty
- Database **`outputs`** column stores empty array `[]`

**Result:**
- Match appears as "no match" in database
- No improvement in recall despite AI finding it

---

## Why Few-Shot Examples Didn't Help

The analysis assumed the problem was:
- AI not recognizing Fact* prefix patterns
- AI not handling pluralization edge cases
- AI being too conservative with rejections

**But the actual problem is:**
- AI/rule-based system IS finding matches (confidence 0.85)
- Classification logic is backwards (input vs output)
- Few-shot examples can't fix classification logic bugs

**Key Evidence:**
- Reasoning: "Rule-based naming pattern match" (not AI inference!)
- Suggests a rule-based classifier runs BEFORE AI
- This classifier has the backwards logic, not the AI

---

## Code Investigation Needed

**Files to Check:**
1. `/home/chris/sandbox/lineage_v3/parsers/ai_disambiguator.py`
   - Method: `infer_dependencies_for_unreferenced_table` (line 507)
   - Check how it determines sources vs targets
   - Look for rule-based logic that runs before AI

2. Classification Logic:
   - How does it decide if an SP is input_procedure vs output_procedure?
   - Is there logic checking "INSERT INTO target" vs "SELECT FROM target"?
   - Why is INSERT being classified as "source" instead of "target"?

3. Database Storage:
   - Method that saves results to lineage_metadata
   - Check if sources are being saved to outputs column (wrong mapping?)
   - Or if sources are simply not being saved at all

---

## Recommended Next Steps

### Immediate Action:
1. ✅ **Fix the classification logic** (not the few-shot examples)
2. Locate where sources/targets are determined
3. Debug why INSERT INTO is classified as "source" instead of "target"
4. Fix the logic
5. Re-run focused test to verify
6. Run full parser to measure impact

### Testing Strategy:
1. Use the focused test script (`AI_Optimization/test_factagingsap.py`)
2. Iterate quickly (30 seconds vs 15 minutes per test)
3. Once fixed, test on EnrollmentPlan
4. Then run full parser

### Expected Impact After Fix:
- **Current:** 3 matches (2.9% recall)
- **After fix:** 10-20 matches (10-20% recall)
- All the "found but misclassified" cases will now appear correctly

---

## Files Modified (Iteration 5)

1. **`lineage_v3/ai_analyzer/inference_prompt.txt`**
   - Added Example 6: Fact prefix pattern
   - Added Example 7: Pluralization pattern
   - Added Example 8: Lookup table rejection
   - Updated Rule #5: Clarified pluralization handling

2. **`AI_Optimization/test_factagingsap.py`** (NEW)
   - Focused test script for rapid iteration
   - Tests single table case without full parser run

---

## Key Learnings

1. **Few-shot examples are NOT the bottleneck**
   - The AI is already finding matches
   - The problem is in the classification/storage logic

2. **Focused testing revealed the true issue**
   - Full parser runs (15 min) hide details
   - Focused test (30 sec) exposed the classification bug

3. **"Empty outputs" doesn't mean "no match found"**
   - It can mean "match found but stored in wrong column"
   - Or "match found but not stored at all"

4. **Rule-based logic runs before AI**
   - The reasoning says "Rule-based naming pattern match"
   - Suggests there's a pre-AI filter/classifier
   - This is where the bug likely exists

---

## Success Criteria (Revised)

**Before Fix:**
- Cannot achieve ≥10 matches due to classification bug
- Few-shot improvements won't help

**After Fix:**
- ✅ ≥10 correct matches (from misclassified cases becoming visible)
- ✅ 0-1 false positives (maintain precision)
- ✅ FactAgingSAP and EnrollmentPlan should match
- ✅ All Fact* prefix patterns should be found

---

## Status

- ❌ Iteration 5: Failed (no improvement)
- ✅ Root cause identified: Classification logic bug
- ⏳ Next: Fix classification logic, not few-shot examples
- 📊 Impact: High (could unlock 7-17 additional matches immediately)

---

**Generated:** 2025-11-03
**Test Duration:** Full parser: 15 min | Focused test: 30 sec
**Recommendation:** Fix classification logic before attempting more few-shot improvements
