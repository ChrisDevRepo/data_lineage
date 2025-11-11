# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

## Project: Data Lineage Visualizer v4.3.0
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **Database:** Azure Synapse Analytics (T-SQL) - extensible to other data warehouses
- **Parser:** v4.3.0 (95.5% accuracy, 97.0% on SPs, multi-dialect support)
- **Confidence:** v2.1.0 (4-value: 0, 75, 85, 100)
- **Frontend:** v3.0.0 | **API:** v4.0.3
- **Features:** Phantom Objects (v4.3.0), UDF Support, Performance-Optimized

## Quick Start

```bash
./start-app.sh  # Backend (8000) + Frontend (3000)
```

**First-time setup:**
```bash
pip install -r requirements.txt && ./start-app.sh
```

## Configuration (v4.3.0 - Pydantic Settings)

**Centralized configuration** via `.env` with type safety:

```bash
# SQL Dialect
SQL_DIALECT=tsql  # Default (Synapse/SQL Server)

# Global Schema Exclusion (v4.3.0)
EXCLUDED_SCHEMAS=sys,dummy,information_schema,tempdb,master,msdb,model

# Phantom Objects (v4.3.0)
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B
PHANTOM_EXCLUDE_DBO_OBJECTS=cte,cte_*,CTE*,ParsedData,#*,@*,temp_*,tmp_*
```

**Supported dialects** (data warehouses only):
- `tsql` - Azure Synapse, SQL Server, Azure SQL *(default)*
- `fabric` - Microsoft Fabric
- `postgres` - PostgreSQL data warehouses
- `oracle` - Oracle Database
- `snowflake` - Snowflake
- `redshift` - Amazon Redshift
- `bigquery` - Google BigQuery

**Configuration File:** `lineage_v3/config/settings.py` (Pydantic BaseSettings)

## Documentation

**Essential:**
- [README.md](README.md) - Project overview & quickstart
- [docs/SETUP.md](docs/SETUP.md) - Installation, configuration, deployment
- [docs/USAGE.md](docs/USAGE.md) - Parser usage, hints, troubleshooting
- [docs/REFERENCE.md](docs/REFERENCE.md) - Technical specs, schema, API
- [docs/RULE_DEVELOPMENT.md](docs/RULE_DEVELOPMENT.md) - YAML rule creation & debugging
- [BUGS.md](BUGS.md) - Issue tracking with business context

**Performance (v4.3.0):**
- [docs/PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md) - Current optimizations & benchmarks ✨ NEW
- [docs/REACT_FLOW_PERFORMANCE.md](docs/REACT_FLOW_PERFORMANCE.md) - React Flow guide for 5K-10K nodes ✨ NEW
- [UAT_READINESS_REPORT.md](UAT_READINESS_REPORT.md) - Phantom objects feature status ✨ NEW

## Parser v4.3.0

**Strategy:** Regex → SQLGlot → Rule Engine → Confidence
**Performance:** 729/763 objects (95.5%), 196/202 SPs (97.0%)
**Validation:** 1,067 production objects tested, ZERO regressions ✅

### MANDATORY: Parser Development Protocol

**Testing approach:**
1. **Before changes:** Document current parse success rate from `smoke_test_analysis.json`
2. **Make changes:** Update YAML rules in `lineage_v3/rules/tsql/` or dialect classes
3. **Test specific SPs:** Create test scripts to verify fixes on problematic stored procedures
4. **Run tests:** `pytest tests/integration/test_synapse_integration.py -v`
5. **Manual smoke test:** Re-run parser on full corpus, compare results
6. **Pass criteria:** Zero regressions + expected improvements

### SQL Cleaning Rules (YAML-based)

**Add new rules** (no Python required):
1. Create YAML file: `lineage_v3/rules/tsql/20_your_rule.yaml`
2. Define pattern and test cases
3. Run tests: `pytest tests/unit/rules/ -v`

**Example rule:**
```yaml
name: remove_print
description: Remove T-SQL PRINT statements
dialect: tsql
enabled: true
priority: 15

pattern: 'PRINT\s+.*'
replacement: ''

test_cases:
  - name: simple_print
    input: "PRINT 'Debug'"
    expected: ""
```

**Debug mode:**
```yaml
debug:
  log_matches: true
  log_replacements: true
  show_context_lines: 2
```

See [docs/RULE_DEVELOPMENT.md](docs/RULE_DEVELOPMENT.md) for complete guide.

## Confidence Model v2.1.0

**4 discrete values:** 0, 75, 85, 100

```python
completeness = (found_tables / expected_tables) * 100
if completeness >= 90: confidence = 100
elif completeness >= 70: confidence = 85
elif completeness >= 50: confidence = 75
else: confidence = 0
```

**Special cases:** Orchestrators (only EXEC) → 100% | Parse failures → 0%

## Phantom Objects & UDF Support (v4.3.0)

**Phantom Objects:** Database objects referenced in SQL but not in catalog metadata

**Features:**
- **Automatic detection** from stored procedure dependencies
- **Negative IDs** (-1 to -∞) to distinguish from real objects
- **Visual indicators:** Orange question mark badge, dashed borders
- **Include-list filtering:** Only create phantoms for configured schemas (CONSUMPTION*, STAGING*, etc.)
- **Universal exclusion:** System schemas (sys, dummy, information_schema) filtered globally

**Configuration:**
```bash
# Include schemas for phantom creation (wildcard support)
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B

# Exclude patterns in dbo schema (CTEs, temp tables)
PHANTOM_EXCLUDE_DBO_OBJECTS=cte,cte_*,CTE*,ParsedData,#*,@*,temp_*,tmp_*
```

**Database Tables:**
- `phantom_objects` - Stores phantom metadata with negative IDs
- `phantom_references` - Tracks which SPs reference each phantom

**Frontend:**
- 🔶 Orange question mark badge on phantom nodes
- 🔶 Dashed orange borders
- 💎 Diamond shape for Functions (UDFs, TVFs, etc.)
- 🟦 Square shape for Stored Procedures
- ⚪ Circle shape for Tables/Views

**UAT Status:** ✅ 223 phantoms exported, system schemas filtered, ready for testing

See [UAT_READINESS_REPORT.md](UAT_READINESS_REPORT.md) for details.

## Performance (v4.3.0)

**Current:** 500-node visible limit prevents browser crashes
**Target:** 5K-10K nodes for production with 60 FPS

**Optimizations Implemented:**
- ✅ All React components wrapped in React.memo
- ✅ All ReactFlow props properly memoized (useCallback, useMemo)
- ✅ Smart node prioritization (Phantoms > SPs > Functions > Tables)
- ✅ QuestionMarkIcon and CustomNode fully optimized

**Performance Grade:** **A-** (Excellent foundation, ready for scale)

**For Production Scale:**
- Remove 500-node limit after UAT validation
- Expected 45-60 FPS with current optimizations
- CSS optimizations available if needed

See [docs/PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md) and [docs/REACT_FLOW_PERFORMANCE.md](docs/REACT_FLOW_PERFORMANCE.md).

## Testing

**Run all tests:**
```bash
pytest tests/ -v  # 58 tests, < 3 seconds
```

**Test coverage:**
- Unit tests: 28 tests (dialect validation)
- Synapse integration: 11 tests (1,067 real objects)
- Total: 58 tests, ZERO regressions ✅

See [TESTING_SUMMARY.md](TESTING_SUMMARY.md) for details.

## Slash Commands

**Available:**
- `/sub_DL_Clean` - Archive old docs, optimize CLAUDE.md

**Planned:**
- `/sub_DL_OptimizeParsing` - Parser evaluation (precision/recall/F1)
- `/sub_DL_Build` - Azure deployment
- `/sub_DL_GitPush` - Commit and push
- `/sub_DL_Restart` - Kill ports 3000/8000, restart servers

## Troubleshooting

**Port conflicts:** `./stop-app.sh`
**Missing dependencies:** `pip install -r requirements.txt && cd frontend && npm install`
**Low confidence:** Add `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints
**CORS errors:** Check `ALLOWED_ORIGINS` in `.env`
**Rule debugging:** Set `debug.log_matches: true` in YAML rule

See [docs/USAGE.md](docs/USAGE.md) for detailed troubleshooting.

## Git Guidelines

- Commit frequently (small, focused commits)
- Push to feature branches (never to main)
- Pull requests required for merging
- No rebasing or force pushing

---

**Last Updated:** 2025-11-11
**Version:** v4.3.0
