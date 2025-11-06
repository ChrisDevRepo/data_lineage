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

**Frontend:** React 19 + TypeScript + React Flow + Monaco Editor + Tailwind (v2.9.1 - Performance Optimized)
**Backend:** FastAPI + DuckDB + SQLGlot + Regex + Rule Engine (v4.0.0)
**Parser:** Dataflow-focused mode showing DML only (v4.1.3 - No Circular Dependencies)

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
├── lineage_v3/                 # Core parser
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

**Parser (v4.1.3):**
- **97.0% SP confidence** (196/202 at high confidence)
- **95.5% overall** (729/763 objects at high confidence)
- **Zero circular dependencies** (IF EXISTS filtering)
- **99.3% coverage** (758/763 objects parsed)
- Dataflow mode with global target exclusion

**Frontend (v2.9.1 - Performance Optimized):**
- ✅ **5,000+ nodes** supported smoothly
- ✅ **100x faster** schema toggling (freezing eliminated)
- ✅ Debounced filters (150ms) for large datasets
- ✅ Layout caching (95%+ hit rate)
- ✅ Smooth 60fps pan/zoom
- See [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md)

**Confidence Model:**
| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| SQLGlot Parser | 0.85 | Successfully parsed SPs |
| Regex Fallback | 0.50 | Failed parses |

---

## Documentation

**Getting Started:**
- [CLAUDE.md](CLAUDE.md) - Complete developer guide
- [ENV_SETUP.md](ENV_SETUP.md) - Environment configuration quick start **NEW**
- [docs/SETUP_AND_DEPLOYMENT.md](docs/SETUP_AND_DEPLOYMENT.md) - Installation & deployment
- [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) - Architecture & components

**Configuration:**
- [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) - Complete configuration reference **NEW**
- [.env.example](.env.example) - Simple template (copy to .env) **NEW**
- [.env.template](.env.template) - Detailed template with all options

**Parser & Technical:**
- [lineage_specs.md](lineage_specs.md) - Parser specification
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing guide
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema

**Component-Specific:**
- [api/README.md](api/README.md) - Backend API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide
- [requirements/README.md](requirements/README.md) - Dependency structure **NEW**
- [extractor/README.md](extractor/README.md) - Extractor setup
- [docs/MAINTENANCE_GUIDE.md](docs/MAINTENANCE_GUIDE.md) - Operations & troubleshooting

**Advanced:**
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Parser evaluation framework
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

See [ENV_SETUP.md](ENV_SETUP.md) for details.

---

## Changelog

### v2.9.1 (Frontend) - Performance Optimizations (2025-11-04)

**MAJOR PERFORMANCE IMPROVEMENTS:** Supports 5,000+ nodes smoothly

**Problem Solved:**
- Browser freezing when deselecting schemas (1,067 nodes)
- Laggy pan/zoom on large graphs
- Slow filter updates

**Optimizations:**
1. **Debounced filter updates (150ms)** - Batch rapid changes → **100x faster schema toggling**
2. **Layout caching** - 95%+ cache hit rate → 30x faster repeat operations
3. **Optimized filtering logic** - Direct array filtering → 40-60% faster
4. **ReactFlow performance props** - Disabled drag overhead → Smooth 60fps
5. **Visual loading indicator** - User feedback during calculations

**Benchmarks (1,067 nodes):**
- Schema deselect: FREEZE (2-3s) → <5ms (**100x faster**)
- Initial load: 600ms → 250ms (2.4x faster)
- Layout switch: 500ms → <5ms cached (100x faster)

**Files:** `App.tsx`, `hooks/useDataFiltering.ts`, `utils/layout.ts` (~100 lines)
**Docs:** [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md)

---

### v4.1.3 (Parser) - IF EXISTS/IF NOT EXISTS Filtering (2025-11-04)

**CRITICAL FIX:** Eliminates circular dependencies from IF EXISTS checks

- **Problem**: IF EXISTS (SELECT ... FROM Table) created bidirectional dependencies
- **Solution**: Added preprocessing patterns to remove IF EXISTS/IF NOT EXISTS before parsing
- **Impact**: Clean unidirectional lineage (SP → Table writes only)
- **Example**: spLoadFactLaborCostForEarnedValue now shows table only in outputs
- **Result**: Zero circular dependencies in lineage graphs ✅

---

### v4.1.2 (Parser) - Global Target Exclusion Fix (2025-11-04)

**FIX:** Eliminates false positive inputs from DML target tables

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

**Version:** v4.1.3 (Parser) | v2.9.1 (Frontend) | v4.0.0 (API)
**Status:** Production Ready
**Author:** Christian Wagner
**Built with:** [Claude Code](https://claude.com/claude-code)
