# CLAUDE.md

## Workflow
- End responses with status (✅ Completed | ⏳ Pending | ❌ Not started | ⚠️ Needs clarification)
- Ask questions last; complete analysis first
- Use TodoWrite tool; update immediately after completion

## Project: Data Lineage Visualizer v4.2.0
- **Stack:** FastAPI + DuckDB + SQLGlot + Regex | React + React Flow
- **System:** Python 3.12.3, Node.js, WSL2
- **Parser:** v4.2.0 | 97.0% SP confidence | 95.5% overall
- **Confidence:** v2.0.0 (Multi-Factor) with detailed breakdown
- **Frontend:** v2.9.2 | **API:** v4.0.3

## Quick Start

### One-Command Startup
```bash
./start-app.sh  # Starts both backend (port 8000) and frontend (port 3000)
```

**What it does:**
- ✅ Auto-detects and activates venv (checks: `./venv`, `../venv`, `./api/venv`, system Python)
- ✅ Auto-installs missing Python dependencies
- ✅ Auto-installs missing Node dependencies
- ✅ Starts backend on `http://localhost:8000`
- ✅ Starts frontend on `http://localhost:3000`

### Component-Specific
```bash
# Backend only
cd api && python3 main.py

# Frontend only
cd frontend && npm run dev

# Parser (incremental / full-refresh)
python lineage_v3/main.py run --parquet parquet_snapshots/
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

## Installation

### First-Time Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd sandbox

# 2. Install dependencies (one command!)
pip install -r requirements.txt

# 3. (Optional) Setup environment configuration
./setup-env.sh  # Only if you need custom settings

# 4. Start application
./start-app.sh
```

### Requirements Structure (Modular)
```
requirements/
├── base.txt      # Shared dependencies (pydantic, rich, dotenv)
├── parser.txt    # Parser: duckdb, sqlglot, pandas + base
├── api.txt       # API: fastapi, uvicorn + base
└── dev.txt       # Dev: pytest, black, ruff, mypy + all

requirements.txt  # Production: installs parser + api
```

**Install options:**
```bash
pip install -r requirements.txt              # Full stack (recommended)
pip install -r requirements/parser.txt       # Parser only
pip install -r requirements/api.txt          # API only
pip install -r requirements/dev.txt          # Development tools
```

## Configuration

### Environment Variables (Optional)

**No .env file needed for local development!** All settings have defaults.

**Create .env only if you need custom settings:**
```bash
cp .env.example .env  # Copy template (works immediately, no editing needed!)
# OR
./setup-env.sh        # Interactive setup with guidance
```

**Common customizations:**
```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000           # CORS origins (comma-separated)
PATH_WORKSPACE_FILE=lineage_workspace.duckdb   # DuckDB workspace path
PATH_OUTPUT_DIR=lineage_output                 # Output directory
LOG_LEVEL=INFO                                 # DEBUG | INFO | WARNING | ERROR
```

**Documentation:**
- [ENV_SETUP.md](ENV_SETUP.md) - Quick .env setup guide
- [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) - Complete configuration reference

## Parser (v4.2.0)
- **Strategy:** Regex → SQLGlot → Rule Engine
- **Performance:** 729/763 objects (95.5%), 196/202 SPs (97.0%)
- **Features:** Comment hints (@LINEAGE_INPUTS/@LINEAGE_OUTPUTS), dataflow mode, global target exclusion, incremental parsing
- **Confidence:** Multi-factor model v2.0.0 with detailed breakdown (5 weighted factors)

### Parser Development (MANDATORY)

**🚨 ALWAYS use `/sub_DL_OptimizeParsing` for parser changes 🚨**

```bash
# 1. Before changes: Create baseline
/sub_DL_OptimizeParsing init --name baseline_$(date +%Y%m%d)_before_description
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description

# 2. Make changes to quality_aware_parser.py

# 3. After changes: Run evaluation (MANDATORY)
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_before_description
/sub_DL_OptimizeParsing compare --run1 run_YYYYMMDD_HHMMSS --run2 run_YYYYMMDD_HHMMSS

# 4. Pass criteria: Zero regressions, expected improvements

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
- 50-90% faster than full refresh

### Confidence Model (v2.0.0 - Multi-Factor)
**5 Weighted Factors (sum to 1.0):**
- **Parse Success (30%)**: Did parsing complete without errors?
- **Method Agreement (25%)**: Do regex and SQLGlot agree?
- **Catalog Validation (20%)**: Do extracted objects exist in catalog?
- **Comment Hints (10%)**: Did developer provide @LINEAGE hints?
- **UAT Validation (15%)**: Has user verified this SP?

**Confidence Levels:**
- **High (0.85)**: total_score ≥ 0.80
- **Medium (0.75)**: total_score ≥ 0.65
- **Low (0.50)**: total_score > 0
- **Failed (0.0)**: total_score = 0

**Every parsed object includes detailed breakdown:**
```json
{
  "parse_success": {"score": 1.0, "weight": 0.30, "contribution": 0.30},
  "method_agreement": {"score": 0.95, "weight": 0.25, "contribution": 0.2375},
  "catalog_validation": {"score": 1.0, "weight": 0.20, "contribution": 0.20},
  "comment_hints": {"score": 0.0, "weight": 0.10, "contribution": 0.0},
  "uat_validation": {"score": 0.0, "weight": 0.15, "contribution": 0.0},
  "total_score": 0.7375,
  "bucketed_confidence": 0.75,
  "label": "Medium",
  "color": "yellow"
}
```

**Single Source of Truth:** `ConfidenceCalculator.calculate_multifactor()`

### Parquet File Detection
- Auto-detects schema
- Required: objects, dependencies, definitions
- Optional: query_logs, table_columns

---

## Essential Documentation

**Getting Started:**
- [README.md](README.md) - Project overview
- [ENV_SETUP.md](ENV_SETUP.md) - Environment configuration quick start
- [docs/SETUP_AND_DEPLOYMENT.md](docs/SETUP_AND_DEPLOYMENT.md) - Installation & deployment
- [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) - Architecture & components

**Configuration:**
- [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) - Complete configuration reference
- [.env.example](.env.example) - Simple template (copy to .env)
- [.env.template](.env.template) - Detailed template with all options

**Parser & Technical:**
- [lineage_specs.md](lineage_specs.md) - Parser specification
- [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL parsing guide
- [docs/COMMENT_HINTS_DEVELOPER_GUIDE.md](docs/COMMENT_HINTS_DEVELOPER_GUIDE.md) - Using @LINEAGE hints
- [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Version history
- [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md) - Database schema

**Evaluation:**
- [docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md](docs/SUB_DL_OPTIMIZE_PARSING_SPEC.md) - Parser evaluation framework
- [evaluation_baselines/README.md](evaluation_baselines/README.md) - Baseline management

**Component-Specific:**
- [api/README.md](api/README.md) - Backend API documentation
- [frontend/README.md](frontend/README.md) - Frontend guide
- [requirements/README.md](requirements/README.md) - Dependency structure
- [docs/MAINTENANCE_GUIDE.md](docs/MAINTENANCE_GUIDE.md) - Operations & troubleshooting

---

## Troubleshooting

**Known Issues & Bug Tracking:** See [BUGS.md](BUGS.md) for documented issues with business context, technical references, and current status.

### Startup Issues

**Port conflicts:**
```bash
./stop-app.sh  # Kill processes on ports 3000 and 8000
```

**Missing dependencies:**
```bash
pip install -r requirements.txt  # Python dependencies
cd frontend && npm install        # Node dependencies
```

**Virtual environment issues:**
```bash
# Create venv if missing
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Parser Issues

**Low confidence (<0.85):**
- Use `/sub_DL_OptimizeParsing` to analyze quality
- Review [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)
- Check [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) for similar issues

**Import errors:**
```bash
python lineage_v3/main.py validate  # Validate environment
pip install -r requirements.txt     # Reinstall dependencies
```

### Frontend Issues

**API connection errors:**
- Check `frontend/.env.development` has correct `VITE_API_URL`
- Verify backend is running on `http://localhost:8000`
- Check browser console for CORS errors

**Build errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Configuration Issues

**CORS errors:**
```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Custom paths not working:**
- Verify `.env` exists (not `.env.example`)
- Check syntax: `PATH_WORKSPACE_FILE=path/to/file.duckdb` (no quotes)
- See [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md)

---

## Git Guidelines

- **Commit frequently** - Small, focused commits
- **Push to feature branches** - Never push directly to main
- **Pull requests required** - For merging to main
- **DON'T:** Rebase, force push, or merge from other branches without approval

---

## Scripts & Utilities

| Script | Purpose |
|--------|---------|
| `start-app.sh` | Start both backend and frontend |
| `stop-app.sh` | Stop all services (kill ports 3000/8000) |
| `setup-env.sh` | Interactive .env setup |

---

## Version Information

**Last Updated:** 2025-11-06
**Project Version:** v4.2.0

For detailed version history and change logs:
- [docs/reference/PARSER_EVOLUTION_LOG.md](docs/reference/PARSER_EVOLUTION_LOG.md) - Parser version history
- [README.md Changelog](README.md#changelog) - Recent releases
- Git commit history - Detailed changes
