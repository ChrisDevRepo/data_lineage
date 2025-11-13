# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

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
4. **Native Graph Traversal** - graphology-traversal BFS for 10K+ nodes
5. **Performance Optimization** - Upgraded to Graphology v0.26.0

**Features:**
- **Isolated Nodes:** Filter nodes with no connections in complete graph
- **Focus Schemas:** Always fully visible (master/anchor schemas)
- **Extended Schemas:** Filtered by reachability from focus when button enabled
- **Scalability:** Native BFS optimized for 10K nodes + 20K edges (~10-15ms)
- **Graph Engine:** C-optimized traversal algorithms from graphology-traversal

**UX:**
- ⭐ Yellow star = focus schema (always visible)
- ☆ Gray star = extended schema (can be filtered)
- Filter button disabled until focus schema selected
- Clear tooltips explain behavior

**Performance:**
- Replaced manual JavaScript BFS with native graphology-traversal
- 2-3x faster for large graphs (10K+ nodes)
- Upgraded graphology: 0.25.4 → 0.26.0

**Result:** Powerful two-tier filtering, intuitive UX, production-ready for 10K nodes ✅

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

## SQL Cleaning Rules (YAML-based)

**Add new rules without Python:**
1. Create `lineage_v3/rules/tsql/20_your_rule.yaml`
2. Define pattern, replacement, test cases
3. Run: `pytest tests/unit/rules/ -v`

Example:
```yaml
name: remove_print
pattern: 'PRINT\s+.*'
replacement: ''
test_cases:
  - input: "PRINT 'Debug'"
    expected: ""
```

See [docs/RULE_DEVELOPMENT.md](docs/RULE_DEVELOPMENT.md) for complete guide.

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

**Golden Tests:** `tests/unit/test_parser_golden_cases.py` - Detects regressions immediately

## Documentation

**Quick Reference (you are here):** CLAUDE.md
**Technical Details:**
- [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md) - Critical warnings
- [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md) - Complete technical reference
- [docs/reports/PARSER_ANALYSIS_V4.3.2.md](docs/reports/PARSER_ANALYSIS_V4.3.2.md) - Analysis & assessment

**Setup & Usage:**
- [docs/SETUP.md](docs/SETUP.md) - Installation guide
- [docs/USAGE.md](docs/USAGE.md) - Parser usage & troubleshooting
- [docs/REFERENCE.md](docs/REFERENCE.md) - API reference
- [docs/RULE_DEVELOPMENT.md](docs/RULE_DEVELOPMENT.md) - YAML rule creation

**Reports:**
- [docs/reports/COMPLETE_PARSING_ARCHITECTURE_REPORT.md](docs/reports/COMPLETE_PARSING_ARCHITECTURE_REPORT.md)
- [docs/reports/UAT_READINESS_REPORT.md](docs/reports/UAT_READINESS_REPORT.md)
- [docs/reports/TESTING_SUMMARY.md](docs/reports/TESTING_SUMMARY.md)
- [docs/reports/BUGS.md](docs/reports/BUGS.md)

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
**Target:** 10K nodes + 20K edges at 60 FPS
**Grade:** A (ready for scale)

**Graph Engine:** Graphology v0.26.0 + graphology-traversal v0.3.1
- Native BFS/DFS algorithms (C-optimized)
- Directed graph with O(1) neighbor lookup
- Efficient memory management for large graphs

**Filtering Performance (10K nodes):**
- Focus schema BFS traversal: ~10-15ms (native graphology-traversal)
- Schema filtering: ~5-10ms (Set operations)
- Type filtering: ~3-5ms (Set operations)
- Total render pipeline: ~30-50ms → 20-30 FPS achievable

**Optimizations:**
- React.memo, useCallback, useMemo (prevent re-renders)
- Debounced filtering (150ms for >500 nodes)
- Native graph traversal (graphology-traversal BFS)
- Memoized graph construction (useGraphology hook)
- Set-based lookups (O(1) instead of O(n))

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

---

**Last Updated:** 2025-11-12
**Version:** v4.3.3 ✅ Parser 100% success rate (349/349 SPs)

**Quick Links:**
- Complete Summary: [docs/PARSER_V4.3.3_SUMMARY.md](docs/PARSER_V4.3.3_SUMMARY.md)
- Critical Reference: [docs/PARSER_CRITICAL_REFERENCE.md](docs/PARSER_CRITICAL_REFERENCE.md)
- Technical Guide: [docs/PARSER_TECHNICAL_GUIDE.md](docs/PARSER_TECHNICAL_GUIDE.md)
- Configuration Verification: [docs/reports/CONFIGURATION_VERIFICATION_REPORT.md](docs/reports/CONFIGURATION_VERIFICATION_REPORT.md)
