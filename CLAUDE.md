# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion
- Use subagents for specialized validation tasks (see Subagents section)

## Project: Data Lineage Visualizer v4.3.3
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **Database:** Azure Synapse Analytics (T-SQL) - extensible to 7 data warehouses
- **Parser:** v4.3.3 ✅ **100% success rate** (349/349 SPs) + simplified rules + phantom fix
- **Confidence:** 82.5% perfect (100), 7.4% good (85), 10.0% acceptable (75)
- **Frontend:** v3.0.1 | **API:** v4.0.3

## ⚠️ BEFORE CHANGING PARSER - READ THIS
**Critical Reference:** [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md)
- WARN mode regression → empty lineage disaster
- RAISE mode is ONLY correct choice
- What NOT to change (defensive checks, regex patterns)
- Testing protocol to prevent regressions

**Technical Details:** [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)
**Complete Summary:** [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md)

## Recent Updates

### v4.3.3 - Frontend Filtering Enhancements (2025-11-13) 🎯
1. **Isolated Nodes Filter** - Hide nodes with no connections (degree = 0)
2. **Focus Schema Filtering** - Two-tier schema filtering (master vs extended)
3. **Star Icon UI** - Click ⭐ to designate focus schemas
4. **BFS Optimization** - Uses graphology-traversal where appropriate
5. **Correctness Testing** - Comprehensive test suite validates all implementations

**Features:**
- **Isolated Nodes:** Filter nodes with no connections in complete graph
- **Focus Schemas:** Always fully visible (master/anchor schemas)
- **Extended Schemas:** Filtered by reachability from focus when button enabled
- **Graph Traversal:** Manual BFS for focus filtering (multi-source + bidirectional)
- **Interactive Trace:** Uses graphology-traversal's `bfsFromNode` (single-source + unidirectional)
- **Scalability:** Production-ready for 10K nodes + 20K edges

**UX:**
- ⭐ Yellow star = focus schema (always visible)
- ☆ Gray star = extended schema (can be filtered)
- Filter button disabled until focus schema selected
- Clear tooltips explain behavior

**Technical Implementation:**
- **Focus Filtering:** Manual BFS (multi-source start, bidirectional traversal)
- **Interactive Trace:** graphology-traversal BFS (single-source, depth-limited, unidirectional)
- O(V + E) performance for both implementations
- See `docs/GRAPHOLOGY_BFS_ANALYSIS.md` for detailed analysis

**Testing:**
- ✅ test_focus_schema_filtering.mjs - 5/5 tests pass (prima example verified)
- ✅ test_interactive_trace_bfs.mjs - 4/4 tests pass (old vs new identical)
- ✅ Comprehensive edge case coverage (cycles, blocking, multiple focus)

**Result:** Powerful two-tier filtering, intuitive UX, optimized graph traversal ✅

### v4.3.3 - Simplified Rules + Phantom Fix (2025-11-12) ⭐
1. **Simplified SQL Cleaning:** 11 → 5 patterns (55% reduction, 75% less code)
2. **Phantom Function Filter:** Fixed to enforce include list
3. **Performance:** 54% faster preprocessing (fewer regex operations)
4. **Code Quality:** Eliminated create-then-remove conflicts
5. **Data Quality:** Removed 8 invalid phantom functions

**Changes:**
- Combined 6 conflicting DECLARE/SET patterns into 1 pattern
- Added `_schema_matches_include_list()` check to phantom functions
- Removed invalid schemas (AA, TS, U, ra, s) from database

**Result:** 100% success maintained, zero regressions, cleaner codebase ✅

### v4.3.2 - Defensive Improvements (2025-11-12) 🛡️
1. Empty Command Node Check - Prevents WARN mode regression
2. Performance Tracking - Logs slow SPs (>1 second)
3. SELECT Simplification - Object-level lineage only
4. SQLGlot Statistics - Per-SP success tracking
5. Golden Test Suite - Regression detection

**Result:** 100% success maintained, zero regressions ✅

## Quick Start

```bash
./start-app.sh  # Backend (8000) + Frontend (3000)
```

**First-time:** `pip install -r requirements.txt && ./start-app.sh`

## Key Directories

```
/
├── api/                    # FastAPI backend
├── frontend/               # React + React Flow UI
├── lineage_v3/             # Core parsing engine
│   ├── parsers/            # quality_aware_parser.py
│   ├── rules/              # YAML cleaning rules
│   └── config/             # Pydantic settings
├── scripts/testing/        # Validation tools
├── docs/                   # Documentation
│   ├── PARSER_CRITICAL_REFERENCE.md
│   ├── PARSER_TECHNICAL_GUIDE.md
│   └── reports/PARSER_ANALYSIS_V4.3.2.md
└── tests/                  # Test suite (73+ tests)
```

## Graph Library Usage (Graphology)

**Library:** [Graphology](https://graphology.github.io/) - Production-ready graph data structure
**Traversal:** [graphology-traversal](https://www.npmjs.com/package/graphology-traversal) - Optimized BFS/DFS algorithms

### ✅ When to Use graphology-traversal

**Use the library for graph traversal when:**
1. ✅ **Single source node** - Starting from 1 node
2. ✅ **Unidirectional traversal** - Going upstream OR downstream (not both)
3. ✅ **Depth-limited** - Stopping at specific levels
4. ✅ **Simple filtering** - Filter by node attributes

**Example: Interactive Trace** (`frontend/hooks/useInteractiveTrace.ts`)
```typescript
import { bfsFromNode } from 'graphology-traversal';

bfsFromNode(graph, startNode, (nodeId, attr, depth) => {
    if (!includedSchemas.has(attr.schema)) return true; // Skip
    if (depth >= maxLevels) return true; // Stop at depth
    visibleIds.add(nodeId);
    return false; // Continue
}, { mode: 'inbound' }); // or 'outbound'
```

### ⚠️ When to Use Manual Implementation

**Use manual BFS when:**
1. ⚠️ **Multiple source nodes** - Starting from 10+ nodes simultaneously
2. ⚠️ **Bidirectional traversal** - Going both upstream AND downstream at once
3. ⚠️ **Complex filtering** - Library workarounds would be more complex than simple loop

**Example: Focus Schema Filtering** (`frontend/hooks/useDataFiltering.ts`)
```typescript
const queue = Array.from(focusNodeIds); // Start from ALL focus nodes
while (queue.length > 0) {
    const nodeId = queue.shift()!;
    const neighbors = graph.neighbors(nodeId); // Bidirectional
    for (const neighbor of neighbors) {
        if (visibleIds.has(neighbor) && !reachable.has(neighbor)) {
            reachable.add(neighbor);
            queue.push(neighbor);
        }
    }
}
```

**Why manual here?**
- Library only accepts 1 starting node (not 10)
- Library mode is 'inbound' OR 'outbound' (not both)
- 12-line manual BFS is simpler than complex library workarounds

### 📚 Documentation

- **Analysis:** [docs/GRAPHOLOGY_BFS_ANALYSIS.md](docs/GRAPHOLOGY_BFS_ANALYSIS.md) - Detailed comparison & decision rationale
- **Tests:**
  - `frontend/test_interactive_trace_bfs.mjs` - Library BFS correctness
  - `frontend/test_focus_schema_filtering.mjs` - Manual BFS correctness

### 🎯 Best Practice

**Always prefer the library WHEN it makes code simpler.**
If library workarounds are more complex than a simple loop, use the loop.

## Configuration

**.env File:**
```bash
SQL_DIALECT=tsql  # Default (Synapse/SQL Server)
EXCLUDED_SCHEMAS=sys,dummy,information_schema,tempdb,master,msdb,model

# v4.3.3: REDESIGNED - Phantoms = EXTERNAL sources ONLY
PHANTOM_EXTERNAL_SCHEMAS=  # Empty = no external dependencies
# Examples: power_consumption,external_lakehouse,partner_erp

PHANTOM_EXCLUDE_DBO_OBJECTS=cte,cte_*,CTE*,ParsedData,#*,@*,temp_*,tmp_*
```

**Supported Dialects:**
- **tsql** (default) - SQL Server / Azure Synapse
- **bigquery** - Google BigQuery
- **snowflake** - Snowflake Data Cloud
- **fabric** - Microsoft Fabric
- **postgres** - PostgreSQL
- **redshift** - Amazon Redshift
- **oracle** - Oracle Database

See [CONFIGURATION_VERIFICATION_REPORT.md](docs/reports/CONFIGURATION_VERIFICATION_REPORT.md) for multi-database configuration.

## Parser Architecture (v4.3.3)

**Regex-First Baseline + SQLGlot Enhancement + Simplified Preprocessing**

1. **Regex Scan** - Full DDL, guaranteed baseline (100% coverage)
2. **SQLGlot Enhancement** - RAISE mode, optional bonus tables (50-80% of statements)
3. **UNION Strategy** - `sources.update()` adds new, keeps existing
4. **Post-Processing** - Remove system schemas, temp tables, non-persistent objects
5. **Confidence** - (found / expected) * 100 → {0, 75, 85, 100}

**Why 100% Success Despite SQLGlot Parsing Only 50-80%?**
- Regex baseline provides guaranteed coverage
- SQLGlot adds bonus (0-5 tables per SP average)
- UNION ensures regex baseline never lost

See [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md) for details.

## Parser Development Protocol

**MANDATORY: Test before and after changes**

```bash
# 1. Before changes - Document baseline
python3 scripts/testing/check_parsing_results.py > baseline_before.txt

# 2. Make changes to quality_aware_parser.py

# 3. Validate results
python3 scripts/testing/check_parsing_results.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt

# 4. Acceptance criteria
# - 100% success rate maintained
# - No regressions in confidence distribution
# - All tests pass: pytest tests/ -v
```

## SQL Cleaning Rules (Python-based)

**Active System:** 17 Python rules in `lineage_v3/parsers/sql_cleaning_rules.py`

### 🚨 MANDATORY Process for Rule Engine Changes

**⚠️ CRITICAL: Always check journal before making changes!**

```bash
# STEP 1: Check change journal (MANDATORY)
cat docs/PARSER_CHANGE_JOURNAL.md | grep -A 10 "DO NOT"
# Review past issues, root causes, and what NOT to change

# STEP 2: Document baseline (MANDATORY)
python3 scripts/testing/check_parsing_results.py > baseline_before.txt

# STEP 3: Make rule changes
# Edit lineage_v3/parsers/sql_cleaning_rules.py

# STEP 4: Run test suite (MANDATORY)
pytest tests/unit/test_parser_golden_cases.py -v  # Regression detection
pytest tests/unit/test_user_verified_cases.py -v  # User-reported cases
python3 scripts/testing/check_parsing_results.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt

# STEP 5: Acceptance criteria
# ✅ 100% success rate maintained
# ✅ No regressions in confidence distribution
# ✅ All user-verified tests pass
# ✅ Rule examples work correctly
# ✅ No new patterns added to "DO NOT" journal
```

**Add new rules:**
1. Edit `lineage_v3/parsers/sql_cleaning_rules.py`
2. Add new rule method (RegexRule or CallbackRule)
3. Register in `_load_default_rules()`
4. Test with built-in examples
5. Run full test suite (see process above)
6. Document in journal if fixing user-reported issue

Example:
```python
@staticmethod
def remove_print() -> RegexRule:
    return RegexRule(
        name="RemovePRINT",
        category=RuleCategory.COMMENT,
        pattern=r'PRINT\s+.*',
        replacement='',
        examples_before=["PRINT 'Debug'"],
        examples_after=[""]
    )
```

See [docs/PYTHON_RULES.md](docs/PYTHON_RULES.md) for complete documentation (17 rules, execution order, critical fixes).

### 🚨 MANDATORY Process for SQLGlot Settings Changes

**⚠️ CRITICAL: Changing ErrorLevel or dialect can break everything!**

```bash
# STEP 1: Check change journal (MANDATORY)
cat docs/PARSER_CHANGE_JOURNAL.md | grep -E "WARN|ErrorLevel|dialect"
# Review: WARN mode regression, ErrorLevel behavior

# STEP 2: Read critical reference (MANDATORY)
cat docs/PARSER_CRITICAL_REFERENCE.md | grep -A 20 "ErrorLevel"
# Understand: RAISE vs WARN vs IGNORE behavior

# STEP 3: Document baseline (MANDATORY)
python3 scripts/testing/check_parsing_results.py > baseline_before.txt

# STEP 4: Make SQLGlot changes
# Only change: lineage_v3/parsers/quality_aware_parser.py
# Settings: error_level, dialect, read_settings

# STEP 5: Run FULL test suite (MANDATORY)
pytest tests/unit/test_parser_golden_cases.py::TestErrorLevelBehavior -v
pytest tests/unit/test_user_verified_cases.py -v
python3 scripts/testing/check_parsing_results.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt

# STEP 6: Acceptance criteria (STRICT)
# ✅ 100% success rate maintained (NO EXCEPTIONS)
# ✅ NO SPs with empty lineage (inputs=[], outputs=[])
# ✅ ErrorLevel tests pass (RAISE mode behavior)
# ✅ All user-verified tests pass
# ✅ Confidence distribution unchanged or improved
```

**Never change without approval:**
- `ErrorLevel.RAISE` → Any other mode
- Dialect settings
- Parser read_settings
- Empty command node check

**If ANY test fails → ROLLBACK IMMEDIATELY**

## Testing & Validation

**Parser Validation:**
```bash
python3 scripts/testing/check_parsing_results.py  # Full results
python3 scripts/testing/analyze_lower_confidence_sps.py  # Why not 100%?
python3 scripts/testing/verify_sp_parsing.py  # Specific SP analysis
./scripts/testing/test_upload.sh  # API end-to-end
```

**Unit Tests:**
```bash
pytest tests/ -v  # 73+ tests, < 1 second
```

**Frontend E2E:**
```bash
cd frontend && npm run test:e2e  # 90+ tests
```

**User-Verified Tests:** `tests/unit/test_parser_golden_cases.py` - Detects regressions immediately

## Documentation

### Quick Reference
- **CLAUDE.md** (you are here) - Main project reference
- [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md) - Complete v4.3.3 summary

### Parser Documentation
**Critical (Read First):**
- [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md) - Critical warnings, what NOT to change
- [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md) - Complete technical reference
- [docs/PARSER_CHANGE_JOURNAL.md](docs/PARSER_CHANGE_JOURNAL.md) - Change history & regression prevention

**Analysis & Reports:**
- [docs/reports/CONFIGURATION_VERIFICATION_REPORT.md](docs/reports/CONFIGURATION_VERIFICATION_REPORT.md) - Multi-database support
- [docs/reports/DATABASE_SUPPORT_ASSESSMENT.md](docs/reports/DATABASE_SUPPORT_ASSESSMENT.md) - Database platform support
- [docs/reports/PHANTOM_FUNCTION_FILTER_BUG.md](docs/reports/PHANTOM_FUNCTION_FILTER_BUG.md) - Phantom function filter fix
- [docs/reports/PHANTOM_ORPHAN_ISSUE.md](docs/reports/PHANTOM_ORPHAN_ISSUE.md) - Phantom orphan handling
- [docs/reports/archive/README.md](docs/reports/archive/README.md) - Archived documentation

### Setup & Usage
- [docs/SETUP.md](docs/SETUP.md) - Installation guide
- [docs/USAGE.md](docs/USAGE.md) - Parser usage & troubleshooting
- [docs/REFERENCE.md](docs/REFERENCE.md) - API reference
- [docs/PYTHON_RULES.md](docs/PYTHON_RULES.md) - SQL cleaning rules documentation

### Testing & Quality
**User-Verified Cases:**
- [tests/fixtures/user_verified_cases/README.md](tests/fixtures/user_verified_cases/README.md) - User-reported bug → permanent test
- [tests/fixtures/user_verified_cases/case_template.yaml](tests/fixtures/user_verified_cases/case_template.yaml) - Template for new cases
- `tests/unit/test_user_verified_cases.py` - Automated test suite

**Validation Scripts:**
- `scripts/testing/run_baseline_validation.sh` - Automated regression detection (before/after/diff)
- `scripts/testing/check_parsing_results.py` - Full parser validation
- `scripts/testing/analyze_lower_confidence_sps.py` - Why not 100% confidence?
- `scripts/testing/verify_sp_parsing.py` - Analyze specific SP

### Development
- [docs/DEVELOPMENT_ACTION_LIST.md](docs/DEVELOPMENT_ACTION_LIST.md) - Master task list (53 tasks, 8 categories)
- [docs/GRAPHOLOGY_BFS_ANALYSIS.md](docs/GRAPHOLOGY_BFS_ANALYSIS.md) - Graph library usage analysis
- `.github/workflows/ci-validation.yml` - CI/CD pipeline configuration
- `.git/hooks/pre-commit` - Local quality gates

## Phantom Objects (v4.3.3 - REDESIGNED)

**What:** External dependencies NOT in our metadata database

**New Philosophy (v4.3.3):**
- Phantoms = **EXTERNAL sources only** (data lakes, partner DBs, external APIs)
- For schemas in OUR metadata DB, missing objects = DB quality issues (not phantoms)
- We are NOT the authority to flag internal missing objects

**Features:**
- Automatic detection from SP dependencies
- Negative IDs (-1 to -∞)
- Visual: 🔗 link icon for external dependencies, dashed borders
- Exact schema matching (no wildcards)
- Only schemas NOT in our metadata database
- Frontend shapes: 💎 Functions, 🟦 SPs, ⚪ Tables/Views

**Configuration:**
```bash
# Only list EXTERNAL schemas (not in our metadata DB)
PHANTOM_EXTERNAL_SCHEMAS=power_consumption,external_lakehouse,partner_erp
# Leave empty if no external dependencies
```

**Status:** ✅ Redesigned v4.3.3, external dependencies only

## Performance

**Current:** 500-node visible limit (prevents crashes)
**Target:** 10K nodes + 20K edges at acceptable performance
**Grade:** A- (production ready, correctness prioritized)

**Graph Engine:** Graphology v0.26.0
- Directed graph with O(1) neighbor lookup
- Efficient memory management for large graphs
- Manual BFS traversal (tested and verified for correctness)

**Filtering Performance (10K nodes):**
- Focus schema BFS traversal: ~15-20ms (manual implementation)
- Schema filtering: ~5-10ms (Set operations)
- Type filtering: ~3-5ms (Set operations)
- Total render pipeline: ~40-60ms → 15-25 FPS acceptable

**Correctness First:**
- Manual BFS used instead of library BFS (tested, verified correct)
- Comprehensive test suite (see frontend/test_bfs_comparison.mjs)
- Data lineage correctness > Performance optimization
- All filtering logic validated with real-world scenarios

**Optimizations:**
- React.memo, useCallback, useMemo (prevent re-renders)
- Debounced filtering (150ms for >500 nodes)
- Memoized graph construction (useGraphology hook)
- Set-based lookups (O(1) instead of O(n))
- Manual BFS with queue (O(V + E), proven correct)

See [docs/PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md) for details.

## Confidence Model v2.1.0

```python
completeness = (found / expected) * 100
if completeness >= 90: confidence = 100  # Perfect
elif completeness >= 70: confidence = 85   # Good
elif completeness >= 50: confidence = 75   # Acceptable
else: confidence = 0  # Poor
```

**Special Cases:** Orchestrators (only EXEC) → 100% | Parse failures → 0%

**Current Distribution:**
- 288 SPs (82.5%) → Confidence 100 ✅
- 26 SPs (7.4%) → Confidence 85 ✅
- 35 SPs (10.0%) → Confidence 75 ✅
- 0 SPs (0.0%) → Confidence 0

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port conflicts | `./stop-app.sh` |
| Missing dependencies | `pip install -r requirements.txt && cd frontend && npm install` |
| Low confidence | Add `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints |
| CORS errors | Check `ALLOWED_ORIGINS` in `.env` |
| Rule debugging | Set `debug.log_matches: true` in YAML rule |

See [docs/USAGE.md](docs/USAGE.md) for detailed troubleshooting.

## Git Guidelines

- Commit frequently (small, focused commits)
- Push to feature branches (never to main)
- Pull requests required for merging
- No rebasing or force pushing

## Subagents (Specialized Validators)

**Location:** `.claude/agents/` - 4 specialized subagents for validation tasks

### When to Use

| Subagent | Use When | Tools | Output |
|----------|----------|-------|--------|
| **parser-validator** | Modifying parser or rules | Read, Bash, Grep | Success rate, confidence distribution, APPROVE/REJECT |
| **rule-engine-reviewer** | Changing SQL cleaning rules | Read, Grep | Journal conflicts, safety assessment, recommendations |
| **baseline-checker** | Before/after parser changes | Bash, Read | Baseline capture, before/after comparison, PASS/FAIL |
| **doc-optimizer** | CLAUDE.md >300 lines | Read, Grep, Bash | Optimization targets, line reduction plan |

### Invocation

**Automatic:** Claude delegates matching tasks automatically

**Manual:**
```
"Use parser-validator to check my changes"
"Use rule-engine-reviewer for this rule"
"Use baseline-checker to capture baseline"
"Use doc-optimizer to reduce CLAUDE.md length"
```

### Example Workflow

```
1. User: "I'm going to modify DECLARE/SET rule"
2. Claude: [rule-engine-reviewer checks journal]
3. Claude: [baseline-checker captures baseline]
4. User: [Makes changes]
5. Claude: [parser-validator validates changes]
6. Result: APPROVE/REJECT with detailed analysis
```

**Details:** See `.claude/agents/README.md` for complete documentation

---

**Last Updated:** 2025-11-14
**Last Verified:** 2025-11-14 (v4.3.3)
**Version:** v4.3.3 ✅ Parser 100% success rate (349/349 SPs)

**Quick Links:**
- Complete Summary: [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md)
- Critical Reference: [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md)
- Technical Guide: [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)
- Configuration Verification: [docs/reports/CONFIGURATION_VERIFICATION_REPORT.md](docs/reports/CONFIGURATION_VERIFICATION_REPORT.md)
