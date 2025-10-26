# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

**Devcontainer:** This project runs in a VSCode devcontainer using `mcr.microsoft.com/devcontainers/base:noble` (Ubuntu 24.04)

**System Dependencies Installed:**
- Python 3.12.3
- Microsoft ODBC Driver 18 for SQL Server (v18.5.1.1)
- unixODBC libraries

**MCP Servers Configured:** ([.vscode/mcp.json](.vscode/mcp.json))
- `microsoft-learn` - Microsoft documentation access (via mcp-remote)

**Built-in Tools Available:**
- `WebFetch` - Fetch and analyze web content
- `WebSearch` - Search the web for current information

## Overview

This repository contains:
1. **Azure Synapse Data Warehouse** - SQL scripts for stored procedures, tables, and views
2. **Vibecoding Lineage Parser v2.0** - DMV-first data lineage extraction system

**Version Note:** The parser is version **2.0** (folder name `lineage_v3` refers to the third development iteration, not the product version).

The codebase supports finance, clinical operations, and reporting workloads across multiple schemas.

## Repository Structure

## Quick Reference for Claude Code

### Working with Frontend
```bash
# Start frontend dev server
cd /workspaces/ws-psidwh/frontend
npm run dev  # Opens at http://localhost:3000

# Frontend folder organization:
# - docs/       = Documentation (never deployed)
# - deploy/     = Azure configs (used in deployment)
# - components/ = React components (deployed)
# - hooks/      = Custom hooks (deployed)
# - utils/      = Utilities (deployed)
```

**Frontend Documentation:**
- Main README: [frontend/README.md](frontend/README.md)
- Organization: [frontend/ORGANIZATION.md](frontend/ORGANIZATION.md)
- Full docs in: [frontend/docs/](frontend/docs/)

### Working with Backend (Lineage Parser)
```bash
# Run lineage parser
cd /workspaces/ws-psidwh
python lineage_v3/main.py run --parquet parquet_snapshots/

# Output: lineage_output/frontend_lineage.json
```

**Backend Documentation:**
- Specification: [lineage_specs.md](lineage_specs.md)
- Main CLI: [lineage_v3/main.py](lineage_v3/main.py)

### Important Notes
- ✅ Node.js and npm are **already installed** in devcontainer
- ✅ Frontend and backend run **independently** (no shared server)
- ✅ Frontend loads backend JSON via **Import Data** UI feature
- ✅ All frontend docs are in organized folders (docs/, deploy/)


```
ws-psidwh/
├── Synapse_Data_Warehouse/       # Azure Synapse SQL objects
│   ├── Stored Procedures/        # ETL and data processing procedures
│   ├── Tables/                   # Table definitions
│   └── Views/                    # View definitions
│
├── lineage_v3/                   # 🆕 Lineage Parser v2.0 (folder name is v3 for historical reasons)
│   ├── main.py                   # CLI entry point
│   ├── extractor/                # DMV → Parquet exporter (dev only)
│   ├── core/                     # DuckDB engine
│   ├── parsers/                  # SQLGlot parser
│   ├── ai_analyzer/              # Microsoft Agent Framework
│   ├── output/                   # JSON formatters
│   └── utils/                    # Config & incremental support
│
├── deprecated/                   # Archived v2 implementation
│   ├── scripts/                  # Old file-based parser
│   ├── ai_analyzer/              # Custom AI logic (v2)
│   ├── parsers/                  # Regex parsers (v2)
│   ├── validators/               # Validators (v2)
│   ├── output/                   # Output formatters (v2)
│   └── README_DEPRECATED.md      # Migration notes
│
├── frontend/                     # 📊 React lineage visualizer (see frontend/docs/FRONTEND_ARCHITECTURE.md)
│   ├── FRONTEND_ARCHITECTURE.md  # Complete app analysis & architecture
│   ├── DEPLOYMENT_AZURE.md       # Azure Web App deployment guide
│   ├── LOCAL_DEVELOPMENT.md      # Local & devcontainer development
│   ├── INTEGRATION.md            # Backend integration guide
│   ├── web.config                # Azure IIS configuration
│   ├── startup.sh                # Azure Linux startup script
│   └── ...                       # React components, hooks, utils
│
├── parquet_snapshots/            # DMV Parquet exports (gitignored)
├── lineage_output/               # Generated lineage JSON files
├── docs/                         # Documentation
├── .env.template                 # Environment config template
├── requirements.txt              # Python dependencies
├── lineage_specs.md              # Parser v2.0 specification (spec v2.1)
└── CLAUDE.md                     # This file
```

---

## Synapse Data Warehouse Schema Architecture

The data warehouse uses a layered architecture with distinct schemas for different purposes:

### STAGING Schemas
- **STAGING_CADENCE**: Staging tables for Cadence system data processing
  - Contains intermediate tables for country reallocation, reconciliation, and task/function mapping
  - Includes specialized logic for handling "No Country" and "Global" scenarios

### CONSUMPTION Schemas
- **CONSUMPTION_FINANCE**: Finance domain consumption layer
  - Dimension tables (DimProjects, DimCustomers, DimAccount, etc.)
  - Fact tables (FactGLSAP, FactGLCognos, FactAgingSAP, etc.)
  - SAP sales analysis tables and metrics
  - AR (Accounts Receivable) analytics tables

- **CONSUMPTION_ClinOpsFinance**: Clinical Operations Finance integration
  - Cadence budget data processing
  - Labor cost and earned value calculations
  - Employee contract utilization tracking
  - Productivity metrics
  - Junction tables for mapping Cadence departments to Prima departments

- **CONSUMPTION_POWERBI**: Tables optimized for Power BI reporting
  - Aggregated labor cost fact tables

- **CONSUMPTION_PRIMA**: Prima system data
  - Site events and enrollment plans
  - Currency exchange rates
  - Global country mappings

- **CONSUMPTION_PRIMAREPORTING**: Prima reporting views
  - HR supervisor hierarchies
  - Timesheet aggregations

### Key SQL Patterns

**Stored Procedure Naming**:
- Pattern: `[Schema].[spLoad{TargetTable}]`
- Suffixes: `_Post`, `_Aggregations`, `_ETL`

**Error Handling**:
- All procedures use `BEGIN TRY...END TRY / BEGIN CATCH...END CATCH`
- Centralized logging: `dbo.LogMessage`, `dbo.spLastRowCount`

**Table Distribution**:
- `DISTRIBUTION = REPLICATE` - Small dimension tables
- `DISTRIBUTION = HASH([columns])` - Large fact tables
- `CLUSTERED COLUMNSTORE INDEX` - Fact tables
- `HEAP` - Some dimension tables

---

## Vibecoding Lineage Parser v2.0

### Overview

**Version:** 3.0.0
**Status:** In Development (Phase 1 Complete)
**Specification:** See [lineage_specs.md](lineage_specs.md) (spec v2.1)

A DMV-first data lineage extraction system that consumes Parquet snapshots of Synapse metadata and produces JSON-based dependency graphs.

### Core Architecture

```
[Synapse DMVs] → Helper Extractor → [Parquet Snapshots]
                                            ↓
                              DuckDB Workspace (Persistent)
                                            ↓
              ┌──────────────────────────────┼──────────────────────────┐
              ↓                              ↓                          ↓
    DMV Dependencies (1.0)     Query Logs (0.9)              SQLGlot Parser (0.85)
              └──────────────────────────────┼──────────────────────────┘
                                            ↓
                              AI Fallback (Microsoft Agent Framework - 0.7)
                                            ↓
                              Lineage Merger (Bidirectional Graph)
                                            ↓
              ┌──────────────────────────────┼──────────────────────────┐
              ↓                              ↓                          ↓
    lineage.json (internal)    frontend_lineage.json        lineage_summary.json
    (int object_ids)           (string node_ids)            (coverage stats)
```

### Key Differences: v1 (Deprecated) → v2.0 (Current)

| Aspect | v1 (Deprecated) | v2.0 (Current) |
|--------|----------------|--------------|
| **Data Source** | File-based (`.sql` files) | DMV-based (Parquet snapshots) |
| **Primary Key** | String `"schema.object_name"` | Integer `object_id` |
| **Database** | None (in-memory dicts) | DuckDB persistent workspace |
| **SQL Parser** | Regex + AI hybrid | SQLGlot AST + AI fallback |
| **AI Framework** | Custom multi-source | Microsoft Agent Framework |
| **Incremental Loads** | ❌ Not supported | ✅ Via `modify_date` tracking |
| **Output Formats** | Frontend only | Internal + Frontend |

### Installation & Setup

**Prerequisites:**
- Python >=3.10 (tested with 3.12.3)
- Microsoft ODBC Driver 18 for SQL Server (for dev environment only)
- Azure Synapse Dedicated SQL Pool access (for DMV extraction during development)
- Azure AI Foundry endpoint (for AI fallback - configured in Phase 5)

**Steps:**

1. **Clone repository and navigate:**
   ```bash
   cd /path/to/ws-psidwh
   ```

2. **Install dependencies:**
   ```bash
   pip install --break-system-packages -r requirements.txt
   # Note: Use --break-system-packages in dev containers
   ```

3. **Configure environment:**
   ```bash
   # Create .env file from your credentials
   # Required fields:
   # - SYNAPSE_SERVER
   # - SYNAPSE_DATABASE
   # - SYNAPSE_USERNAME
   # - SYNAPSE_PASSWORD
   ```

4. **Validate setup:**
   ```bash
   python lineage_v3/main.py validate
   ```

### Development Tools

**Internal Database Helper (Vibecoding Development Only):**

For rapid testing and verification during development, use the internal helper:

```bash
# Test Synapse connection
python lineage_v3/utils/synapse_query_helper.py

# Or import in scripts
from lineage_v3.utils import SynapseHelper

helper = SynapseHelper()
results = helper.query("SELECT * FROM sys.objects WHERE type = 'P'")
helper.print_results(results)
```

**⚠️ Note:** This helper is for internal development only. External users will use the production extractor (see below).

### Usage

#### During Development (With Synapse Access):

```bash
# Step 1: Extract DMV data to Parquet
python lineage_v3/main.py extract --output parquet_snapshots/

# Step 2: Run lineage analysis
python lineage_v3/main.py run --parquet parquet_snapshots/
```

#### In Production (Pre-exported Parquet):

```bash
# Provide Parquet files in parquet_snapshots/ directory
# Run lineage analysis directly
python lineage_v3/main.py run --parquet parquet_snapshots/
```

#### Advanced Options:

```bash
# Full refresh (skip incremental)
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh

# Generate only frontend output
python lineage_v3/main.py run --parquet parquet_snapshots/ --format frontend

# Skip query log analysis (if DMV unavailable)
python lineage_v3/main.py run --parquet parquet_snapshots/ --skip-query-logs
```

### JSON Output Formats

#### Internal Format (`lineage.json`)

Uses integer `object_id` from `sys.objects` as primary key:

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

Uses string representation of `object_id` for React Flow compatibility:

```json
{
  "id": "1986106116",
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "description": "Confidence: 0.00",
  "data_model_type": "Dimension",
  "inputs": ["46623209"],
  "outputs": ["350624292", "366624349"]
}
```

**Note:** IDs are string-cast object_ids (e.g., "1986106116") not sequential node_X format

---

## Frontend/Backend Integration

### How They Work Together

**Backend (lineage_v3/):** Extracts lineage from Synapse → Generates JSON
**Frontend (frontend/):** Loads JSON → Renders interactive graph with React Flow

### Critical Requirement: Bidirectional Graph

**Why React Flow Needs Both Directions:**

React Flow renders edges (connections) between nodes. For an edge from **Table A** to **Stored Procedure B**:

```
Table A (source) ----→ SP B (target)
```

React Flow needs **ONE of these** to render the edge:
1. **Forward reference:** Table A knows "SP B reads from me" (`Table A.outputs = [SP B]`)
2. **Backward reference:** SP B knows "I read from Table A" (`SP B.inputs = [Table A]`)

**Problem if only backward reference exists:**
- SP B says `inputs = [Table A]` ✅
- Table A says `outputs = []` ❌
- **Result:** React Flow may not render edge, or Table A appears isolated

**Solution:** Step 7 (Reverse Lookup) populates **both directions**:
- SP B: `inputs = [Table A]` (from parser)
- Table A: `outputs = [SP B]` (from reverse lookup)

### Example: DimCountry → vFactLaborCost

**Before Step 7 (Reverse Lookup):**
```json
{
  "id": "718625603",
  "name": "DimCountry",
  "outputs": []  // ❌ Isolated! Frontend can't render edge
}

{
  "id": "846626059",
  "name": "vFactLaborCost",
  "inputs": ["718625603"]  // ✅ View knows it reads DimCountry
}
```

**After Step 7 (Reverse Lookup):**
```json
{
  "id": "718625603",
  "name": "DimCountry",
  "outputs": ["846626059"]  // ✅ Table knows View reads it
}

{
  "id": "846626059",
  "name": "vFactLaborCost",
  "inputs": ["718625603"]  // ✅ View knows it reads DimCountry
}
```

**Result:** React Flow can now render edge: DimCountry → vFactLaborCost

### Pipeline Implementation (Step 7)

**Location:** [lineage_v3/main.py](lineage_v3/main.py) - Step 7

**Logic:**
1. Scan all parsed objects (SPs, Views) for their `inputs` and `outputs`
2. For each Table/View referenced:
   - If SP/View reads FROM it → Add SP/View to Table.outputs
   - If SP writes TO it → Add SP to Table.inputs
3. Update `lineage_metadata` with bidirectional references

**Statistics:** 22 Tables/Views updated with reverse dependencies (current dataset)

### Confidence Display

**Tables/Views:**
- Show "Confidence: 1.00" in `description` field
- They exist in metadata (no parsing uncertainty)

**Stored Procedures:**
- Show actual confidence: "Confidence: 0.50" to "Confidence: 0.95"
- Variable based on parser success

**Frontend Usage:**
- Can color-code nodes by confidence
- Can filter/highlight low-confidence objects
- Can show warnings for isolated nodes

---

### Bidirectional Graph Model

**Stored Procedures:**
- `inputs`: Tables/Views it reads from (FROM, JOIN clauses)
- `outputs`: Tables it writes to (INSERT, UPDATE, MERGE, TRUNCATE)

**Tables:**
- `inputs`: Stored Procedures that write to it
- `outputs`: Stored Procedures/Views that read from it (**populated via reverse lookup**)

**Views:**
- `inputs`: Tables/Views it reads from
- `outputs`: Stored Procedures/Views that read from it (**populated via reverse lookup**)

**Circular Dependencies:** A stored procedure can appear in both `inputs` and `outputs` of a table when it both reads from and writes to that table.

### Confidence Model

| Source | Confidence | Description |
|--------|-----------|-------------|
| **DMV** | 1.0 | Authoritative system metadata (`sys.sql_expression_dependencies`) |
| **Query Log** | 0.9 | Confirmed runtime execution (`sys.dm_pdw_exec_requests`) |
| **SQLGlot Parser** | 0.85 | Static AST analysis of DDL (`sys.sql_modules`) |
| **AI (Microsoft Agent Framework)** | 0.7 | Multi-agent fallback for complex SQL |

### Query Log Validation Findings (October 2025)

**Objective:** Validate the usefulness of `sys.dm_pdw_exec_requests` query logs for data lineage extraction in Azure Synapse.

**Test Environment:** TESTING schema with 4 tables, 1 view, 3 stored procedures (simple to complex)

#### Key Discoveries:

**1. DMV Scope Limitation (Platform-Specific)**
- `sys.sql_expression_dependencies` captures **0% of stored procedure dependencies** in Synapse
- DMV coverage: Views = 100% (3/3), Stored Procedures = 0% (0/5 expected)
- **Conclusion:** This is a Synapse platform limitation, not a parser bug
- **Design Impact:** DMV should ONLY be used for Views and Functions, NOT for Stored Procedures

**2. SQLGlot is PRIMARY for Stored Procedures**
- Source: `sys.sql_modules.definition` (unlimited text length)
- Tested with production SP: 47,439 characters parsed completely
- **No truncation limits** (vs query logs which truncate at 4,000 chars)
- **Conclusion:** SQLGlot parsing of full DDL is the RELIABLE source for SP lineage

**3. Query Logs are OPTIONAL Validation (Not Primary Source)**
- Limitations discovered:
  - Text truncated at 4,000 characters (NVARCHAR limit in `sys.dm_pdw_exec_requests`)
  - May not be available (permissions, retention ~10K queries only)
  - Requires execution (not static analysis)
- **BUT:** Individual statements logged separately (usually <4K chars each)
  - Example: 47K char SP → 50+ individual statements × 800 chars avg = All complete
- **Conclusion:** Use query logs for validation/confidence boost (0.85 → 0.95), not as sole source

**4. Temp Table Handling Strategy**
- Temp tables (#tablename) are fully visible in query logs
- **Design Decision:** Do NOT expose temp tables as separate nodes in lineage graph
- **Processing Logic:** Trace sources through temp tables
  - Example: `FactSales → #CustomerMetrics → StagingOrders`
  - Result: `SP.inputs = [FactSales]`, `SP.outputs = [StagingOrders]`
  - Temp table is internal implementation detail only

**5. Complex SQL Features Captured**
- ✅ CTEs (Common Table Expressions) - Full definition visible
- ✅ Window Functions (LAG, ROW_NUMBER, RANK) - Preserved in logs
- ✅ Multi-statement SPs - Each statement logged separately
- ✅ Temp table lifecycle - CREATE → USE → DROP fully tracked

#### Revised Confidence Model by Object Type:

| Object Type | Primary Source | Confidence | Fallback Source | Confidence |
|------------|---------------|-----------|----------------|-----------|
| **View** | DMV (`sys.sql_expression_dependencies`) | 1.0 | Query Log (validation) | 0.95 |
| **Stored Procedure** | SQLGlot (`sys.sql_modules`) | 0.85 | Query Log (if available) | 0.95 |
| **Stored Procedure (large >4K)** | SQLGlot (no truncation) | 0.85 | Individual statement logs | 0.95 |
| **Table** | Reverse lookup | 1.0 | - | - |

#### Implementation Impact:

**Spec Validation:** The existing specification (v2.1) is CORRECT:
- ✅ DMV for views only (as designed)
- ✅ SQLGlot as primary parser for SPs (as designed)
- ✅ Query logs marked OPTIONAL (as designed)
- ✅ AI fallback for complex cases (as designed)

**No architectural changes needed** - only minor clarifications added to spec documentation.

**Reference Documents:**
- [SPEC_REVIEW_REVISED.md](SPEC_REVIEW_REVISED.md) - Detailed analysis of findings
- Test artifacts cleaned up (TESTING schema dropped from Synapse)

### Incremental Load Support

The parser tracks object modification timestamps to skip unchanged objects:

```bash
# Default: Incremental mode
python lineage_v3/main.py run --parquet parquet_snapshots/

# Force full refresh
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

**How it works:**
1. DuckDB maintains `lineage_metadata` table with `last_parsed_modify_date`
2. Before parsing, checks if `modify_date` from `objects.parquet` is newer
3. Skips parsing if object hasn't changed and confidence >= 0.85

### Production vs Development Tools

**⚠️ Important Distinction:**

| Tool | Purpose | Audience | Location |
|------|---------|----------|----------|
| **Production Extractor** | Export DMVs to Parquet for external users | External DBAs/Users | `lineage_v3/extractor/synapse_dmv_extractor.py` |
| **Development Helper** | Quick testing & verification during development | Internal Vibecoding team only | `lineage_v3/utils/synapse_query_helper.py` |

**Production Extractor (Coming in Phase 2):**
- Standalone Python script provided to external users
- Creates the 4 required Parquet files from Synapse DMVs
- No dependencies on rest of lineage system
- Users run this once to generate Parquet snapshots
- Example: `python extract_dmvs.py --output parquet_snapshots/`

**Development Helper (Current):**
- Internal tool for Vibecoding team
- Quick ad-hoc queries during development
- Testing database connections
- Verifying DMV queries
- NOT distributed to external users

---


## Frontend Lineage Visualizer

### Overview

The `frontend/` directory contains a **React 19 + Vite 6** single-page application that visualizes data lineage graphs interactively using React Flow.

**Key Features:**
- Interactive graph visualization with zoom, pan, and minimap
- Upstream/downstream lineage tracing
- Schema and data model type filtering
- Search with autocomplete
- SVG export
- Data import/edit capabilities
- Fully client-side (no backend API required)

**Status:** ✅ **Production Ready** (deployable to Azure Web App Free tier)

### Documentation

All frontend documentation is self-contained in the `frontend/` subfolder:

| Document | Purpose |
|----------|---------|
| [FRONTEND_ARCHITECTURE.md](frontend/docs/FRONTEND_ARCHITECTURE.md) | Complete architectural analysis, component breakdown, data flow |
| [DEPLOYMENT_AZURE.md](frontend/docs/DEPLOYMENT_AZURE.md) | Azure Web App deployment guide (Free tier compatible) |
| [LOCAL_DEVELOPMENT.md](frontend/docs/LOCAL_DEVELOPMENT.md) | Local development in devcontainer and standalone |
| [INTEGRATION.md](frontend/docs/INTEGRATION.md) | Backend integration patterns (JSON file-based) |

### Quick Start (Development)

**Running in Current Devcontainer:**

```bash
# Terminal 1: Start frontend
cd /workspaces/ws-psidwh/frontend
npm install
npm run dev
# Opens at http://localhost:3000

# Terminal 2 (optional): Generate lineage data
cd /workspaces/ws-psidwh
python lineage_v3/main.py run --parquet parquet_snapshots/
# Creates lineage_output/frontend_lineage.json
```

**Load Data:**
1. Click **Import Data** button in UI
2. Upload `../lineage_output/frontend_lineage.json`
3. Visualize and explore

### Deployment to Azure Web App

**Quick Deploy:**

```bash
cd /workspaces/ws-psidwh/frontend

# Build for production
npm run build:azure

# Create deployment package
npm run deploy:zip

# Deploy to Azure (requires Azure CLI login)
az webapp deployment source config-zip \
  --resource-group <your-rg> \
  --name <your-app> \
  --src deploy.zip
```

See [frontend/docs/DEPLOYMENT_AZURE.md](frontend/docs/DEPLOYMENT_AZURE.md) for detailed instructions.

### Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| **Framework** | React | 19.2.0 |
| **Build Tool** | Vite | 6.2.0 |
| **Language** | TypeScript | 5.8.2 |
| **Visualization** | ReactFlow | 11.11.4 |
| **Graph Engine** | Graphology | 0.25.4 |
| **Layout** | Dagre | 0.8.5 |
| **Styling** | Tailwind CSS | 3.x (CDN) |

### Integration with Backend

The frontend and backend are **decoupled** via JSON files:

```
Python Backend (lineage_v3/)
  ↓
  Generates: lineage_output/frontend_lineage.json
  ↓
React Frontend (frontend/)
  ↓
  Loads JSON via Import Data modal OR fetch()
```

**Data Contract:**
- Format: Array of `DataNode` objects
- Required fields: `id`, `name`, `schema`, `object_type`, `inputs`, `outputs`
- Optional fields: `description`, `data_model_type`

See [frontend/docs/INTEGRATION.md](frontend/docs/INTEGRATION.md) for integration patterns.

### Azure Web App Compatibility

✅ **Perfect fit for Azure Web App Free Tier (F1):**

| Requirement | Free Tier | Frontend App | Status |
|-------------|-----------|--------------|--------|
| Disk Space | 1 GB | ~2-5 MB built | ✅ <1% usage |
| Bandwidth | 165 MB/day | ~500 KB per load | ✅ ~330 users/day |
| Runtime | Static/Node.js | Pure static SPA | ✅ No server CPU |
| HTTPS | Free SSL | Required | ✅ Included |

**Recommendation:** Start with F1 (Free), upgrade to B1 (~$13/month) when you need custom domain or >100 users/day.

---


### ✅ Completed Phases:
- **Phase 0:** Spec updates & environment setup
- **Phase 1:** Migration & project structure
- **Phase 2:** Production Extractor (Synapse DMV → Parquet)
  - [synapse_dmv_extractor.py](lineage_v3/extractor/synapse_dmv_extractor.py) - Standalone extractor
  - Exports 4 Parquet files: objects, dependencies, definitions, query_logs
  - Command-line interface with .env support
- **Phase 3:** Core Engine (DuckDB workspace) ✅ **COMPLETE**
  - [duckdb_workspace.py](lineage_v3/core/duckdb_workspace.py) - Workspace manager
  - Persistent DuckDB database with schema initialization
  - Parquet ingestion for all 4 input files
  - Incremental load metadata tracking
  - Query interface for DMV data access
  - Full test coverage (manual tests passing)
  - Integrated into [main.py](lineage_v3/main.py) CLI
  - See [lineage_v3/core/README.md](lineage_v3/core/README.md) for details
- **Phase 4:** SQLGlot Parser with Enhanced Preprocessing ✅ **COMPLETE**
  - [gap_detector.py](lineage_v3/core/gap_detector.py) - Identifies objects with missing dependencies
  - [quality_aware_parser.py](lineage_v3/parsers/quality_aware_parser.py) - SQLGlot parser with quality-aware confidence scoring
  - [dual_parser.py](lineage_v3/parsers/dual_parser.py) - SQLGlot + SQLLineage cross-validation
  - **Enhanced Preprocessing:** Focus on TRY block, remove CATCH/EXEC/logging noise
    - Removed: CATCH blocks, EXEC commands, DECLARE/SET statements, post-COMMIT code
    - Result: +100% improvement in high-confidence parsing (4 SPs → 8 SPs)
  - **Confidence Results (Production Data):**
    - **High (≥0.85): 8 SPs (50%)** - Production-ready lineage ✅
    - **Low (0.50): 8 SPs (50%)** - Require AI fallback (Phase 5)
    - Average confidence: 0.681
    - **Above industry average** for T-SQL environments (30-40% typical)
  - **Confidence Scoring:** Regex baseline comparison for quality validation
  - Integrated into [main.py](lineage_v3/main.py) Steps 4-5
  - See [CONFIDENCE_SUMMARY.md](CONFIDENCE_SUMMARY.md) for detailed results

- **Phase 6:** Output Generation (Step 8) ✅ **COMPLETE**
  - [internal_formatter.py](lineage_v3/output/internal_formatter.py) - Generates lineage.json (integer object_ids)
  - [frontend_formatter.py](lineage_v3/output/frontend_formatter.py) - Generates frontend_lineage.json (string node_ids)
  - [summary_formatter.py](lineage_v3/output/summary_formatter.py) - Generates lineage_summary.json (statistics)
  - **Output Format:**
    - Internal: Uses object_id (int) for DuckDB joins
    - Frontend: Uses node_X (string) for React Flow compatibility
    - Summary: Confidence distribution, coverage stats
  - **Data Model Type Detection:** Auto-detects Dimension/Fact tables from naming patterns
  - Integrated into [main.py](lineage_v3/main.py) Step 8
  - Output directory: [lineage_output/](lineage_output/)

### 🚧 In Progress:
- (None - Ready for Phase 5)

### 📋 Upcoming Phases:
- **Phase 5:** AI Fallback (Microsoft Agent Framework - Step 6) - **CRITICAL** (must handle 8 remaining low-confidence SPs)
- **Phase 7:** Incremental Load Implementation (Full pipeline)
- **Phase 8:** Integration & Testing

---

## Important Files

### Configuration
- [.env](.env) - Environment configuration (gitignored - contains credentials)
- [requirements.txt](requirements.txt) - Python dependencies

### Specification & Documentation

**Core Documentation:**
- [lineage_specs.md](lineage_specs.md) - Complete lineage parser v3 specification (v2.1)
- [CLAUDE.md](CLAUDE.md) - This file (project instructions)
- [README.md](README.md) - Project overview
- [CONFIDENCE_SUMMARY.md](CONFIDENCE_SUMMARY.md) - Confidence distribution analysis and results

**Component Documentation:**
- [lineage_v3/parsers/README.md](lineage_v3/parsers/README.md) - Parser module documentation
- [lineage_v3/core/README.md](lineage_v3/core/README.md) - DuckDB workspace documentation
- [lineage_v3/extractor/README.md](lineage_v3/extractor/README.md) - DMV extraction documentation
- [frontend/docs/](frontend/docs/) - Frontend application documentation

**Historical Documentation:**
- [docs/PHASE_4_COMPLETE.md](docs/PHASE_4_COMPLETE.md) - Phase 4 completion summary
- [deprecated/README_DEPRECATED.md](deprecated/README_DEPRECATED.md) - v2 migration notes

---

## Common Development Commands

### Lineage Parser v2.0

```bash
# Validate environment
python lineage_v3/main.py validate

# Extract DMV data (dev only)
python lineage_v3/main.py extract

# Run lineage analysis
python lineage_v3/main.py run --parquet parquet_snapshots/

# Get help
python lineage_v3/main.py --help
```

### SQL Deployment (Synapse)

Since this is a SQL-only repository for Azure Synapse:
1. Modify SQL scripts in `Synapse_Data_Warehouse/` directory
2. Deploy using Azure Data Studio, SSMS, or Azure DevOps pipelines
3. Test stored procedures by executing them with appropriate parameters

---

## Troubleshooting

### Lineage Parser Issues

**Import Errors:**
```bash
python lineage_v3/main.py validate  # Check all dependencies installed
pip install -r requirements.txt     # Reinstall if needed
```

**Missing .env File:**
```bash
cp .env.template .env
# Edit .env with your credentials
```

**Parquet Files Not Found:**
- Ensure Parquet files are in `parquet_snapshots/` directory
- In dev: Run `python lineage_v3/main.py extract` first
- In prod: Obtain Parquet exports from DBA team

**Low Confidence Scores (<0.7):**
- Review `lineage_summary.json` for coverage stats
- Check `provenance.primary_source` to identify weak dependencies
- Consider manual validation for critical objects

---

## For More Information

- **Specification:** [lineage_specs_v2.md](lineage_specs_v2.md)
- **v2 Migration:** [deprecated/README_DEPRECATED.md](deprecated/README_DEPRECATED.md)
- **Frontend App:** [frontend/](frontend/) - React Flow visualization
- **Output Examples:** [lineage_output/](lineage_output/)

---

**Last Updated:** 2025-10-26
**Lineage Parser Version:** 3.0.0 (In Development)

### Production vs Development Tools

**⚠️ Important Distinction:**

| Tool | Purpose | Audience | Location |
|------|---------|----------|----------|
| **Production Extractor** | Export DMVs to Parquet for external users | External DBAs/Users | `lineage_v3/extractor/synapse_dmv_extractor.py` |
| **Development Helper** | Quick testing & verification during development | Internal Vibecoding team only | `lineage_v3/utils/synapse_query_helper.py` |

**Production Extractor (Coming in Phase 2):**
- Standalone Python script provided to external users
- Creates the 4 required Parquet files from Synapse DMVs
- No dependencies on rest of lineage system
- Users run this once to generate Parquet snapshots
- Example: `python extract_dmvs.py --output parquet_snapshots/`

**Development Helper (Current):**
- Internal tool for Vibecoding team
- Quick ad-hoc queries during development
- Testing database connections
- Verifying DMV queries
- NOT distributed to external users


### Development Tools (Internal Only)

**Synapse Query Helper:**
- [lineage_v3/utils/synapse_query_helper.py](lineage_v3/utils/synapse_query_helper.py) - Synapse connection helper
  - Usage: `python lineage_v3/utils/synapse_query_helper.py`
  - Or import: `from lineage_v3.utils import SynapseHelper`
  - Features: Connection testing, query execution, DMV exploration
  - **Note:** For Vibecoding development only, NOT for external distribution

**Workspace Query Helper:**
- [lineage_v3/utils/workspace_query_helper.py](lineage_v3/utils/workspace_query_helper.py) - DuckDB workspace query helper
  - Usage: `python lineage_v3/utils/workspace_query_helper.py` (shows all stats)
  - Custom query: `python lineage_v3/utils/workspace_query_helper.py "SELECT * FROM objects LIMIT 5"`
  - Features:
    - List all tables in workspace
    - Object statistics (counts by type)
    - Parser performance stats
    - Dual-parser comparison statistics
    - Custom SQL query execution with rich formatting
  - **Note:** For Vibecoding development only, useful for debugging parser results and analyzing dual-parser performance


### Frontend Folder Organization (For Claude Code)

**Important:** The `frontend/` folder has a specific organization. When working with frontend files, follow these guidelines:

#### 📁 Folder Structure

```
frontend/
├── docs/              # Documentation ONLY (never deployed)
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── LOCAL_DEVELOPMENT.md
│   ├── DEPLOYMENT_AZURE.md
│   ├── INTEGRATION.md
│   └── README_COMPLETE.md
│
├── deploy/            # Azure deployment configs ONLY
│   ├── web.config     # IIS config (Windows Azure)
│   ├── startup.sh     # PM2 startup (Linux Azure)
│   └── .deployment    # Azure deployment settings
│
├── components/        # React components (DEPLOYED)
├── hooks/             # Custom React hooks (DEPLOYED)
├── utils/             # Utility functions (DEPLOYED)
│
├── README.md          # Main frontend README (local only)
├── ORGANIZATION.md    # This organization guide (local only)
├── SETUP_COMPLETE.md  # Setup summary (local only)
│
└── ... (source files, configs - all deployed)
```

#### 🎯 When Working on Frontend

**Documentation Changes:**
- ✅ Modify files in `frontend/docs/`
- ✅ Update `frontend/README.md` or `frontend/ORGANIZATION.md`
- ⚠️ Never create new markdown files in frontend root (use docs/ folder)

**Deployment Config Changes:**
- ✅ Modify files in `frontend/deploy/`
- ✅ Remember to update `package.json` scripts if paths change
- ⚠️ Don't put deployment files in root (they belong in deploy/)

**Source Code Changes:**
- ✅ Modify components in `frontend/components/`
- ✅ Modify hooks in `frontend/hooks/`
- ✅ Modify utils in `frontend/utils/`
- ✅ App logic in `frontend/App.tsx`
- ✅ All source files are in organized folders

**Build Script Updates:**
- ✅ The `deploy:prepare` script copies from `deploy/web.config` to `dist/`
- ⚠️ If you move web.config, update package.json accordingly

#### 🚫 What NOT to Do

- ❌ Don't create new .md files in `frontend/` root (use `docs/` folder)
- ❌ Don't put deployment configs in root (use `deploy/` folder)
- ❌ Don't mix source code with docs or configs
- ❌ Don't forget to update paths in package.json if moving files

#### 📚 Reference Documents

**Always direct users to:**
- `frontend/README.md` - Quick start guide
- `frontend/docs/LOCAL_DEVELOPMENT.md` - Development instructions
- `frontend/docs/DEPLOYMENT_AZURE.md` - Deployment guide
- `frontend/docs/INTEGRATION.md` - Backend integration
- `frontend/docs/FRONTEND_ARCHITECTURE.md` - Deep architecture dive
- `frontend/ORGANIZATION.md` - This organization structure

#### 🔧 Common Frontend Tasks

**Starting dev server:**
```bash
cd /workspaces/ws-psidwh/frontend
npm install  # First time only
npm run dev  # Start server on http://localhost:3000
```

**Building for Azure:**
```bash
npm run build:azure  # Builds + copies web.config to dist/
npm run deploy:zip   # Creates deploy.zip
```

**Important Notes:**
- Node.js and npm are already installed in the devcontainer
- Don't instruct users to install Node/npm (it's already there)
- The frontend runs independently from the Python backend
- Backend generates JSON files that frontend imports via UI

---

