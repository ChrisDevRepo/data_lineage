# Data Lineage Visualizer - System Overview

**Version:** 4.1.3 (Parser) | 2.9.x (Frontend) | 4.0.3 (API)
**Status:** Production Ready
**Last Updated:** 2025-11-06

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Performance Characteristics](#performance-characteristics)
7. [Security Model](#security-model)

---

## Introduction

The Data Lineage Visualizer is a **3-tier monolithic web application** that provides interactive visualization of data lineage for Azure Synapse Analytics environments. It enables data engineers and analysts to understand data flow, trace dependencies, and analyze the impact of changes across complex data warehouses.

### Key Capabilities

- **Automated Lineage Extraction** - Parses SQL definitions from Azure Synapse using multi-strategy approach (Regex + SQLGlot + Rule Engine)
- **Interactive Visualization** - Browser-based graph exploration with 5,000+ node capacity
- **Path Tracing** - Upstream/downstream dependency analysis and impact assessment
- **Full-Text Search** - Search across all SQL definitions and object metadata
- **No Live Database Required** - Works entirely with pre-exported Parquet snapshots

### Target Users

- **Data Engineers** - Understanding data pipelines and dependencies
- **Data Analysts** - Tracing data sources and transformations
- **DBAs** - Impact analysis before schema changes
- **Data Governance Teams** - Documenting data lineage for compliance

---

## System Architecture

### High-Level Architecture

The system follows a **3-tier monolithic architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                     TIER 1: Presentation                        │
│                  React Frontend (Browser)                       │
│   - React Flow graph visualization                             │
│   - Monaco Editor (SQL viewer)                                 │
│   - Tailwind CSS UI                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST/JSON (HTTP)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     TIER 2: Business Logic                      │
│                  FastAPI Backend + Parser                       │
│   ┌──────────────┐        ┌──────────────────┐                │
│   │  FastAPI API │◄──────►│ Quality-Aware     │                │
│   │  Gateway     │        │ Parser (v4.1.3)   │                │
│   │  (v4.0.3)    │        │                   │                │
│   └──────────────┘        └──────────────────┘                │
└────────────────────────────┬────────────────────────────────────┘
                             │ SQL Queries
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     TIER 3: Persistence                         │
│                  DuckDB File-Based Database                     │
│   - Objects, Dependencies, Definitions                          │
│   - Lineage metadata and confidence scores                     │
│   - Query logs (optional validation)                           │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Stateless Frontend** - All state derived from API responses
2. **Background Processing** - Long-running parser jobs don't block UI
3. **File-Based Persistence** - No database server required (DuckDB file)
4. **Ephemeral Storage** - Job files in `/tmp/` (acceptable for this use case)
5. **Incremental Processing** - Re-parse only changed or low-confidence objects

---

## Technology Stack

### Frontend (Tier 1)

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.2.0 | UI framework |
| **TypeScript** | 5.8.2 | Type safety |
| **Vite** | 6.2.0 | Build tool |
| **ReactFlow** | 11.11.4 | Graph visualization |
| **Graphology** | 0.25.4 | Graph algorithms (path finding) |
| **Dagre** | 0.8.5 | Layout engine (hierarchical) |
| **Monaco Editor** | 4.7.0 | SQL viewer with syntax highlighting |
| **Tailwind CSS** | 3.x | Styling |

### Backend (Tier 2)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12+ | Runtime |
| **FastAPI** | 0.115+ | API framework |
| **DuckDB** | 1.4.1 | In-process SQL database |
| **SQLGlot** | 25.x | SQL parser |
| **Pydantic** | 2.x | Data validation |

### Parser Components

| Component | Strategy | Confidence |
|-----------|----------|-----------|
| **DMV Metadata** | Direct from sys views | 1.0 (Perfect) |
| **Query Log Validation** | Execution history | 0.95 (Validated) |
| **SQLGlot Parser** | AST-based SQL parsing | 0.85 (High) |
| **Regex Fallback** | Pattern matching | 0.50 (Medium) |
| **Rule Engine** | Custom T-SQL handling | Boosts confidence |

### Infrastructure

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Development** | WSL2 Ubuntu | Linux environment on Windows |
| **Production** | Azure App Service | PaaS deployment |
| **Frontend Hosting** | Azure Static Web Apps | CDN-backed static hosting |

---

## Core Components

### 1. PySpark Extractor (Not Included)

**Location:** `/extractor/`
**Purpose:** Exports DMV data from Azure Synapse to Parquet files

**Exports:**
- `objects.parquet` - Tables, views, SPs from `sys.objects` + `sys.schemas`
- `dependencies.parquet` - From `sys.sql_expression_dependencies`
- `definitions.parquet` - SQL DDL from `sys.sql_modules`
- `query_logs.parquet` (optional) - From `sys.dm_pdw_exec_requests`
- `table_columns.parquet` (optional) - Column metadata for DDL

**Note:** Extractor runs in Synapse environment, not part of this web application.

### 2. FastAPI Backend

**Location:** `/api/`
**Port:** 8000
**Version:** 4.0.3

**Key Features:**
- **Upload Endpoint** - Accepts 3-5 Parquet files
- **Background Processing** - Non-blocking parse jobs with polling
- **Job Management** - Create, monitor, cleanup jobs
- **Search API** - Full-text DDL search across all objects
- **Health Checks** - `/health` endpoint for orchestration

**Job Lifecycle:**
```
1. POST /api/upload-parquet → Create job_id, save files
2. Background thread starts parsing
3. GET /api/status/{job_id} → Poll every 2s for progress
4. GET /api/result/{job_id} → Retrieve final lineage JSON
```

### 3. Quality-Aware Parser

**Location:** `/lineage_v3/`
**Version:** 4.1.3
**Performance:** 95.5% high confidence (729/763 objects)

**Features:**
- **Multi-Strategy Parsing** - Regex → SQLGlot → Rule Engine → Validation
- **Confidence Scoring** - Unified calculator for all parsing methods
- **Dataflow Mode** - Shows only DML (filters out DDL and admin queries)
- **SP-to-SP Lineage** - Tracks EXEC/EXECUTE stored procedure calls
- **Incremental Mode** - Re-parses only new/modified/low-confidence objects
- **Zero Circular Dependencies** - IF EXISTS filtering eliminates false dependencies

**Parsing Pipeline:**
```
1. Load Parquet → DuckDB
2. Identify objects to parse (new/modified/low confidence)
3. For each stored procedure:
   a. Preprocess (normalize semicolons, remove IF EXISTS)
   b. Try SQLGlot parser
   c. Fallback to regex if SQLGlot fails
   d. Apply rule engine (orchestrator detection, target exclusion)
   e. Calculate confidence score
4. Validate with query logs (if available)
5. Generate frontend JSON
```

### 4. React Frontend

**Location:** `/frontend/`
**Port:** 3000
**Version:** 2.9.x

**Key Features:**
- **Interactive Graph** - Pan, zoom, select, highlight dependencies
- **Trace Mode** - Upstream/downstream exploration, path-between-nodes
- **SQL Viewer** - Click nodes to view definitions with syntax highlighting
- **Detail Search** - Full-text search with resizable side panels
- **Smart Filtering** - Schema, object type, pattern-based filtering
- **Trace Lock** - Preserve traced subset after exiting trace mode
- **Performance Optimizations** - Debounced filters, layout caching (5,000+ nodes)

**State Management:**
- React hooks (useState, useEffect, useMemo, useCallback)
- No Redux/MobX (kept simple for this application)

### 5. DuckDB Workspace

**File:** `lineage_workspace.duckdb` (per job)
**Purpose:** Stores parsed lineage, metadata, and confidence scores

**Key Tables:**
- `objects` - All database objects (tables, views, SPs)
- `dependencies` - Source → target relationships
- `definitions` - SQL DDL definitions
- `lineage_metadata` - Confidence scores, parsing sources
- `query_logs` (optional) - Execution history for validation

See [DUCKDB_SCHEMA.md](DUCKDB_SCHEMA.md) for complete schema documentation.

---

## Data Flow

### End-to-End Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Synapse Environment                                           │
│    - PySpark Notebook exports DMV data to ADLS                  │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼ Download Parquet files
┌──────────────────────────────────────────────────────────────────┐
│ 2. User's Local Machine                                          │
│    - Downloads 3-5 Parquet files from ADLS                      │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼ Upload via UI or curl
┌──────────────────────────────────────────────────────────────────┐
│ 3. FastAPI Backend (http://localhost:8000)                       │
│    POST /api/upload-parquet?incremental=true                    │
│    - Saves files to /tmp/jobs/{job_id}/                         │
│    - Starts background processing thread                        │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼ Background thread processes
┌──────────────────────────────────────────────────────────────────┐
│ 4. Quality-Aware Parser (lineage_v3/)                            │
│    a. Load Parquet → DuckDB workspace                           │
│    b. Parse stored procedures (SQLGlot + Regex + Rules)         │
│    c. Validate with query logs (if available)                   │
│    d. Calculate confidence scores (unified model)               │
│    e. Generate frontend_lineage.json                            │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼ Polling for completion
┌──────────────────────────────────────────────────────────────────┐
│ 5. React Frontend (http://localhost:3000)                        │
│    - Poll GET /api/status/{job_id} every 2 seconds             │
│    - Fetch GET /api/result/{job_id} when complete              │
│    - Render lineage graph with ReactFlow                       │
│    - Enable search, tracing, SQL viewing                        │
└──────────────────────────────────────────────────────────────────┘
```

### Parsing Decision Tree

```
For each stored procedure:

1. Has it changed since last parse?
   Yes → Parse
   No → Skip to next (incremental mode)

2. SQLGlot parse attempt
   Success → Confidence 0.85
   Failure → Regex fallback

3. Regex parse attempt
   Success → Confidence 0.50
   Failure → Confidence 0.50 (minimal metadata)

4. Apply rule engine
   - Orchestrator SP (no tables, has SP calls) → Boost to 0.85
   - Global target exclusion → Remove false inputs
   - IF EXISTS filtering → Remove circular dependencies

5. Query log validation (if available)
   - SP found in execution history → Boost to 0.95

6. Save to lineage_metadata table
```

---

## Performance Characteristics

### Parser Performance (v4.1.3)

| Metric | Value | Notes |
|--------|-------|-------|
| **Overall Confidence** | 95.5% (729/763) | High-confidence objects (≥0.85) |
| **SP Confidence** | 97.0% (196/202) | Exceeds 95% goal |
| **Coverage** | 99.3% (758/763) | Objects with any lineage data |
| **Parse Speed** | ~50-200 SPs/sec | Depends on complexity |
| **Incremental Speedup** | 50-90% faster | vs full refresh |

### Frontend Performance (v2.9.x)

| Metric | Value | Notes |
|--------|-------|-------|
| **Max Nodes** | 5,000+ | Smooth performance |
| **Initial Load** | 250-500ms | 1,000 nodes |
| **Schema Toggle** | <5ms | Debounced (was 2-3s freeze) |
| **Layout Cache Hit Rate** | 95%+ | Repeat operations |
| **Pan/Zoom** | 60fps | Smooth interaction |

**Optimizations:**
1. **Debounced Filters** - 150ms delay batches rapid changes (100x faster)
2. **Layout Caching** - Stores computed layouts for reuse
3. **Optimized Filtering** - O(n) array operations instead of O(n²)
4. **ReactFlow Props** - Disabled expensive drag overhead

See [frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md](../frontend/docs/PERFORMANCE_OPTIMIZATIONS_V2.9.1.md) for details.

### Backend Performance (API v4.0.3)

| Metric | Value | Notes |
|--------|-------|-------|
| **Upload Processing** | 2-10 seconds | 763 objects dataset |
| **Full Parse** | 30-120 seconds | All 202 SPs |
| **Incremental Parse** | 5-30 seconds | Typical changes |
| **Search Query** | 50-200ms | Full-text DDL search |
| **Health Check** | <10ms | `/health` endpoint |

---

## Security Model

### Development Environment

**Current Configuration:**
- CORS: Allow all origins (`*`)
- Authentication: None
- Network: Localhost only (ports 3000, 8000)

**Risk:** ✅ Acceptable for local development

### Production Deployment (Azure)

**Required Security Layers:**

#### 1. Azure Built-in Authentication (Easy Auth)

**Purpose:** Identity-level security
**Configuration:**
- Enable in Azure App Service → Authentication
- Choose provider (Microsoft Entra ID, Google, etc.)
- Set "Action when not authenticated" to "Log in with [Provider]"

**Effect:** Users must authenticate before accessing application

#### 2. CORS (Cross-Origin Resource Sharing)

**Purpose:** Website-level security
**Configuration:**
```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.azurewebsites.net"],  # Specific domain
    allow_credentials=True,  # Required for Azure Auth
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Effect:** Only authorized frontend can call backend API

#### 3. Network Isolation (Optional)

**Options:**
- Azure Private Link
- VNet integration
- API Management gateway

**Use Case:** Restrict API to internal network only

### Data Security

**Sensitive Data Handling:**
1. **Parquet Files** - May contain sensitive column names, queries
   - Store in `/tmp/` (ephemeral)
   - Clean up via DELETE /api/jobs/{job_id}
   - Never commit sample data to git

2. **Environment Variables** - `.env` file gitignored
   - No credentials required in v4.0.0+ (AI removed)
   - Azure App Service uses managed identities

3. **Database Files** - `*.duckdb` gitignored
   - Ephemeral job storage only
   - No long-term data retention

---

## Related Documentation

**Setup & Deployment:**
- [SETUP_AND_DEPLOYMENT.md](SETUP_AND_DEPLOYMENT.md) - Installation and deployment
- [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md) - Operations and troubleshooting

**Technical Details:**
- [DUCKDB_SCHEMA.md](DUCKDB_SCHEMA.md) - Database schema
- [PARSING_USER_GUIDE.md](PARSING_USER_GUIDE.md) - Parser behavior and SQL support
- [PARSER_EVOLUTION_LOG.md](PARSER_EVOLUTION_LOG.md) - Version history

**Component-Specific:**
- [api/README.md](../api/README.md) - Backend API documentation
- [frontend/README.md](../frontend/README.md) - Frontend guide
- [extractor/README.md](../extractor/README.md) - Synapse extractor setup

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Status:** ✅ Production Ready
