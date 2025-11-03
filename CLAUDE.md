# CLAUDE.md

## Workflow

- End responses with status (✅ Done | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last, complete analysis first
- Use TodoWrite tool, update after each task
- **KEEP ROOT CLEAN:** Put `.md` in `docs/`, scripts in `temp/`

---

## Project

**Data Lineage Visualizer v3.8.0** - Azure Synapse parser + React visualization

- **Stack:** FastAPI + DuckDB + SQLGlot + Azure OpenAI | React + React Flow
- **Status:** Production (84.2% high-confidence parsing, 202 SPs)
- **System:** Python 3.12.3, Node.js, WSL2

---

## Quick Start

```bash
# Backend
cd api && python3 main.py  # http://localhost:8000

# Frontend
cd frontend && npm run dev  # http://localhost:3000

# Parser
python lineage_v3/main.py run --parquet parquet_snapshots/  # incremental
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

---

## Parser Development

🚨 **ALWAYS use `/sub_DL_OptimizeParsing` for parser changes**

1. Create baseline: `/sub_DL_OptimizeParsing init --name baseline_YYYYMMDD_description`
2. Run before: `/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD`
3. Make changes to `quality_aware_parser.py`, `ai_disambiguator.py`, etc.
4. Run after: `/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD`
5. Compare: `/sub_DL_OptimizeParsing compare --run1 RUN1 --run2 RUN2`
6. Update: [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)

**Pass criteria:** Zero regressions (≥0.85 stays ≥0.85) + expected improvements

❌ **Never** skip evaluation or commit without running subagent

---

## Sub-Agents

| Command | Purpose |
|---------|---------|
| `/sub_DL_OptimizeParsing` | Parser evaluation (regex/SQLGlot/AI comparison) |
| `/sub_DL_TestFrontend` | Automated browser tests + visual regression |
| `/sub_DL_Clean` | Archive old docs, optimize CLAUDE.md |
| `/sub_DL_Build` | Build Azure deployment package |
| `/sub_DL_GitPush` | Commit and push to remote |
| `/sub_DL_Restart` | Restart backend (8000) + frontend (3000) |

Docs: `.claude/commands/*.md`

---

## Key Features

**Incremental Parsing (default):**
- DuckDB persists, only re-parses modified/new + low confidence (<0.85)
- 50-90% faster

**Parquet Detection:**
- Auto-detects by schema: objects, dependencies, definitions (required); query_logs, table_columns (optional)

**Confidence Model:**
| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| SQLGlot | 0.85 | Parsed SPs |
| AI (Validated) | 0.85-0.95 | Complex SPs |
| Regex | 0.50 | Fallback |

---

## Git

- **Branch:** `feature/frontend-ui-fixes`
- **Main:** `main`
- **Do:** Commit often, push to origin
- **Don't:** Rebase, merge from others, merge to main without approval

---

## Environment

```bash
cp .env.template .env
```

Required for AI:
```
AZURE_OPENAI_ENDPOINT=https://...cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

---

## Docs

**Core:**
- [README.md](README.md) - Overview
- [lineage_specs.md](lineage_specs.md) - Parser spec
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing

**API/Frontend:**
- [api/README.md](api/README.md)
- [frontend/README.md](frontend/README.md)
- [frontend/docs/UI_STANDARDIZATION_GUIDE.md](frontend/docs/UI_STANDARDIZATION_GUIDE.md)

**Evaluation:**
- [docs/AI_DISAMBIGUATION_SPEC.md](docs/AI_DISAMBIGUATION_SPEC.md)
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md)
- [evaluation_baselines/README.md](evaluation_baselines/README.md)

**Other:**
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md)
- [docs/QUERY_LOGS_ANALYSIS.md](docs/QUERY_LOGS_ANALYSIS.md)

---

## Troubleshooting

```bash
# Import errors
python lineage_v3/main.py validate
pip install -r requirements.txt

# Port conflicts
lsof -ti:8000 | xargs -r kill  # Backend
lsof -ti:3000 | xargs -r kill  # Frontend
```

**Low confidence:** Use `/sub_DL_OptimizeParsing`, check [PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)

**Frontend errors:** Check JSON path/format in Import modal, browser console

---

**Versions:** Parser v3.8.0 | Frontend v2.9.0 | API v3.0.1 | Updated: 2025-11-03
