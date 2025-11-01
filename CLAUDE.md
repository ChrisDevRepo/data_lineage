# CLAUDE.md

Instructions for Claude Code when working with this repository.

## Project Overview

**Data Lineage Visualizer v3.7.0** - DMV-first lineage parser for Azure Synapse with React visualization.

**Status:** Production Ready (80.7% high-confidence parsing, 2x industry average)

**Stack:**
- Backend: FastAPI + DuckDB + SQLGlot parser + Azure OpenAI
- Frontend: React + React Flow + Monaco Editor
- Extractor: PySpark (DMV → Parquet)

---

## Development Environment

**System:**
- Python 3.12.3
- Node.js (frontend)
- WSL2 (Linux 6.6.87.2-microsoft-standard-WSL2)

**Working Directory:** `/home/chris/sandbox`

**MCP Servers:** ([.vscode/mcp.json](.vscode/mcp.json))
- `microsoft-learn` - Microsoft docs access

---

## Repository Structure

```
/home/chris/sandbox/
├── api/                          # FastAPI backend (v3.0.1)
│   ├── main.py                   # 7 REST endpoints
│   ├── background_tasks.py       # Parquet processing
│   ├── models.py                 # Pydantic schemas
│   └── README.md
│
├── frontend/                     # React visualizer (v2.9.0)
│   ├── src/
│   │   ├── components/           # React Flow components
│   │   ├── hooks/                # Custom hooks
│   │   └── utils/
│   ├── docs/
│   │   └── UI_STANDARDIZATION_GUIDE.md
│   └── README.md
│
├── lineage_v3/                   # Core parser (v3.7.0)
│   ├── main.py                   # CLI entry point
│   ├── core/
│   │   ├── duckdb_workspace.py   # Persistent DuckDB
│   │   └── gap_detector.py
│   ├── parsers/
│   │   ├── quality_aware_parser.py   # Main SQLGlot parser
│   │   ├── ai_disambiguator.py       # Azure OpenAI fallback
│   │   ├── query_log_validator.py    # Query log validation
│   │   └── deprecated/               # Old parsers (archived)
│   ├── output/
│   │   ├── internal_formatter.py     # lineage.json
│   │   └── frontend_formatter.py     # frontend_lineage.json
│   └── ai_analyzer/
│       ├── production_prompt.txt     # AI few-shot prompt
│       └── test_azure_openai.py
│
├── extractor/                    # PySpark DMV extractor
│   ├── synapse_pyspark_dmv_extractor.py
│   └── README.md
│
├── docs/                         # Documentation
│   ├── PARSING_USER_GUIDE.md     # SQL parsing guide
│   ├── PARSER_EVOLUTION_LOG.md   # Version history
│   ├── AI_DISAMBIGUATION_SPEC.md # AI implementation
│   └── DUCKDB_SCHEMA.md
│
├── tests/
│   └── parser_regression_test.py # Parser regression testing
│
├── baselines/                    # Parser baselines (for regression tests)
├── data/                         # API persistent storage (gitignored)
├── .env.template                 # Config template
├── requirements.txt              # Python dependencies
├── lineage_specs.md              # Parser specification
├── README.md                     # Main overview
└── CLAUDE.md                     # This file
```

---

## Quick Start

### 1. Backend API

```bash
cd /home/chris/sandbox/api
python3 main.py
# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Upload Parquet Files:**
```bash
# Filenames don't matter - auto-detected by schema
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" \
  -F "files=@part-00000.snappy.parquet" \
  -F "files=@part-00001.snappy.parquet" \
  -F "files=@part-00002.snappy.parquet"
```

**Required Parquet Files (3):**
1. Objects metadata (from `sys.objects`, `sys.schemas`)
2. Dependencies (from `sys.sql_expression_dependencies`)
3. Definitions (from `sys.sql_modules`)

**Optional Parquet Files (2):**
4. Query logs (from `sys.dm_pdw_exec_requests`) - for validation
5. Table columns (from `sys.tables`, `sys.columns`) - for DDL generation

### 2. Frontend

```bash
cd /home/chris/sandbox/frontend
npm run dev
# Opens: http://localhost:3000
```

**After frontend code changes:**
```bash
cd /home/chris/sandbox/frontend && lsof -ti:3000 | xargs -r kill && npm run dev
```

### 3. CLI Parser

```bash
cd /home/chris/sandbox

# Incremental mode (default - recommended)
python lineage_v3/main.py run --parquet parquet_snapshots/

# Full refresh (re-parse everything)
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# Validate environment
python lineage_v3/main.py validate
```

**Output:** `lineage_output/frontend_lineage.json` (ready for frontend)

---

## Key Features

### Incremental Parsing (Default)

**How it works:**
- DuckDB workspace persists between runs
- Only re-parses modified/new objects (checks `modify_date`)
- Also re-parses low confidence objects (<0.85)
- **50-90% faster** for typical updates

**Usage:**
```bash
# CLI (default)
python lineage_v3/main.py run --parquet parquet_snapshots/

# API (default incremental=true)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" -F "files=@..."
```

### Parquet File Detection

**Auto-detection by schema** - Filenames don't matter!

Backend checks column names:
- `objects.parquet`: `object_id`, `schema_name`, `object_name`, `object_type`
- `dependencies.parquet`: `referencing_object_id`, `referenced_object_id`
- `definitions.parquet`: `object_id`, `definition`

### Confidence Model

| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| SQLGlot Parser | 0.85 | Successfully parsed SPs |
| AI (Validated) | 0.85-0.95 | Complex SPs (3-layer validation) |
| Regex Fallback | 0.50 | Failed parses |

**Current Performance:**
- Total SPs: 202
- High Confidence (≥0.85): 163 (80.7%)
- Average Confidence: 0.800

---

## Parser Development Guidelines

**CRITICAL: Read before modifying parser code**

### Mandatory Process for Parser Changes

1. **Document Issue** in [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
2. **Capture Baseline:**
   ```bash
   python tests/parser_regression_test.py --capture-baseline baselines/baseline_$(date +%Y%m%d).json
   ```
3. **Modify Parser** ([lineage_v3/parsers/quality_aware_parser.py](lineage_v3/parsers/quality_aware_parser.py))
4. **Run Regression Test:**
   ```bash
   python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
   python tests/parser_regression_test.py --compare baselines/baseline_YYYYMMDD.json
   ```
5. **Requirements to Pass:**
   - Zero regressions (no high-confidence SPs drop below 0.85)
   - At least one SP improves as expected
6. **Update Documentation** ([docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md))
7. **Commit with descriptive message**

---

## Git Guidelines

**Branch:** `feature/frontend-ui-fixes`
**Main Branch:** `main`

**DO:**
- ✅ Commit frequently
- ✅ Push to remote: `git push origin feature/frontend-ui-fixes`

**DON'T:**
- ❌ Pull with rebase
- ❌ Merge from other branches
- ❌ Merge to main/master (requires approval)

---

## Environment Setup

**Create `.env` file:**
```bash
cp .env.template .env
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
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing best practices

**API & Frontend:**
- [api/README.md](api/README.md) - API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide

**AI Features:**
- [docs/AI_DISAMBIGUATION_SPEC.md](docs/AI_DISAMBIGUATION_SPEC.md) - AI implementation
- [docs/AI_PHASE4_ACTION_ITEMS.md](docs/AI_PHASE4_ACTION_ITEMS.md) - Implementation checklist
- [docs/AI_MODEL_EVALUATION.md](docs/AI_MODEL_EVALUATION.md) - Testing results

**Additional:**
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema
- [docs/QUERY_LOGS_ANALYSIS.md](docs/QUERY_LOGS_ANALYSIS.md) - Query log strategy
- [frontend/docs/UI_STANDARDIZATION_GUIDE.md](frontend/docs/UI_STANDARDIZATION_GUIDE.md) - UI design system

---

## Troubleshooting

**Import Errors:**
```bash
python lineage_v3/main.py validate  # Check dependencies
pip install -r requirements.txt     # Reinstall
```

**Missing .env:**
```bash
cp .env.template .env
# Edit with your credentials
```

**Low Confidence (<0.85):**
- Review [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
- Check `lineage_output/frontend_lineage.json` for coverage
- Review `provenance.primary_source` to identify weak dependencies

**Frontend Not Loading:**
- Verify JSON path in Import Data modal
- Check browser console for errors
- Ensure JSON format matches schema

---

**Last Updated:** 2025-11-01
**Parser Version:** v3.7.0 (Production Ready)
**Frontend Version:** v2.9.0 (Production Ready)
**API Version:** v3.0.1 (Production Ready)
