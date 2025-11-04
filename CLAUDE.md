# CLAUDE.md

Instructions for Claude Code when working with this repository.

## Workflow Guidelines

- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Never proceed with ambiguous requirements
- Use TodoWrite tool; update immediately after task completion

---

## Project Overview

**Data Lineage Visualizer v4.1.2** - Slim parser for Azure Synapse with React visualization

- **Status:** Production (No AI)
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **System:** Python 3.12.3, Node.js, WSL2
- **Dir:** `/home/chris/sandbox`
- **Branch:** `feature/dataflow-mode`

---

## Quick Start

```bash
# Backend (http://localhost:8000)
cd /home/chris/sandbox/api && python3 main.py

# Frontend (http://localhost:3000)
cd /home/chris/sandbox/frontend && npm run dev

# CLI Parser
python lineage_v3/main.py run --parquet parquet_snapshots/  # Incremental
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

---

## Parser Architecture (v4.1.2)

**Three-Stage Strategy:**
1. **Regex Baseline**: Pattern matching (tables + SP calls)
2. **SQLGlot Parser**: AST parsing + smart semicolon normalization
3. **Rule Engine**: Quality checks (future)

**Current Performance:**
- **729/763 objects at high confidence (95.5%)** - ✅ VERIFIED
- **196/202 SPs at high confidence (97.0%)** - ✅ EXCEEDED 95% GOAL
- Coverage: 758/763 objects (99.3%)
- SP-to-SP lineage: 151 business dependencies tracked

**Latest Features (v4.1.2):**
- **Dataflow Mode**: Shows only DML operations (INSERT, UPDATE, DELETE, MERGE)
- **Global Target Exclusion**: Eliminates false positive inputs from DML targets
- **Administrative Query Filtering**: Removes SELECT COUNT, IF EXISTS, watermark queries
- **Clean Lineage Graphs**: No noise from housekeeping or error handling operations

---

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
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing guide

**API & Frontend:**
- [api/README.md](api/README.md)
- [frontend/README.md](frontend/README.md)
- [frontend/docs/UI_STANDARDIZATION_GUIDE.md](frontend/docs/UI_STANDARDIZATION_GUIDE.md)

**Evaluation:**
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md)
- [evaluation_baselines/README.md](evaluation_baselines/README.md)

**Additional:**
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md)
- [docs/QUERY_LOGS_ANALYSIS.md](docs/QUERY_LOGS_ANALYSIS.md)

---

## Troubleshooting

**Import Errors:**
```bash
python lineage_v3/main.py validate
pip install -r requirements.txt
```

**Low Confidence (<0.85):**
- Use `/sub_DL_OptimizeParsing` to analyze quality
- Review [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
- Improve regex patterns + SQLGlot preprocessing

**Frontend Issues:**
- Check JSON path in Import Data modal
- Verify JSON format
- Check browser console

**Port Conflicts:**
```bash
lsof -ti:8000 | xargs -r kill  # Backend
lsof -ti:3000 | xargs -r kill  # Frontend
```

---

**Last Updated:** 2025-11-04
**Version:** v4.1.2 (Global Target Exclusion Fix)
**Parser:** 97.0% SP confidence | 95.5% overall | Dataflow mode with false positive elimination
**Frontend:** v2.9.0 | **API:** v4.0.0
