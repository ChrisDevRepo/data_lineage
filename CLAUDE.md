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
├── frontend/                     # React Flow visualization app
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
python lineage_v3/utils/db_helper.py

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

Uses string `node_X` format for React Flow compatibility:

```json
{
  "id": "node_0",
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "description": "",
  "data_model_type": "Dimension",
  "inputs": ["node_1"],
  "outputs": ["node_2", "node_3"]
}
```

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
| **Development Helper** | Quick testing & verification during development | Internal Vibecoding team only | `lineage_v3/utils/db_helper.py` |

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

## Development Status

### ✅ Completed Phases:
- **Phase 0:** Spec updates & environment setup
- **Phase 1:** Migration & project structure
- **Setup:** Development environment validated
  - Python 3.12.3 installed
  - All 137 dependencies installed
  - ODBC drivers configured
  - Database connection tested
  - Internal helper created

### 🚧 In Progress:
- **Phase 2:** Production Extractor (Synapse DMV → Parquet)

### 📋 Upcoming Phases:
- **Phase 3:** Core Engine (DuckDB workspace)
- **Phase 4:** SQLGlot Parser
- **Phase 5:** AI Fallback (Microsoft Agent Framework)
- **Phase 6:** Output Formatters
- **Phase 7:** Incremental Load Implementation
- **Phase 8:** Integration & Testing

---

## Important Files

### Configuration
- [.env](.env) - Environment configuration (gitignored - contains credentials)
- [requirements.txt](requirements.txt) - Python dependencies

### Specification & Documentation
- [lineage_specs_v2.md](lineage_specs_v2.md) - Complete v3 specification (v2.1)
- [CLAUDE.md](CLAUDE.md) - This file

### Legacy Documentation (Archived)
- [deprecated/README_DEPRECATED.md](deprecated/README_DEPRECATED.md) - v2 migration notes
- Old v2 docs moved to [deprecated/](deprecated/) folder

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
| **Development Helper** | Quick testing & verification during development | Internal Vibecoding team only | `lineage_v3/utils/db_helper.py` |

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
- [lineage_v3/utils/db_helper.py](lineage_v3/utils/db_helper.py) - Database helper for testing and verification
  - Usage: `python lineage_v3/utils/db_helper.py`
  - Or import: `from lineage_v3.utils import SynapseHelper`
  - Features: Connection testing, query execution, DMV exploration
  - **Note:** For Vibecoding development only, NOT for external distribution

