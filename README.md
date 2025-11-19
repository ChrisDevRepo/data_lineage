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
- **Flexible Data Sources** - Parquet files (default) OR direct database connection (optional v0.10.0)
- **Incremental Refresh** - Only process changed procedures for faster updates

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repo-url>
cd sandbox

# Install dependencies (one command!)
pip install -r requirements.txt

# (Optional) Setup environment configuration - only if you need custom settings
./setup-env.sh

# Start application
./start-app.sh
```

**What `start-app.sh` does:**
- ✅ Auto-detects and activates virtual environment (multiple locations)
- ✅ Auto-installs missing Python dependencies
- ✅ Auto-installs missing Node dependencies
- ✅ Starts backend on `http://localhost:8000`
- ✅ Starts frontend on `http://localhost:3000`

**Manual Start (Alternative):**
```bash
# Terminal 1 - Backend API
cd api && python3 main.py

# Terminal 2 - Frontend
cd frontend && npm run dev
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

**Frontend:** React 19 + TypeScript + React Flow + Monaco Editor + Tailwind (v0.9.0)
**Backend:** FastAPI + DuckDB + SQLGlot + Regex + YAML Rule Engine (v0.9.0)
**Parser:** v4.3.3 - 100% success rate (349/349 SPs) + YAML rules + Developer Mode

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
sandbox/
├── api/                        # FastAPI backend
├── frontend/                   # React visualization
├── engine/                 # Core parser
│   └── config/                 # Configuration (Pydantic settings)
├── requirements/               # Modular dependencies (NEW)
│   ├── base.txt               # Shared dependencies
│   ├── parser.txt             # Parser-specific
│   ├── api.txt                # API-specific
│   └── dev.txt                # Development tools
├── docs/                       # Documentation
│   ├── CONFIGURATION_GUIDE.md # Complete config reference (NEW)
│   ├── SYSTEM_OVERVIEW.md     # Architecture guide
│   └── SETUP_AND_DEPLOYMENT.md # Installation guide
├── extractor/                  # PySpark DMV extractor
├── tests/                      # Test suite
├── start-app.sh               # One-command startup (NEW)
├── stop-app.sh                # Stop all services (NEW)
├── setup-env.sh               # Interactive .env setup (NEW)
├── .env.example               # Environment template (NEW)
├── ENV_SETUP.md               # Quick config guide (NEW)
├── requirements.txt           # Production dependencies
├── README.md                  # This file
└── CLAUDE.md                  # Developer guide
```

---

## Performance

**Parser (v4.3.3):**
- ✅ **100% success rate** (349/349 stored procedures)
- ✅ **82.5% perfect** (288 SPs at confidence 100)
- ✅ **7.4% good** (26 SPs at confidence 85)
- ✅ **10.0% acceptable** (35 SPs at confidence 75)
- ✅ **Zero parse failures** (YAML-based SQL cleaning)
- Regex-first baseline + SQLGlot enhancement strategy

**Frontend (v0.9.0):**
- ✅ **5,000+ nodes** supported smoothly
- ✅ **Developer Mode** (logs viewer + YAML rules browser)
- ✅ Debounced filters (150ms) for large datasets
- ✅ Interactive trace mode with BFS graph traversal
- ✅ Smooth 60fps pan/zoom

**Confidence Model v2.1.0 (Simplified):**
| Completeness | Confidence | Description |
|-------------|-----------|-------------|
| ≥ 90% | 100 | Perfect - All expected tables found |
| ≥ 70% | 85 | Good - Most tables found |
| ≥ 50% | 75 | Acceptable - Partial coverage |
| < 50% | 0 | Poor - Needs hints or investigation |

---

## Documentation

**Getting Started:**
- [CLAUDE.md](CLAUDE.md) - Complete developer guide
- [ENV_SETUP.md](docs/archive/ENV_SETUP.md) - Environment configuration quick start **NEW**
- [docs/SETUP_AND_DEPLOYMENT.md](docs/SETUP.md) - Installation & deployment
- [docs/SYSTEM_OVERVIEW.md](docs/documentation-mode/01_CURRENT_SYSTEM_ARCHITECTURE.md) - Architecture & components

**Configuration:**
- [docs/CONFIGURATION_GUIDE.md](docs/SETUP.md) - Complete configuration reference **NEW**
- [.env.example](.env.example) - Simple template (copy to .env) **NEW**
- [.env.template](.env.template) - Detailed template with all options

**Parser & Technical:**
- [docs/PARSING_USER_GUIDE.md](docs/USAGE.md) - SQL parsing guide
- [docs/PARSER_EVOLUTION_LOG.md](docs/REFERENCE.md) - Version history
- [docs/DUCKDB_SCHEMA.md](docs/REFERENCE.md) - Database schema

**Component-Specific:**
- [api/README.md](api/README.md) - Backend API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide
- [requirements/README.md](requirements/README.md) - Dependency structure **NEW**
- [docs/MAINTENANCE_GUIDE.md](docs/USAGE.md) - Operations & troubleshooting

**Advanced:**
- [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md) - Frontend performance

---

## Requirements

**System:**
- Python 3.10+ (required by Click 8.3.0)
- Node.js 18+
- Linux, macOS, or WSL2

**Dependencies:**

Modular structure for flexible deployment:
```bash
# Full stack (recommended)
pip install -r requirements.txt

# Component-specific
pip install -r requirements/parser.txt  # Parser only
pip install -r requirements/api.txt     # API only
pip install -r requirements/dev.txt     # Development tools
```

**Configuration (Optional):**

No `.env` file needed for local development! All settings have defaults.

Create `.env` only if you need custom settings:
```bash
cp .env.example .env  # Works immediately, no editing needed
# OR
./setup-env.sh        # Interactive setup with guidance
```

See [ENV_SETUP.md](docs/archive/ENV_SETUP.md) for details.

---

## Support

**Known Issues:** See [BUGS.md](BUGS.md) for tracked bugs and feature requests
**Developer Guide:** See [CLAUDE.md](CLAUDE.md) for setup, workflows, and troubleshooting
**GitHub Issues:** Use GitHub issue tracker for new bugs or questions

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Christian Wagner

---

**Status:** Production Ready
**Author:** Christian Wagner
**Built with:** [Claude Code](https://claude.com/claude-code)
