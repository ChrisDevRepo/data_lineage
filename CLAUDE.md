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

## Project: Data Lineage Visualizer v0.10.0
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **Database:** Azure Synapse Analytics (T-SQL) - extensible to 7 data warehouses
- **Data Sources:** Parquet files (default) OR Direct database connection (optional v0.10.0)
- **Parser:** v4.3.4 ✅ **100% parsing success** (349/349 SPs) | **71.3% catalog coverage** (249/349 with real dependencies)
- **Confidence:** 82.5% perfect (100), 7.4% good (85), 10.0% acceptable (75)
- **Frontend:** v0.10.0 | **API:** v0.10.0 | **License:** MIT
## ⚠️ BEFORE CHANGING PARSER - READ THIS
**Critical Reference:** [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md)
- WARN mode regression → empty lineage disaster
- RAISE mode is ONLY correct choice
- What NOT to change (defensive checks, regex patterns)
- Testing protocol to prevent regressions
**Technical Details:** [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)
**Complete Summary:** [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md)

## Recent Updates

### v0.10.0 - Database Direct Connection (2025-11-19) 🔌
- **Direct Database Metadata Refresh:**
  - Optional feature for automated metadata extraction (disabled by default)
  - Connect directly to SQL Server/Synapse/Fabric without Parquet file generation
  - "Refresh from Database" button in Import modal (only shown when DB_ENABLED=true)
  - Same processing pipeline as Parquet upload (database → Parquet → lineage)
- **Incremental Refresh:**
  - Hash-based change detection (SHA2_256 of procedure definitions)
  - Only fetches and processes modified procedures
  - Metadata cache tracks previous hashes
  - Significant performance improvement for large databases
- **Connector Framework:**
  - Abstract base class + factory pattern for multi-database support
  - YAML-based query configuration (`engine/connectors/queries/{dialect}/metadata.yaml`)
  - T-SQL connector as reference implementation (pyodbc-based)
  - Extensible to PostgreSQL, Snowflake, Oracle, BigQuery, etc.
- **Security:**
  - Azure Key Vault integration for production secrets
  - Docker secrets support for containerized deployments
  - SSL/TLS enforcement, connection timeout configuration
  - Environment variables: `DB_ENABLED`, `DB_CONNECTION_STRING`, `DB_TIMEOUT`, `DB_SSL_ENABLED`
- **Documentation:**
  - Complete specification: [docs/DATABASE_CONNECTOR_SPECIFICATION.md](docs/DATABASE_CONNECTOR_SPECIFICATION.md)
  - Metadata contract for DBAs
  - Step-by-step connector implementation guide
  - Connection string examples for 5 databases
- **Result:** Enterprise-ready automated metadata extraction ✅

### v0.9.0 - Production-Ready Open Source Release (2025-11-19) 🚀
- **Developer Mode:**
  - Read-only panel with Logs viewer and YAML Rules browser
  - Access via Help → "For Developers" section (hidden by design)
  - Backend APIs: `/api/debug/logs`, `/api/rules/{dialect}`, `/api/rules/{dialect}/{filename}`, `/api/rules/reset/{dialect}`
  - Reset rules to defaults from pristine copies in `engine/rules/defaults/`
- **Enhanced DEBUG Logging:**
  - Per-object parsing logs show SQLGlot vs Regex fallback vs Hardcoded hints
  - Format: `[PARSE] schema.object: Path=[...] Regex=[...] SQLGlot=[...] Hints=[...] Final=[...] Confidence=X`
  - Only visible at DEBUG level (set `LOG_LEVEL=DEBUG` in `.env`)
- **Log File Cleanup:**
  - Auto-cleanup old logs based on retention policy (default: 7 days)
  - Triggered on data import/upload
  - Configurable via `LOG_RETENTION_DAYS` in `.env`
- **Runtime Modes:**
  - `RUN_MODE` environment variable: demo | debug | production
  - Helper properties: `settings.is_demo_mode`, `settings.is_debug_mode`, `settings.is_production_mode`
- **MIT License:**
  - Open source under MIT license
  - Copyright (c) 2025 Christian Wagner
- **Result:** Production-ready for open source distribution ✅

### v4.3.5 (2024-11-19) - SELECT INTO Support + Cleanup

**Bug Fix:** Added SELECT INTO target detection to simplified parser.

**Changes:**
- Fixed missing output detection for aggregation SPs using `SELECT...INTO`
- Removed AI placeholder code (unused columns and tracking)
- Fixed imports: `sql_cleaning_rules` → `simplified_rule_engine`
- Fixed DuckDB API calls: `execute_query()` → `connection.execute().fetchall()`

**Golden Record:**
- `case_002_aggregations_missing_outputs.yaml` - Documents SELECT INTO bug
- Will pass after database reparse with fix

**Validation:**
- ✅ Parser only uses catalog objects (no CTEs/temp tables/non-catalog)
- ✅ 855 unique object IDs in lineage, all validated against catalog
- ✅ 4 stale IDs found (objects deleted after parsing - expected)

### v4.3.4 (2024-11-19) - Complete Phantom Removal

**Major simplification:** Removed ~2000 lines of phantom object tracking code.

**Philosophy Change:**
- **Old:** Track external dependencies as "phantom" objects with negative IDs
- **New:** If not in catalog → filtered out (cleaner, simpler)

**What Was Removed:**
- Phantom detection, creation, and tracking logic
- `phantom_objects` and `phantom_references` tables
- `PhantomSettings` configuration
- Phantom promotion utility

**Impact:**
- Simpler architecture (no special cases)
- Better data quality signals (missing = incomplete metadata export)
- 71.3% catalog coverage (correct filtering of deleted tables)
- 100% parsing success maintained

### v4.3.3 - Trace Mode Enhancements + Phantom Handling (2025-11-17) 🎯
- **Trace Mode UX Improvements:**
  - Blue border highlights trace start node with distinctive visual indicator
  - "Trace Mode" badge in navbar with tooltip showing start node, upstream/downstream levels
  - Extended Filter Schema auto-disables on trace start, disabled during active trace
  - Extended Filter Schema button triggers fit view after filtering
  - Schema/type filtering fully functional during trace mode (AND logic with trace results)
- **Context Menu Improvements:**
  - "Start Tracing" option hidden when trace filter already applied
  - Phantom objects have no right-click context menu (cannot trace external dependencies)
- **Schema Dropdown Fixes:**
  - "None" button now clears all focus stars (⭐)
  - Unchecking schema auto-removes focus star if present
- **Golden Test Case Added:**
  - `case_001_consumption_powerbi_phantom.yaml` for spLoadFactLaborCostForEarnedValue_Post
  - Documents CONSUMPTION_POWERBI phantom detection requirements
- **Result:** Enhanced trace mode usability with clear visual feedback and consistent behavior ✅

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
├── engine/             # Core parsing engine
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
# Runtime mode (v0.9.0)
RUN_MODE=production  # demo | debug | production
LOG_LEVEL=INFO       # DEBUG shows per-object parsing details
LOG_RETENTION_DAYS=7 # Auto-cleanup old logs on import

# Database configuration
SQL_DIALECT=tsql  # Default (Synapse/SQL Server)
EXCLUDED_SCHEMAS=sys,dummy,information_schema,tempdb,master,msdb,model
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

## SQL Cleaning Rules (YAML-based v0.9.0)

**Active System:** 17 YAML rules in `engine/rules/tsql/` + multi-dialect support

**Key Features:**
- **Declarative YAML rules** - Power users can extend without Python
- **Pristine defaults** in `engine/rules/defaults/` for reset functionality
- **Multi-step patterns** for complex transformations
- **Developer Mode** - View, browse, and reset rules via GUI
- **Comprehensive testing** - Each rule has test cases

### 🚨 MANDATORY Process for Rule Engine Changes

**⚠️ CRITICAL: Always check journal before making changes!**
1. Check docs/PARSER_CHANGE_JOURNAL.md (MANDATORY)
2. Document baseline: `source venv/bin/activate && python scripts/testing/check_parsing_results.py > baseline_before.txt`
3. Make rule changes in `engine/rules/tsql/*.yaml` (or create new dialect directory)
4. Run tests: `source venv/bin/activate && pytest tests/unit/test_parser_golden_cases.py -v`
5. Compare: `diff baseline_before.txt baseline_after.txt`

**Acceptance Criteria:**
- ✅ 100% success rate maintained (NO EXCEPTIONS)
- ✅ NO regressions in confidence distribution
- ✅ All user-verified tests pass

See `engine/rules/README.md` for complete YAML rule documentation and examples.

### 🚨 MANDATORY Process for SQLGlot Settings Changes

**⚠️ CRITICAL: Changing ErrorLevel or dialect can break everything!**
- RAISE mode is ONLY correct choice
- Never change: ErrorLevel.RAISE, dialect settings, parser read_settings
- If ANY test fails → ROLLBACK IMMEDIATELY

See docs/PARSER_CHANGE_JOURNAL.md for past regressions and what NOT to change.

## Developer Mode (v0.9.0)

**Access:** Help (?) → "For Developers" section → "Open Developer Panel" button

**Features:**
- **Logs Tab:**
  - Last 500 log entries with color-coding (ERROR=red, WARNING=yellow, DEBUG=blue)
  - Refresh button for real-time updates
  - Useful for debugging parsing issues and rule application

- **YAML Rules Tab:**
  - Browse all rules for current dialect
  - View YAML content (read-only)
  - Shows: priority, enabled status, category
  - "Reset to Defaults" button (copies from `engine/rules/defaults/`)

**API Endpoints:**
```
GET  /api/debug/logs?lines=500&level=DEBUG
GET  /api/rules/{dialect}
GET  /api/rules/{dialect}/{filename}
POST /api/rules/reset/{dialect}
```

**Enhanced DEBUG Logging:**
Set `LOG_LEVEL=DEBUG` in `.env` to see per-object parsing details:
```
[PARSE] dbo.spMyProc: Path=[SQLGlot] Regex=[5S + 3T + 2SP] SQLGlot=[2S + 1T] Hints=[0In + 0Out] Final=[7S + 4T] Confidence=100
```

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

**📖 NEW: GitHub-Optimized Documentation (v0.10.0)**
- **README.md** - Scannable landing page with badges, Mermaid diagrams, tables (GitHub optimized)
- **QUICKSTART.md** - 5-10 min setup guide for power users & DBAs
- **docs/ARCHITECTURE.md** - Complete system architecture, data flow, parser details
- **docs/GITHUB_DOCUMENTATION_GUIDE.md** - Maintenance guide for documentation

**🚨 CRITICAL FILES - PROTECTED (DO NOT DELETE):**
- **docs/PARSER_DEVELOPMENT_PROCESS.md** ⭐ - Main workflow guide (Parse → Test → Fix → Document)
- **docs/PARSER_CRITICAL_REFERENCE.md** ⭐ - Critical warnings, read BEFORE parser changes
- **docs/PARSER_CHANGE_JOURNAL.md** ⭐ - MANDATORY: check before rule/SQLGlot changes
- **docs/PARSER_TECHNICAL_GUIDE.md** ⭐ - Complete technical architecture

**Protection:** Listed in `.claudeignore`. See `docs/README.md` for protection details and recovery procedures.

**Other Essential References:**
- docs/PARSER_V4.3.3_SUMMARY.md - Complete v4.3.3 summary
- docs/DATABASE_CONNECTOR_SPECIFICATION.md - DBA guide for direct database connection
- INVESTIGATION_COMPLETE.md - Latest investigation findings
- REPARSE_ITERATION_SUMMARY.md - Recent iteration results

**CI/CD & Testing:**
- .github/workflows/README.md - CI/CD workflows, validation requirements
- tests/integration/README.md - Integration tests (64 tests), running locally
- tests/fixtures/user_verified_cases/README.md - User-verified test cases

**Quick Access:**
- Setup: docs/SETUP.md | Usage: docs/USAGE.md | Architecture: docs/ARCHITECTURE.md
- Configuration: docs/reports/CONFIGURATION_VERIFICATION_REPORT.md

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

**Last Updated:** 2025-11-19
**Last Verified:** 2025-11-19 (v0.10.0)
**Version:** v0.10.0 ✅ Direct database connection + Parser 100% success rate (349/349 SPs)

**Quick Links:**
- **NEW:** Quick Start: [QUICKSTART.md](QUICKSTART.md) (5-10 min setup for power users & DBAs)
- **NEW:** Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (complete system documentation)
- **NEW:** GitHub Guide: [docs/GITHUB_DOCUMENTATION_GUIDE.md](docs/GITHUB_DOCUMENTATION_GUIDE.md)
- License: [LICENSE](LICENSE) (MIT)
- Database Connector: [docs/DATABASE_CONNECTOR_SPECIFICATION.md](docs/DATABASE_CONNECTOR_SPECIFICATION.md)
- YAML Rules: [engine/rules/README.md](engine/rules/README.md)
- Parser Summary: [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md)
- Critical Reference: [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md)
- Technical Guide: [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)
- CI/CD Workflows: [.github/workflows/README.md](.github/workflows/README.md)
- Integration Tests: [tests/integration/README.md](tests/integration/README.md)
- **Note:** Major development should be done in git branch and PR must be approved by user