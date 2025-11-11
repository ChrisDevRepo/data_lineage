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
- **Frontend:** v2.9.2 | **API:** v4.0.3

## Quick Start

```bash
./start-app.sh  # Backend (8000) + Frontend (3000)
```

**First-time setup:**
```bash
pip install -r requirements.txt && ./start-app.sh
```

## Configuration

**Default: Azure Synapse (T-SQL)**

All configuration in `.env`:
```bash
SQL_DIALECT=tsql  # Default (Synapse/SQL Server)
```

**Supported dialects** (data warehouses only):
- `tsql` - Azure Synapse, SQL Server, Azure SQL *(default)*
- `fabric` - Microsoft Fabric
- `postgres` - PostgreSQL data warehouses
- `oracle` - Oracle Database
- `snowflake` - Snowflake
- `redshift` - Amazon Redshift
- `bigquery` - Google BigQuery

## Documentation

**Essential:**
- [README.md](README.md) - Project overview & quickstart
- [docs/SETUP.md](docs/SETUP.md) - Installation, configuration, deployment
- [docs/USAGE.md](docs/USAGE.md) - Parser usage, hints, troubleshooting
- [docs/REFERENCE.md](docs/REFERENCE.md) - Technical specs, schema, API
- [docs/RULE_DEVELOPMENT.md](docs/RULE_DEVELOPMENT.md) - YAML rule creation & debugging ✨ NEW
- [BUGS.md](BUGS.md) - Issue tracking with business context

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
