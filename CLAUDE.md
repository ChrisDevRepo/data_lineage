# CLAUDE.md

Instructions for Claude Code when working with this repository.

## Workflow Guidelines

- **Provide Brief Summary**: End each response with status (completed/pending tasks)
- **Use Status Flags**: ✅ Completed | ⏳ Awaiting verification | ❌ Not started | ⚠️ Needs clarification
- **Ask Questions Last**: Complete analysis first, group questions at end
- **Clarify Before Coding**: Never proceed with ambiguous requirements
- **Track Progress**: Use TodoWrite tool, update immediately after completing tasks

---

## Project Overview

**Data Lineage Visualizer v3.7.0** - DMV-first lineage parser for Azure Synapse with React visualization

- **Status:** Production Ready (80.7% high-confidence parsing)
- **Stack:** FastAPI + DuckDB + SQLGlot + Azure OpenAI | React + React Flow
- **System:** Python 3.12.3, Node.js, WSL2
- **Working Directory:** `/home/chris/sandbox`

---

## Quick Start

### Backend
```bash
cd /home/chris/sandbox/api && python3 main.py
# http://localhost:8000 | Docs: http://localhost:8000/docs
```

### Frontend
```bash
cd /home/chris/sandbox/frontend && npm run dev
# http://localhost:3000
```

### CLI Parser
```bash
python lineage_v3/main.py run --parquet parquet_snapshots/  # Incremental (default)
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

---

## Parser Development (MANDATORY PROCESS)

**🚨 ALWAYS use `/sub_DL_OptimizeParsing` for parser changes 🚨**

### Required Steps
1. **Before changes:** Create baseline
   ```bash
   /sub_DL_OptimizeParsing init --name baseline_$(date +%Y%m%d)_before_description
   /sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description
   ```

2. **Make parser changes** (quality_aware_parser.py, ai_disambiguator.py, etc.)

3. **After changes:** Run evaluation (MANDATORY)
   ```bash
   /sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description
   /sub_DL_OptimizeParsing compare --run1 run_YYYYMMDD_HHMMSS --run2 run_YYYYMMDD_HHMMSS
   ```

4. **Pass Criteria:**
   - ✅ Zero regressions (no objects ≥0.85 drop below 0.85)
   - ✅ Expected improvements verified
   - ✅ Progress toward 95% goal

5. **Update:** [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) with results

**DO NOT:**
- ❌ Skip evaluation "because change is small"
- ❌ Commit parser changes without running subagent
- ❌ Rely on manual testing or spot-checks

---

## Sub-Agents

### `/sub_DL_OptimizeParsing` - Parser Evaluation
- Runs all 3 methods (regex, SQLGlot, AI) independently
- Calculates precision/recall/F1 scores
- Tracks progress toward 95% confidence goal
- Docs: [.claude/commands/sub_DL_OptimizeParsing.md](.claude/commands/sub_DL_OptimizeParsing.md)

### `/sub_DL_TestFrontend` - Frontend Testing
- Automated browser testing using MCP Playwright
- Functional tests: UI, search, graph, export features
- Visual regression: 3 baseline screenshots (desktop 1920x1080)
- Screenshots: `/tmp/` (auto-cleanup), baselines: `test_baselines/desktop/` (versioned)
- Docs: [.claude/commands/sub_DL_TestFrontend.md](.claude/commands/sub_DL_TestFrontend.md)

### `/sub_DL_Clean` - Documentation Cleanup
- Archives outdated docs to `docs/archive/YYYY-MM-DD/`
- Optimizes CLAUDE.md (target: 100-200 lines)
- Verifies documentation links
- Docs: [.claude/commands/sub_DL_Clean.md](.claude/commands/sub_DL_Clean.md)

### `/sub_DL_Build` - Azure Deployment
- Builds deployment package for Azure Synapse
- Docs: [.claude/commands/sub_DL_Build.md](.claude/commands/sub_DL_Build.md)

### `/sub_DL_GitPush` - Git Push
- Commits and pushes changes to remote
- Docs: [.claude/commands/sub_DL_GitPush.md](.claude/commands/sub_DL_GitPush.md)

### `/sub_DL_Restart` - Server Restart
- Kills ports 3000/8000 and restarts both servers
- Docs: [.claude/commands/sub_DL_Restart.md](.claude/commands/sub_DL_Restart.md)

---

## Key Features

### Incremental Parsing (Default)
- DuckDB persists between runs
- Only re-parses modified/new objects + low confidence (<0.85)
- 50-90% faster for typical updates

### Parquet File Detection
- Auto-detects by schema (filenames don't matter)
- Required: objects, dependencies, definitions
- Optional: query_logs, table_columns

### Confidence Model
| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| SQLGlot | 0.85 | Successfully parsed SPs |
| AI (Validated) | 0.85-0.95 | Complex SPs |
| Regex Fallback | 0.50 | Failed parses |

**Current:** 202 SPs, 163 (80.7%) high confidence (≥0.85)

---

## Git Guidelines

- **Branch:** `feature/frontend-ui-fixes`
- **Main:** `main`
- **DO:** Commit frequently, push to origin
- **DON'T:** Pull with rebase, merge from other branches, merge to main (requires approval)

---

## Environment Setup

```bash
cp .env.template .env  # Edit with your credentials
```

**Required for AI features:**
```
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

---

## Essential Documentation

**Start Here:**
- [README.md](README.md) - Project overview
- [lineage_specs.md](lineage_specs.md) - Parser specification
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing guide

**API & Frontend:**
- [api/README.md](api/README.md) - API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide
- [frontend/docs/UI_STANDARDIZATION_GUIDE.md](frontend/docs/UI_STANDARDIZATION_GUIDE.md) - UI design system

**AI & Evaluation:**
- [docs/AI_DISAMBIGUATION_SPEC.md](docs/AI_DISAMBIGUATION_SPEC.md) - AI implementation
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Parser evaluation spec
- [evaluation_baselines/README.md](evaluation_baselines/README.md) - Baseline lifecycle

**Additional:**
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema
- [docs/QUERY_LOGS_ANALYSIS.md](docs/QUERY_LOGS_ANALYSIS.md) - Query log strategy

---

## Troubleshooting

**Import Errors:**
```bash
python lineage_v3/main.py validate
pip install -r requirements.txt
```

**Low Confidence (<0.85):**
- Use `/sub_DL_OptimizeParsing` to analyze parsing quality
- Review [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)

**Frontend Not Loading:**
- Check JSON path in Import Data modal
- Verify JSON format matches schema
- Check browser console for errors

**Port Conflicts:**
```bash
lsof -ti:8000 | xargs -r kill  # Backend
lsof -ti:3000 | xargs -r kill  # Frontend
```

---

**Last Updated:** 2025-11-02
**Parser Version:** v3.7.0
**Frontend Version:** v2.9.0
**API Version:** v3.0.1
