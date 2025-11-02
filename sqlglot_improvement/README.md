# SQLGlot Optimization Working Directory

**Date:** 2025-11-02
**Current Status:** 86/202 SPs (42.6%) high confidence
**Goal:** Phase 1: 50-70% | Phase 2: 85-90% | Phase 3: 95-99%

---

## Quick Start

### Run Phase 1 Iteration Test
```bash
cd /home/chris/sandbox/sqlglot_improvement

# Test current iteration
python scripts/test_iteration.py "Iteration 1: No preprocessing"

# Analyze failures
python scripts/analyze_sqlglot_failures.py

# Measure results
python scripts/measure_phase1_results.py
```

### Directory Structure

```
sqlglot_improvement/
├── README.md                  # This file
├── MASTER_PLAN.md             # Complete 3-phase strategy
├── docs/                      # Supporting documentation
│   ├── SQLGLOT_RESEARCH_FINDINGS.md
│   ├── PLAN_A5_SEMICOLON_ADDITION.md
│   ├── PLAN_B_BLOCK_EXTRACTION.md
│   ├── APPROACH_COMPARISON.md
│   ├── FINAL_IMPLEMENTATION_SUMMARY.md
│   ├── PHASE1_FINAL_RESULTS.md
│   ├── ROOT_CAUSE_42_PERCENT.md
│   └── SQLGLOT_LIMITATION_BREAKDOWN.md
└── scripts/                   # Testing and analysis scripts
    ├── test_iteration.py
    ├── analyze_sqlglot_failures.py
    ├── measure_phase1_results.py
    ├── test_semicolon_addition.py
    ├── test_semicolon_on_real_sp.py
    ├── test_leading_semicolons.py
    └── validate_plan_a5_patterns.py
```

---

## Files Overview

### MASTER_PLAN.md
**Complete 3-phase optimization strategy**

Contains:
- Problem analysis (why only 42.6%)
- Plan A results (statement removal: 78 SPs)
- Plan A.5 results (leading semicolons: 86 SPs - current)
- Plan B documentation (block extraction - deferred)
- Phase 1: 5 iterative tests (simple regex, 10-15 min each)
- Phase 2: AI fallback with complexity detection
- Phase 3: Multishot training for 95-99% accuracy
- Industry research (OpenMetadata, DataHub, etc.)
- Implementation checklist

**Start here** for complete understanding of the strategy.

---

## Phase 1: Iterative SQLGlot Optimization

### Goal
Reach 100-140 SPs (50-70%) with simple regex preprocessing.

### Iterations (5 max, ~1 hour total)

#### Iteration 1: No Preprocessing (Baseline)
**Test if original DDL parses better**
```python
# In quality_aware_parser.py
def _preprocess_ddl(self, ddl: str) -> str:
    return ddl  # No preprocessing
```
Expected: 70-80 SPs (35-40%)

#### Iteration 2: GO Replacement Only
**Fix batch separator issue**
```python
patterns = [
    (r'\bGO\b', ';', re.IGNORECASE),
]
```
Expected: 80-90 SPs (40-45%)

#### Iteration 3: GO + Comment Removal
**Remove comments that might confuse tokenizer**
```python
patterns = [
    (r'--[^\n]*', '', 0),
    (r'/\*.*?\*/', '', re.DOTALL),
    (r'\bGO\b', ';', re.IGNORECASE),
]
```
Expected: 85-95 SPs (42-47%)

#### Iteration 4: Add Session Option Removal
**Remove SET NOCOUNT, SET ANSI_NULLS**
```python
patterns = [
    # Comments + GO (from Iteration 3)
    (r'--[^\n]*', '', 0),
    (r'/\*.*?\*/', '', re.DOTALL),
    (r'\bGO\b', ';', re.IGNORECASE),

    # Session options (new)
    (r'\bSET\s+NOCOUNT\s+(ON|OFF)\b', '', re.IGNORECASE),
    (r'\bSET\s+ANSI_NULLS\s+(ON|OFF)\b', '', re.IGNORECASE),
    (r'\bSET\s+QUOTED_IDENTIFIER\s+(ON|OFF)\b', '', re.IGNORECASE),
]
```
Expected: 90-100 SPs (45-50%)

#### Iteration 5: Add Utility SP Removal
**Remove LogMessage, spLastRowCount calls**
```python
patterns = [
    # All from Iteration 4 +

    # Utility SPs (CRITICAL: use [^\n;]* not [^;]*)
    (r'\bEXEC(?:UTE)?\s+\[?[^\]]+\]?\.\[?(LogMessage|LogError|spLastRowCount)\]?[^\n;]*;?',
     '', re.IGNORECASE),
]
```
Expected: 95-110 SPs (47-55%)

### Testing Process

**Before each iteration:**
```bash
# 1. Update quality_aware_parser.py with new patterns
# 2. Run full parse
cd /home/chris/sandbox
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# 3. Test iteration
python sqlglot_improvement/scripts/test_iteration.py "Iteration X"

# 4. Analyze failures
python sqlglot_improvement/scripts/analyze_sqlglot_failures.py
```

**Compare with baseline:**
- Baseline: 86 SPs (42.6%)
- If new result > 86 → Keep changes
- If new result ≤ 86 → Revert changes

**After 5 iterations:**
- Select best result
- Document final patterns
- Proceed to Phase 2

---

## Phase 2: AI Fallback Strategy

### Goal
Reach 170-180 SPs (85-90%) by using AI for complex cases.

### Complexity Detection

**Red Flags (auto-send to AI):**
- `sp_executesql` - Dynamic SQL
- `EXEC(@var)` - Dynamic EXEC
- `DECLARE CURSOR` - Cursor logic
- `CREATE TABLE #` - Temp tables
- `BEGIN TRY` - Error handling
- `BEGIN TRANSACTION` - Transaction management

**Complexity Score:**
```
Score = (Lines × 10) + (Dependencies × 50) + (Parameters × 20)

Thresholds:
- Simple: < 5000 (try SQLGlot)
- Medium: 5000-10000 (try SQLGlot with validation)
- Complex: ≥ 10000 (use AI directly)
```

### Implementation
See MASTER_PLAN.md Phase 2 section for complete `parse_with_fallback()` logic.

---

## Phase 3: Multishot Training

### Goal
Reach 190-200 SPs (95-99%) by improving AI accuracy with examples.

### Strategy
1. Run Phase 2 on all SPs
2. Manually review 20-30 low-confidence SPs
3. Create ground truth for 20 test cases
4. Categorize failure patterns
5. Create multishot examples (10 examples)
6. Update AI prompt with examples
7. Re-test on 20 test cases
8. If improved → apply to full dataset

See MASTER_PLAN.md Phase 3 section for multishot prompt template.

---

## Scripts Reference

### test_iteration.py
**Purpose:** Test current iteration and report results

**Usage:**
```bash
python scripts/test_iteration.py "Iteration 1: No preprocessing"
```

**Output:**
```
Testing Iteration: Iteration 1: No preprocessing
============================================================

Results:
  High Confidence (≥0.85):  75/202 (37.1%)
  Medium Confidence (0.75-0.84): 10/202 (5.0%)
  Low Confidence (<0.75):   117/202 (57.9%)

============================================================
❌ REGRESSION: -11 SPs vs baseline (75 vs 86)
```

### analyze_sqlglot_failures.py
**Purpose:** Analyze parse log for failure patterns

**Usage:**
```bash
python scripts/analyze_sqlglot_failures.py
```

**Output:**
```
SQLGLOT FAILURE ANALYSIS
================================================================================

Total fallback messages: 489

================================================================================
FAILURE CATEGORIES
================================================================================

Truncated CREATE PROC: 174 occurrences
------------------------------------------------------------
  • CREATE PROC [...] @Thread [SM
  • CREATE PROC [...] AS \nSET NOCOUNT O
  ... and 172 more

DECLARE fragments: 43 occurrences
------------------------------------------------------------
  • DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int\nDECLA
  ... and 42 more
```

### measure_phase1_results.py
**Purpose:** Measure confidence distribution from database

**Usage:**
```bash
python scripts/measure_phase1_results.py
```

**Output:**
```
Phase 1 Results:
  High Confidence (≥0.85):  86/202 (42.6%)
  Medium Confidence (0.75-0.84): 11/202 (5.4%)
  Low Confidence (<0.75):   105/202 (52.0%)

Comparison with Baseline (46 SPs):
  +40 SPs (+87.0%)
```

### validate_plan_a5_patterns.py
**Purpose:** Validate preprocessing patterns don't break DDL

**Usage:**
```bash
python scripts/validate_plan_a5_patterns.py
```

**Output:**
```
Validating Plan A.5 Patterns:
  ✅ Comment removal: 125 comments removed
  ✅ Session options: 18 SET statements removed
  ✅ Utility SPs: 8 EXEC calls removed
  ✅ Leading semicolons: 342 semicolons added
  ⚠️ Double semicolons: 0 (good)
```

---

## Documentation Reference

### SQLGLOT_RESEARCH_FINDINGS.md
**Key Finding:** Parameters work fine; STATEMENT DELIMITERS are the issue
- SQLGlot GitHub issue #3095 confirms
- T-SQL uses newlines/GO, SQLGlot expects semicolons

### PLAN_A5_SEMICOLON_ADDITION.md
**Analysis of leading semicolons approach**
- Comparison with removal approach
- Pattern design rationale
- Expected impact (50-60%)
- Actual result (42.6%)

### PLAN_B_BLOCK_EXTRACTION.md
**Alternative approach: Extract and simplify blocks**
- Detailed implementation steps
- Challenges (variable tracking, subqueries, dynamic SQL)
- Why deferred (complexity vs benefit)
- When to revisit

### PHASE1_FINAL_RESULTS.md
**Test results from leading semicolons approach**
- 86 SPs (42.6%) high confidence
- +40 SPs vs baseline (+87.0%)
- +8 SPs vs Plan A (+10.3%)
- Observed issues (181 validation failures)

### ROOT_CAUSE_42_PERCENT.md
**Why only 42% instead of 50%?**
- Leading semicolons broke CREATE PROC structure
- SQLGlot sees incomplete statements
- 181/202 SPs had preprocessing validation failures
- Theoretical max ~45-55% for SQLGlot on T-SQL

### SQLGLOT_LIMITATION_BREAKDOWN.md
**Detailed failure categorization**
- 181 preprocessing validation failures
- 174 truncated CREATE PROC statements
- 43 DECLARE fragments
- 36 BEGIN/END orphans
- Recovery potential analysis

---

## Current Implementation

### File: `/home/chris/sandbox/lineage_v3/parsers/quality_aware_parser.py`

**Lines 131-167:** Preprocessing patterns (Plan A.5)

```python
def _get_preprocessing_patterns(self) -> List[Tuple[Pattern, str, int]]:
    """Get preprocessing regex patterns."""

    patterns = [
        # Remove single-line comments
        (r'--[^\n]*', '', 0),

        # Remove multi-line comments
        (r'/\*.*?\*/', '', re.DOTALL),

        # Remove session options
        (r'\bSET\s+NOCOUNT\s+(ON|OFF)\b', '', re.IGNORECASE),
        (r'\bSET\s+ANSI_NULLS\s+(ON|OFF)\b', '', re.IGNORECASE),

        # FIXED: Remove utility SP calls (stop at newline)
        (r'\bEXEC(?:UTE)?\s+\[?[^\]]+\]?\.\[?(LogMessage|LogError|spLastRowCount)\]?[^\n;]*;?',
         '', re.IGNORECASE),

        # Add leading semicolons (user's insight)
        (r'(?<!;)\n(\s*\bDECLARE\b)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bSET\s+@)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bINSERT\s+INTO\b)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bUPDATE\s+)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bDELETE\s+)', r'\n;\1', 0),
        (r'(?<!;)(?<!\()(?<!AS\s)\n(\s*\bSELECT\b)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bCREATE\s+)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bDROP\s+)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bTRUNCATE\s+)', r'\n;\1', 0),
        (r'(?<!;)\n(\s*\bEXEC(?:UTE)?\s+)', r'\n;\1', 0),
    ]

    return patterns
```

---

## Known Issues

### Issue 1: Preprocessing Validation Failures (181 SPs)
**Description:** Leading semicolons remove table references during preprocessing
**Evidence:** `Preprocessing removed table references! Original: 5 tables, Cleaned: 0 tables. Lost: 5`
**Impact:** Parser falls back to original DDL (bypasses preprocessing)
**Fix:** Phase 1 iterations will test simpler patterns

### Issue 2: Truncated CREATE PROC (174 SPs)
**Description:** Leading semicolons split CREATE PROC from its body
**Evidence:** `'CREATE PROC [...] @Thread [SM' contains unsupported syntax`
**Root Cause:** SQLGlot sees `CREATE PROC ... AS` then `;DECLARE` starts new statement
**Fix:** Don't add semicolons inside CREATE PROC body (tested in iterations)

### Issue 3: Utility SP Pattern Too Greedy
**Description:** Pattern `[^;]*` matched to end of file instead of end of line
**Evidence:** Entire SP body removed after utility call
**Fix:** Changed to `[^\n;]*` to stop at newline (FIXED in current code)

---

## Success Criteria

| Phase | Target | Duration | Status |
|-------|--------|----------|--------|
| **Phase 1** | 100-140 SPs (50-70%) | ~1 hour | ⏳ Ready to start |
| **Phase 2** | 170-180 SPs (85-90%) | ~2 hours | ⏳ Planned |
| **Phase 3** | 190-200 SPs (95-99%) | ~4 hours | ⏳ Planned |

**Total Effort:** ~7 hours (1 day)
**Total Cost:** ~$0.03 per full parse

---

## Next Steps

1. **Review MASTER_PLAN.md** - Understand complete strategy
2. **Start Phase 1 Iteration 1** - Test no preprocessing baseline
3. **Run 5 iterations** - Test each pattern combination
4. **Document best result** - Select winning approach
5. **Proceed to Phase 2** - Implement AI fallback

---

## Getting Help

**Questions about:**
- Strategy → See MASTER_PLAN.md
- Current results → See docs/PHASE1_FINAL_RESULTS.md
- Failure analysis → See docs/ROOT_CAUSE_42_PERCENT.md
- Implementation → See lineage_v3/parsers/quality_aware_parser.py:131-167

**Tools:**
- Regression prevention → Use `/sub_DL_OptimizeParsing` subagent
- Testing → Use scripts in `scripts/` directory
- Validation → Check `/tmp/parse_output.log` for errors

---

**Last Updated:** 2025-11-02
**Maintainer:** Claude Code (Sonnet 4.5)
**Status:** Phase 1 ready to execute
