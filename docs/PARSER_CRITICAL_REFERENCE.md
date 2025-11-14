# Parser Critical Reference - AVOID REGRESSIONS

**⚠️ READ THIS BEFORE CHANGING THE PARSER ⚠️**

---

## 🚨 The WARN Mode Disaster (What NOT to Do)

### What Happened
```python
# BEFORE (Working):
parsed = parse_one(stmt, dialect='tsql', error_level=ErrorLevel.RAISE)

# CHANGED TO (Broken):
parsed = parse_one(stmt, dialect='tsql', error_level=ErrorLevel.WARN)
```

### Result
- ✅ All SPs "passed" (no exceptions)
- ❌ **BUT lineage was COMPLETELY EMPTY** (no inputs, no outputs)
- ❌ Silent failure - looked like it worked, but data was useless

### Root Cause
```python
# WARN mode returns Command nodes with NO .expression
parsed = parse_one(stmt, error_level=ErrorLevel.WARN)
# Returns: exp.Command with parsed.expression = None

# Your code checked:
if parsed:  # ✅ True (Command exists)
    tables = extract(parsed)  # ❌ Returns [] (no expression = no tables)
```

**Result:** Every SP got `inputs=[]` and `outputs=[]` → Complete data loss

---

## ✅ SQLGlot ErrorLevel Modes - USE RAISE ONLY

```python
class ErrorLevel:
    IGNORE = auto()    # ❌ NEVER USE - Silently fails, no errors, returns garbage
    WARN = auto()      # ❌ NEVER USE - Returns empty Command nodes, silent data loss
    RAISE = auto()     # ✅ USE THIS - Fails fast with exception, fallback to regex works
    IMMEDIATE = auto() # ⚠️ TOO STRICT - Fails on first minor syntax issue
```

**RULE: ALWAYS USE `ErrorLevel.RAISE`**

### Why RAISE is Correct
1. **Explicit failures** - Throws exception if parsing fails
2. **Regex fallback works** - Your try/except catches it, uses regex baseline
3. **No silent data loss** - Either get tables OR exception (never empty)
4. **Proven in production** - Current 100% success rate uses RAISE

---

## ✅ Current Architecture (DO NOT CHANGE)

```
Step 1: REGEX SCAN (Guaranteed Baseline)
  ├─ Runs on FULL DDL (no splitting = no JOIN context loss)
  ├─ Patterns: FROM, JOIN, INSERT, UPDATE, DELETE, MERGE
  └─ Result: expected_tables count

Step 2: SQLGLOT ENHANCEMENT (Optional Bonus)
  ├─ Preprocess DDL (clean T-SQL syntax)
  ├─ Parse with ErrorLevel.RAISE (strict, fails fast)
  ├─ If exception → skip, regex already has it
  └─ Result: Additional tables found via AST

Step 3: COMBINE RESULTS
  ├─ sources = regex_sources ∪ sqlglot_sources
  ├─ targets = regex_targets ∪ sqlglot_targets
  └─ sources_final = sources - targets

Step 4: CONFIDENCE CALCULATION
  ├─ completeness = (found_tables / expected_tables) * 100
  ├─ ≥90% → 100
  ├─ 70-89% → 85
  ├─ 50-69% → 75
  └─ <50% OR parse failed → 0
```

**WHY THIS WORKS:**
- Regex provides **guaranteed baseline** (handles T-SQL quirks)
- SQLGlot provides **enhancement** (better precision on standard SQL)
- Combined = **best of both worlds**
- **Industry standard** (DataHub, LineageX use same approach)

---

## 🧪 Golden Test Cases (Detect Regressions)

**File:** `tests/unit/test_parser_golden_cases.py`

**Run before ANY parser change:**
```bash
pytest tests/unit/test_parser_golden_cases.py -v
```

**What it tests:**
1. **Specific SPs have correct inputs/outputs** (not empty!)
2. **ErrorLevel modes behave correctly** (RAISE vs WARN vs IGNORE)
3. **Confidence model returns {0, 75, 85, 100}** only
4. **Empty lineage regression** (detects WARN mode issue)

**If ANY test fails → REGRESSION DETECTED**

---

## ⚠️ Confidence Model (Keep it Simple)

```python
# SIMPLE 4-VALUE MODEL (v2.1.0)
completeness_pct = (found_tables / expected_tables) * 100

if parse_failed:
    confidence = 0
elif completeness_pct >= 90:
    confidence = 100
elif completeness_pct >= 70:
    confidence = 85
elif completeness_pct >= 50:
    confidence = 75
else:
    confidence = 0
```

**Values come from:**
- `expected_tables` = Regex baseline count (FULL DDL)
- `found_tables` = Combined regex + SQLGlot (validated against catalog)

**RULE: No complex formulas, no black box calculations**

---

## 🚫 What NOT to Change

### ❌ DO NOT change ErrorLevel from RAISE
```python
# ❌ WRONG - Causes empty lineage
error_level=ErrorLevel.WARN

# ❌ WRONG - Silently fails
error_level=ErrorLevel.IGNORE

# ✅ CORRECT - Fails fast, regex fallback works
error_level=ErrorLevel.RAISE
```

### ❌ DO NOT remove defensive checks
```python
# v4.3.2: Defensive check (KEEP THIS!)
if parsed and not (isinstance(parsed, exp.Command) and not parsed.expression):
    # Process AST
else:
    # Empty Command node, use regex baseline
```

### ❌ DO NOT simplify IF EXISTS regex
```python
# ✅ CORRECT - Handles nested parens: COUNT(*)
r'\bIF\s+EXISTS\s*\((?:[^()]|\([^()]*\))*\)\s*'

# ❌ WRONG - Breaks on COUNT(*), stops at first )
r'\bIF\s+EXISTS\s*\([^)]*\)\s*'
```

### ❌ DO NOT remove DECLARE/SET filtering
```python
# v4.1.2 FIX - Prevents false positive inputs (KEEP THIS!)
r'DECLARE\s+(@\w+)\s+(\w+(?:\([^\)]*\))?)\s*=\s*\((?:[^()]|\([^()]*\))*\)'
```

---

## ✅ Testing Protocol (Before ANY Change)

### 1. Record Baseline
```bash
python3 scripts/testing/check_parsing_results.py > baseline_before.txt
```

### 2. Make ONE Change at a Time
- Never change multiple things at once
- Test after each change
- Rollback immediately if regression

### 3. Run Golden Tests
```bash
pytest tests/unit/test_parser_golden_cases.py -v
```

### 4. Validate Results
```bash
python3 scripts/testing/check_parsing_results.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt
```

### 5. Acceptance Criteria
- ✅ Success rate: 100% (maintained)
- ✅ No SPs with empty lineage (inputs=[], outputs=[])
- ✅ Confidence distribution: Unchanged or improved
- ✅ All golden tests pass

**If ANY criterion fails → ROLLBACK IMMEDIATELY**

---

## 📊 Current Metrics (Baseline)

**Version:** v4.3.3
**Success Rate:** 100% (349/349 SPs with dependencies)
**Confidence Distribution:**
- 100: 82.5% (288 SPs)
- 85: 7.4% (26 SPs)
- 75: 10.0% (35 SPs)

**Average per SP:**
- Inputs: 3.20
- Outputs: 1.87

**Verified Test SPs:**
- spLoadFactLaborCostForEarnedValue_Post (confidence 100)
- spLoadDimTemplateType (confidence 100)

---

## 🎯 Quick Decision Guide

**Someone suggests changing ErrorLevel?**
→ ❌ NO. RAISE is correct, WARN/IGNORE cause empty lineage.

**Someone suggests "simplifying" regex patterns?**
→ ⚠️ RISKY. Current patterns handle edge cases (nested parens, balanced brackets).
→ Test with golden test suite before accepting.

**Someone suggests replacing _extract_from_ast?**
→ ❌ NO. 124 lines of battle-tested edge case handling.

**Performance issue with parsing?**
→ ✅ YES. Check logs for slow SPs (>1 second), optimize those specific cases.

**New confidence model suggestion?**
→ ⚠️ QUESTION IT. Current model is simple (4 values) and transparent.
→ Complexity often hides flaws. Keep it simple.

**SQLGlot failing to parse complex SP?**
→ ✅ EXPECTED. Regex baseline handles it. Don't "fix" by changing error_level.

---

## 🔍 Red Flags (Signs of Regression)

### 🚨 CRITICAL RED FLAGS
1. **All SPs suddenly "pass"** but lineage looks empty
   → WARN/IGNORE mode activated, immediate rollback

2. **Success rate drops** below 100%
   → Something broke the regex baseline, investigate immediately

3. **Confidence distribution shifts** dramatically (e.g., all become 0 or 100)
   → Confidence calculation broken, rollback

### ⚠️ WARNING FLAGS
1. **Test SPs change** (spLoadFactLaborCostForEarnedValue_Post, spLoadDimTemplateType)
   → Run golden tests immediately

2. **New pattern of parse errors** in logs
   → Preprocessing may have broken, check cleaned DDL

3. **Performance degradation** (parsing takes >5 seconds)
   → Check if regex patterns became too complex

---

## 📝 When to Update This Document

**Update this document if:**
1. New ErrorLevel mode discovered (document behavior)
2. New regression pattern found (add to Red Flags)
3. Golden test cases change (update metrics)
4. Architecture changes (update flow diagram)

**Version this document:** Increment when major learnings added

**Current Version:** 1.0 (2025-11-12)

---

## 🎓 Lessons Learned

1. **"All tests pass" ≠ "Code is correct"**
   - WARN mode made all tests pass, but data was empty
   - Always validate ACTUAL outputs, not just absence of errors

2. **Silent failures are the worst**
   - WARN/IGNORE modes fail silently
   - Prefer loud failures (RAISE mode) with explicit fallbacks

3. **Regex-first is industry best practice**
   - Not a hack, not a workaround
   - DataHub, LineageX, and others use same approach
   - SQLGlot can't handle all T-SQL quirks

4. **Simple is better than complex**
   - 4-value confidence model (0, 75, 85, 100) is transparent
   - Complex multi-factor models hide flaws
   - Users understand percentage-based bucketing

5. **Golden test cases save time**
   - One regression test prevents hours of debugging
   - Test specific SPs with known correct outputs
   - Catch regressions before they reach production

---

**Remember:** This parser has 100% success rate. Changes should be defensive only.

**Last Verified:** 2025-11-14 (v4.3.3)
