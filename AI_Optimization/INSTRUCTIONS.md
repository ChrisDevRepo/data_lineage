# AI Few-Shot Optimization - Instructions

**Work Directory:** `/home/chris/sandbox/AI_Optimization/`
**Goal:** Improve AI few-shot examples to increase recall from 2.9% to 10-15%

---

## Quick Start

1. **Read:** `COMPLETE_ANALYSIS.md` - Understand the problem
2. **Follow:** Steps below to fix it iteratively
3. **Use:** Existing sub-agents and tools (don't create new ones)
4. **Save:** All logs and results to `AI_Optimization/results/`

---

## The Problem (Summary)

- **Current:** AI finds only 3 matches from 104 unreferenced tables (2.9% recall)
- **Cause:** Few-shot examples don't cover real patterns (Fact* prefix, pluralization, etc.)
- **Fix:** Add 3 real failed cases as few-shot examples

---

## Step-by-Step Workflow

### Step 1: Create Baseline

**Use Sub-Agent:**
```bash
/sub_DL_OptimizeParsing init --name baseline_iter4_before_fewshot_fix
```

**What This Does:**
- Creates evaluation baseline in `/home/chris/sandbox/evaluation_baselines/`
- Saves current state for comparison

---

### Step 2: Run Baseline Test

**Use Sub-Agent:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_iter4_before_fewshot_fix
```

**What This Does:**
- Runs full parser test (all 104 unreferenced tables)
- Takes ~10-15 minutes
- Saves results to DuckDB: `/home/chris/sandbox/lineage_v3/lineage_workspace.duckdb`

**Expected Results:**
- 3 matches found
- 101 empty arrays
- 0 false positives

**Save Log:**
```bash
# Log will be in parser output
# Copy relevant section to: AI_Optimization/results/baseline_iter4_output.log
```

---

### Step 3: Edit Few-Shot Prompt

**File to Edit:**
```
/home/chris/sandbox/lineage_v3/ai_analyzer/inference_prompt.txt
```

**What to Add:**

**Add Example 6 (after current Example 5, around line 115):**
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

**Add Example 7 (after Example 6):**
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
```

**Add Example 8 (after Example 7):**
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

**Update Rule #5 (around line 125 in CRITICAL CONSTRAINTS section):**

**Before:**
```
5. **Pluralization matters - do not assume plural/singular equivalence**
```

**After:**
```
5. **Match exact table name in SQL code. Check actual INSERT/SELECT statements. SP name pluralization doesn't matter - only the table name in SQL code matters.**
```

---

### Step 4: Run Test with Changes

**Use Sub-Agent:**
```bash
/sub_DL_OptimizeParsing run --mode full --baseline baseline_iter4_before_fewshot_fix
```

**What This Does:**
- Runs full parser test with updated prompt
- Takes ~10-15 minutes
- Overwrites previous DuckDB results

**Save Log:**
```bash
# Copy output to: AI_Optimization/results/iter5_v1_output.log
```

---

### Step 5: Validate Results

**Use Existing Script:**
```bash
cd /home/chris/sandbox/sqlglot_improvement
PYTHONPATH=/home/chris/sandbox/lineage_v3:$PYTHONPATH \
python scripts/query_ai_results.py > ../AI_Optimization/results/iter5_v1_validation.txt
```

**What to Check:**
- ✅ Total matches: Should be ≥10 (up from 3)
- ✅ False positives: Should be ≤1
- ✅ Specific tables: Check if FactAgingSAP, EnrollmentPlan appear

**Example Output:**
```
================================================================================
TOP 20 AI-INFERRED TABLES (found 12 results)
================================================================================

Table: CONSUMPTION_FINANCE.FactAgingSAP
Confidence: 0.95 | Source: ai
  → CONSUMPTION_FINANCE.spLoadFactAgingSAP

Table: CONSUMPTION_PRIMA.EnrollmentPlan
Confidence: 0.90 | Source: ai
  → CONSUMPTION_PRIMA.spLoadEnrollmentPlans
...
```

---

### Step 6: Compare Results

**Use Sub-Agent:**
```bash
/sub_DL_OptimizeParsing compare --run1 <RUN1_ID> --run2 <RUN2_ID>
```

**Get Run IDs:**
```bash
# Check evaluation_baselines/ for run directories
ls -lt /home/chris/sandbox/evaluation_baselines/baseline_iter4_before_fewshot_fix/runs/
```

**What to Check:**
- Coverage improvement
- No regressions on existing 3 matches
- False positive rate

---

### Step 7: Decide Next Action

**If Results Are Good (≥10 matches, 0-1 FP):**
1. ✅ Document success in `AI_Optimization/results/ITERATION_5_SUCCESS.md`
2. ✅ Update `docs/PARSER_EVOLUTION_LOG.md`
3. ✅ Commit changes with `/sub_DL_GitPush`

**If Results Are OK (8-9 matches, 0 FP):**
1. Add Example 9: Partial name match (see COMPLETE_ANALYSIS.md section 5)
2. Repeat Steps 4-7

**If Results Are Poor (<8 matches or >2 FP):**
1. Analyze which matches are false positives
2. Check if specific patterns are causing issues
3. Adjust examples or rollback
4. Document findings in `AI_Optimization/results/iteration_5_analysis.md`

---

## Tools Reference

### Sub-Agent: `/sub_DL_OptimizeParsing`

**Purpose:** Test parser changes with before/after comparison

**Commands:**
- `init --name <baseline_name>` - Create baseline
- `run --mode full --baseline <name>` - Run test
- `compare --run1 <id> --run2 <id>` - Compare results
- `report --baseline <name>` - Show summary

**Location:** `.claude/commands/sub_DL_OptimizeParsing.md`

### Validation Script: `query_ai_results.py`

**Purpose:** Show AI matches in readable format

**Location:** `/home/chris/sandbox/sqlglot_improvement/scripts/query_ai_results.py`

**Usage:**
```bash
cd /home/chris/sandbox/sqlglot_improvement
PYTHONPATH=/home/chris/sandbox/lineage_v3:$PYTHONPATH python scripts/query_ai_results.py
```

### Database: `lineage_workspace.duckdb`

**Purpose:** Stores AI inference results

**Location:** `/home/chris/sandbox/lineage_v3/lineage_workspace.duckdb`

**Key Tables:**
- `objects` - All database objects (tables, SPs, views)
- `lineage_metadata` - Lineage info including AI results
- `dependencies` - Object dependencies

**Query Example:**
```sql
-- Count AI matches
SELECT COUNT(*)
FROM lineage_metadata
WHERE primary_source = 'ai'
  AND outputs IS NOT NULL
  AND outputs <> '[]'
```

---

## File Organization

### AI_Optimization/ Structure

```
AI_Optimization/
├── COMPLETE_ANALYSIS.md           ← Read this first
├── INSTRUCTIONS.md                ← This file
│
├── docs/                          ← Context documents
│   ├── ITERATION_4_RESULTS.md
│   ├── FEWSHOT_RESEARCH_FINDINGS_2025_11_03.md
│   └── ...
│
├── prompts/                       ← Prompt versions
│   └── inference_prompt_iter4_baseline.txt
│
├── results/                       ← Test results and logs
│   ├── baseline_iter4_output.log
│   ├── iter5_v1_output.log
│   ├── iter5_v1_validation.txt
│   └── ITERATION_5_SUCCESS.md (after success)
│
└── scripts/                       ← Helper scripts (if needed)
    └── (empty - use existing tools)
```

### Files to Edit (Outside AI_Optimization)

**Primary:**
- `/home/chris/sandbox/lineage_v3/ai_analyzer/inference_prompt.txt` - Add examples here

**Reference Only (Don't Edit):**
- `/home/chris/sandbox/lineage_v3/parsers/ai_disambiguator.py` - AI logic
- `/home/chris/sandbox/lineage_v3/lineage_workspace.duckdb` - Results DB

---

## Success Criteria

### Minimum (Must Achieve)
- ✅ ≥10 correct matches (vs 3 currently)
- ✅ 0-1 false positives
- ✅ ≥95% precision
- ✅ Zero regressions on existing 3 matches

### Stretch Goal
- ✅ ≥15 correct matches
- ✅ 100% precision (0 false positives)
- ✅ Coverage of common patterns (Fact*, Dim*, pluralization)

---

## Iterative Process

**Philosophy:** Test → Analyze → Adjust → Repeat

1. **Small changes:** Add 1-2 examples at a time
2. **Test after each change:** Use sub-agent
3. **Document results:** Save logs to results/
4. **Compare before/after:** Use compare command
5. **Iterate until success:** Stop when criteria met

**Don't:**
- ❌ Add all examples at once (hard to debug)
- ❌ Skip testing steps
- ❌ Make changes without baseline
- ❌ Commit without validation

---

## Common Issues & Solutions

### Issue 1: False Positives Return

**Symptom:** AI matches tables to SPs that don't reference them

**Solution:**
- Review the false positive matches
- Add negative example showing why it should be rejected
- Strengthen CRITICAL CONSTRAINTS rules

### Issue 2: Still Too Conservative

**Symptom:** <8 matches found after adding examples

**Solution:**
- Add more positive examples (Example 9: partial match)
- Check if examples are too restrictive
- Consider increasing SP count from 10 to 15

### Issue 3: Lost Existing Matches

**Symptom:** Original 3 matches no longer found

**Solution:**
- Rollback changes immediately
- Review what changed in rules or examples
- Test with just 1 example at a time

---

## Best Practices

### From Research

1. **Use real failed cases** (not synthetic examples)
   - FactAgingSAP, EnrollmentPlan from actual data
   - 2-3x more effective than made-up examples

2. **Balance positive/negative examples**
   - Current: 60% positive, 40% negative
   - Keep this ratio with new examples

3. **Stay under token limit**
   - Current: ~2,000 tokens per request
   - Limit: 5,500 tokens
   - Safe to add 3-4 examples

4. **Test iteratively**
   - Add 2-3 examples → test → analyze
   - Don't add all at once

---

## Quick Reference Commands

```bash
# Create baseline
/sub_DL_OptimizeParsing init --name baseline_iter4_before_fewshot_fix

# Run test
/sub_DL_OptimizeParsing run --mode full --baseline baseline_iter4_before_fewshot_fix

# Validate results
cd /home/chris/sandbox/sqlglot_improvement && \
PYTHONPATH=/home/chris/sandbox/lineage_v3:$PYTHONPATH \
python scripts/query_ai_results.py

# Compare runs
/sub_DL_OptimizeParsing compare --run1 RUN1 --run2 RUN2

# Save results
# Copy output to: AI_Optimization/results/
```

---

**Status:** ✅ Ready to Start
**Next:** Step 1 - Create baseline, then follow steps 2-7 iteratively
