# Parser Change Management System

**Status**: 🟢 Fully Implemented (2025-10-28)

## Overview

This document explains the **Parser Change Management System** - a structured approach to prevent regression and ensure continuous improvement of SQL parser quality.

---

## Problem Statement

**Before this system:**
- Parser changes were made ad-hoc without tracking
- Regex patterns modified without measuring impact
- No way to know if changes helped or hurt overall quality
- Risk of "one step forward, two steps back" - fixing one SP breaks two others
- No historical record of what was tried and what worked

**Result**: Parser quality plateaus or regresses over time.

---

## Solution: Structured Change Management

### Three-Pillar System

#### 1. **Evolution Log** - [docs/PARSER_EVOLUTION_LOG.md](PARSER_EVOLUTION_LOG.md)
**Purpose**: Single source of truth for all parser changes

**Contents**:
- Baseline metrics (current parser performance)
- Change log (historical record of all modifications)
- Proposed changes (document BEFORE implementing)
- Known patterns requiring work
- Quality goals (short/medium/long-term targets)

**When to Use**:
- Before making ANY parser change (document proposal)
- After testing change (record actual results)
- Quarterly review (assess method effectiveness)

#### 2. **Regression Test** - [tests/parser_regression_test.py](../tests/parser_regression_test.py)
**Purpose**: Automated detection of quality regressions

**Features**:
- Capture baseline snapshots before changes
- Compare current results against baseline
- Flag any SPs that drop below 0.85 confidence
- Show improvements, regressions, and unchanged objects
- Exit with error code if regressions detected (CI/CD integration)

**Usage**:
```bash
# Before parser changes
python tests/parser_regression_test.py --capture-baseline baselines/baseline_YYYYMMDD.json

# After parser changes
python tests/parser_regression_test.py --compare baselines/baseline_YYYYMMDD.json
```

#### 3. **Guidelines in CLAUDE.md** - [CLAUDE.md:1267-1462](../CLAUDE.md#L1267-L1462)
**Purpose**: Enforced process for Claude Code when modifying parser

**Contents**:
- Mandatory 7-step process
- Parser architecture explanation
- Method effectiveness assessment framework
- Long-term strategy questions
- Current baseline metrics

**Enforcement**: Claude Code reads CLAUDE.md before every session, ensuring process is followed.

---

## The 7-Step Process

### Step 1: Document Issue (Before Coding)
**Action**: Update [docs/PARSER_EVOLUTION_LOG.md](PARSER_EVOLUTION_LOG.md) with "Proposed Changes" section

**Required Information**:
- What's broken? (specific SP name, symptoms)
- Why is it broken? (root cause analysis)
- Expected improvement (quantified: "spX: 0.50 → 0.85, outputs: 0 → 2")
- Potential risks (could this break other SPs?)

**Example**:
```markdown
### [Unreleased] - Proposed Changes

#### Issue #1: Missing TRUNCATE Support
**Impact**: 2+ SPs affected
**Root Cause**: _extract_from_ast() doesn't handle exp.TruncateTable
**Expected Improvement**: spLoadGLCognosData 0.50 → 0.85 (outputs: 0 → 2)
**Risk**: Low - TRUNCATE is new addition, won't affect existing parsing
```

### Step 2: Capture Baseline
**Action**: Save current parser state before making ANY changes

```bash
python tests/parser_regression_test.py --capture-baseline baselines/baseline_$(date +%Y%m%d).json
```

**Output**:
```
✓ Baseline captured: 16 stored procedures
  Average Confidence: 0.681
  High Confidence (≥0.85): 8 (50.0%)
✓ Saved to: baselines/baseline_20251028.json
```

**Why Critical**: Without baseline, you can't measure if your change helped or hurt.

### Step 3: Make Parser Changes
**Action**: Modify [lineage_v3/parsers/quality_aware_parser.py](../lineage_v3/parsers/quality_aware_parser.py)

**Requirements**:
- Update version number in docstring (e.g., 3.4.0 → 3.5.0)
- Add detailed comments explaining WHY (not just what)
- Keep changes focused (one issue per change)

**Example**:
```python
# Version: 3.5.0 - Add TRUNCATE support
# Issue: spLoadGLCognosData missing outputs due to TRUNCATE not being extracted
# Fix: Add TruncateTable extraction in _extract_from_ast()

for truncate in parsed.find_all(exp.TruncateTable):
    if truncate.this:  # truncate.this is the table node
        name = self._extract_dml_target(truncate.this)
        if name:
            targets.add(name)
```

### Step 4: Run Regression Test
**Action**: Re-run parser and compare against baseline

```bash
# Re-run parser
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# Compare
python tests/parser_regression_test.py --compare baselines/baseline_20251028.json
```

**Pass Criteria**:
- ✅ Zero regressions (no SP with ≥0.85 drops below 0.85)
- ✅ At least one SP improves as expected
- ✅ Average confidence ≥ baseline
- ✅ High confidence count ≥ baseline

**Example Output**:
```
📊 Overall Statistics:
   Total Objects: 16
   Regressions: 0 ✓
   Improvements: 2 ✓
   Unchanged: 14

📈 Confidence Metrics:
   Average: 0.681 → 0.728 (+0.047) 📈
   High Confidence (≥0.85): 8 → 10 (+2) 📈

✅ IMPROVEMENTS (2):
   spLoadGLCognosData            0.50       0.85       +0.35
   spLoadFactGLCOGNOS           0.85       0.95       +0.10

✅ REGRESSION TEST PASSED
```

### Step 5: Manual Validation
**Action**: Spot-check improved SPs to verify correctness

**Questions**:
1. Do the parsed inputs/outputs match manual SQL analysis?
2. Are there false positives? (tables that don't exist in code)
3. Are there false negatives? (tables that should be there but aren't)

**How**:
```bash
# Extract specific SP from lineage
python -c "
import json
data = json.load(open('lineage_output/frontend_lineage.json'))
sp = [n for n in data if n['name'] == 'spLoadGLCognosData'][0]
print('Inputs:', sp['inputs'])
print('Outputs:', sp['outputs'])
"
```

Then manually read the SQL and verify.

### Step 6: Update Documentation
**Action**: Record actual results in [docs/PARSER_EVOLUTION_LOG.md](PARSER_EVOLUTION_LOG.md)

**Move from "Proposed Changes" to "Change Log"**:
```markdown
### [3.5.0] - 2025-10-28

#### Enhancement: TRUNCATE Statement Support
**Impact**: 2 SPs improved

**Fix Applied**:
- Added exp.TruncateTable extraction in _extract_from_ast()
- TRUNCATE targets now properly captured as outputs

**Results**:
- spLoadGLCognosData: 0.50 → 0.85 ✓ (outputs: 0 → 2)
- spLoadFactGLCOGNOS: 0.85 → 0.95 ✓ (query log validated)
- Average confidence: 0.681 → 0.728 (+6.9%)
- High confidence SPs: 8 → 10 (+25%)
- No regressions ✓

**Lessons Learned**:
- TRUNCATE is commonly used in staging/load SPs
- AST extraction needs to cover ALL DML operations
- Easy win - simple fix, big impact
```

### Step 7: Commit with Descriptive Message
**Action**: Commit with structured message

**Format**:
```bash
git add lineage_v3/parsers/quality_aware_parser.py \
        docs/PARSER_EVOLUTION_LOG.md \
        baselines/baseline_20251028.json

git commit -m "Parser: Add TRUNCATE support - improves 2 SPs to high confidence

- Add TruncateTable extraction in _extract_from_ast() method
- spLoadGLCognosData: 0.50 → 0.85 (outputs: 0 → 2)
- spLoadFactGLCOGNOS: 0.85 → 0.95 (query log validated)
- Average confidence: 0.681 → 0.728 (+6.9%)
- Zero regressions in baseline SPs ✓
- Updated PARSER_EVOLUTION_LOG.md with results

Closes #issue-number"
```

---

## Method Effectiveness Tracking

### Purpose
Over time, answer these questions:
1. Is regex baseline still useful or just complexity?
2. Is SQLGlot the right parser or should we try alternatives?
3. Is query log validation adding value?

### How to Track

**After each parser change, add to Evolution Log**:
```markdown
### Method Effectiveness Analysis

**Regex Baseline**:
- Agreement with SQLGlot: 87% (14/16 SPs within ±10%)
- Disagreements: spLoadGLCognosData (regex found 3 tables, SQLGlot 0 due to bug)
- **Verdict**: Keep - caught SQLGlot TRUNCATE bug ✓

**SQLGlot Parser**:
- Success rate: 93% (15/16 SPs parsed without errors)
- High confidence (≥0.85): 10 SPs (62.5%)
- Known failure patterns: 11+ nested CTEs (1 SP)
- **Verdict**: Primary method - working well ✓

**Query Log Validation**:
- Validation rate: 68% (11/16 SPs appear in logs)
- Confidence boosts: 3 SPs (0.85 → 0.95)
- Disagreements: 0 (all validated matches parsed lineage)
- **Verdict**: High value - keep ✓
```

### Quarterly Review Questions

**Every 3 months, review in team meeting**:

1. **Regex vs SQLGlot**:
   - Trend: Is regex agreement improving or worsening?
   - Decision: If >95% agreement for 2+ quarters → Consider removing regex

2. **SQLGlot Performance**:
   - Trend: Is high-confidence % increasing?
   - Decision: If plateaus at <80% → Test alternative parsers

3. **Query Log Value**:
   - Trend: Is validation rate stable?
   - Decision: If drops <40% → Consider removing (low ROI)

4. **Preprocessing Effectiveness**:
   - Trend: Did recent preprocessing changes help?
   - Decision: If caused regressions → Roll back

---

## Success Metrics

### Current Baseline (2025-10-28)
- Total SPs: 16
- High Confidence (≥0.85): 8 (50%)
- Average Confidence: 0.681

### Short-Term Goals (Q1 2025)
- [ ] High Confidence: 50% → 75% (+4 SPs)
- [ ] Average Confidence: 0.681 → 0.80
- [ ] Document 3+ parser improvements in Evolution Log

### Medium-Term Goals (Q2 2025)
- [ ] High Confidence: 75% → 90%
- [ ] AI Fallback for remaining 10%
- [ ] Decide on regex baseline (keep/remove)

### Long-Term Goals (Q3 2025)
- [ ] High Confidence: 90%+
- [ ] Very High Confidence (0.95): 50%+
- [ ] Zero false positives (user validated)

---

## Anti-Patterns to Avoid

### ❌ Don't: Make "Quick Fixes" Without Process
**Problem**: Tempting to modify regex pattern without testing
**Result**: Breaks 3 SPs to fix 1 SP
**Solution**: Always follow 7-step process, even for "small" changes

### ❌ Don't: Skip Baseline Capture
**Problem**: "I'll remember what the scores were"
**Result**: Can't prove your change helped, can't detect regressions
**Solution**: Baseline capture takes 5 seconds - always do it

### ❌ Don't: Ignore Regressions
**Problem**: "It only regressed one SP, but improved three"
**Result**: Slowly degrades parser quality over time
**Solution**: Fix regressions before merging OR document as known issue

### ❌ Don't: Change Multiple Things at Once
**Problem**: "Let me fix TRUNCATE AND improve preprocessing together"
**Result**: Can't tell which change caused improvement/regression
**Solution**: One issue per PR, one change at a time

---

## Integration with CI/CD (Future)

**Proposed GitHub Actions workflow**:
```yaml
name: Parser Regression Test

on:
  pull_request:
    paths:
      - 'lineage_v3/parsers/**'

jobs:
  regression-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run parser
        run: python lineage_v3/main.py run --parquet parquet_snapshots/

      - name: Regression test
        run: |
          python tests/parser_regression_test.py \
            --compare baselines/baseline_latest.json

      - name: Comment results
        uses: actions/github-script@v5
        with:
          script: |
            // Post regression test results as PR comment
```

**Benefits**:
- Automatic regression detection on every PR
- Forces developer to fix regressions before merge
- Visible quality metrics in PR comments

---

## File Structure

```
ws-psidwh/
├── docs/
│   ├── PARSER_EVOLUTION_LOG.md       # Historical record of all changes
│   └── PARSER_CHANGE_MANAGEMENT.md   # This file (system overview)
│
├── tests/
│   └── parser_regression_test.py     # Automated regression detection
│
├── baselines/
│   ├── baseline_20251028.json        # Snapshot before TRUNCATE fix
│   ├── baseline_20251029.json        # After TRUNCATE fix
│   └── baseline_latest.json          # Symlink to most recent
│
├── lineage_v3/parsers/
│   ├── quality_aware_parser.py       # Main parser (modify with care!)
│   └── query_log_validator.py        # Query log validation
│
└── CLAUDE.md                          # Guidelines for Claude Code (lines 1267-1462)
```

---

## FAQ

### Q: What if I need to make an emergency fix?
**A**: Still follow the process, just expedite it:
1. Capture baseline (5 seconds)
2. Make fix
3. Run regression test (2 minutes)
4. If passes, commit and document ASAP
5. Update Evolution Log within 24 hours

### Q: What if my change causes a regression in 1 SP but improves 5 SPs?
**A**: Two options:
1. **Recommended**: Fix the regression before merging (root cause likely fixable)
2. **Acceptable**: Document in Evolution Log as known issue, create follow-up ticket

### Q: How often should we review method effectiveness?
**A**:
- **Quarterly** for strategic review (keep/remove methods)
- **After each change** for tactical tracking (did this specific change help?)

### Q: What if baseline is unavailable (e.g., parquet files expired)?
**A**:
- Use most recent baseline from `baselines/` directory
- Document in Evolution Log that baseline may be stale
- Re-capture fresh baseline ASAP

---

## References

- **Evolution Log**: [docs/PARSER_EVOLUTION_LOG.md](PARSER_EVOLUTION_LOG.md)
- **Regression Test**: [tests/parser_regression_test.py](../tests/parser_regression_test.py)
- **User Guide**: [docs/PARSING_USER_GUIDE.md](PARSING_USER_GUIDE.md)
- **Parser Code**: [lineage_v3/parsers/quality_aware_parser.py](../lineage_v3/parsers/quality_aware_parser.py)
- **Claude Guidelines**: [CLAUDE.md](../CLAUDE.md#L1267-L1462)

---

**Last Updated**: 2025-10-28
**Status**: 🟢 System Fully Operational
**Next Review**: 2025-11-28 (1 month)
