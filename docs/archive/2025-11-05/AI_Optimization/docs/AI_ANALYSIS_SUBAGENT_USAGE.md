# AI Analysis Subagent Usage Guide

**Created:** 2025-11-03
**Purpose:** Document how to use `/sub_DL_AnalyzeAI` for analyzing AI inference test results

---

## Why This Subagent Exists

### Problem It Solves

When analyzing AI inference results, the main agent would:
- Burn 5-10k tokens on database queries
- Lose focus on the root cause (prompt improvements)
- Get distracted by raw data instead of patterns
- Waste context window on repetitive analysis

### Solution

The `/sub_DL_AnalyzeAI` subagent:
- Uses Haiku model (3-5k tokens, cost-effective)
- Runs in isolated context window
- Performs all DB queries and pattern analysis
- Returns **concise structured findings** to main agent
- Preserves main agent context for prompt engineering

**Token Efficiency:** Main agent receives ~2k token summary instead of consuming 10k+ tokens doing analysis

---

## When to Use This Subagent

**✅ Use the subagent when:**
- Analyzing AI inference test results after a full parser run
- Investigating why AI success rate is low
- Identifying failure patterns across multiple tables
- Preparing for next iteration of prompt improvements

**❌ Don't use the subagent when:**
- Debugging a single table's AI inference (use direct DB query)
- Checking if test is still running (use grep on log file)
- Making code changes (main agent should do this)

---

## How to Invoke the Subagent

### From Main Agent

```
Use the Task tool with:
- subagent_type: "general-purpose"
- model: "haiku" (cost-effective for analysis)
- description: "Analyze AI inference test results"
- prompt: "Analyze the AI inference test results from Iteration [N].

          Test log: sqlglot_improvement/ai_test_iter[N]_[description].log
          Database: lineage_v3/lineage_workspace.duckdb

          Follow the analysis steps in the /sub_DL_AnalyzeAI command.
          Return a structured report identifying failure patterns and recommendations."
```

### Example Invocation

```
Task(
  subagent_type="general-purpose",
  model="haiku",
  description="Analyze AI inference test results",
  prompt="""Analyze the AI inference test results from Iteration 3.

Test log: sqlglot_improvement/ai_test_iter3_enum_full.log
Database: lineage_v3/lineage_workspace.duckdb

Follow the analysis steps in the /sub_DL_AnalyzeAI command.
Return a structured report identifying failure patterns and recommendations."""
)
```

---

## What the Subagent Returns

### Structured Report Format

```markdown
# AI Inference Analysis - Iteration [N]

## Test Summary
- Total unreferenced tables: X
- AI attempted inference: Y tables
- Success rate: Z% (target: >90%)
- Hallucinations: N (should be 0)

## Success/Failure Breakdown
✅ Successful inferences: X (Y%)
❌ Failed inferences: Z (W%)

## Failure Pattern Analysis
### Pattern 1: [Name] (X tables, Y%)
**Description:** ...
**Example:** ...
**Root Cause:** ...

### Pattern 2: [Name] (X tables, Y%)
...

## Recommendations for Next Iteration
### Priority 1: [Recommendation]
**Why:** ...
**Expected Impact:** ...
**Implementation:** ...

## Sample Failed Cases for Few-Shot Examples
[2-3 actual failed cases]
```

---

## Real Example - Iteration 3 Analysis

### Input
```
Test log: sqlglot_improvement/ai_test_iter3_enum_full.log
Database: lineage_v3/lineage_workspace.duckdb
```

### Output (Key Findings)

**Test Summary:**
- Success rate: 2.2% (1/46 unreferenced tables)
- Hallucinations: 0 ✅ (enum constraint worked)
- Total AI-inferred tables: 207 (broader usage than just unreferenced)

**Critical Discovery:**
The 45 "failed" tables were actually **correct rejections** - AI returned confidence=0.0 with reasoning explaining no SQL match found. This is desired behavior, not a bug.

**Recommendations:**
1. Investigate the 207 AI-inferred tables for accuracy (spot-check sample)
2. Add few-shot examples showing when plural/singular matches ARE valid
3. Enhance SP filtering to reduce token usage

**Impact on Main Agent:**
- Main agent received concise findings in ~2k tokens
- Avoided 10+ manual DB queries
- Can now focus on implementing recommendations

---

## Analysis Steps the Subagent Performs

### Step 1: Extract Test Summary
```bash
grep "AI inference complete" <log_file>
grep "Successfully inferred:" <log_file>
grep "Could not infer:" <log_file>
```

### Step 2: Check Hallucinations
```bash
grep "SP not found in catalog" <log_file> | wc -l
# Should be 0 if enum constraint working
```

### Step 3: Query Database
```python
# Get AI-inferred tables breakdown
SELECT COUNT(*), confidence
FROM lineage_metadata
WHERE primary_source = 'ai'
GROUP BY confidence

# Check for empty outputs (rejections)
SELECT table_name, confidence
FROM objects o
JOIN lineage_metadata lm ON o.object_id = lm.object_id
WHERE lm.outputs = '[]' AND lm.primary_source = 'ai'
```

### Step 4: Analyze Patterns
- Group failures by type (name mismatch, plural/singular, no SP found)
- Count tables in each pattern
- Identify root causes

### Step 5: Generate Recommendations
- Prioritize by expected impact
- Provide specific implementation details
- Estimate accuracy improvement

---

## Token Efficiency Comparison

### Without Subagent (Old Approach)
```
Main Agent Context Usage:
1. Run DB schema query: +500 tokens
2. Query AI-inferred tables: +1000 tokens
3. Check sample tables: +2000 tokens
4. Analyze SQL code: +3000 tokens
5. Pattern analysis: +2000 tokens
6. Write recommendations: +1500 tokens
Total: ~10,000 tokens consumed
```

### With Subagent (New Approach)
```
Main Agent Context Usage:
1. Invoke subagent: +500 tokens (prompt)
2. Receive report: +2000 tokens (structured findings)
Total: ~2,500 tokens consumed

Subagent Context Usage:
- Fresh context window (doesn't pollute main)
- Uses Haiku model (3x cheaper than Sonnet)
- Discarded after analysis complete
```

**Token Savings:** 75% reduction (10k → 2.5k)
**Cost Savings:** ~80% (Haiku vs Sonnet for analysis)
**Context Preservation:** Main agent stays focused on prompt engineering

---

## Best Practices

### 1. Run After Full Parser Test
```bash
# First: Run parser test
cd lineage_v3
../venv/bin/python main.py run --parquet ../parquet_snapshots/ --full-refresh 2>&1 | tee ../sqlglot_improvement/ai_test_iter[N].log

# Second: Invoke subagent for analysis
Task(subagent_type="general-purpose", model="haiku", ...)
```

### 2. Save Subagent Output
The main agent should save the subagent's report to a file:

```markdown
# File: sqlglot_improvement/docs/ITERATION_[N]_ANALYSIS.md
[Paste subagent output here]
```

### 3. Use Findings for Next Iteration
Main agent uses the structured recommendations to:
- Update few-shot examples in `inference_prompt.txt`
- Adjust JSON Schema if needed
- Modify SP filtering logic in `ai_disambiguator.py`

### 4. Track Improvements
```markdown
| Iteration | Hallucinations | Success Rate | Changes Made |
|-----------|----------------|--------------|--------------|
| 2         | 69%            | 16.4%        | N/A          |
| 3         | 0%             | 2.2%         | Enum constraint |
| 4         | TBD            | TBD          | Few-shot enhancement |
```

---

## Troubleshooting

### Subagent Returns "Database Not Found"
**Fix:** Ensure full parser test completed successfully before running analysis
```bash
ls -lh lineage_v3/lineage_workspace.duckdb
# Should show file size > 0
```

### Subagent Says "No AI-Inferred Tables"
**Fix:** Check if AI inference was actually run during parser test
```bash
grep "Step 7.6: AI Inference" sqlglot_improvement/ai_test_iter*.log
```

### Subagent Analysis Seems Wrong
**Fix:** Verify log file path is correct
```bash
ls -lh sqlglot_improvement/ai_test_iter*.log
# Check timestamps match your test run
```

---

## Maintenance

### When to Update the Subagent

**Update `.claude/commands/sub_DL_AnalyzeAI.md` when:**
- Database schema changes (new columns in `lineage_metadata`)
- New analysis patterns discovered (add to "Pattern Analysis" section)
- Output format needs adjustment (update "Output Format" section)

**DO NOT update when:**
- Just analyzing a new iteration (subagent is reusable as-is)
- Minor changes to few-shot examples (doesn't affect analysis)

---

## Integration with Parser Development Workflow

```
1. Implement prompt/code changes
   ↓
2. Run parser test: /sub_DL_OptimizeParsing run --mode full
   ↓
3. Analyze results: Task(sub_DL_AnalyzeAI)
   ↓
4. Main agent receives structured findings
   ↓
5. Main agent implements recommendations
   ↓
6. Repeat until >90% accuracy achieved
```

---

## Summary

**Purpose:** Token-efficient analysis of AI inference test results
**Model:** Haiku (cost-effective)
**Token Savings:** 75% reduction vs manual analysis
**Usage:** After full parser test, before next iteration planning
**Output:** Structured report with patterns and recommendations

**Critical Rule:** 🚨 **ALWAYS use this subagent for AI inference analysis** - Don't waste main agent tokens on DB queries

---

**Status:** ✅ Production-Ready
**Tested:** Iteration 3 (2025-11-03)
**Maintained By:** Main agent (this document)
