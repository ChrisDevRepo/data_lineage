# Open Action Items - v4.0.0 Slim Parser

**Date:** 2025-11-03
**Branch:** `feature/slim-parser-no-ai`
**Last Updated:** Post-baseline creation

---

## 🔴 Critical Issues (Immediate)

### 1. DECLARE Pattern Bug (HIGH PRIORITY)
**File:** `lineage_v3/parsers/quality_aware_parser.py:119`
**Status:** 🔴 KNOWN ISSUE (Documented, Not Fixed)
**Impact:** Affects 10-20 SPs, removes business logic from DDL

**Problem:**
Greedy regex `\bDECLARE\s+@\w+\s+[^;]+;` removes everything from DECLARE to the next semicolon, which can span thousands of characters in T-SQL (where semicolons are optional).

**Result:**
- Empty input/output arrays
- Confidence drops to 0.5
- Missing TRUNCATE, INSERT, SELECT statements

**Proposed Solution:**
```python
# Current (line 119):
(r'\bDECLARE\s+@\w+\s+[^;]+;', '', 0),

# Fixed (match single line only):
(r'\bDECLARE\s+@\w+\s+[^\n;]+(?:;|\n)', '', 0),
```

**Next Steps:**
1. Test fix with affected SPs
2. Run evaluation to measure impact
3. Update baseline after fix

**Reference:** `docs/PARSER_ISSUE_DECLARE_PATTERN.md`

---

## 🟡 High Priority (Week 1)

### 2. Analyze Low-Confidence Objects
**Status:** ⏳ PENDING
**Target:** 108 objects below 0.85 threshold

**Current State:**
- Regex: 155/263 (58.94%) high confidence
- SQLGlot: 121/263 (46.01%) high confidence
- **Gap:** Need 95 more objects to reach 95% goal (250/263)

**Action Items:**
1. Extract list of low-confidence objects from evaluation report
2. Identify common failure patterns:
   - Complex CTEs (11+ nested)
   - Missing DECLARE fix (see Issue #1)
   - T-SQL specific syntax (MERGE, OUTPUT, etc.)
   - Dynamic SQL patterns
3. Categorize by failure type
4. Prioritize by impact (frequency × complexity)

**Tools:**
```bash
# Extract low-confidence objects
jq '.objects[] | select(.sqlglot.overall_f1 < 0.85) | {name: .object_name, f1: .sqlglot.overall_f1}' optimization_reports/latest.json | head -20
```

---

### 3. Enhance Regex Patterns
**Status:** ⏳ PENDING
**Priority:** HIGH (Regex outperforms SQLGlot: 58.94% vs 46.01%)

**Focus Areas:**
1. **MERGE statements** - Complex T-SQL construct
2. **OUTPUT clauses** - INSERT/UPDATE/DELETE OUTPUT
3. **Dynamic SQL** - EXEC sp_executesql patterns
4. **Subqueries in FROM** - Derived tables
5. **Unqualified table names** - Schema inference

**Next Steps:**
1. Review regex patterns in `quality_aware_parser.py:_regex_scan()`
2. Add test cases for each pattern type
3. Measure improvement with evaluation tool

---

### 4. Improve SQLGlot Preprocessing
**Status:** ⏳ PENDING
**Priority:** HIGH (SQLGlot currently 46% vs target 95%)

**Known Limitations:**
- Complex CTEs (11+ nested) fail parsing
- T-SQL specific syntax not fully supported
- DECLARE pattern bug (see Issue #1)

**Action Items:**
1. Review `_preprocess_ddl()` method
2. Add T-SQL specific cleanup patterns
3. Test with failing SPs
4. Consider alternative parsers for edge cases (sqlparse, moz-sql-parser)

---

## 🟢 Medium Priority (Weeks 2-4)

### 5. Implement Rule Engine
**Status:** ❌ NOT STARTED
**Target:** 70-80% high confidence (184-210 objects)

**Concept:**
Post-processing rules to clean and validate parsed dependencies:
- Schema inference rules (default to `dbo` if unqualified)
- Pattern-based corrections (known table aliases)
- Validation rules (check against catalog)
- Confidence boosting (regex + SQLGlot agreement)

**Design:**
```python
class RuleEngine:
    def apply_rules(self, sources, targets, ddl):
        # 1. Schema inference
        # 2. Alias resolution
        # 3. Catalog validation
        # 4. Confidence calculation
        return cleaned_sources, cleaned_targets, confidence_boost
```

**Next Steps:**
1. Design rule engine architecture
2. Implement basic rules
3. Test on evaluation set
4. Measure improvement

---

### 6. Query Log Validation Integration
**Status:** ⚠️ PARTIALLY IMPLEMENTED
**Current:** Exists in codebase but not integrated with slim parser

**Purpose:**
Cross-validate parsed dependencies with actual query execution logs (0.85 → 0.95 confidence boost).

**Files:**
- `lineage_v3/parsers/query_log_validator.py` (exists)
- Integration needed in evaluation pipeline

**Next Steps:**
1. Review query_log_validator implementation
2. Add to evaluation runner
3. Measure accuracy improvement
4. Document validation criteria

**Reference:** `docs/QUERY_LOGS_ANALYSIS.md`

---

## 🔵 Low Priority (Months 2-3)

### 7. Performance Optimization
**Status:** ⏳ PENDING
**Target:** Maintain 50-90% speed improvement with incremental parsing

**Areas:**
1. Caching parsed results
2. Parallel parsing for large batches
3. Incremental parsing optimizations
4. DuckDB query optimization

---

### 8. Update SUB_DL_OPTIMIZE_PARSING for v4.0
**Status:** ⚠️ NEEDS UPDATE
**Issue:** Documentation references AI extraction method (removed in v4.0)

**File:** `docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md`

**Changes Needed:**
1. Remove AI extraction references
2. Update to Regex + SQLGlot only
3. Update evaluation report format
4. Remove AI cost tracking

---

### 9. Testing & Documentation
**Status:** ⏳ ONGOING

**Frontend Tests:**
- ✅ Smoke test passed
- ⏳ Full test suite needed
- ⏳ Visual regression baselines

**Parser Tests:**
- ⏳ Unit tests for regex patterns
- ⏳ Unit tests for SQLGlot preprocessing
- ⏳ Integration tests with evaluation runner

**Documentation:**
- ✅ V4_SLIM_PARSER_BASELINE.md created
- ✅ CLAUDE.md updated
- ✅ README.md updated
- ⏳ PARSING_USER_GUIDE.md needs v4.0 review
- ⏳ API documentation needs update

---

## 📊 Progress Tracking

### Current Metrics (v4.0.0 Baseline)
- **Total Objects:** 263 (202 SPs + 61 Views)
- **High Confidence (Regex):** 155/263 (58.94%)
- **High Confidence (SQLGlot):** 121/263 (46.01%)
- **Target:** 250/263 (95.05%)
- **Gap:** ~95-108 objects

### Milestone Targets

| Milestone | Target | Objects | Timeline |
|-----------|--------|---------|----------|
| **Current** | Baseline | 155/263 (58.94%) | ✅ Done |
| **M1: Fix DECLARE** | +10-20 | 165-175/263 (63-67%) | Week 1 |
| **M2: Enhance Regex** | +20-30 | 185-205/263 (70-78%) | Weeks 2-3 |
| **M3: Rule Engine** | +10-20 | 195-225/263 (74-86%) | Weeks 3-4 |
| **M4: SQLGlot Improve** | +15-25 | 210-250/263 (80-95%) | Months 2-3 |
| **M5: Goal Reached** | 95%+ | 250+/263 (95%+) | Month 3 |

---

## 🎯 Recommended Priority Order

1. **Week 1 (Critical):**
   - Fix DECLARE pattern bug (#1)
   - Analyze low-confidence objects (#2)
   - Quick wins from pattern analysis

2. **Weeks 2-3 (High Priority):**
   - Enhance regex patterns (#3)
   - Improve SQLGlot preprocessing (#4)
   - Target: 70-80% high confidence

3. **Weeks 3-4 (Medium Priority):**
   - Implement rule engine (#5)
   - Integrate query log validation (#6)
   - Target: 80-90% high confidence

4. **Months 2-3 (Refinement):**
   - Performance optimization (#7)
   - Edge case handling
   - Documentation updates
   - Target: 95%+ high confidence

---

## 📝 Notes

- All action items tracked in evaluation baseline: `optimization_reports/run_20251103_151848.json`
- Parser changes MUST be evaluated with `/sub_DL_OptimizeParsing` before commit
- No regressions allowed: Objects ≥0.85 must stay ≥0.85
- Update `docs/PARSER_EVOLUTION_LOG.md` after each improvement

---

**Last Updated:** 2025-11-03
**Branch:** feature/slim-parser-no-ai
**Version:** 4.0.0 (Slim - No AI)
