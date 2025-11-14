# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Python Environment

**ALWAYS use the virtual environment for this project:**
```bash
source venv/bin/activate  # Always activate before running Python commands
```

All Python commands in this document assume the virtual environment is activated.

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
- **Frontend:** v1.0.0 | **API:** v4.0.3
## ⚠️ BEFORE CHANGING PARSER - READ THIS
**Critical Reference:** [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md)
- WARN mode regression → empty lineage disaster
- RAISE mode is ONLY correct choice
- What NOT to change (defensive checks, regex patterns)
- Testing protocol to prevent regressions
**Technical Details:** [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)
**Complete Summary:** [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md)

## Recent Updates

### v4.3.3 - CI/CD Workflows + Integration Tests (2025-11-14) 🚀
- Parser Validation Workflow: 5 automated jobs validate parser changes
- 64 pytest integration tests (database validation, confidence analysis, SQLGlot performance)
- Baseline comparison blocks regressions (confidence distribution)
- Tests skip gracefully in CI without workspace database
- **Result:** Comprehensive automated validation prevents regressions ✅

See .github/workflows/README.md and tests/integration/README.md for details.

### v4.3.3 - Frontend Filtering + Simplified Rules (2025-11-13) 🎯
- Isolated Nodes Filter, Focus Schema Filtering, Interactive Trace (BFS)
- Two-tier filtering, ⭐ UI for focus designation, 10K nodes ready
- Tests pass: 5/5 focus, 4/4 trace, edge cases covered
- **Result:** Powerful filtering + optimized graph traversal ✅

### v4.3.3 - Simplified Rules + Phantom Fix (2025-11-12) ⭐
- SQL patterns: 11 → 5 (55% reduction), phantom filter fixed
- 54% faster preprocessing, eliminated conflicts, removed 8 invalid schemas
- **Result:** 100% success maintained, zero regressions ✅

## Quick Start

```bash
./start-app.sh  # Backend (8000) + Frontend (3000)
```

**First-time:** `pip install -r requirements.txt && ./start-app.sh`

## Key Directories

```
/
├── .github/workflows/      # CI/CD pipelines (parser validation, PR checks)
├── api/                    # FastAPI backend
├── frontend/               # React + React Flow UI
├── lineage_v3/             # Core parsing engine
│   ├── parsers/            # quality_aware_parser.py, SQL cleaning rules
│   └── config/             # Pydantic settings
├── scripts/testing/        # Validation tools
├── docs/                   # Documentation
│   ├── PARSER_CRITICAL_REFERENCE.md
│   ├── PARSER_TECHNICAL_GUIDE.md
│   └── reports/
└── tests/                  # Test suite (137+ tests: 73 unit + 64 integration)
    ├── unit/               # Unit tests (parser, API, fixtures)
    └── integration/        # Integration tests (database validation, SQLGlot)
```

## Graph Library Usage (Graphology - Frontend)

**Decision:** Use [graphology-traversal](https://www.npmjs.com/package/graphology-traversal) when:
- Single source node (1 node, not 10+)
- Unidirectional traversal (upstream OR downstream, not both)
- Depth-limited traversal (stopping at specific levels)
- Simple node filtering (by attributes)

**Why Manual BFS for Focus Filtering:**
- Multiple source nodes (10+ focus nodes simultaneously)
- Bidirectional traversal (both upstream AND downstream)
- 12-line manual BFS simpler than complex library workarounds

**Best Practice:** Always prefer the library WHEN it makes code simpler. If library workarounds are more complex than a simple loop, use the loop.

See docs/GRAPHOLOGY_BFS_ANALYSIS.md for detailed comparison and code examples.
See frontend/test_*.mjs for correctness validation.

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
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_before.txt

# 2. Make changes to quality_aware_parser.py

# 3. Validate results
source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt

# 4. Acceptance criteria
# - 100% success rate maintained
# - No regressions in confidence distribution
# - All tests pass: source venv/bin/activate && pytest tests/ -v
```

## SQL Cleaning Rules (Python-based)

**Active System:** 17 Python rules in `lineage_v3/parsers/sql_cleaning_rules.py`

### 🚨 MANDATORY Process for Rule Engine Changes

**⚠️ CRITICAL: Always check journal before making changes!**
1. Check docs/PARSER_CHANGE_JOURNAL.md (MANDATORY)
2. Document baseline: `source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_before.txt`
3. Make rule changes in lineage_v3/parsers/sql_cleaning_rules.py
4. Run tests: `source venv/bin/activate && pytest tests/unit/test_parser_golden_cases.py -v`
5. Compare: `diff baseline_before.txt baseline_after.txt`

**Acceptance Criteria:**
- ✅ 100% success rate maintained (NO EXCEPTIONS)
- ✅ NO regressions in confidence distribution
- ✅ All user-verified tests pass

See docs/PYTHON_RULES.md for rule examples and complete documentation.

### 🚨 MANDATORY Process for SQLGlot Settings Changes

**⚠️ CRITICAL: Changing ErrorLevel or dialect can break everything!**
- RAISE mode is ONLY correct choice
- Never change: ErrorLevel.RAISE, dialect settings, parser read_settings
- If ANY test fails → ROLLBACK IMMEDIATELY

See docs/PARSER_CHANGE_JOURNAL.md for past regressions and what NOT to change.

## Testing & Validation

**CI/CD Workflows (Automated):**
- **Parser Validation** - Triggers on parser file changes, runs 5 jobs (unit tests, integration tests, baseline comparison)
- **CI Validation** - Full pipeline on every push (backend, frontend, E2E)
- **PR Validation** - Fast quality checks and parser change warnings

See `.github/workflows/README.md` for complete workflow documentation.

**Local Testing:**
```bash
# Unit tests (73 tests)
source venv/bin/activate && pytest tests/unit/ -v

# Integration tests (64 tests, requires workspace database)
source venv/bin/activate && pytest tests/integration/ -v

# All tests
source venv/bin/activate && pytest tests/ -v  # 137+ tests

# Single unit test file
source venv/bin/activate && pytest tests/unit/test_parser_golden_cases.py -v

# Single unit test
source venv/bin/activate && pytest tests/unit/test_parser_golden_cases.py::test_specific_case -v

# Single integration test module
source venv/bin/activate && pytest tests/integration/test_database_validation.py -v

# Frontend E2E (Playwright)
cd frontend && npm run test:e2e           # Run all E2E tests
cd frontend && npm run test:e2e:ui        # Interactive UI mode
cd frontend && npm run test:e2e:headed    # Watch tests run
cd frontend && npm run test:e2e:debug     # Debug mode

# Single E2E test
cd frontend && npx playwright test tests/e2e/smoke.spec.ts
```

**Parser Validation Scripts:**
```bash
source venv/bin/activate && python scripts/testing/check_parsing_results.py  # Full results
source venv/bin/activate && python scripts/testing/analyze_lower_confidence_sps.py  # Why not 100%?
source venv/bin/activate && python scripts/testing/verify_sp_parsing.py  # Specific SP analysis
./scripts/testing/test_upload.sh  # API end-to-end
```

**User-Verified Tests:** `tests/unit/test_parser_golden_cases.py` - Detects regressions immediately

**Integration Test Modules (64 tests):**
- `test_database_validation.py` - Overall statistics, confidence distribution (13 tests)
- `test_sp_parsing_details.py` - Phantom detection, table validation (8 tests)
- `test_confidence_analysis.py` - Why some SPs have lower confidence (11 tests)
- `test_sqlglot_performance.py` - SQLGlot enhancement impact (14 tests)
- `test_failure_analysis.py` - Root cause investigation (8 tests)
- `test_sp_deep_debugging.py` - Debugging workflows (10 tests)

See `tests/integration/README.md` for complete test documentation.

## Documentation

**🚨 CRITICAL FILES - PROTECTED (DO NOT DELETE):**
- **docs/PARSER_DEVELOPMENT_PROCESS.md** ⭐ - Main workflow guide (Parse → Test → Fix → Document)
- **docs/PARSER_CRITICAL_REFERENCE.md** ⭐ - Critical warnings, read BEFORE parser changes
- **docs/PARSER_CHANGE_JOURNAL.md** ⭐ - MANDATORY: check before rule/SQLGlot changes
- **docs/PARSER_TECHNICAL_GUIDE.md** ⭐ - Complete technical architecture

**Protection:** Listed in `.claudeignore`. See `docs/README.md` for protection details and recovery procedures.

**Other Essential References:**
- docs/PARSER_V4.3.3_SUMMARY.md - Complete v4.3.3 summary
- INVESTIGATION_COMPLETE.md - Latest investigation findings
- REPARSE_ITERATION_SUMMARY.md - Recent iteration results

**CI/CD & Testing:**
- .github/workflows/README.md - CI/CD workflows, validation requirements
- tests/integration/README.md - Integration tests (64 tests), running locally
- tests/fixtures/user_verified_cases/README.md - User-verified test cases

**Quick Access:**
- Setup: docs/SETUP.md | Usage: docs/USAGE.md | API: docs/REFERENCE.md
- Configuration: docs/reports/CONFIGURATION_VERIFICATION_REPORT.md

## Phantom Objects (v4.3.3)

**What:** External dependencies (data lakes, partner DBs) NOT in our metadata database

**Features:**
- Automatic detection from SP dependencies, negative IDs (-1 to -∞)
- Visual: 🔗 link icon, dashed borders
- Exact schema matching (no wildcards), only external schemas

**Configuration:**
PHANTOM_EXTERNAL_SCHEMAS=power_consumption,external_lakehouse,partner_erp

**Status:** ✅ Redesigned v4.3.3

## Performance

**Status:** 500-node visible limit | **Target:** 10K nodes + 20K edges | **Grade:** A-
**Engine:** Graphology v0.26.0 - Directed graph with O(1) neighbor lookup

**Correctness First:**
- Data lineage correctness prioritized over performance optimization
- Manual BFS used instead of library (tested, verified correct)
- Comprehensive test suite validates all implementations
- 40-60ms render pipeline → 15-25 FPS acceptable

**Optimizations:** React.memo, useCallback, useMemo, debounced filtering, memoized graph, Set-based lookups

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

**Available:** parser-validator, rule-engine-reviewer, baseline-checker, doc-optimizer
**Location:** .claude/agents/

**Automatic:** Claude delegates matching tasks automatically
**Manual:** "Use parser-validator to check my changes"

See .claude/agents/README.md for complete table, tools, and example workflows.

---

**Last Updated:** 2025-11-14
**Last Verified:** 2025-11-14 (v4.3.3)
**Version:** v4.3.3 ✅ Parser 100% success rate (349/349 SPs)

**Quick Links:**
- Complete Summary: [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md)
- Critical Reference: [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md)
- Technical Guide: [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)
- CI/CD Workflows: [.github/workflows/README.md](.github/workflows/README.md)
- Integration Tests: [tests/integration/README.md](tests/integration/README.md)
- Configuration Verification: [docs/reports/CONFIGURATION_VERIFICATION_REPORT.md](docs/reports/CONFIGURATION_VERIFICATION_REPORT.md)
- memorize major development should be done in git branch and the pr must be approved from user