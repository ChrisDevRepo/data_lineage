# Iteration 4: Root Cause Analysis - False Positives

**Date:** 2025-11-03
**Status:** Root cause identified - Code bug causing false positives
**Working Directory:** `/home/chris/sandbox/sqlglot_improvement/`

---

## Executive Summary

**CRITICAL BUG FOUND in `ai_disambiguator.py`:**

The AI is being asked to select from 50 SPs, but only receives SQL code for 10 SPs. For the other 40 SPs, AI has NO SQL CODE and is guessing based on names, causing 87.5% false positive rate.

---

## The Problem

**Validation Results (Iteration 3):**
- 8 tables received AI matches
- 7 matches are FALSE POSITIVES (87.5%)
- Only 1 match is correct (12.5%)

**Example False Positive:**
- Table: `ADMIN.Logs`
- AI matched to: 4 SPs (`sp_SetUpControlsHistoricalSnapshotRun`, `sp_GetRunningHistoricalSnapshotRun`, etc.)
- Reality: NONE of those SPs reference `Logs` in their SQL code

---

## Root Cause: Mismatch Between SQL Snippets and Enum List

**File:** `lineage_v3/parsers/ai_disambiguator.py`

### The Bug

```python
def _infer_with_ai(self, table_schema, table_name, all_sp_data):
    # Line 582: Filter to 50 most relevant SPs
    relevant_sps = self._filter_relevant_sps(table_schema, table_name, all_sp_data)[:50]

    # Line 586: Build enum list from ALL 50 SPs
    sp_enum_list = [f"{sp['schema']}.{sp['name']}" for sp in relevant_sps]

    # Line 589: Build prompt (which calls _build_inference_prompt)
    prompt = self._build_inference_prompt(table_schema, table_name, relevant_sps)
```

```python
def _build_inference_prompt(self, table_schema, table_name, all_sp_data):
    relevant_sps = self._filter_relevant_sps(table_schema, table_name, all_sp_data)

    sp_catalog_parts = []
    # Line 731: Only include SQL for first 10 SPs ❌
    for sp in relevant_sps[:10]:
        sp_info = f"- {sp['schema']}.{sp['name']}"

        ddl = sp.get('definition') or sp.get('ddl')
        if ddl:
            sql_snippet = self._extract_sql_logic(ddl, max_lines=10)
            sp_info += f"\n  {sql_snippet}"

        sp_catalog_parts.append(sp_info)
```

### What Happens

1. **AI receives:** SQL code for 10 SPs
2. **Enum constraint allows:** Selection from 50 SPs
3. **For 40 SPs:** AI has SP name only, NO SQL CODE
4. **Result:** AI guesses based on name similarity, causing false positives

### Example Scenario

**Target Table:** `ADMIN.Logs`

**AI receives SQL for:**
1. `ADMIN.sp_SetUpPipelineRun` (with SQL)
2. `ADMIN.sp_LoadControlData` (with SQL)
3. ... (8 more SPs with SQL)

**Enum allows selection from:**
1-10. (SPs with SQL) ✅
11. `ADMIN.sp_SetUpControlsHistoricalSnapshotRun` (NO SQL) ❌
12. `ADMIN.sp_GetRunningHistoricalSnapshotRun` (NO SQL) ❌
13. ... (38 more SPs without SQL) ❌

**AI Logic:**
- "I see a table called `Logs`"
- "I see SPs with names like `sp_SetUpControls...`, `sp_GetRunning...`"
- "These sound like they might use a Logs table for tracking"
- **Returns these SPs even though SQL code is not provided**

---

## Validation Confirms the Bug

### Test 1: False Positive Verification

Checked if `ADMIN.Logs` is referenced in matched SPs:

```
✅ Checked 4 matched SPs:
   ❌ sp_SetUpControlsHistoricalSnapshotRun: NO reference to Logs
   ❌ sp_GetRunningHistoricalSnapshotRun: NO reference to Logs
   ❌ sp_GetReadyHistoricalSnapshotRunDetail: NO reference to Logs
   ❌ sp_VerifyProcessSetRunSucceeded: NO reference to Logs
```

**Conclusion:** AI matched based on semantic similarity, not SQL code.

### Test 2: True Negative Verification

Checked 5 tables that returned empty arrays:

```
✅ All 5 correct:
   - No SPs found that reference these tables
   - Empty arrays were correct rejections (true negatives)
```

**Conclusion:** When AI has SQL code, it makes correct decisions.

---

## Why This Happened

1. **Token Limit Concern (Line 731):**
   - Comment says: "Limit to 10 to include SQL snippets without exceeding token limit"
   - Developer limited SQL snippets to 10 SPs to save tokens

2. **Enum List Not Updated (Line 582-586):**
   - Enum list includes all 50 SPs
   - Allows AI to select from SPs without SQL code

3. **AI Guesses Without Data:**
   - When AI can't find SQL match in the 10 provided
   - But sees plausible names in the 50-item enum list
   - Makes guesses based on name patterns

---

## The Fix Strategy

### Option 1: Match Enum to SQL Snippets (RECOMMENDED)

**Change:** Only include SPs with SQL in the enum list

```python
def _infer_with_ai(self, table_schema, table_name, all_sp_data):
    # Filter to relevant SPs
    relevant_sps = self._filter_relevant_sps(table_schema, table_name, all_sp_data)

    # ONLY include SPs that will have SQL code in prompt (consistent limit)
    relevant_sps_with_sql = relevant_sps[:10]  # ← Same limit as _build_inference_prompt

    # Build enum list from SAME 10 SPs
    sp_enum_list = [f"{sp['schema']}.{sp['name']}" for sp in relevant_sps_with_sql]

    # Build prompt with SQL for same 10 SPs
    prompt = self._build_inference_prompt(table_schema, table_name, relevant_sps_with_sql)
```

**Pros:**
- Eliminates false positives (AI can only select from SPs it has SQL for)
- No token cost increase
- Simple one-line fix

**Cons:**
- Limits AI to 10 SPs per table (acceptable given current 2% success rate)

### Option 2: Include SQL for All 50 SPs

**Change:** Increase token budget and include SQL for all 50

**Pros:**
- AI has more options

**Cons:**
- Significant token cost increase (5x more SQL code)
- May exceed token limits for complex SPs
- Not necessary given current low success rate

---

## Recommendation

**Implement Option 1: Match enum list to SQL snippets**

**Reasoning:**
1. Current success rate is 2% (1 out of 46 tables)
2. Having 50 options vs 10 won't improve success rate if AI is making false positives
3. Need to eliminate false positives first, then optimize coverage
4. Token efficiency is important for production

**Expected Impact:**
- False positive rate: 87.5% → ~0%
- True positive rate: Should remain at 12.5% (1 correct match)
- Net result: 1 correct match, 0 false positives (vs current: 1 correct, 7 false)

---

## Implementation Plan (Iteration 4)

1. ✅ **Root cause identified**
2. **Apply fix** (Option 1)
   - File: `lineage_v3/parsers/ai_disambiguator.py`
   - Line 582: Change `[:50]` to `[:10]`
   - Or better: Pass `relevant_sps_with_sql` to `_build_inference_prompt`
3. **Test with Iteration 3 data**
   - Run same 46 unreferenced tables
   - Validate: 0 false positives
   - Check: Same 1 true positive
4. **Document results**
5. **If successful, consider Option 2 for Iteration 5** (increase to 20-30 SPs with SQL)

---

## Files to Modify

**Primary:**
- `lineage_v3/parsers/ai_disambiguator.py:573-645` (`_infer_with_ai` method)

**Secondary (if needed):**
- `lineage_v3/ai_analyzer/inference_prompt.txt` (add stronger warnings about SQL-only matching)

---

## Next Steps

1. Implement Option 1 fix
2. Test on same dataset
3. Validate: 0 false positives, 1 true positive
4. Document Iteration 4 results
5. Plan Iteration 5: Gradually increase SP count (10 → 20 → 30) while maintaining 0% false positives
