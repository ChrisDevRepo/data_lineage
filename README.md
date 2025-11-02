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
**Backend:** FastAPI + DuckDB + SQLGlot + Azure OpenAI
**Parser:** DMV-first with 80.7% high-confidence (2x industry average)

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

**Current Metrics (v3.7.0):**
- Total SPs: 202
- High Confidence (≥0.85): 163 (80.7%)
- Average Confidence: 0.800

**Confidence Model:**
| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| SQLGlot Parser | 0.85 | Successfully parsed SPs |
| AI (Validated) | 0.85-0.95 | Complex SPs |
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
- [docs/AI_DISAMBIGUATION_SPEC.md](docs/AI_DISAMBIGUATION_SPEC.md) - AI implementation
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history

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
# Edit .env with Azure OpenAI credentials (for AI features)
```

---

## Support

**Issues:** Use GitHub issue tracker
**Developer Guide:** See [CLAUDE.md](CLAUDE.md)

---

**Version:** v3.7.0 (Parser) | v2.9.0 (Frontend) | v3.0.1 (API)
**Status:** Production Ready
**Author:** Christian Wagner
**Built with:** [Claude Code](https://claude.com/claude-code)
