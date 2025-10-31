# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

**Devcontainer:** This project runs in a VSCode devcontainer using `mcr.microsoft.com/devcontainers/base:noble` (Ubuntu 24.04)

**System Dependencies Installed:**
- Python 3.12.3
- Microsoft ODBC Driver 18 for SQL Server (v18.5.1.1)
- unixODBC libraries
- Node.js (for frontend)

**MCP Servers Configured:** ([.vscode/mcp.json](.vscode/mcp.json))
- `microsoft-learn` - Microsoft documentation access (via mcp-remote)

**Built-in Tools Available:**
- `WebFetch` - Fetch and analyze web content
- `WebSearch` - Search the web for current information

### ⚠️ VSCode Devcontainer Safety Guidelines

**CRITICAL:** This project runs in a VSCode devcontainer. When managing processes and ports:

**✅ SAFE to kill:**
- Frontend dev server: `lsof -ti:3000 | xargs -r kill` (port 3000)
- Backend API server: `lsof -ti:8000 | xargs -r kill` (port 8000)
- Python processes: `pkill -f "python lineage_v3/main.py"` (specific scripts)
- Node processes: `pkill -f "vite"` (specific processes)

**❌ NEVER kill:**
- VSCode server processes (ports 8080-8082, or any process with "vscode" in name)
- SSH/Remote connection processes
- Docker/container runtime processes
- System services (systemd, dbus, etc.)

**Best Practices:**
1. **Be specific:** Target exact ports or process names, never use `pkill -9 python` or `killall node`
2. **Check first:** Use `lsof -i :PORT` or `ps aux | grep PROCESS` to identify processes before killing
3. **Use `-r` flag:** Always use `xargs -r` to prevent errors when no processes are found
4. **Graceful shutdown:** Prefer `SIGTERM` (default) over `SIGKILL` (`-9`) when possible

## Git Workflow

**Current Branch:** `feature/v3-implementation`

**IMPORTANT:** All v3.0 development work stays in the `feature/v3-implementation` branch until approved for merge.

**Git Guidelines:**
- ✅ Commit frequently to `feature/v3-implementation`
- ✅ Push to remote: `git push origin feature/v3-implementation`
- ❌ **DO NOT** pull with rebase
- ❌ **DO NOT** merge from other branches
- ❌ **DO NOT** merge to main/master
- 📋 Branch will be merged to main only after full v3.0 approval

## Overview

This repository contains:
1. **Azure Synapse Data Warehouse** - SQL scripts for stored procedures, tables, and views
2. **Vibecoding Lineage Parser v3.0** - DMV-first data lineage system with React-based visualization
3. **AI-Assisted Disambiguation** - Azure OpenAI integration for resolving ambiguous table references

**Current Status:** v3.7.0 Production Ready (97.5% high-confidence parsing, 3.2x industry average)

**AI Enhancement Status:** Phase 4 Complete - Production ready with critical bug fixes applied

The codebase supports finance, clinical operations, and reporting workloads across multiple schemas.

## Repository Structure

```
ws-psidwh/
├── Synapse_Data_Warehouse/       # Azure Synapse SQL objects
│   ├── Stored Procedures/        # ETL and data processing procedures
│   ├── Tables/                   # Table definitions
│   └── Views/                    # View definitions
│
├── extractor/                    # ✅ PySpark DMV Extractor (Production Ready)
│   ├── synapse_pyspark_dmv_extractor.py  # Spark Job script
│   └── README.md                 # Deployment guide
│
├── api/                          # ✅ FastAPI Backend (Production Ready)
│   ├── main.py                   # FastAPI application with 7 endpoints
│   ├── background_tasks.py       # Background processing wrapper
│   ├── models.py                 # Pydantic request/response models
│   ├── requirements.txt          # API dependencies
│   ├── README.md                 # Complete API documentation
│   └── TEST_RESULTS.md           # Comprehensive test report
│
├── lineage_v3/                   # ✅ Core Parser (v3.6.0)
│   ├── main.py                   # CLI entry point & orchestration
│   ├── core/                     # DuckDB workspace engine
│   │   ├── duckdb_workspace.py   # Persistent database manager
│   │   └── gap_detector.py       # Missing dependency detection
│   ├── parsers/                  # SQL parsing implementations
│   │   ├── quality_aware_parser.py  # ✅ ACTIVE: Main parser (v3.6.0)
│   │   ├── dual_parser.py        # ✅ ACTIVE: Dual validation wrapper
│   │   ├── query_log_validator.py  # ✅ ACTIVE: Query log cross-validation
│   │   └── deprecated/           # Archived old implementations
│   ├── ai_analyzer/              # 🧪 AI-Assisted Disambiguation (Phase 1)
│   │   └── test_azure_openai.py  # Smoke test helper for Azure OpenAI
│   ├── output/                   # JSON formatters
│   │   ├── internal_formatter.py # lineage.json (int object_ids)
│   │   ├── frontend_formatter.py # frontend_lineage.json (string ids)
│   │   └── summary_formatter.py  # lineage_summary.json (stats)
│   └── utils/                    # Dev helpers (internal use only)
│
├── frontend/                     # ✅ React Visualizer (v2.9.0)
│   ├── components/               # React Flow components
│   ├── hooks/                    # Custom React hooks
│   ├── utils/                    # Utility functions
│   ├── docs/                     # Frontend documentation
│   │   ├── FRONTEND_ARCHITECTURE.md  # Architecture deep dive
│   │   ├── LOCAL_DEVELOPMENT.md      # Dev setup guide
│   │   ├── DEPLOYMENT_AZURE.md       # Azure deployment
│   │   └── UI_STANDARDIZATION_GUIDE.md  # UI design system guide
│   ├── deploy/                   # Azure deployment configs
│   ├── README.md                 # Quick start guide
│   └── CHANGELOG.md              # Feature history
│
├── docs/                         # 📚 Core Documentation
│   ├── PARSING_USER_GUIDE.md     # ⭐ SQL parsing best practices
│   ├── PARSER_EVOLUTION_LOG.md   # Parser version history
│   ├── DUCKDB_SCHEMA.md          # Database schema reference
│   ├── QUERY_LOGS_ANALYSIS.md    # Query log validation strategy
│   ├── AI_DISAMBIGUATION_SPEC.md # AI disambiguation specification
│   ├── AI_PHASE4_ACTION_ITEMS.md # AI implementation action items
│   ├── AI_MODEL_EVALUATION.md    # AI model evaluation results
│   ├── DETAIL_SEARCH_SPEC.md     # Detail search specification
│   └── UNIFIED_DDL_FEATURE.md    # Unified DDL feature docs
│
├── tests/                        # Testing & validation
│   └── parser_regression_test.py # ⭐ Parser regression testing
│
├── baselines/                    # Parser performance baselines
│   └── baseline_20251028_*.json  # Latest baseline snapshot
│
├── lineage_output/               # Generated lineage JSON (gitignored)
├── data/                         # API persistent storage (gitignored)
├── .env.template                 # Environment config template
├── requirements.txt              # Python dependencies
├── lineage_specs.md              # Parser v3.0 specification
├── README.md                     # Main project overview
└── CLAUDE.md                     # This file
```

---

## Quick Start Guide

### Working with Frontend (v2.9.0)

```bash
# Start frontend dev server
cd /workspaces/ws-psidwh/frontend
npm run dev  # Opens at http://localhost:3000

# IMPORTANT: After making frontend code changes, ALWAYS restart the dev server
cd /workspaces/ws-psidwh/frontend && lsof -ti:3000 | xargs -r kill && npm run dev
```

**Frontend Documentation:**
- Quick start: [frontend/README.md](frontend/README.md)
- Changelog: [frontend/CHANGELOG.md](frontend/CHANGELOG.md)
- Architecture: [frontend/docs/FRONTEND_ARCHITECTURE.md](frontend/docs/FRONTEND_ARCHITECTURE.md)
- Deployment: [frontend/docs/DEPLOYMENT_AZURE.md](frontend/docs/DEPLOYMENT_AZURE.md)
- UI Design System: [frontend/docs/UI_STANDARDIZATION_GUIDE.md](frontend/docs/UI_STANDARDIZATION_GUIDE.md)

**Latest Features (v2.9.0):**
- 🎨 **UI Redesign Phase 1** - Unified design system with modern gradient accents
- 🔍 **Path-Based Tracing** - Interactive upstream/downstream lineage exploration
- 📝 **Monaco SQL Viewer** - Professional SQL editor with syntax highlighting
- 🔒 **Trace Lock** - Preserve traced subset after exiting trace mode
- 📊 **DDL Display** - View table structure and stored procedure definitions
- 🎯 **Smart Filtering** - Schema, type, and pattern-based filtering

**Dual-Mode DDL System:**

The SQL Viewer automatically switches between two modes based on dataset size:

1. **Small Mode (JSON ≤10MB)**:
   - DDL is embedded directly in the JSON file
   - No backend API calls needed
   - Instant SQL display from memory
   - Best for: Sample data, demos, small datasets

2. **Large Mode (Parquet)**:
   - DDL fetched on-demand from DuckDB via API
   - Minimal memory footprint
   - Scalable to thousands of objects
   - Best for: Production data, full warehouse lineage

**How it works:**
- Frontend checks if `ddl_text` property exists in node data
- If present → Uses embedded DDL (Small mode)
- If absent → Calls `/api/ddl/{object_id}` (Large mode)
- Automatic, transparent switching - no user configuration needed

### Working with Backend API (v3.0.1)

```bash
# Start FastAPI server
cd /workspaces/ws-psidwh/api
python3 main.py  # Opens at http://localhost:8000

# Upload Parquet files via API
# IMPORTANT: Filenames don't matter! Backend auto-detects file types by schema.
curl -X POST http://localhost:8000/api/upload-parquet \
  -F "files=@part-00000.snappy.parquet" \
  -F "files=@part-00001.snappy.parquet" \
  -F "files=@part-00002.snappy.parquet" \
  -F "files=@part-00003.snappy.parquet" \
  -F "files=@part-00004.snappy.parquet"

# Incremental mode (default - recommended)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" -F "files=@..."

# Full refresh mode (re-parse everything)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" -F "files=@..."
```

**API Documentation:**
- API guide: [api/README.md](api/README.md)
- Test results: [api/TEST_RESULTS.md](api/TEST_RESULTS.md)

**Required Parquet Files:**
1. `objects.parquet` - Database objects metadata
2. `dependencies.parquet` - DMV-based dependencies (views/functions)
3. `definitions.parquet` - Object DDL from sys.sql_modules

**Optional Parquet Files:**
4. `query_logs.parquet` - Runtime query execution (for validation)
5. `table_columns.parquet` - Table column metadata (for DDL generation)

### Working with CLI Parser (v3.6.0)

```bash
# Run lineage analysis from Parquet snapshots
cd /workspaces/ws-psidwh
python lineage_v3/main.py run --parquet parquet_snapshots/

# Output: lineage_output/frontend_lineage.json (ready for frontend)

# Full refresh (re-parse everything)
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# Validate environment setup
python lineage_v3/main.py validate

# Get help
python lineage_v3/main.py --help
```

**Parser Documentation:**
- User guide: [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) ⭐ **Start here!**
- Evolution log: [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
- Specification: [lineage_specs.md](lineage_specs.md)


### Working with AI Disambiguation (Phase 1 - Testing)

```bash
# Test Azure OpenAI connection and model performance
cd /workspaces/ws-psidwh
python3 lineage_v3/ai_analyzer/test_azure_openai.py

# Prerequisites: Add to .env
# AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
# AZURE_OPENAI_API_KEY=your-api-key
# AZURE_OPENAI_MODEL_NAME=gpt-4.1-nano
# AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano
# AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**AI Documentation:**
- **[docs/AI_DISAMBIGUATION_SPEC.md](docs/AI_DISAMBIGUATION_SPEC.md)** ⭐ **Complete implementation specification (Phase 4 ready)**
- **[docs/AI_PHASE4_ACTION_ITEMS.md](docs/AI_PHASE4_ACTION_ITEMS.md)** ⭐ **Implementation checklist and action items**
- **[docs/AI_MODEL_EVALUATION.md](docs/AI_MODEL_EVALUATION.md)** - Testing results (Phase 1-3)
- [lineage_v3/ai_analyzer/README.md](lineage_v3/ai_analyzer/README.md) - Test overview and production artifacts
- [lineage_v3/ai_analyzer/COST_ANALYSIS.md](lineage_v3/ai_analyzer/COST_ANALYSIS.md) - ROI analysis ($100/year, 18x ROI)
- [lineage_v3/ai_analyzer/HALLUCINATION_ANALYSIS.md](lineage_v3/ai_analyzer/HALLUCINATION_ANALYSIS.md) - Risk assessment (LOW, 0% observed)
- [lineage_v3/ai_analyzer/TRAINING_DECISION.md](lineage_v3/ai_analyzer/TRAINING_DECISION.md) - Fine-tuning not recommended
- [lineage_v3/ai_analyzer/production_prompt.txt](lineage_v3/ai_analyzer/production_prompt.txt) - Production few-shot system prompt
- Test scripts: Phase 1-3 in [lineage_v3/ai_analyzer/](lineage_v3/ai_analyzer/)

**Phase 3 Results (2025-10-31):**
- ✅ Model: `gpt-4.1-nano` validated
- ✅ Accuracy: 91.7% on production scenarios (11/12 correct)
- ✅ Few-shot prompt (+33.4% vs zero-shot baseline)
- ✅ Cost: ~$0.0006 per disambiguation (~$0.15 per full parse run)
- ✅ Ready for Phase 4: Production integration

## Core Architecture

### Data Flow Pipeline

```
[Synapse DMVs] → PySpark Extractor → [Parquet Snapshots]
                                            ↓
                              DuckDB Workspace (Persistent)
                                            ↓
              ┌──────────────────────────────┼──────────────────────────┐
              ↓                              ↓                          ↓
    DMV Dependencies (1.0)                              SQLGlot Parser (0.85)
    (Views/Functions)                                   (Stored Procedures)
              └──────────────────────────────┼──────────────────────────┘
                                            ↓
                              Query Log Validation (0.85 → 0.95)
                              (Cross-validates parsed SPs)
                                            ↓
                              Lineage Merger (Bidirectional Graph)
                                            ↓
              ┌──────────────────────────────┼──────────────────────────┐
              ↓                              ↓                          ↓
    lineage.json (internal)    frontend_lineage.json        lineage_summary.json
    (int object_ids)           (string node_ids)            (coverage stats)
```

### Confidence Model

| Source | Confidence | Applied To | Description |
|--------|-----------|------------|-------------|
| **DMV** | 1.0 | Views, Functions | System metadata (`sys.sql_expression_dependencies`) |
| **Query Log** | 0.95 | Stored Procedures | Runtime execution confirmation |
| **SQLGlot Parser** | 0.85 | Stored Procedures | Static AST analysis of DDL |
| **Regex Baseline** | 0.50 | Stored Procedures | Fallback when SQLGlot fails |

**Current Performance (v3.6.0):**
- Total Objects: 202 stored procedures
- High Confidence (≥0.85): 163 (80.7%)
- Average Confidence: 0.800
- **2x better than industry average** (30-40% typical for T-SQL)

### JSON Output Formats

#### Internal Format (`lineage.json`)
Uses integer `object_id` from `sys.objects`:
```json
{
  "id": 1001,
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "inputs": [2002],
  "outputs": [3003],
  "provenance": {
    "primary_source": "dmv",
    "confidence": 1.0
  }
}
```

#### Frontend Format (`frontend_lineage.json`)
Uses string representation for React Flow:
```json
{
  "id": "1986106116",
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "description": "Confidence: 1.00",
  "data_model_type": "Dimension",
  "inputs": ["46623209"],
  "outputs": ["350624292", "366624349"],
  "ddl_text": "CREATE TABLE [CONSUMPTION_FINANCE].[DimCustomers] (\n    [CustomerID] int NOT NULL,\n    [CustomerName] nvarchar(200) NULL\n);"
}
```

**Note:** `ddl_text` contains:
- **Tables:** Generated CREATE TABLE statement (if `table_columns.parquet` provided)
- **Views/SPs:** Full DDL from `sys.sql_modules`
- `null` if metadata not available

---

## Parsing Modes

### Incremental Parsing (Default - Recommended)

**How it works:**
1. DuckDB workspace persists between uploads
2. Fresh data loaded from Parquet files
3. **Only modified objects are re-parsed** (compares `modify_date`)
4. Objects parsed if:
   - Never parsed before (new objects)
   - Modified since last parse (`modify_date > last_parsed_modify_date`)
   - Low confidence (<0.85, needs improvement)

**Benefits:**
- ⚡ **50-90% faster** for typical updates
- ✅ Smart detection of changes
- ✅ Preserves high-quality parse results

**Usage:**
```bash
# CLI (default)
python lineage_v3/main.py run --parquet parquet_snapshots/

# API (checkbox in UI, or query param)
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" -F "files=@..."
```

### Full Refresh Mode (Optional)

**How it works:**
1. All DuckDB tables are truncated
2. Fresh data loaded from Parquet files
3. **All objects re-parsed from scratch**

**When to use:**
- ✅ Ensuring parser bug fixes are applied to all objects
- ✅ Complete re-analysis needed
- ✅ Testing with fresh state

**Usage:**
```bash
# CLI
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# API
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" -F "files=@..."
```

---

## SQL Parsing Best Practices

### For DBAs and Developers

To achieve the best parsing results (confidence ≥0.85), follow these guidelines when writing stored procedures:

**✅ DO:**

1. **Use semicolons** to separate SQL statements
   ```sql
   TRUNCATE TABLE dbo.Staging;  -- ← Semicolon
   INSERT INTO dbo.Target SELECT * FROM dbo.Source;
   ```

2. **Use schema-qualified table names**
   ```sql
   -- GOOD: Explicit schema
   SELECT * FROM CONSUMPTION_FINANCE.DimCustomers;

   -- ACCEPTABLE: Defaults to dbo
   SELECT * FROM Customers;
   ```

3. **Separate error handling from business logic**
   ```sql
   BEGIN TRY
       -- Core business logic here (parsed)
       INSERT INTO dbo.Target SELECT * FROM dbo.Source;
   END TRY
   BEGIN CATCH
       -- Error handling (automatically filtered)
       EXEC dbo.LogError;
   END CATCH
   ```

**❌ DON'T:**

1. **Mix business logic with logging**
   ```sql
   -- BAD: ErrorLog appears in lineage
   INSERT INTO dbo.ErrorLog VALUES ('Starting...');
   INSERT INTO dbo.Target SELECT * FROM dbo.Source;
   ```

2. **Use dynamic SQL when static SQL works**
   ```sql
   -- BAD: Can't parse at compile time
   DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM ' + @TableName;
   EXEC(@sql);

   -- GOOD: Use static SQL when table is known
   SELECT * FROM dbo.Customers;
   ```

**📘 Complete Guide:** See [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) for:
- Supported SQL patterns (JOINs, CTEs, MERGE, etc.)
- What's out of scope (temp tables, dynamic SQL)
- Troubleshooting low confidence scores
- Understanding parser results

---

## Parser Development Guidelines

### CRITICAL: Read Before Modifying Parser Code

**Purpose:** Prevent regression and ensure continuous improvement of parser quality.

**Key Documents:**
- **Evolution Log:** [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md) - Track all changes
- **Regression Test:** [tests/parser_regression_test.py](tests/parser_regression_test.py) - Automated testing
- **User Guide:** [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) - SQL patterns

### Mandatory Process for Parser Changes

**NEVER modify parser code without following this process:**

#### Step 1: Document Issue
1. Identify the specific parsing problem (which SP fails, why?)
2. Document in [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
3. Include root cause, expected improvement, potential risks

#### Step 2: Capture Baseline
```bash
python tests/parser_regression_test.py --capture-baseline baselines/baseline_$(date +%Y%m%d).json
```

#### Step 3: Make Parser Changes
- Modify [lineage_v3/parsers/quality_aware_parser.py](lineage_v3/parsers/quality_aware_parser.py)
- Update version number in docstring
- Add detailed comments explaining WHY

#### Step 4: Run Regression Test
```bash
# Re-run parser with changes
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# Compare against baseline
python tests/parser_regression_test.py --compare baselines/baseline_YYYYMMDD.json
```

**Requirements to Pass:**
- ✅ Zero regressions (no high-confidence SPs drop below 0.85)
- ✅ At least one SP improves as expected
- ✅ Average confidence increases or stays same

#### Step 5: Update Documentation
- Update [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
- Document lessons learned
- Update baseline metrics

#### Step 6: Commit with Descriptive Message
```bash
git commit -m "Parser: Fix TRUNCATE handling - improves 2 SPs to 0.85

- Add TruncateTable extraction in _extract_from_ast()
- Zero regressions in baseline SPs
- Updated PARSER_EVOLUTION_LOG.md"
```

**Current Parser Status (v3.6.0):**
- Total SPs: 202
- High Confidence (≥0.85): 163 (80.7%)
- Average Confidence: 0.800
- Known Limitations: Ultra-complex SPs (11+ nested CTEs, 40K+ chars) exceed SQLGlot capability

---

## Synapse Data Warehouse Schema Architecture

The data warehouse uses a layered architecture with distinct schemas:

### STAGING Schemas
- **STAGING_CADENCE**: Staging tables for Cadence system data processing

### CONSUMPTION Schemas
- **CONSUMPTION_FINANCE**: Finance domain consumption layer
  - Dimension tables (DimProjects, DimCustomers, DimAccount, etc.)
  - Fact tables (FactGLSAP, FactGLCognos, FactAgingSAP, etc.)

- **CONSUMPTION_ClinOpsFinance**: Clinical Operations Finance integration
  - Cadence budget data, labor costs, earned value calculations

- **CONSUMPTION_POWERBI**: Tables optimized for Power BI reporting

- **CONSUMPTION_PRIMA**: Prima system data

- **CONSUMPTION_PRIMAREPORTING**: Prima reporting views

### Key SQL Patterns

**Stored Procedure Naming:**
- Pattern: `[Schema].[spLoad{TargetTable}]`
- Suffixes: `_Post`, `_Aggregations`, `_ETL`

**Error Handling:**
- All procedures use `BEGIN TRY...END TRY / BEGIN CATCH...END CATCH`
- Centralized logging: `dbo.LogMessage`, `dbo.spLastRowCount`

**Table Distribution:**
- `DISTRIBUTION = REPLICATE` - Small dimension tables
- `DISTRIBUTION = HASH([columns])` - Large fact tables
- `CLUSTERED COLUMNSTORE INDEX` - Fact tables

---

## Development Tools (Internal Use Only)

The following tools are for Vibecoding development team only, NOT for external distribution:

### Synapse Query Helper
- **File:** [lineage_v3/utils/synapse_query_helper.py](lineage_v3/utils/synapse_query_helper.py)
- **Usage:** `python lineage_v3/utils/synapse_query_helper.py`
- **Purpose:** Quick Synapse connection testing and DMV exploration during development

### Workspace Query Helper
- **File:** [lineage_v3/utils/workspace_query_helper.py](lineage_v3/utils/workspace_query_helper.py)
- **Usage:** `python lineage_v3/utils/workspace_query_helper.py`
- **Purpose:** DuckDB workspace queries, parser stats, debugging

**Note:** External users should use the production extractor ([extractor/synapse_pyspark_dmv_extractor.py](extractor/synapse_pyspark_dmv_extractor.py)) to generate Parquet files.

---

## Testing

### Smoke Tests (Devcontainer-Compatible)

Automated smoke tests validate critical paths without requiring GUI/browser:

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend serving
curl http://localhost:3000 | grep -q "react" && echo "✅ Frontend OK"

# API integration with CORS
curl -H "Origin: http://localhost:3000" http://localhost:8000/api/metadata
```

**Current Status:** ✅ All 8 smoke tests pass (see docs/OPTIMIZATION_COMPLETE.md)

### E2E Testing with Playwright (Outside Docker)

For comprehensive UI/UX testing, use Playwright **on your local machine or in CI/CD**:

**Why not in devcontainer?**
- Requires ~150MB of system libraries (chromium, libnss3, libatk, etc.)
- Adds unnecessary complexity to development environment
- Better suited for local development or GitHub Actions

**Setup (Local Machine):**
```bash
# On your local machine (NOT in devcontainer)
cd frontend/
npm install -D @playwright/test
npx playwright install chromium

# Run tests
npx playwright test
npx playwright test --headed  # With visible browser
```

**CI/CD Integration:**
See example GitHub Actions workflow in `docs/OPTIMIZATION_COMPLETE.md`

**Recommended Test Cases:**
- Concurrent upload blocking (HTTP 409)
- CORS security validation
- Frontend console error detection
- Upload workflow end-to-end

**Documentation:** [docs/OPTIMIZATION_COMPLETE.md](docs/OPTIMIZATION_COMPLETE.md#e2e-testing-with-playwright-post-uat)

---

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
python lineage_v3/main.py validate  # Check all dependencies
pip install -r requirements.txt     # Reinstall if needed
```

**Missing .env File:**
```bash
cp .env.template .env
# Edit .env with your credentials
```

**Parquet Files Not Found:**
- Ensure Parquet files are in `parquet_snapshots/` directory
- In dev: Run extractor script
- In prod: Obtain Parquet exports from DBA team

**Low Confidence Scores (<0.85):**
- Review [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) for SQL best practices
- Check `lineage_summary.json` for coverage stats
- Review `provenance.primary_source` to identify weak dependencies
- Consider manual validation for critical objects

**Frontend Not Loading Data:**
- Verify JSON file path in Import Data modal
- Check browser console for errors
- Ensure JSON format matches expected schema

---

## Git Safety & Cleanup

### What's Gitignored

The repository is configured to exclude:
- **Log files:** `*.log`
- **Database files:** `*.db`, `*.sqlite`, `lineage_workspace.*`
- **Generated output:** `lineage_output/*.json`, `data/latest_frontend_lineage.json`
- **Build artifacts:** `dist/`, `build/`, `node_modules/`, `__pycache__/`
- **Credentials:** `.env`, `.env.local`
- **Parquet snapshots:** `parquet_snapshots/*.parquet` (may contain sensitive data)

---

## For More Information

### Essential Documentation
- **User Guide:** [docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md) ⭐ **SQL parsing best practices**
- **Main README:** [README.md](README.md) - Project overview
- **Specification:** [lineage_specs.md](lineage_specs.md) - Parser v3.0 spec
- **Frontend Guide:** [frontend/README.md](frontend/README.md) - Frontend quick start
- **API Guide:** [api/README.md](api/README.md) - API documentation

### Additional Resources
- **Parser Evolution:** [docs/PARSER_EVOLUTION_LOG.md](docs/PARSER_EVOLUTION_LOG.md)
- **DuckDB Schema:** [docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md)
- **Query Logs Analysis:** [docs/QUERY_LOGS_ANALYSIS.md](docs/QUERY_LOGS_ANALYSIS.md)
- **AI Disambiguation:** [docs/AI_DISAMBIGUATION_SPEC.md](docs/AI_DISAMBIGUATION_SPEC.md)
- **AI Phase 4 Actions:** [docs/AI_PHASE4_ACTION_ITEMS.md](docs/AI_PHASE4_ACTION_ITEMS.md)
- **AI Model Evaluation:** [docs/AI_MODEL_EVALUATION.md](docs/AI_MODEL_EVALUATION.md)
- **Detail Search Spec:** [docs/DETAIL_SEARCH_SPEC.md](docs/DETAIL_SEARCH_SPEC.md)
- **Unified DDL Feature:** [docs/UNIFIED_DDL_FEATURE.md](docs/UNIFIED_DDL_FEATURE.md)
- **Frontend Architecture:** [frontend/docs/FRONTEND_ARCHITECTURE.md](frontend/docs/FRONTEND_ARCHITECTURE.md)
- **Azure Deployment:** [frontend/docs/DEPLOYMENT_AZURE.md](frontend/docs/DEPLOYMENT_AZURE.md)

---

**Last Updated:** 2025-10-31
**Parser Version:** v3.6.0 (Production Ready)
**Frontend Version:** v2.9.0 (Production Ready - UI Redesign Phase 1)
**API Version:** v3.0.1 (Production Ready)

---

## Testing

### Smoke Tests (Devcontainer-Compatible)

Automated smoke tests validate critical paths without requiring GUI/browser:

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend serving
curl http://localhost:3000 | grep -q "react" && echo "✅ Frontend OK"

# API integration with CORS
curl -H "Origin: http://localhost:3000" http://localhost:8000/api/metadata
```

**Current Status:** ✅ All 8 smoke tests pass (see [docs/OPTIMIZATION_COMPLETE.md](docs/OPTIMIZATION_COMPLETE.md))

### E2E Testing with Playwright (Outside Docker)

For comprehensive UI/UX testing, use Playwright **on your local machine or in CI/CD**:

**Why not in devcontainer?**
- Requires ~150MB of system libraries (chromium, libnss3, libatk, etc.)
- Adds unnecessary complexity to development environment  
- Better suited for local development or GitHub Actions

**Setup (Local Machine):**
```bash
# On your local machine (NOT in devcontainer)
cd frontend/
npm install -D @playwright/test
npx playwright install chromium

# Run tests
npx playwright test
npx playwright test --headed  # With visible browser
```

**CI/CD Integration:**
See example GitHub Actions workflow in [docs/OPTIMIZATION_COMPLETE.md](docs/OPTIMIZATION_COMPLETE.md)

**Recommended Test Cases:**
- Concurrent upload blocking (HTTP 409)
- CORS security validation
- Frontend console error detection
- Upload workflow end-to-end

**Documentation:** [docs/OPTIMIZATION_COMPLETE.md](docs/OPTIMIZATION_COMPLETE.md#e2e-testing-with-playwright-post-uat)
