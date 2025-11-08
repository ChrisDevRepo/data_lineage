# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

## Project: Data Lineage Visualizer v4.2.0
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **Parser:** v4.2.0 (95.5% accuracy, 97.0% on SPs)
- **Confidence:** v2.1.0 (4-value: 0, 75, 85, 100) | v2.0.0 (multi-factor) available
- **Frontend:** v2.9.2 | **API:** v4.0.3

## Quick Start

```bash
./start-app.sh  # Backend (8000) + Frontend (3000)
```

**Component-specific:**
```bash
cd api && python3 main.py              # Backend only
cd frontend && npm run dev             # Frontend only
python lineage_v3/main.py run --parquet parquet_snapshots/  # Parser
```

**First-time setup:**
```bash
pip install -r requirements.txt && ./start-app.sh
```

## Configuration

**Default works!** No .env needed for local development.

**Custom settings (optional):**
```bash
cp .env.example .env  # OR ./setup-env.sh
```

See [docs/guides/CONFIGURATION_GUIDE.md](docs/guides/CONFIGURATION_GUIDE.md) for details.

## Parser v4.2.0

**Strategy:** Regex → SQLGlot → Rule Engine
**Features:** Comment hints (@LINEAGE_*), incremental parsing, confidence scoring
**Performance:** 729/763 objects (95.5%), 196/202 SPs (97.0%)

### Parser Development (MANDATORY)

🚨 **ALWAYS use `/sub_DL_OptimizeParsing` for parser changes** 🚨

```bash
# 1. Create baseline before changes
/sub_DL_OptimizeParsing init --name baseline_YYYYMMDD_description
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_description

# 2. Make changes to quality_aware_parser.py

# 3. Evaluate after changes (MANDATORY)
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_description
/sub_DL_OptimizeParsing compare --run1 run_X --run2 run_Y

# 4. Pass criteria: Zero regressions, expected improvements
# 5. Update docs/reference/PARSER_EVOLUTION_LOG.md
```

**DO NOT:**
- Skip evaluation "because change is small"
- Commit parser changes without running subagent
- Rely on manual testing

## Sub-Agents

- **`/sub_DL_OptimizeParsing`** - Parser evaluation (precision/recall/F1)
- **`/sub_DL_TestFrontend`** - Browser testing (functional + visual regression)
- **`/sub_DL_Clean`** - Archive old docs, optimize CLAUDE.md
- **`/sub_DL_Build`** - Azure deployment
- **`/sub_DL_GitPush`** - Commit and push
- **`/sub_DL_Restart`** - Kill ports 3000/8000, restart servers

## Key Features

### Incremental Parsing
- DuckDB persists between runs
- Re-parses only modified/new + low confidence (<0.85) objects
- 50-90% faster than full refresh

### Confidence Model v2.1.0 (Default)

**4 discrete values:** 0, 75, 85, 100

```python
completeness = (found_tables / expected_tables) * 100
if completeness >= 90: confidence = 100
elif completeness >= 70: confidence = 85
elif completeness >= 50: confidence = 75
else: confidence = 0
```

**Special cases:**
- Orchestrators (only EXEC, no tables) → 100%
- Parse failures → 0%

**Source:** `ConfidenceCalculator.calculate_simple()`
**Spec:** [CONFIDENCE_MODEL_SIMPLIFIED.md](CONFIDENCE_MODEL_SIMPLIFIED.md)

### Confidence Model v2.0.0 (Legacy)

**5 weighted factors:** Parse Success (30%) + Method Agreement (25%) + Catalog Validation (20%) + Comment Hints (10%) + UAT (15%)
**Source:** `ConfidenceCalculator.calculate_multifactor()`

## Essential Documentation

**Getting Started:**
- [README.md](README.md) - Project overview
- [docs/guides/SETUP_AND_DEPLOYMENT.md](docs/guides/SETUP_AND_DEPLOYMENT.md) - Installation
- [docs/reference/SYSTEM_OVERVIEW.md](docs/reference/SYSTEM_OVERVIEW.md) - Architecture

**Guides:**
- [docs/guides/CONFIGURATION_GUIDE.md](docs/guides/CONFIGURATION_GUIDE.md) - Configuration
- [docs/guides/PARSING_USER_GUIDE.md](docs/guides/PARSING_USER_GUIDE.md) - SQL parsing
- [docs/guides/COMMENT_HINTS_DEVELOPER_GUIDE.md](docs/guides/COMMENT_HINTS_DEVELOPER_GUIDE.md) - @LINEAGE hints
- [docs/guides/MAINTENANCE_GUIDE.md](docs/guides/MAINTENANCE_GUIDE.md) - Troubleshooting

**Reference:**
- [docs/reference/PARSER_SPECIFICATION.md](docs/reference/PARSER_SPECIFICATION.md) - Parser spec
- [docs/reference/PARSER_EVOLUTION_LOG.md](docs/reference/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/reference/DUCKDB_SCHEMA.md](docs/reference/DUCKDB_SCHEMA.md) - Database schema
- [docs/reference/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/reference/SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Evaluation framework

**Component:**
- [api/README.md](api/README.md) - Backend API
- [frontend/README.md](frontend/README.md) - Frontend
- [requirements/README.md](requirements/README.md) - Dependencies

**Bug Tracking:**
- [BUGS.md](BUGS.md) - Known issues with business context and status

## Troubleshooting

**Port conflicts:** `./stop-app.sh`
**Missing dependencies:** `pip install -r requirements.txt && cd frontend && npm install`
**Low confidence:** Use `/sub_DL_OptimizeParsing` to analyze
**CORS errors:** Check `ALLOWED_ORIGINS` in `.env`

See [docs/guides/MAINTENANCE_GUIDE.md](docs/guides/MAINTENANCE_GUIDE.md) for detailed troubleshooting.

## Git Guidelines

- **Commit frequently** - Small, focused commits
- **Push to feature branches** - Never push directly to main
- **Pull requests required** - For merging to main
- **DON'T:** Rebase, force push, or merge without approval

## Scripts

| Script | Purpose |
|--------|---------|
| `start-app.sh` | Start backend + frontend |
| `stop-app.sh` | Stop all services (kill ports) |
| `setup-env.sh` | Interactive .env setup |

---

**Last Updated:** 2025-11-08
**Version:** v4.2.0
