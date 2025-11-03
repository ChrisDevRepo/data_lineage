# Project Status - Data Lineage Visualizer v4.0.0

**Single Source of Truth for Project Status, Issues, and Action Items**

**Last Updated:** 2025-11-03
**Branch:** `feature/slim-parser-no-ai`
**Version:** 4.0.0 (Slim - No AI)

---

## 📊 Current Status

### Overview
- **Architecture:** Slim parser (Regex + SQLGlot + Rule Engine)
- **Dependencies:** None (removed Azure OpenAI)
- **Baseline:** `baseline_2025_11_03_v4_slim_no_ai` (263 objects)
- **Performance:** 155/263 (58.94%) high confidence
- **Goal:** 250/263 (95.05%) high confidence
- **Gap:** 95 objects need improvement

### Key Metrics (Baseline Evaluation)
| Metric | Regex | SQLGlot | Target |
|--------|-------|---------|--------|
| **High Confidence (≥0.85)** | 155/263 (58.94%) | 121/263 (46.01%) | 250/263 (95.05%) |
| **Micro F1** | 0.7882 | 0.7118 | 0.95+ |
| **Macro F1** | 0.7719 | 0.7085 | 0.95+ |

### System Health
- ✅ Frontend: Running, tested (smoke test passed)
- ✅ Backend: Running (port 8000, v4.0.0)
- ✅ Parser: Import successful, baseline created
- ✅ Evaluation: Tools working, reports generated

---

## 🔴 CRITICAL ISSUES (Fix Immediately)

### Issue #1: DECLARE Pattern Bug 🔥
**Severity:** HIGH | **Impact:** 10-20 SPs | **Status:** 🔴 KNOWN, NOT FIXED

**Problem:**
Greedy regex removes business logic from DECLARE to next semicolon (can be thousands of chars).

**Location:** `lineage_v3/parsers/quality_aware_parser.py:119`

**Current Code:**
```python
# Line 119 - THE PROBLEM
(r'\bDECLARE\s+@\w+\s+[^;]+;', '', 0),
```

**Impact:**
- Removes TRUNCATE, INSERT, SELECT statements
- Results in empty input/output arrays
- Confidence drops from 0.85+ to 0.5
- Blocks path to 95% goal

**Example:** `spLoadPrimaReportingSiteEventsWithAllocations`
- Expected: 5 inputs, 1 output
- Actual: 0 inputs, 0 outputs
- Lost: 11,649 chars of business logic

**Fix (Test Required):**
```python
# Match single line only (stop at newline or semicolon)
(r'\bDECLARE\s+@\w+\s+[^\n;]+(?:;|\n)', '', 0),
```

**Action Steps:**
1. Test fix with affected SPs
2. Run evaluation: `/sub_DL_OptimizeParsing run --mode full --baseline baseline_2025_11_03_v4_slim_no_ai`
3. Compare results: expect +10-20 objects to move from 0.5 → 0.85
4. Update baseline if successful
5. Document in PARSER_EVOLUTION_LOG.md

**References:**
- Full analysis: `docs/PARSER_ISSUE_DECLARE_PATTERN.md`
- Parser code: `lineage_v3/parsers/quality_aware_parser.py`

**Priority:** 🔴 IMMEDIATE (Week 1, Day 1)

---

### Issue #2: 108 Objects Below Confidence Threshold
**Severity:** HIGH | **Impact:** Blocks 95% goal | **Status:** 🟡 NEEDS ANALYSIS

**Problem:**
108 objects have confidence <0.85 (37% of total dataset).

**Breakdown:**
- Regex high confidence: 155/263 (58.94%) → 108 objects below
- SQLGlot high confidence: 121/263 (46.01%) → 142 objects below
- Need to improve: 95 objects minimum to reach 250/263 (95%)

**Action Steps:**
1. **Extract Low-Confidence List:**
```bash
jq '.objects[] | select(.regex.overall_f1 < 0.85) | {id: .object_id, name: .object_name, regex_f1: .regex.overall_f1, sqlglot_f1: .sqlglot.overall_f1}' optimization_reports/latest.json > temp/low_confidence_objects.json
```

2. **Categorize by Failure Pattern:**
   - DECLARE bug victims (Issue #1) → ~10-20 objects
   - Complex CTEs (11+ nested) → ~5-10 objects
   - MERGE statements → unknown
   - Dynamic SQL (EXEC sp_executesql) → unknown
   - Unqualified table names → unknown
   - Missing OUTPUT clauses → unknown

3. **Prioritize by Impact:**
   - Frequency: How many SPs affected?
   - Complexity: How hard to fix?
   - Value: How much confidence gain?

4. **Create Fix Plan:**
   - Group similar patterns
   - Implement targeted fixes
   - Measure improvement iteratively

**Expected Outcome:**
Categorized list of failure patterns with estimated fix effort and confidence gain.

**References:**
- Evaluation report: `optimization_reports/run_20251103_151848.json`
- Baseline: `evaluation_baselines/baseline_2025_11_03_v4_slim_no_ai.duckdb`

**Priority:** 🔴 IMMEDIATE (Week 1, Day 2-3)

---

## 🟡 HIGH PRIORITY (Weeks 1-4)

### Task #3: Enhance Regex Patterns
**Target:** +20-30 objects | **Timeline:** Weeks 2-3 | **Status:** ⏳ PENDING

**Why:** Regex currently outperforms SQLGlot (58.94% vs 46.01%)

**Focus Areas:**
1. **MERGE Statements**
   - Complex T-SQL construct with USING clause
   - Pattern: `MERGE INTO target USING source ON condition WHEN MATCHED...`

2. **OUTPUT Clauses**
   - INSERT/UPDATE/DELETE OUTPUT INTO @table / #table
   - Pattern: `INSERT ... OUTPUT inserted.* INTO @Results`

3. **Dynamic SQL**
   - EXEC sp_executesql with parameters
   - Pattern: `EXEC sp_executesql N'SELECT ... FROM ...'`

4. **Derived Tables**
   - Subqueries in FROM clause
   - Pattern: `FROM (SELECT ... FROM base_table) AS derived`

5. **Schema Inference**
   - Unqualified table names (assume dbo schema)
   - Pattern: `FROM Customers` → `FROM dbo.Customers`

**Implementation:**
- File: `lineage_v3/parsers/quality_aware_parser.py`
- Method: `_regex_scan()` lines 306-380
- Add patterns to existing source_patterns and target_patterns

**Testing:**
```bash
# Create test baseline
/sub_DL_OptimizeParsing init --name baseline_regex_improvements

# Before changes
/sub_DL_OptimizeParsing run --mode full --baseline baseline_regex_improvements

# Make changes to regex patterns

# After changes
/sub_DL_OptimizeParsing run --mode full --baseline baseline_regex_improvements

# Compare
/sub_DL_OptimizeParsing compare --run1 <before> --run2 <after>
```

**Success Criteria:**
- Zero regressions (no objects drop from ≥0.85 to <0.85)
- +20-30 objects gain confidence ≥0.85
- Total high confidence: 175-185/263 (67-70%)

**Priority:** 🟡 HIGH (Week 2-3)

---

### Task #4: Improve SQLGlot Preprocessing
**Target:** +15-25 objects | **Timeline:** Weeks 2-4 | **Status:** ⏳ PENDING

**Why:** SQLGlot underperforms (46% vs target 95%)

**Known Limitations:**
1. Complex CTEs (11+ nested) fail parsing
2. T-SQL specific syntax not fully supported
3. DECLARE bug affects preprocessing (see Issue #1)
4. BEGIN/END blocks sometimes confuse parser

**Improvement Areas:**

1. **Enhanced T-SQL Cleanup**
   - Review `_preprocess_ddl()` method (lines 568-633)
   - Add patterns for T-SQL constructs:
     - MERGE statements
     - OUTPUT clauses
     - WAITFOR statements
     - Transaction control (SAVE TRANSACTION)

2. **Better CTE Handling**
   - Current: Removes CTEs entirely
   - Better: Parse CTEs to understand nested references
   - Alternative: Keep CTE structure for SQLGlot

3. **Statement Splitting**
   - Review `_split_statements()` method (lines 635-655)
   - Handle T-SQL GO batches better
   - Preserve statement boundaries

4. **Error Recovery**
   - When SQLGlot fails, fallback to regex (already implemented)
   - Log parse failures for analysis
   - Consider alternative parsers for complex cases

**Alternative Parsers to Test:**
- `sqlparse` - Pure Python, more forgiving
- `moz-sql-parser` - Mozilla's SQL parser
- `pglast` - PostgreSQL parser (limited T-SQL support)

**Testing Strategy:**
Focus on specific failing SPs with known patterns.

**Success Criteria:**
- +15-25 objects gain confidence ≥0.85
- Complex CTEs handled better (measure separately)
- Total high confidence: 190-210/263 (72-80%)

**Priority:** 🟡 HIGH (Week 3-4)

---

### Task #5: Implement Rule Engine
**Target:** +10-20 objects | **Timeline:** Weeks 3-4 | **Status:** ❌ NOT STARTED

**Concept:**
Post-processing layer to clean, validate, and boost confidence of parsed results.

**Architecture:**
```python
class RuleEngine:
    """Post-processing rules for dependency cleanup and validation."""

    def __init__(self, workspace: DuckDBWorkspace):
        self.workspace = workspace
        self.catalog = self._load_catalog()

    def apply_rules(self, sources: Set[str], targets: Set[str], ddl: str,
                    quality_check: Dict) -> Tuple[Set[str], Set[str], float]:
        """
        Apply rules to clean and validate dependencies.

        Returns: (cleaned_sources, cleaned_targets, confidence_boost)
        """
        # 1. Schema inference (dbo default)
        sources = self._infer_schemas(sources)
        targets = self._infer_schemas(targets)

        # 2. Alias resolution (known table aliases)
        sources = self._resolve_aliases(sources)
        targets = self._resolve_aliases(targets)

        # 3. Catalog validation (remove invalid references)
        sources = self._validate_catalog(sources)
        targets = self._validate_catalog(targets)

        # 4. Confidence boost (regex + SQLGlot agreement)
        confidence_boost = self._calculate_boost(quality_check)

        return sources, targets, confidence_boost
```

**Rules to Implement:**

1. **Schema Inference Rules**
   - If table unqualified, assume `dbo` schema
   - Example: `Customers` → `dbo.Customers`

2. **Alias Resolution Rules**
   - Known table aliases from query logs
   - Example: `v_Customer` → `dbo.ViewCustomers`

3. **Catalog Validation Rules**
   - Remove tables not in object catalog
   - Flag suspicious references (typos, old tables)

4. **Confidence Boosting Rules**
   - If regex AND SQLGlot agree: boost by 0.05-0.10
   - If query log confirms: boost by 0.10 (see Task #6)
   - If catalog validated: baseline confidence maintained

5. **Pattern-Based Corrections**
   - Common patterns from production logs
   - Example: Staging tables always write to Consumption

**Integration Point:**
- File: `lineage_v3/parsers/quality_aware_parser.py`
- Method: `parse_object()` after line 196 (after confidence determination)

**Success Criteria:**
- +10-20 objects gain confidence ≥0.85
- No false positives introduced
- Total high confidence: 205-225/263 (78-86%)

**Priority:** 🟡 HIGH (Week 3-4)

---

## 🟢 MEDIUM PRIORITY (Months 2-3)

### Task #6: Integrate Query Log Validation
**Target:** +10-15 objects | **Timeline:** Month 2 | **Status:** ⚠️ CODE EXISTS, NOT INTEGRATED

**What Exists:**
- File: `lineage_v3/parsers/query_log_validator.py`
- Purpose: Cross-validate parsed dependencies with execution logs
- Boost: 0.85 → 0.95 confidence if validated

**What's Missing:**
Integration with evaluation pipeline and rule engine.

**Action Steps:**
1. Review `query_log_validator.py` implementation
2. Add validation step to rule engine (Task #5)
3. Update evaluation runner to include query log results
4. Measure accuracy improvement

**Expected Impact:**
- Objects validated by query logs: +0.10 confidence
- Estimated: 100+ SPs have query log evidence
- Could boost 10-15 objects from 0.85 → 0.95

**References:**
- Code: `lineage_v3/parsers/query_log_validator.py`
- Spec: `docs/QUERY_LOGS_ANALYSIS.md`

**Priority:** 🟢 MEDIUM (Month 2)

---

### Task #7: Performance Optimization
**Target:** Maintain 3-5x speed | **Timeline:** Month 2-3 | **Status:** ⏳ PENDING

**Current Performance:**
- Slim parser: ~0.5-1s per SP (vs 3-5s with AI)
- Incremental parsing: 50-90% faster for updates
- Evaluation run: ~5 seconds for 263 objects

**Optimization Areas:**

1. **Caching**
   - Cache parsed results by DDL hash
   - Skip re-parsing if DDL unchanged
   - Invalidate cache on definition updates

2. **Parallel Processing**
   - Process multiple SPs concurrently
   - Use ProcessPoolExecutor for CPU-bound work
   - Target: 2-4x speedup on multi-core

3. **Incremental Parsing**
   - Already implemented, but can optimize
   - Only re-parse: modified DDL + low confidence (<0.85)
   - Skip: high confidence + unchanged DDL

4. **DuckDB Query Optimization**
   - Add indexes on frequently queried columns
   - Optimize workspace queries
   - Use prepared statements

**Success Criteria:**
- Maintain current speed or improve
- Full evaluation: <10 seconds for 263 objects
- Incremental runs: <2 seconds for typical updates

**Priority:** 🟢 MEDIUM (Month 2-3, as needed)

---

## 🔵 LOW PRIORITY (Ongoing)

### Task #8: Update Documentation
**Timeline:** Ongoing | **Status:** ⏳ IN PROGRESS

**Completed:**
- ✅ `CLAUDE.md` - Updated for v4.0.0
- ✅ `README.md` - AI references removed
- ✅ `docs/V4_SLIM_PARSER_BASELINE.md` - Baseline results
- ✅ `docs/OPEN_ACTION_ITEMS.md` - Action tracking (superseded by this file)
- ✅ `PROJECT_STATUS.md` - This file (master document)

**Needs Update:**
- ⏳ `docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md` - Remove AI extraction references
- ⏳ `docs/PARSING_USER_GUIDE.md` - Review for v4.0.0 relevance
- ⏳ `api/README.md` - Update API version to 4.0.0
- ⏳ `frontend/README.md` - Confirm no AI references

**Action:** Update as parser evolves, not blocking.

**Priority:** 🔵 LOW (Ongoing)

---

### Task #9: Expand Test Coverage
**Timeline:** Ongoing | **Status:** ⏳ IN PROGRESS

**Current State:**
- ✅ Frontend smoke test: PASSED
- ⏳ Frontend full test suite: NOT RUN
- ⏳ Parser unit tests: MISSING
- ⏳ Integration tests: MINIMAL

**Test Priorities:**

1. **Parser Unit Tests** (HIGH)
   - Test regex patterns independently
   - Test SQLGlot preprocessing
   - Test rule engine (when implemented)
   - Coverage target: 80%+

2. **Integration Tests** (MEDIUM)
   - End-to-end parsing flow
   - Evaluation runner accuracy
   - Baseline creation/comparison

3. **Frontend Tests** (MEDIUM)
   - Full test suite with `/sub_DL_TestFrontend full`
   - Visual regression with `/sub_DL_TestFrontend visual`
   - Create new baselines if UI changes

**Action:** Add tests as features are implemented.

**Priority:** 🔵 LOW (Ongoing, increases with stability)

---

## 📅 Roadmap & Milestones

### Week 1 (CRITICAL) 🔴
**Focus:** Fix blocking issues, analyze problems

- [x] Create baseline (263 objects)
- [x] Run evaluation (58.94% high confidence)
- [x] GUI smoke test (PASSED)
- [ ] **Fix DECLARE bug** → +10-20 objects (Issue #1)
- [ ] **Analyze 108 low-confidence objects** (Issue #2)
- [ ] Quick wins from analysis

**Target:** 165-175/263 (63-67%) high confidence

---

### Weeks 2-3 (HIGH PRIORITY) 🟡
**Focus:** Enhance parsing methods

- [ ] Enhance regex patterns (Task #3) → +20-30 objects
- [ ] Improve SQLGlot preprocessing (Task #4) → +15-25 objects
- [ ] Test alternative parsers for complex CTEs

**Target:** 185-205/263 (70-78%) high confidence

---

### Weeks 3-4 (HIGH PRIORITY) 🟡
**Focus:** Add rule engine

- [ ] Design rule engine architecture (Task #5)
- [ ] Implement core rules (schema inference, aliases, validation)
- [ ] Test on evaluation set
- [ ] Measure improvement

**Target:** 195-225/263 (74-86%) high confidence

---

### Month 2 (MEDIUM PRIORITY) 🟢
**Focus:** Integration and optimization

- [ ] Integrate query log validation (Task #6) → +10-15 objects
- [ ] Performance optimization (Task #7)
- [ ] Edge case handling
- [ ] Documentation updates

**Target:** 210-240/263 (80-91%) high confidence

---

### Month 3 (REFINEMENT) 🟢
**Focus:** Reach 95% goal

- [ ] Iterate on rule engine with production feedback
- [ ] Handle remaining edge cases
- [ ] Comprehensive testing
- [ ] Production readiness

**Target:** 250+/263 (95%+) high confidence ✅ **GOAL REACHED**

---

## 📚 Documentation Index

### Primary Documents (Start Here)
- **THIS FILE** (`PROJECT_STATUS.md`) - Single source of truth
- `CLAUDE.md` - Developer guide for working with repo
- `README.md` - Project overview and quick start
- `docs/V4_SLIM_PARSER_BASELINE.md` - Baseline evaluation results

### Architecture & Specs
- `lineage_specs.md` - Parser specification
- `docs/DUCKDB_SCHEMA.md` - Database schema
- `docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md` - Evaluation tool spec (needs v4.0 update)

### Issue Documentation
- `docs/PARSER_ISSUE_DECLARE_PATTERN.md` - Issue #1 (DECLARE bug) detailed analysis
- `docs/PARSER_EVOLUTION_LOG.md` - Parser version history and lessons learned

### User Guides
- `docs/PARSING_USER_GUIDE.md` - SQL parsing best practices
- `docs/QUERY_LOGS_ANALYSIS.md` - Query log validation strategy
- `docs/SETUP/` - MCP tools and browser testing guides

### API & Frontend
- `api/README.md` - API documentation
- `frontend/README.md` - Frontend guide
- `frontend/docs/UI_STANDARDIZATION_GUIDE.md` - UI design system

### Evaluation & Testing
- `evaluation_baselines/` - Baseline snapshots (.duckdb files)
- `optimization_reports/` - Evaluation reports (.json files)
- `temp/` - Utility scripts (create_baseline.py, run_evaluation.py)

---

## 🔧 Key Files Reference

### Parser Core
```
lineage_v3/parsers/
├── quality_aware_parser.py  # Main parser (Regex + SQLGlot)
│   ├── _regex_scan()              # Lines 306-380 - Regex extraction
│   ├── _preprocess_ddl()          # Lines 568-633 - T-SQL cleanup
│   ├── _sqlglot_parse()           # Lines 382-410 - SQLGlot parsing
│   └── Line 119: DECLARE BUG 🔴   # Fix this!
├── query_log_validator.py   # Query log validation (not integrated)
└── __init__.py              # Module exports (updated for v4.0)
```

### Evaluation Tools
```
temp/
├── create_baseline.py       # Create evaluation baseline
└── run_evaluation.py        # Run Regex + SQLGlot evaluation

evaluation_baselines/
└── baseline_2025_11_03_v4_slim_no_ai.duckdb  # Current baseline

optimization_reports/
├── run_20251103_151848.json  # Latest evaluation
└── latest.json → run_20251103_151848.json
```

### Configuration
```
CLAUDE.md               # Instructions for Claude Code
.env                    # Environment variables (Azure OpenAI not needed)
.env.template           # Template for .env
```

---

## 🚀 Quick Start for Next Developer

### 1. Understand Current State
```bash
# Read this file first (PROJECT_STATUS.md)
# Then review baseline results
cat docs/V4_SLIM_PARSER_BASELINE.md

# Check evaluation report
jq '.summary' optimization_reports/latest.json
```

### 2. Fix DECLARE Bug (Issue #1)
```bash
# Edit parser
nano lineage_v3/parsers/quality_aware_parser.py
# Line 119: Change pattern to non-greedy

# Test fix
/sub_DL_OptimizeParsing run --mode full --baseline baseline_2025_11_03_v4_slim_no_ai

# Compare results (expect +10-20 objects improved)
```

### 3. Analyze Low-Confidence Objects (Issue #2)
```bash
# Extract list
jq '.objects[] | select(.regex.overall_f1 < 0.85)' optimization_reports/latest.json > temp/low_conf.json

# Categorize by pattern
# Group similar failure types
# Prioritize fixes
```

### 4. Iterate
```bash
# Make improvements
# Run evaluation
# Compare results
# Update PARSER_EVOLUTION_LOG.md
# Commit with evaluation proof
```

---

## 📞 Getting Help

### Documentation Questions
- Primary: This file (`PROJECT_STATUS.md`)
- Details: Referenced docs in Documentation Index section

### Parser Questions
- Issue #1: `docs/PARSER_ISSUE_DECLARE_PATTERN.md`
- History: `docs/PARSER_EVOLUTION_LOG.md`
- Best practices: `docs/PARSING_USER_GUIDE.md`

### Evaluation Questions
- Spec: `docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md`
- Results: `docs/V4_SLIM_PARSER_BASELINE.md`
- Reports: `optimization_reports/latest.json`

### Development Questions
- Guide: `CLAUDE.md`
- Git: Current branch `feature/slim-parser-no-ai`
- Testing: `/sub_DL_OptimizeParsing` and `/sub_DL_TestFrontend`

---

## ✅ Success Criteria

### Definition of Done (95% Goal)
- [ ] 250+ objects with confidence ≥0.85 (95.05%)
- [ ] Zero regressions from baseline
- [ ] All critical issues resolved
- [ ] Documentation updated
- [ ] Tests passing (frontend + parser)
- [ ] Performance maintained (<10s full evaluation)

### Code Quality Standards
- All parser changes evaluated with `/sub_DL_OptimizeParsing`
- Comparison reports prove improvements
- No commits without evaluation proof
- Update `docs/PARSER_EVOLUTION_LOG.md` for each change

### Monitoring
- Weekly evaluation runs
- Track progress toward 250/263 goal
- Document learnings and patterns
- Adjust roadmap based on results

---

**REMEMBER:**
- 🔴 Fix Issue #1 (DECLARE bug) FIRST - it's blocking ~10-20 objects
- 📊 Always run evaluation before committing parser changes
- 📝 Update this file as status changes
- 🎯 Focus on 95% goal: need 95 more objects from current 155

---

**Version:** 1.0
**Created:** 2025-11-03
**Last Updated:** 2025-11-03
**Next Review:** After Issue #1 fix
