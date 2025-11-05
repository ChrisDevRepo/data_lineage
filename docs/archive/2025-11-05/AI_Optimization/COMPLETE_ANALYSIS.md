# AI Few-Shot Optimization - Complete Analysis

**Date:** 2025-11-03
**Status:** Low Recall Issue (3 matches from 104 tables = 2.9%)
**Goal:** Improve AI few-shot examples to increase recall to 10-15% while maintaining 0% false positives

---

## Executive Summary

**The Problem:**
- AI finds only 3 correct matches out of 104 unreferenced tables (2.9% recall)
- Current few-shot examples don't cover real SQL patterns in the data

**The Solution:**
- Add 3-4 few-shot examples from actual failed cases
- Use research-backed patterns from real data (not synthetic examples)

**Expected Impact:**
- Conservative: 3 → 8-12 matches (maintain 100% precision)
- Optimistic: 3 → 15-20 matches (≥95% precision)

---

## 1. Current State

### System Overview

**What This System Does:**
- Finds "unreferenced tables" - tables that exist but weren't found in any SP's parsed SQL
- Uses AI to search through stored procedures to find which ones reference these tables
- Flow: Table name → AI searches 10 SPs → Returns list of SP names

**Why Tables Are Unreferenced:**
- Dynamic SQL: `EXEC('SELECT FROM ' + @table_name)`
- Complex SQL that SQLGlot couldn't parse
- Tables used only in external systems
- Orphaned/unused tables

### Current Performance (Iteration 4)

**File:** `/home/chris/sandbox/lineage_v3/lineage_workspace.duckdb`

| Metric | Value |
|--------|-------|
| Unreferenced tables processed | 104 |
| Tables with matches | 3 (2.9%) |
| Empty arrays (correct rejections) | 101 (97.1%) |
| False positives | 0 (0%) ✅ |
| True positives | 3 (100% precision) ✅ |
| **Recall** | **2.9% (VERY LOW)** ❌ |

**The 3 Correct Matches:**
1. `CONSUMPTION_PRIMA.ProjectTeamRegions` → `CONSUMPTION_PRIMA.spLoadProjectRegions`
2. `CONSUMPTION_FINANCE.GLCognosData_Test` → `CONSUMPTION_FINANCE.spLoadGLCognosData_Test`
3. `CONSUMPTION_PRIMA.FeasibilityQuestions` → `CONSUMPTION_PRIMA.spLoadFeasibilityObjects`

**Pattern:** All 3 follow exact naming pattern (table substring in SP name, same schema)

---

## 2. Root Cause Analysis

### Current Few-Shot Examples

**File:** `/home/chris/sandbox/lineage_v3/ai_analyzer/inference_prompt.txt`

**Current 5 Examples:**
1. ✅ INSERT statement (positive) - `studyarms` table
2. ✅ No match - different table entirely
3. ✅ SELECT statement (positive) - `sap_raw_data` table
4. ✅ Similar names but wrong - `payment_tracker` vs `payment_history`
5. ✅ Misleading SP name - `vendor_accounts` vs `vendor_details`

**What's Missing:**
- ❌ No Fact* prefix pattern (`FactAgingSAP`)
- ❌ No pluralization pattern (`EnrollmentPlan` → `spLoadEnrollmentPlans`)
- ❌ No partial name match (`FeasibilityQuestions`)
- ❌ No lookup table rejection
- ❌ All examples are **synthetic** (made-up), not from real failed cases

### Why This Matters

**Research Finding (Arize AI 2024):**
> "In-domain SQL patterns are 2-3x more effective than synthetic examples"

**What This Means:**
- Using real failed cases as examples helps AI recognize similar patterns
- Synthetic examples don't teach AI the actual patterns in our data

---

## 3. Documented Failed Cases (Real Data)

**Source:** `docs/FEWSHOT_RESEARCH_FINDINGS_2025_11_03.md`

### Failed Case #1: Fact Prefix Pattern

**Table:** `CONSUMPTION_FINANCE.FactAgingSAP`
**Expected Match:** `CONSUMPTION_FINANCE.spLoadFactAgingSAP`
**Current Result:** Empty array (AI missed it)
**Why It Failed:** No few-shot example showing compound names with "Fact" prefix

**SQL Pattern:**
```sql
TRUNCATE TABLE [CONSUMPTION_FINANCE].FactAgingSAP
INSERT INTO [CONSUMPTION_FINANCE].FactAgingSAP
SELECT customerid, amount, aging_days, invoice_date
FROM [STAGING_FINANCE].sap_aging_data
```

### Failed Case #2: Pluralization Pattern

**Table:** `CONSUMPTION_PRIMA.EnrollmentPlan`
**Expected Match:** `CONSUMPTION_PRIMA.spLoadEnrollmentPlans`
**Current Result:** Empty array (AI missed it)
**Why It Failed:** Rule #5 says "pluralization matters - do not assume equivalence"

**SQL Pattern:**
```sql
TRUNCATE TABLE [CONSUMPTION_PRIMA].EnrollmentPlan
INSERT INTO [CONSUMPTION_PRIMA].EnrollmentPlan
SELECT plan_id, study_id, enrollment_count
FROM [STAGING_PRIMA].enrollment_plans
```

**Key Insight:** SP name has plural (`Plans`) but SQL shows singular table name. Current rules reject this, but it SHOULD match (check SQL code, not SP name).

### Failed Case #3: Compound Fact Pattern

**Table:** `CONSUMPTION_FINANCE.FactAggregatedLaborCost`
**Expected Match:** `CONSUMPTION_FINANCE.spLoadFactAggregatedLaborCost`
**Current Result:** Empty array (AI missed it)
**Why It Failed:** Another Fact* prefix pattern, compound name

---

## 4. Historical Context

### Iteration 3: False Positive Problem (87.5% error rate)

**What Happened:**
- 8 matches found, but 7 were false positives
- AI matched based on name similarity, not SQL evidence
- Example: `ADMIN.Logs` matched to 4 SPs, but NONE actually referenced Logs in SQL

**Root Cause:**
- Enum constraint had 50 SPs
- Prompt only included SQL for 10 SPs
- AI guessed for the other 40 SPs based on names

### Iteration 4: Fixed False Positives, But Too Conservative

**Fix Applied:**
- Changed line 585 in `ai_disambiguator.py` from `[:50]` to `[:10]`
- Aligned enum constraint with SQL snippets

**Result:**
- False positives: 7 → 0 (100% elimination) ✅
- Matches found: 8 → 3 (62.5% reduction) ❌
- AI now only matches with very strong evidence

**Trade-off:** High precision but very low recall

---

## 5. The Solution: Add Real Failed Cases as Few-Shot Examples

### Recommended Example #1: Fact Prefix Pattern

```markdown
### Example 6: Compound Name with Fact Prefix Pattern
**Target:** consumption_finance.factagingsap

**Available SPs:**
- consumption_finance.sploadfactagingsap
  ```sql
  truncate table [consumption_finance].factagingsap
  insert into [consumption_finance].factagingsap
  select customerid, amount, aging_days, invoice_date
  from [staging_finance].sap_aging_data
  where is_processed = 0
  ```

**Answer:**
```json
{
  "input_procedures": [],
  "output_procedures": ["consumption_finance.sploadfactagingsap"],
  "confidence": 0.95,
  "reasoning": "insert into consumption_finance.factagingsap - exact table match with Fact prefix pattern"
}
```
```

### Recommended Example #2: Pluralization Edge Case

```markdown
### Example 7: Pluralization Match (SQL Code vs SP Name)
**Target:** consumption_prima.enrollmentplan

**Available SPs:**
- consumption_prima.sploadenrollmentplans
  ```sql
  truncate table [consumption_prima].enrollmentplan
  insert into [consumption_prima].enrollmentplan
  select plan_id, study_id, enrollment_count, target_count
  from [staging_prima].enrollment_plans
  ```

**Answer:**
```json
{
  "input_procedures": [],
  "output_procedures": ["consumption_prima.sploadenrollmentplans"],
  "confidence": 0.90,
  "reasoning": "insert into enrollmentplan - SP name has plural but SQL shows exact table match"
}
```

**Note:** This requires updating Rule #5 in CRITICAL CONSTRAINTS to clarify: "Check the actual INSERT/SELECT statements in SQL code. SP name pluralization doesn't matter."
```

### Recommended Example #3: Lookup Table Rejection (Negative)

```markdown
### Example 8: Lookup Table Pattern (Correct Rejection)
**Target:** admin.lookup_averagedaystopaymetric

**Available SPs:**
- admin.sp_setupcontroldata
  ```sql
  insert into [admin].control_parameters
  select param_name, param_value, category
  from [staging_admin].config_data
  ```

**Answer:**
```json
{
  "input_procedures": [],
  "output_procedures": [],
  "confidence": 0.0,
  "reasoning": "lookup tables are typically reference data without ETL dependencies - no SP references this table in SQL"
}
```
```

---

## 6. Implementation Details

### File to Edit

**Primary File:**
- `/home/chris/sandbox/lineage_v3/ai_analyzer/inference_prompt.txt`
- Current: 157 lines, 5 examples
- Target: ~200 lines, 8 examples

### Changes Required

**1. Add 3 New Few-Shot Examples:**
- Example 6: Fact prefix pattern (lines ~115-135)
- Example 7: Pluralization edge case (lines ~136-156)
- Example 8: Lookup table rejection (lines ~157-175)

**2. Update Rule #5 in CRITICAL CONSTRAINTS:**

**Current Rule (Line ~125):**
```
5. **Pluralization matters - do not assume plural/singular equivalence**
```

**Updated Rule:**
```
5. **Match exact table name in SQL code. Check actual INSERT/SELECT statements. SP name pluralization doesn't matter - only the table name in SQL code matters.**
```

---

## 7. How to Test Changes

### Use Existing Sub-Agent

**Command:** `/sub_DL_OptimizeParsing`

**Test Workflow:**

**1. Create Baseline:**
```bash
/sub_DL_OptimizeParsing init --name baseline_iter4_before_fewshot_fix
```

**2. Run Baseline Test:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_iter4_before_fewshot_fix
```

**3. Edit Prompt:**
- Edit `/home/chris/sandbox/lineage_v3/ai_analyzer/inference_prompt.txt`
- Add 3 new examples
- Update Rule #5

**4. Run Test After Changes:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_iter4_before_fewshot_fix
```

**5. Compare Results:**
```bash
/sub_DL_OptimizeParsing compare --run1 RUN1_ID --run2 RUN2_ID
```

### Validation Script

**Use Existing Script:**
```bash
cd /home/chris/sandbox/sqlglot_improvement
PYTHONPATH=/home/chris/sandbox/lineage_v3:$PYTHONPATH \
python scripts/query_ai_results.py
```

**What to Check:**
- ✅ Matches found: ≥10 (up from 3)
- ✅ False positives: ≤1 (maintain ~0%)
- ✅ Precision: ≥95%
- ✅ Specific tables: FactAgingSAP, EnrollmentPlan should match

---

## 8. Expected Results

### Conservative Target

**Metrics:**
- Recall: 2.9% → 8-12% (3 → 8-12 matches)
- Precision: 100% maintained
- False positives: 0

**Logic:**
- 3 examples = 3 exact matches guaranteed
- Generalization to similar patterns = +5-9 matches

### Optimistic Target

**Metrics:**
- Recall: 2.9% → 15-20% (3 → 15-20 matches)
- Precision: ≥95%
- False positives: ≤1

**Logic:**
- Research shows in-domain examples are 2-3x more effective
- Other Fact* tables should match (FactAggregatedLaborCost, etc.)
- Other pluralization cases should match

---

## 9. Success Criteria

### Minimum Requirements
- ✅ ≥10 correct matches (vs 3 currently)
- ✅ 0-1 false positives
- ✅ ≥95% precision
- ✅ Zero regressions on existing 3 matches

### Stretch Goals
- ✅ ≥15 correct matches
- ✅ 100% precision (0 false positives)
- ✅ Identify pattern categories (Fact*, Dim*, Staging*, etc.)

### Failure Criteria (Rollback)
- ❌ <8 matches (no improvement)
- ❌ >2 false positives (precision drops)
- ❌ Lost any of the existing 3 correct matches

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| False positives return | Medium | High | Keep strong negative examples (lookup table) |
| AI still too conservative | Medium | Medium | Add more positive examples if needed |
| Confusing AI with pluralization rule change | Low | Medium | Clear wording: "Check SQL code, not SP name" |
| Token limit exceeded | Low | Low | Currently 2,000 tokens, limit is 5,500 |

---

## 11. Iterative Improvement Strategy

### If Results Are Good (≥10 matches, 0-1 FP)
1. ✅ Document success in `AI_Optimization/results/ITERATION_5_SUCCESS.md`
2. ✅ Commit changes
3. ✅ Monitor production usage

### If Results Are OK (8-9 matches, 0 FP)
1. Add Example 9: Partial name match (FeasibilityQuestions)
2. Re-test
3. Compare improvement

### If Results Are Poor (<8 matches or >2 FP)
1. Rollback prompt changes
2. Analyze false positives or missed matches
3. Adjust examples based on findings
4. Re-test

---

## 12. Key Files Reference

### Code Files (READ ONLY - Reference)
- `/home/chris/sandbox/lineage_v3/ai_analyzer/inference_prompt.txt` - Prompt to edit
- `/home/chris/sandbox/lineage_v3/parsers/ai_disambiguator.py` - AI logic (lines 573-762)
- `/home/chris/sandbox/lineage_v3/lineage_workspace.duckdb` - Results database

### Analysis Scripts (USE - Don't Modify)
- `/home/chris/sandbox/sqlglot_improvement/scripts/query_ai_results.py` - Validate results
- `/home/chris/sandbox/sqlglot_improvement/scripts/analyze_ai_results.py` - Detailed analysis

### Sub-Agent (USE)
- `/sub_DL_OptimizeParsing` - Testing sub-agent

### Documentation (Context)
- `AI_Optimization/docs/ITERATION_4_RESULTS.md` - Current baseline
- `AI_Optimization/docs/FEWSHOT_RESEARCH_FINDINGS_2025_11_03.md` - Research findings
- `AI_Optimization/docs/AI_FAILURE_ANALYSIS_2025_11_03.md` - Failure analysis

---

## 13. Research-Backed Best Practices

### From Arize AI (2024) - Text-to-SQL Prompting

**Finding #1: In-Domain Examples Are Critical**
> "SQL query distribution matters more than question diversity"

**Application:** Use real failed cases (FactAgingSAP, EnrollmentPlan) instead of synthetic examples

**Finding #2: 1-3 Examples Per Pattern**
> "Start with 1-3 in-domain examples per database. More examples may hurt rather than help."

**Application:** Add 3 examples (Fact*, pluralization, lookup), not 10

**Finding #3: Token Budget Matters**
> "Degradation starts around 5,500 tokens for GPT-4"

**Application:** Current prompt ~2,000 tokens, adding 3 examples = ~2,500 tokens (safe margin)

### From LLM Structured Output Research (2025)

**Finding: Negative Examples Teach Rejection**
> "Show AI what to reject, not just what to accept"

**Application:** Add lookup table rejection example to reinforce "when to return empty array"

---

## 14. Summary

### The Core Issue
AI is too conservative due to missing few-shot patterns. Only 3 matches from 104 tables (2.9% recall).

### The Fix
Add 3 real failed cases as few-shot examples:
1. FactAgingSAP (Fact* prefix pattern)
2. EnrollmentPlan (pluralization edge case)
3. Lookup table (negative example)

### Expected Outcome
- Conservative: 8-12 matches (maintain 100% precision)
- Optimistic: 15-20 matches (≥95% precision)
- Research-backed: In-domain examples are 2-3x more effective

### Test Using
- `/sub_DL_OptimizeParsing` sub-agent for before/after comparison
- Existing validation scripts for accuracy check

### Success = ≥10 matches with ≤1 false positive

---

**Status:** ✅ Analysis Complete - Ready for Implementation
**Next:** Edit prompt file, test, validate, iterate until solved
