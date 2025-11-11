# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

## Project: Data Lineage Visualizer v4.2.0
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **Parser:** v4.2.0 (95.5% accuracy, 97.0% on SPs)
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

## Documentation

**Essential:**
- [README.md](README.md) - Project overview & quickstart
- [docs/SETUP.md](docs/SETUP.md) - Installation, configuration, deployment
- [docs/USAGE.md](docs/USAGE.md) - Parser usage, hints, troubleshooting
- [docs/REFERENCE.md](docs/REFERENCE.md) - Technical specs, schema, API
- [docs/RULE_ENGINE.md](docs/RULE_ENGINE.md) - SQL cleaning rules (17 rules, +27% success)
- [BUGS.md](BUGS.md) - Issue tracking with business context

## Parser v4.2.0

**Strategy:** Regex → SQLGlot → Rule Engine → Confidence
**Performance:** 729/763 objects (95.5%), 196/202 SPs (97.0%)

### MANDATORY: Parser Development Protocol

**Testing approach:**
1. **Before changes:** Document current parse success rate from `smoke_test_analysis.json`
2. **Make changes:** Update `lineage_v3/parsers/sql_cleaning_rules.py` or `quality_aware_parser.py`
3. **Test specific SPs:** Create test scripts to verify fixes on problematic stored procedures
4. **Manual smoke test:** Re-run parser on full corpus, compare results
5. **Pass criteria:** Zero regressions + expected improvements

**Rule Engine Development:**
- See [docs/RULE_ENGINE.md](docs/RULE_ENGINE.md) for rule implementation guide
- Test new rules with `rule.test()` before deploying
- Use verbose mode during development: `engine.apply_all(sql, verbose=True)`

**Note:** `/sub_DL_OptimizeParsing` evaluation framework is planned but not yet implemented.

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

See [docs/USAGE.md](docs/USAGE.md) for detailed troubleshooting.

## Git Guidelines

- Commit frequently (small, focused commits)
- Push to feature branches (never to main)
- Pull requests required for merging
- No rebasing or force pushing

---

**Last Updated:** 2025-11-11
**Version:** v4.2.0
