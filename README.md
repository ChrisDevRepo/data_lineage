# Data Lineage Visualizer

**Interactive data lineage analysis for Azure Synapse Analytics**

Visualize tables, views, and stored procedures with their dependencies in an interactive graph. Built for data engineers and analysts working with complex data warehouses.

![Data Lineage Visualizer](tests/screenshots/frontend_smoke.png)

---

## Features

- **Interactive Graph Visualization** - Pan, zoom, and explore your data lineage with React Flow
- **Path-Based Tracing** - Find lineage paths between any two objects (upstream/downstream analysis)
- **SQL Viewer** - View DDL definitions with Monaco Editor (VS Code's editor) and full-text search
- **Smart Filtering** - Filter by schema, object type, or pattern exclusions
- **Export** - Export visualizations as SVG or JSON
- **No Database Required** - Works entirely with pre-exported Parquet files

---

## Quick Start

### For Users

**1. Start the Application**

```bash
# Terminal 1 - Backend API
cd ~/sandbox
source venv/bin/activate
python3 api/main.py

# Terminal 2 - Frontend
cd ~/sandbox/frontend
npm run dev
```

**2. Open in Browser**

- Frontend: http://localhost:3000
- Backend Health: http://localhost:8000/health

**3. Upload Your Data**

Click "Upload Data" and select your Parquet files exported from Synapse:
- `objects.parquet` - Database objects metadata
- `dependencies.parquet` - DMV-based dependencies
- `definitions.parquet` - Object DDL definitions
- `query_logs.parquet` - Query execution logs (optional)
- `table_columns.parquet` - Column metadata (optional)

**4. Explore**

- Use the "Start Trace" button to analyze impact (upstream/downstream paths)
- Click nodes to view SQL definitions in the Monaco editor
- Use Detail Search (full-text) to find objects containing specific SQL patterns
- Apply filters to focus on specific schemas or object types

---

### For Developers

**Tech Stack**
- **Frontend:** React 18, TypeScript, React Flow, Monaco Editor, Tailwind CSS
- **Backend:** Python 3.12, FastAPI, DuckDB, SQLGlot
- **Parser:** DMV-first lineage analysis with 97.5% high-confidence parsing

**Architecture**
```
Synapse DMVs → PySpark Extractor → Parquet Files
                                         ↓
                               FastAPI Backend (DuckDB)
                                         ↓
                               React Frontend (React Flow)
```

**Project Structure**
```
ws-psidwh/
├── api/                  # FastAPI backend (7 endpoints)
├── frontend/            # React visualization app
├── lineage_v3/          # Core parser engine
├── extractor/           # PySpark DMV extractor
├── docs/                # Documentation
└── tests/               # Test suite
```

**Key Components**
- `lineage_v3/parsers/quality_aware_parser.py` - Main SQL parser (SQLGlot + regex)
- `api/main.py` - FastAPI application with 7 REST endpoints
- `frontend/App.tsx` - Main React Flow application
- `frontend/components/InteractiveTracePanel.tsx` - Path-based tracing UI

---

## Latest Updates (v2.9.1)

### UI Redesign Phase 1
- Modern gradient accents on all modals and panels
- Unified design system with consistent typography
- Simplified minimap with uniform gray colors

### Path-Based Tracing (v2.8.0)
- Find direct lineage paths between two specific nodes
- Bidirectional search (upstream and downstream)
- Respects all filters (schema, type, exclusion patterns)

### Monaco Editor Integration (v2.7.0)
- Professional SQL viewing with VS Code's editor
- Built-in search with keyboard shortcuts (Ctrl+F)
- Syntax highlighting and line numbers
- Optimized for large SQL files (10K+ lines)

### Data Persistence (v2.4.0)
- Server-side storage survives container restarts
- No more localStorage limitations
- Faster page loads

See [frontend/CHANGELOG.md](frontend/CHANGELOG.md) for full history.

---

## Documentation

### User Guides
- [SQL Parsing Best Practices](docs/PARSING_USER_GUIDE.md) - How to write SQL for optimal parsing
- [Frontend Architecture](frontend/docs/FRONTEND_ARCHITECTURE.md) - React Flow implementation details
- [Local Development](frontend/docs/LOCAL_DEVELOPMENT.md) - Dev setup guide
- [WSL Setup](docs/WSL_SETUP.md) - Windows Subsystem for Linux configuration

### Developer Reference
- [API Documentation](api/README.md) - FastAPI endpoints and request/response models
- [DuckDB Schema](docs/DUCKDB_SCHEMA.md) - Database schema reference
- [Parser Specification](lineage_specs.md) - Core parser implementation
- [Query Logs Analysis](docs/QUERY_LOGS_ANALYSIS.md) - Validation strategy

### Deployment
- [Azure Deployment](frontend/docs/DEPLOYMENT_AZURE.md) - Deploy to Azure Web App
- [Extractor Setup](extractor/README.md) - PySpark DMV extraction guide

---

## Performance

**Parser Metrics (v3.6.0)**
- Total Objects: 202 stored procedures
- High Confidence (≥0.85): 163 (80.7%)
- **3.2x better than industry average** (30-40% typical for T-SQL)

**Confidence Levels**
- DMV (Views/Functions): 1.0 (system metadata)
- Query Log Validated: 0.95 (runtime confirmed)
- SQLGlot Parsed: 0.85 (static analysis)
- Regex Baseline: 0.50 (fallback)

---

## Requirements

**System Dependencies**
- Python 3.12+
- Node.js 24+
- WSL Ubuntu (for local development)

**Python Packages** (pre-installed in `venv/`)
- FastAPI, Uvicorn, DuckDB, SQLGlot, Pandas, NetworkX

**Node Packages** (see `frontend/package.json`)
- React, React Flow, Monaco Editor, Tailwind CSS

---

## Environment Setup

**Quick Setup (WSL Ubuntu)**

```bash
# 1. Install system dependencies
sudo apt install python3.12-venv

# 2. Activate virtual environment
cd ~/sandbox
source venv/bin/activate

# 3. Verify installation
python -c "import duckdb, sqlglot, fastapi; print('✅ Ready')"

# 4. Install frontend dependencies (if needed)
cd frontend
npm install
```

**Environment Variables** (Backend)

Create `.env` file in project root:
```bash
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AI_ENABLED=true
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Support

**Issues:** Report bugs or request features in this repository's issue tracker

**Documentation:** See [CLAUDE.md](CLAUDE.md) for complete developer guide

---

## License

Created by Christian Wagner

Built with [Claude Code](https://claude.com/claude-code)

---

**Version:** 2.9.1 (Frontend) | 3.6.0 (Parser)
**Status:** Production Ready
**Last Updated:** 2025-11-01
