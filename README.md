# Data Lineage Visualizer

**Interactive lineage analysis for Azure Synapse Analytics**

Visualize tables, views, and stored procedures with their dependencies. Built for data engineers working with complex data warehouses.

![Data Lineage Visualizer](tests/screenshots/frontend_smoke.png)

---

## Features

- **Interactive Graph** - Pan, zoom, explore with React Flow
- **Path Tracing** - Find upstream/downstream dependencies between objects
- **SQL Viewer** - Monaco Editor (VS Code) with syntax highlighting
- **Smart Filtering** - Schema, type, pattern-based filtering
- **No Database Required** - Works with pre-exported Parquet files

---

## Quick Start

### 1. Start Services

**Automated (Recommended):**
```bash
cd /home/chris/sandbox
./start-app.sh
# Starts both backend (8000) and frontend (3000)
# Logs: /tmp/backend.log and /tmp/frontend.log
```

**Manual (Alternative):**
```bash
# Terminal 1 - Backend API
cd /home/chris/sandbox
python3 api/main.py

# Terminal 2 - Frontend
cd /home/chris/sandbox/frontend
npm run dev
```

**Stop Services:**
```bash
./stop-app.sh
```

### 2. Upload Data

**Upload Parquet files** via UI or curl:

```bash
# Filenames don't matter - auto-detected by schema
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" \
  -F "files=@part-00000.snappy.parquet" \
  -F "files=@part-00001.snappy.parquet" \
  -F "files=@part-00002.snappy.parquet"
```

**Required Files (3):**
- Objects (from `sys.objects`, `sys.schemas`)
- Dependencies (from `sys.sql_expression_dependencies`)
- Definitions (from `sys.sql_modules`)

**Optional Files (2):**
- Query logs (from `sys.dm_pdw_exec_requests`) - for validation
- Table columns (from `sys.tables`, `sys.columns`) - for DDL

### 3. Explore

- **Trace Mode** - Analyze upstream/downstream impact
- **SQL Viewer** - Click nodes to view definitions
- **Detail Search** - Full-text search across all SQL
- **Filters** - Focus on specific schemas/types

---

## Tech Stack

**Frontend:** React 18 + TypeScript + React Flow + Monaco Editor + Tailwind
**Backend:** FastAPI + DuckDB + SQLGlot + Regex + Rule Engine
**Parser:** Dataflow-focused mode showing DML only (v4.1.0)

**Architecture:**
```
Synapse DMVs → PySpark Extractor → Parquet Files
                                         ↓
                               FastAPI Backend (DuckDB)
                                         ↓
                               React Frontend (React Flow)
```

---

## Repository Structure

```
/home/chris/sandbox/
├── api/                  # FastAPI backend
├── frontend/            # React visualization
├── lineage_v3/          # Core parser
├── extractor/           # PySpark DMV extractor
├── docs/                # Documentation
├── tests/               # Test suite
├── README.md            # This file
└── CLAUDE.md            # Developer guide
```

---

## Performance

**Current Status (v4.0.0 - Slim):**
- Starting fresh with slim architecture
- Goal: Iteratively improve confidence through rule engine
- Target: 95% high-confidence coverage

**Confidence Model:**
| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| SQLGlot Parser | 0.85 | Successfully parsed SPs |
| Regex Fallback | 0.50 | Failed parses |

---

## Documentation

**Essential:**
- [CLAUDE.md](CLAUDE.md) - Complete developer guide
- [lineage_specs.md](lineage_specs.md) - Parser specification
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL best practices

**Component-Specific:**
- [api/README.md](api/README.md) - API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide
- [extractor/README.md](extractor/README.md) - Extractor setup

**Advanced:**
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Parser evaluation

---

## Requirements

**System:**
- Python 3.12+
- Node.js 24+
- WSL2 Ubuntu (development)

**Setup:**
```bash
# Python packages
pip install -r requirements.txt

# Node packages
cd frontend && npm install
```

**Environment Variables:**
```bash
cp .env.template .env
# Azure OpenAI credentials not required in v4.0.0 (slim architecture)
```

---

## Changelog

### v4.1.2 - Global Target Exclusion Fix (2025-11-04)

**CRITICAL FIX:** Eliminates false positive inputs from DML target tables

**Problem Solved:**
- DML targets (e.g., INSERT INTO target) were appearing in both inputs AND outputs
- Root cause: Multi-statement processing accumulated sources globally, but target exclusion was per-statement
- Example: `spLoadGLCognosData` showed GLCognosData as input (wrong) and output (correct)

**Solution:**
- Global target exclusion after all statements parsed: `sources_final = sources - targets`
- Works for INSERT, UPDATE, MERGE, DELETE operations
- Handles CTEs, temp tables, and complex multi-statement SPs

**Impact:**
- Clean lineage graphs with no false positive inputs
- Accurate data flow visualization
- Smoke test: 100% passing (spLoadGLCognosData now shows only legitimate inputs)

**Files Modified:**
- `lineage_v3/parsers/quality_aware_parser.py` - Global exclusion logic
- `temp/smoke_test/` - Automated test suite with comprehensive documentation

### v4.1.0 - Dataflow-Focused Lineage (2025-11-04)

**BREAKING CHANGE:** Switches from "complete" mode to "dataflow" mode by default

**What Changed:**
- Parser now shows ONLY data transformation operations (DML)
- Filters out housekeeping (TRUNCATE/DROP) and administrative queries (SELECT COUNT)
- Cleaner, more focused lineage graphs

**What's Shown:**
- ✅ INSERT, UPDATE, DELETE, MERGE, SELECT INTO
- ❌ TRUNCATE, DROP, SELECT COUNT, CATCH blocks, ROLLBACK paths

See [PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) for complete details.

### v4.0.3 - SP-to-SP Direction Fix (2025-11-04)
- Fixed SP-to-SP lineage to show correct arrow direction
- EXEC/EXECUTE calls now properly shown as outputs (not inputs)
- Corrects 151 SP-to-SP relationships

### v4.0.2 - Orchestrator SP Confidence (2025-11-03)
- Fixed confidence scoring for orchestrator SPs (SP calls only, no tables)
- 97.0% SP confidence achieved (exceeded 95% goal)

---

## Support

**Issues:** Use GitHub issue tracker
**Developer Guide:** See [CLAUDE.md](CLAUDE.md)

---

**Version:** v4.1.0 (Parser) | v2.9.0 (Frontend) | v4.0.0 (API)
**Status:** Production Ready
**Author:** Christian Wagner
**Built with:** [Claude Code](https://claude.com/claude-code)
