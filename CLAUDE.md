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

### v4.3.3 - Frontend Filtering + Simplified Rules (2025-11-13) 🎯
- Isolated Nodes Filter, Focus Schema Filtering, Interactive Trace (BFS)
- Two-tier filtering, ⭐ UI for focus designation, 10K nodes ready
- Tests pass: 5/5 focus, 4/4 trace, edge cases covered
- **Result:** Powerful filtering + optimized graph traversal ✅

See docs/GRAPHOLOGY_BFS_ANALYSIS.md for technical details.

### v4.3.3 - Simplified Rules + Phantom Fix (2025-11-12) ⭐
- SQL patterns: 11 → 5 (55% reduction), phantom filter fixed
- 54% faster preprocessing, eliminated conflicts, removed 8 invalid schemas
- **Result:** 100% success maintained, zero regressions ✅

### v4.3.2 - Defensive Improvements (2025-11-12) 🛡️
- Empty command node check, performance tracking, SELECT simplification
- **Result:** 100% success, zero regressions ✅

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
1. Check docs/PARSER_CHANGE_JOURNAL.md (MANDATORY)
2. Document baseline: `python3 scripts/testing/check_parsing_results.py > baseline_before.txt`
3. Make rule changes in lineage_v3/parsers/sql_cleaning_rules.py
4. Run tests: `pytest tests/unit/test_parser_golden_cases.py -v`
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

**Essential References:**
- PARSER_CRITICAL_REFERENCE.md - Critical warnings, BEFORE making parser changes
- PARSER_TECHNICAL_GUIDE.md - Complete technical architecture
- PARSER_CHANGE_JOURNAL.md - MANDATORY: check before rule/SQLGlot changes
- PARSER_V4.3.3_SUMMARY.md - Complete v4.3.3 summary

**Quick Access:**
- Setup: docs/SETUP.md | Usage: docs/USAGE.md | API: docs/REFERENCE.md
- Configuration: docs/reports/CONFIGURATION_VERIFICATION_REPORT.md
- Performance: docs/PERFORMANCE_ANALYSIS.md
- User-Verified Tests: tests/fixtures/user_verified_cases/README.md

See docs/DOCUMENTATION.md for complete index.

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

See docs/PERFORMANCE_ANALYSIS.md for detailed metrics and optimization details.

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
- Configuration Verification: [docs/reports/CONFIGURATION_VERIFICATION_REPORT.md](docs/reports/CONFIGURATION_VERIFICATION_REPORT.md)
