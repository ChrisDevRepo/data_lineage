# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

## Project: Data Lineage Visualizer v4.1.3
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **System:** Python 3.12.3, Node.js, WSL2
- **Dir:** `/home/chris/sandbox`
- **Branch:** `feature/dataflow-mode`
- **Parser:** 97.0% SP confidence | 95.5% overall
- **Frontend:** v2.9.2

## Quick Start
```bash
# Backend: http://localhost:8000
cd /home/chris/sandbox/api && python3 main.py

# Frontend: http://localhost:3000
cd /home/chris/sandbox/frontend && npm run dev

# Parser (incremental / full-refresh)
python lineage_v3/main.py run --parquet parquet_snapshots/
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

## Parser (v4.1.3)
- **Strategy:** Regex → SQLGlot → Rule Engine
- **Performance:** 729/763 objects (95.5%), 196/202 SPs (97.0%)
- **Features:** Dataflow mode, global target exclusion, admin query filtering

## Parser Development (MANDATORY)

**🚨 ALWAYS use `/sub_DL_OptimizeParsing` for parser changes 🚨**

```bash
# 1. Before changes: Create baseline
/sub_DL_OptimizeParsing init --name baseline_$(date +%Y%m%d)_before_description
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description

# 2. Make changes to quality_aware_parser.py

# 3. After changes: Run evaluation (MANDATORY)
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description
/sub_DL_OptimizeParsing compare --run1 run_YYYYMMDD_HHMMSS --run2 run_YYYYMMDD_HHMMSS

# 4. Pass criteria: Zero regressions, expected improvements, progress toward 95%

# 5. Update docs/PARSER_EVOLUTION_LOG.md
```

**DO NOT:**
- Skip evaluation "because change is small"
- Commit parser changes without running subagent
- Rely on manual testing

---

## Sub-Agents

- **`/sub_DL_OptimizeParsing`** - Parser evaluation (precision/recall/F1)
- **`/sub_DL_TestFrontend`** - Browser testing (functional + visual regression)
- **`/sub_DL_Clean`** - Archive old docs, optimize CLAUDE.md
- **`/sub_DL_Build`** - Azure deployment package
- **`/sub_DL_GitPush`** - Commit and push to remote
- **`/sub_DL_Restart`** - Kill ports 3000/8000, restart servers

See [.claude/commands/](/.claude/commands/) for detailed docs.

---

## Key Features

### Incremental Parsing
- DuckDB persists between runs
- Re-parses only modified/new + low confidence objects (<0.85)
- 50-90% faster

### Parquet File Detection
- Auto-detects by schema
- Required: objects, dependencies, definitions
- Optional: query_logs, table_columns

### Confidence Model
| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| SQLGlot | 0.85 | Successfully parsed SPs |
| Regex | 0.50 | Failed parses |

### Quality Assurance
- **`check_unrelated_objects.py`** - Finds objects with no inputs AND outputs
  - Pattern analysis (INSERT, UPDATE, FROM, JOIN)
  - Export: `temp/unrelated_objects_report.json`

---

## Git Guidelines

- **Branch:** `feature/slim-parser-no-ai` | **Main:** `main`
- **DO:** Commit frequently, push to origin
- **DON'T:** Rebase, merge from other branches, merge to main (requires approval)

---

## Essential Documentation

**Start Here:**
- [README.md](README.md) - Project overview
- [lineage_specs.md](lineage_specs.md) - Parser spec
- [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) - **NEW** Architecture & components
- [docs/SETUP_AND_DEPLOYMENT.md](docs/SETUP_AND_DEPLOYMENT.md) - **NEW** Installation & deployment
- [docs/MAINTENANCE_GUIDE.md](docs/MAINTENANCE_GUIDE.md) - **NEW** Operations & troubleshooting

**Parser & Technical:**
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing guide
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema

**Evaluation:**
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Parser evaluation framework
- [evaluation_baselines/README.md](evaluation_baselines/README.md) - Baseline management

**Component-Specific:**
- [api/README.md](api/README.md) - Backend API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide
- [frontend/docs/UI_STANDARDIZATION_GUIDE.md](frontend/docs/UI_STANDARDIZATION_GUIDE.md) - UI design system
- [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md) - Performance optimizations

---

## Troubleshooting

**Import Errors:**
```bash
python lineage_v3/main.py validate

# Install all dependencies (production)
pip install -r requirements.txt

# Or install specific components
pip install -r requirements/parser.txt  # Parser only
pip install -r requirements/api.txt     # API only
pip install -r requirements/dev.txt     # Development tools
```

**Low Confidence (<0.85):**
- Use `/sub_DL_OptimizeParsing` to analyze quality
- Review [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
- Improve regex patterns + SQLGlot preprocessing

**Frontend Issues:**
- Check JSON path in Import Data modal
- Verify JSON format
- Check browser console

**Performance (Large Datasets >1,000 nodes):**
- **v2.9.1 optimizations:** Debouncing, layout caching, optimized filtering
- See [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md)
- **Supports 5,000+ nodes** smoothly (100x faster schema toggling)

**Port Conflicts:**
```bash
lsof -ti:8000 | xargs -r kill  # Backend
lsof -ti:3000 | xargs -r kill  # Frontend
```

---

**Last Updated:** 2025-11-06 (Repository Cleanup & Production Documentation)
**Version:** v4.1.3 (IF EXISTS Administrative Query Filtering)
**Parser:** 97.0% SP confidence | 95.5% overall | Dataflow mode + no circular dependencies
**Frontend:** v2.9.2 (Global exclusion patterns + UI simplified) | **API:** v4.0.3

**Recent Changes (2025-11-06):**
- ✅ Repository cleaned for production readiness
- ✅ Archived outdated development documents to docs/archive/2025-11-06/
- ✅ Removed experimental sqlglot_improvement/ directory
- ✅ Created comprehensive production documentation (SYSTEM_OVERVIEW, SETUP_AND_DEPLOYMENT, MAINTENANCE_GUIDE)
- ✅ Cleaned temp/ directory and optimization_reports/
