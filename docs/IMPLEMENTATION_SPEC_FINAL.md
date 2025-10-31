# Vibecoding Lineage Parser v3 - Complete Implementation Specification

**Version:** 3.0 FINAL
**Date:** 2025-10-27
**Status:** ✅ **APPROVED - READY FOR IMPLEMENTATION**
**Timeline:** 4 weeks

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Approved Changes](#2-approved-changes)
3. [Architecture Overview](#3-architecture-overview)
4. [Feature 1: PySpark DMV Extractor](#4-feature-1-pyspark-dmv-extractor)
5. [Feature 2: Single Container Deployment](#5-feature-2-single-container-deployment)
6. [Feature 3: SQL Viewer](#6-feature-3-sql-viewer)
7. [Implementation Timeline](#7-implementation-timeline)
8. [Technical Specifications](#8-technical-specifications)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Guide](#10-deployment-guide)
11. [Critical Review & Risk Assessment](#11-critical-review--risk-assessment)

---

## 1. Executive Summary

### Overview

This document specifies three approved features for Vibecoding Lineage Parser v3:

1. **PySpark DMV Extractor** - Replace Python script with PySpark notebook (runs in Synapse Spark)
2. **Single Container Deployment** - Combine frontend + backend in one Docker container
3. **SQL Viewer** - Right-click object → View formatted SQL in split view

### Key Design Decisions

**Configuration Decisions (Q1-Q4):**
- ✅ **Q1: Polling** - Poll status every 2 seconds (simple, acceptable)
- ✅ **Q2: Job Storage** - Use `/tmp/jobs/` (lost on restart, acceptable)
- ✅ **Q3: DDL in JSON** - Include DDL text in JSON (each SP <100 KB, total manageable)
- ✅ **Q4: SQL Formatting** - Syntax highlighting like SQL editor (read-only view)

### Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Week 1** | 5 days | PySpark DMV extractor notebook |
| **Week 2-3** | 10 days | Single container (backend API + frontend upload) |
| **Week 4** | 5 days | SQL Viewer feature |
| **TOTAL** | **4 weeks** | Complete system |

### Success Criteria

- ✅ User can extract DMV data in Synapse Studio (GUI, no CLI)
- ✅ User can upload Parquet files in browser (no local Python)
- ✅ User sees progress during parsing (2-second updates)
- ✅ User can view SQL definitions in app (syntax-highlighted)

---

## 2. Approved Changes

### Change 1: PySpark DMV Extractor ✅

**Current State:**
```
User → Installs Python + ODBC locally
     → Runs: python synapse_dmv_extractor.py
     → Generates Parquet files locally
```

**New State:**
```
User → Opens Synapse Studio (browser)
     → Runs PySpark notebook (clicks "Run All")
     → Generates Parquet files in ADLS
     → Downloads files to local machine
```

**Benefits:**
- ✅ No local Python installation
- ✅ No ODBC driver setup
- ✅ GUI-based (Synapse Studio)
- ✅ Parallel processing (Spark distributed)

**Status:** ✅ Approved (1 week)

### Change 2: Single Container Deployment ✅

**Current State:**
```
Frontend: Separate container (Azure Web App)
Backend: CLI (user runs locally: python main.py run --parquet ...)
```

**New State:**
```
Single Container (Docker):
  ├── Frontend (React SPA)
  ├── Backend (FastAPI + existing Python code)
  └── Nginx (routes /api/* to backend, /* to frontend)

User workflow:
  → Upload Parquet files in browser
  → Backend processes server-side (existing code unchanged)
  → Frontend polls for status every 2 seconds
  → Graph renders when complete
```

**Benefits:**
- ✅ No CLI required (fully GUI-based)
- ✅ No local Python needed
- ✅ Progress updates during parsing
- ✅ Backend deployed with frontend

**Status:** ✅ Approved (2 weeks)

### Change 3: SQL Viewer ✅

**Current State:**
```
User → Sees object in graph
     → No way to view SQL
     → Must open Synapse Studio separately
```

**New State:**
```
User → Right-clicks object in graph
     → Split view appears:
         ├── Left: Graph (50% width)
         └── Right: SQL viewer (50% width)
              ├── Syntax-highlighted SQL (like SQL editor)
              ├── Read-only view
              ├── Full-text search
              └── Scrollbars
```

**Benefits:**
- ✅ View SQL without leaving app
- ✅ Syntax highlighting (professional appearance)
- ✅ Full-text search (find keywords quickly)

**Status:** ✅ Approved (1 week)

---

## 3. Architecture Overview

### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DMV EXTRACTION (Cloud - Synapse Studio)                   │
│                                                                     │
│  User → Opens Synapse Studio (browser GUI)                         │
│       → Imports PySpark notebook                                   │
│       → Edits configuration (database name, output path)           │
│       → Clicks "Run All"                                           │
│       → PySpark connects to Synapse SQL Pool (JDBC)                │
│       → Queries DMVs (sys.objects, sys.sql_expression_dependencies)│
│       → Saves to ADLS Gen2:                                        │
│           - objects.parquet                                        │
│           - dependencies.parquet                                   │
│           - definitions.parquet                                    │
│           - query_logs.parquet (optional)                          │
│       → User downloads files from ADLS to local machine            │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: PARSING & VISUALIZATION (Single Docker Container)         │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Frontend (React SPA)                                       │   │
│  │                                                            │   │
│  │  1. User uploads 4 Parquet files                          │   │
│  │  2. POST /api/upload-parquet → Backend                    │   │
│  │  3. Poll GET /api/status/{job_id} every 2 seconds         │   │
│  │  4. Display progress: "Parsing 8/16 objects... 50%"       │   │
│  │  5. GET /api/result/{job_id} when complete                │   │
│  │  6. Render graph (React Flow)                             │   │
│  │  7. Right-click object → View SQL (split view)            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                               ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Backend (FastAPI + Python)                                 │   │
│  │                                                            │   │
│  │  POST /api/upload-parquet:                                │   │
│  │    ↓ Save files to /tmp/jobs/{job_id}/                    │   │
│  │    ↓ Start background task                                │   │
│  │                                                            │   │
│  │  Background Task (FastAPI BackgroundTasks):               │   │
│  │    ↓ Import existing modules (NO CODE CHANGES):           │   │
│  │       from lineage_v3.core import DuckDBWorkspace         │   │
│  │       from lineage_v3.parsers import QualityAwareParser   │   │
│  │       from lineage_v3.output import FrontendFormatter     │   │
│  │                                                            │   │
│  │    ↓ Run existing pipeline:                               │   │
│  │       workspace = DuckDBWorkspace()                       │   │
│  │       workspace.load_parquet(job_dir)  ← UNCHANGED        │   │
│  │       parser = QualityAwareParser(workspace)              │   │
│  │       for obj in objects_to_parse:                        │   │
│  │           result = parser.parse_object(obj)  ← UNCHANGED  │   │
│  │           workspace.update_metadata(...)                  │   │
│  │       formatter = FrontendFormatter(workspace)            │   │
│  │       formatter.generate(..., include_ddl=True)           │   │
│  │                                                            │   │
│  │    ↓ Save result.json to /tmp/jobs/{job_id}/             │   │
│  │    ↓ Update status.json (for polling)                     │   │
│  │                                                            │   │
│  │  GET /api/status/{job_id}:                                │   │
│  │    ↓ Read status.json                                     │   │
│  │    ↓ Return {status, progress, message, errors}           │   │
│  │                                                            │   │
│  │  GET /api/result/{job_id}:                                │   │
│  │    ↓ Read result.json                                     │   │
│  │    ↓ Return frontend_lineage.json (with DDL text)         │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  File System: /tmp/jobs/                                           │
│    ├── abc-123-uuid/                                               │
│    │   ├── objects.parquet           (uploaded)                   │
│    │   ├── dependencies.parquet      (uploaded)                   │
│    │   ├── definitions.parquet       (uploaded)                   │
│    │   ├── query_logs.parquet        (optional)                   │
│    │   ├── status.json               (polling)                    │
│    │   │   {"status": "parsing", "progress": 50, ...}             │
│    │   └── result.json               (complete)                   │
│    │       [frontend_lineage with DDL text]                       │
│    └── xyz-789-uuid/ ...                                           │
│                                                                     │
│  Nginx Configuration:                                              │
│    ├── /api/* → FastAPI (port 8000)                                │
│    └── /* → React static files                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Existing Python Code Unchanged** - Core parsing logic (`DuckDBWorkspace`, `QualityAwareParser`) runs as-is
2. **Server-Side Processing** - Parquet parsing happens in container, not browser
3. **Async Background Tasks** - FastAPI BackgroundTasks for long-running operations
4. **Polling for Status** - Simple HTTP polling every 2 seconds (no WebSocket complexity)
5. **Ephemeral Job Storage** - `/tmp/jobs/` cleaned up on container restart (acceptable)

---

## 4. Feature 1: PySpark DMV Extractor

### 4.1. Overview

Replace `synapse_dmv_extractor.py` (local Python + ODBC) with PySpark notebook that runs on Synapse Spark cluster.

### 4.2. User Workflow

**Step-by-Step:**

1. User opens Synapse Studio in browser
2. User navigates to: Develop → Notebooks
3. User clicks "+ Import" and selects `synapse_pyspark_dmv_extractor.py`
4. User edits Cell 1 (Configuration):
   ```python
   # USER CONFIGURATION
   SYNAPSE_SQL_POOL = "myworkspace.sql.azuresynapse.net"
   DATABASE_NAME = "MyDatabase"
   OUTPUT_PATH = "abfss://lineage@mystorageaccount.dfs.core.windows.net/parquet_snapshots/"
   SKIP_QUERY_LOGS = False  # Set True if no VIEW SERVER STATE permission
   ```
5. User clicks "Run All" button
6. User watches progress in cell outputs (real-time)
7. Notebook completes (~5-10 minutes)
8. User downloads files from ADLS using:
   - Azure Storage Explorer (GUI), OR
   - Azure CLI: `az storage blob download-batch`, OR
   - Synapse Studio (for files <100 MB)

### 4.3. Technical Implementation

**File Structure:**
```python
# synapse_pyspark_dmv_extractor.py
# Format: Synapse notebook (cells marked with # CELL N:)

# CELL 1: Configuration
SYNAPSE_SQL_POOL = ""
DATABASE_NAME = ""
OUTPUT_PATH = ""

# CELL 2: Connection Setup
jdbc_url = f"jdbc:sqlserver://{SYNAPSE_SQL_POOL}:1433;database={DATABASE_NAME}"
jdbc_properties = {
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
    "authentication": "ActiveDirectoryMSI",  # Managed Identity (no credentials!)
    "encrypt": "true"
}

# CELL 3: Helper Function - Extract to Single Parquet
def extract_to_parquet(query, output_filename, description):
    # Read from SQL using JDBC
    df = spark.read.format("jdbc") \
        .option("url", jdbc_url) \
        .option("query", query) \
        .options(**jdbc_properties) \
        .load()

    # Write to ADLS using Spark native (creates directory output)
    # .coalesce(1) ensures single partition (single part file)
    output_path = f"{OUTPUT_PATH}{output_filename}"
    df.coalesce(1).write.mode("overwrite").parquet(output_path)

# CELL 4-7: Extract each DMV
extract_to_parquet(QUERY_OBJECTS, "objects.parquet", "objects")
extract_to_parquet(QUERY_DEPENDENCIES, "dependencies.parquet", "dependencies")
extract_to_parquet(QUERY_DEFINITIONS, "definitions.parquet", "definitions")
if not SKIP_QUERY_LOGS:
    extract_to_parquet(QUERY_LOGS, "query_logs.parquet", "query logs")

# CELL 8: Summary
print("✅ Extraction complete!")
print(f"Files saved to: {OUTPUT_PATH}")
```

**SQL Queries:**
```python
QUERY_OBJECTS = """
    SELECT
        o.object_id,
        s.name AS schema_name,
        o.name AS object_name,
        CASE o.type
            WHEN 'U' THEN 'Table'
            WHEN 'V' THEN 'View'
            WHEN 'P' THEN 'Stored Procedure'
        END AS object_type,
        o.create_date,
        o.modify_date
    FROM sys.objects o
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    WHERE o.type IN ('U', 'V', 'P')
        AND o.is_ms_shipped = 0
    ORDER BY s.name, o.name
"""

QUERY_DEPENDENCIES = """
    SELECT
        d.referencing_id AS referencing_object_id,
        d.referenced_id AS referenced_object_id,
        d.referenced_schema_name,
        d.referenced_entity_name
    FROM sys.sql_expression_dependencies d
    WHERE d.referencing_id IS NOT NULL
        AND d.referenced_id IS NOT NULL
"""

QUERY_DEFINITIONS = """
    SELECT
        m.object_id,
        o.name AS object_name,
        s.name AS schema_name,
        m.definition
    FROM sys.sql_modules m
    JOIN sys.objects o ON m.object_id = o.object_id
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    WHERE o.is_ms_shipped = 0
"""

QUERY_LOGS = """
    SELECT TOP 10000
        r.request_id,
        r.session_id,
        r.submit_time,
        SUBSTRING(r.command, 1, 4000) AS command_text
    FROM sys.dm_pdw_exec_requests r
    WHERE r.submit_time >= DATEADD(day, -7, GETDATE())
        AND r.command IS NOT NULL
"""
```

### 4.4. Platform Support

**Primary:** Azure Synapse Analytics
- ✅ Managed Identity authentication (no credentials)
- ✅ `mssparkutils.fs` for file operations
- ✅ ADLS Gen2 paths (`abfss://`)

**Optional:** Databricks (if needed later)
- ⚠️ Requires username/password or secrets
- ⚠️ Uses `dbutils.fs` instead of `mssparkutils.fs`
- ⚠️ DBFS paths (`dbfs:/`)

**Decision:** Start with Synapse only, add Databricks later if requested

### 4.5. Parquet Output Strategy

**Spark Native Behavior:** Spark writes partitioned output to directories:
```
objects.parquet/
  ├── _SUCCESS
  └── part-00000-abc123.snappy.parquet  ✅ Single partition (via .coalesce(1))
```

**Solution:** Use `.coalesce(1)` for single partition, DuckDB reads directories natively:
```python
df = spark.read.jdbc(...)
df.coalesce(1).write.mode("overwrite").parquet(output_path)
# Creates: objects.parquet/part-00000-{uuid}.parquet
```

**Why This Works:**
- ✅ **No pandas needed** - Spark native output
- ✅ **DuckDB compatible** - `read_parquet()` supports directories
- ✅ **Simpler deployment** - No additional dependencies
- ✅ **Scalable** - Works for any data size

**DuckDB Reading:**
```python
# DuckDB automatically reads from directories
SELECT * FROM read_parquet('objects.parquet/*.parquet')

# Or use glob pattern for specific files
SELECT * FROM read_parquet('objects.parquet/part-*.parquet')
```

**Data Size Analysis:**
| File | Expected Size | Spark Memory |
|------|---------------|---------------|
| objects.parquet/ | <1 MB | <10 MB (one partition) |
| dependencies.parquet/ | <5 MB | <50 MB (one partition) |
| definitions.parquet/ | <10 MB | <100 MB (one partition) |
| query_logs.parquet/ | <5 MB | <50 MB (one partition) |
| **TOTAL** | **<20 MB** | **<200 MB** ✅ Safe for small executor |

---

## 5. Feature 2: Single Container Deployment

### 5.1. Overview

Combine frontend (React) and backend (FastAPI + Python) in a single Docker container with Nginx routing.

### 5.2. User Workflow

**Step-by-Step:**

1. User has 4 Parquet files downloaded locally (from Phase 1)
2. User opens frontend in browser: `https://myapp.azurewebsites.net`
3. User clicks "Import Data" button
4. User selects upload mode: "Upload Parquet Files" (new option)
5. User uploads 4 files:
   - objects.parquet
   - dependencies.parquet
   - definitions.parquet
   - query_logs.parquet (optional)
6. User clicks "Upload & Parse"
7. Frontend shows progress modal:
   ```
   ⏳ Processing your data...

   Progress: [████████████░░░░░░░░] 60%
   Status: Parsing stored procedures (10/16 complete)

   Elapsed: 45 seconds
   Estimated remaining: 30 seconds
   ```
8. When complete, graph renders automatically
9. If errors/warnings, shown in modal

### 5.3. Backend API Specification

#### Endpoint 1: Upload Parquet Files

**Route:** `POST /api/upload-parquet`

**Request:**
```http
POST /api/upload-parquet HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="objects"; filename="objects.parquet"
Content-Type: application/octet-stream

[binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="dependencies"; filename="dependencies.parquet"
Content-Type: application/octet-stream

[binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="definitions"; filename="definitions.parquet"
Content-Type: application/octet-stream

[binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="query_logs"; filename="query_logs.parquet"
Content-Type: application/octet-stream

[binary data]
------WebKitFormBoundary--
```

**Response:**
```json
{
  "job_id": "abc-123-def-456",
  "status": "processing",
  "message": "Upload complete. Processing started."
}
```

**Implementation:**
```python
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from pathlib import Path
import uuid

app = FastAPI()

@app.post("/api/upload-parquet")
async def upload_parquet(
    background_tasks: BackgroundTasks,
    objects: UploadFile = File(...),
    dependencies: UploadFile = File(...),
    definitions: UploadFile = File(...),
    query_logs: Optional[UploadFile] = File(None)
):
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    job_dir = Path(f"/tmp/jobs/{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded files
    async def save_file(upload: UploadFile, filename: str):
        content = await upload.read()
        with open(job_dir / filename, "wb") as f:
            f.write(content)

    await save_file(objects, "objects.parquet")
    await save_file(dependencies, "dependencies.parquet")
    await save_file(definitions, "definitions.parquet")
    if query_logs:
        await save_file(query_logs, "query_logs.parquet")

    # Initialize status file
    write_status(job_id, {
        "status": "processing",
        "progress": 0,
        "message": "Starting lineage analysis...",
        "started_at": datetime.now().isoformat()
    })

    # Start background processing
    background_tasks.add_task(process_lineage, job_id, job_dir)

    return {"job_id": job_id, "status": "processing"}
```

#### Endpoint 2: Get Job Status

**Route:** `GET /api/status/{job_id}`

**Request:**
```http
GET /api/status/abc-123-def-456 HTTP/1.1
```

**Response (Processing):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "processing",
  "progress": 60,
  "message": "Parsing stored procedures (10/16 complete)",
  "started_at": "2025-10-27T10:30:00Z",
  "elapsed_seconds": 45
}
```

**Response (Complete):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "complete",
  "progress": 100,
  "message": "Lineage analysis complete",
  "started_at": "2025-10-27T10:30:00Z",
  "completed_at": "2025-10-27T10:32:00Z",
  "elapsed_seconds": 120,
  "stats": {
    "total_objects": 100,
    "high_confidence": 50,
    "medium_confidence": 30,
    "low_confidence": 20
  }
}
```

**Response (Error):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "error",
  "message": "Failed to parse stored procedure spLoadDimCustomers",
  "errors": [
    "Invalid SQL syntax at line 45",
    "Table dbo.InvalidTable not found"
  ],
  "warnings": [
    "Query logs not provided - validation skipped"
  ]
}
```

**Implementation:**
```python
@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    status_file = Path(f"/tmp/jobs/{job_id}/status.json")

    if not status_file.exists():
        return {"status": "not_found", "message": "Job not found"}

    with open(status_file) as f:
        status = json.load(f)

    # Calculate elapsed time
    started_at = datetime.fromisoformat(status['started_at'])
    now = datetime.now()
    elapsed = (now - started_at).total_seconds()
    status['elapsed_seconds'] = int(elapsed)

    return status
```

#### Endpoint 3: Get Result

**Route:** `GET /api/result/{job_id}`

**Request:**
```http
GET /api/result/abc-123-def-456 HTTP/1.1
```

**Response:**
```json
[
  {
    "id": "1001",
    "name": "DimCustomers",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Table",
    "description": "Confidence: 1.00",
    "data_model_type": "Dimension",
    "inputs": [],
    "outputs": ["2001", "3001"],
    "ddl_text": null
  },
  {
    "id": "2001",
    "name": "spLoadDimCustomers",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Stored Procedure",
    "description": "Confidence: 0.85",
    "data_model_type": "Other",
    "inputs": ["1001", "1002"],
    "outputs": ["3001"],
    "ddl_text": "CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimCustomers]\nAS\nBEGIN\n    INSERT INTO DimCustomers\n    SELECT * FROM StagingCustomers;\nEND"
  }
]
```

**Implementation:**
```python
@app.get("/api/result/{job_id}")
async def get_result(job_id: str):
    result_file = Path(f"/tmp/jobs/{job_id}/result.json")

    if not result_file.exists():
        # Check if still processing
        status = get_status(job_id)
        if status['status'] == 'processing':
            return JSONResponse(
                status_code=202,
                content={"message": "Job still processing"}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"message": "Result not found"}
            )

    with open(result_file) as f:
        return json.load(f)
```

### 5.4. Background Processing (Existing Code Integration)

**Key Principle:** Run existing Python code unchanged!

```python
def process_lineage(job_id: str, job_dir: Path):
    """
    Background task that runs existing lineage_v3 code.

    This function is a WRAPPER - it calls existing modules without modification.
    """
    try:
        # Update status: Loading
        write_status(job_id, {
            "status": "processing",
            "progress": 10,
            "message": "Loading Parquet files into DuckDB..."
        })

        # ============================================================
        # EXISTING CODE - NO MODIFICATIONS
        # ============================================================

        from lineage_v3.core import DuckDBWorkspace
        from lineage_v3.parsers import QualityAwareParser
        from lineage_v3.output import FrontendFormatter

        # Step 1: Load Parquet (EXISTING METHOD)
        workspace = DuckDBWorkspace(workspace_path=f"{job_dir}/workspace.duckdb")
        workspace.connect()

        row_counts = workspace.load_parquet(
            parquet_dir=str(job_dir),
            full_refresh=True
        )

        write_status(job_id, {
            "status": "processing",
            "progress": 20,
            "message": f"Loaded {row_counts['objects']} objects, {row_counts['dependencies']} dependencies"
        })

        # Step 2: Load DMV dependencies for Views (EXISTING LOGIC)
        views_with_dmv = workspace.query("""
            SELECT DISTINCT d.referencing_object_id, o.object_name, o.modify_date
            FROM dependencies d
            JOIN objects o ON d.referencing_object_id = o.object_id
            WHERE o.object_type = 'View'
        """)

        for i, view in enumerate(views_with_dmv):
            view_id, view_name, modify_date = view
            deps = workspace.query("""
                SELECT referenced_object_id
                FROM dependencies
                WHERE referencing_object_id = ?
            """, [view_id])

            inputs = [dep[0] for dep in deps if dep[0] is not None]

            workspace.update_metadata(
                object_id=view_id,
                modify_date=modify_date,
                primary_source='dmv',
                confidence=1.0,
                inputs=inputs,
                outputs=[]
            )

            progress = 20 + (i / len(views_with_dmv)) * 10
            write_status(job_id, {
                "status": "processing",
                "progress": int(progress),
                "message": f"Loaded DMV dependencies for Views ({i+1}/{len(views_with_dmv)})"
            })

        # Step 3: Detect gaps and parse SPs (EXISTING LOGIC)
        write_status(job_id, {
            "status": "processing",
            "progress": 30,
            "message": "Parsing stored procedures..."
        })

        parser = QualityAwareParser(workspace)
        objects_to_parse = workspace.get_objects_to_parse(full_refresh=True)

        total_objects = len(objects_to_parse)

        for i, obj in enumerate(objects_to_parse):
            # Parse object (EXISTING METHOD)
            result = parser.parse_object(obj['object_id'])

            # Store in metadata (EXISTING METHOD)
            workspace.update_metadata(
                object_id=obj['object_id'],
                modify_date=obj['modify_date'],
                primary_source=result['source'],
                confidence=result['confidence'],
                inputs=result['inputs'],
                outputs=result['outputs']
            )

            # Update progress
            progress = 30 + ((i + 1) / total_objects) * 50
            write_status(job_id, {
                "status": "processing",
                "progress": int(progress),
                "message": f"Parsing stored procedures ({i+1}/{total_objects})"
            })

        # Step 4: Reverse lookup (EXISTING LOGIC)
        write_status(job_id, {
            "status": "processing",
            "progress": 85,
            "message": "Building bidirectional graph..."
        })

        # Get all parsed objects
        all_objects = workspace.query("SELECT * FROM lineage_metadata")

        # Build reverse lookup map
        table_outputs = {}  # table_id -> [sp_ids that read from it]
        table_inputs = {}   # table_id -> [sp_ids that write to it]

        for obj in all_objects:
            obj_id = obj[0]
            inputs = json.loads(obj[5])
            outputs = json.loads(obj[6])

            for inp_id in inputs:
                if inp_id not in table_outputs:
                    table_outputs[inp_id] = []
                table_outputs[inp_id].append(obj_id)

            for out_id in outputs:
                if out_id not in table_inputs:
                    table_inputs[out_id] = []
                table_inputs[out_id].append(obj_id)

        # Update tables with reverse dependencies
        for table_id in set(list(table_outputs.keys()) + list(table_inputs.keys())):
            current = workspace.query(
                "SELECT inputs, outputs FROM lineage_metadata WHERE object_id = ?",
                [table_id]
            )

            if current:
                current_inputs = json.loads(current[0][0])
                current_outputs = json.loads(current[0][1])
            else:
                current_inputs = []
                current_outputs = []

            new_inputs = list(set(current_inputs + table_inputs.get(table_id, [])))
            new_outputs = list(set(current_outputs + table_outputs.get(table_id, [])))

            workspace.query("""
                UPDATE lineage_metadata
                SET inputs = ?, outputs = ?
                WHERE object_id = ?
            """, [json.dumps(new_inputs), json.dumps(new_outputs), table_id])

        # Step 5: Generate frontend JSON (EXISTING METHOD, MODIFIED TO INCLUDE DDL)
        write_status(job_id, {
            "status": "processing",
            "progress": 90,
            "message": "Generating output JSON..."
        })

        formatter = FrontendFormatter(workspace)

        # Query all lineage data
        internal_lineage = workspace.query("""
            SELECT
                m.object_id,
                o.object_name,
                o.schema_name,
                o.object_type,
                m.inputs,
                m.outputs,
                m.primary_source,
                m.confidence
            FROM lineage_metadata m
            JOIN objects o ON m.object_id = o.object_id
        """)

        # Convert to dict format
        lineage_list = []
        for row in internal_lineage:
            lineage_list.append({
                'id': row[0],
                'name': row[1],
                'schema': row[2],
                'object_type': row[3],
                'inputs': json.loads(row[4]),
                'outputs': json.loads(row[5]),
                'provenance': {
                    'primary_source': row[6],
                    'confidence': row[7]
                }
            })

        # Generate frontend JSON with DDL text
        frontend_json = formatter.generate(
            lineage_list,
            output_path=f"{job_dir}/result.json",
            include_ddl=True  # NEW PARAMETER
        )

        # ============================================================
        # END EXISTING CODE
        # ============================================================

        # Step 6: Calculate stats
        stats = workspace.get_stats()

        # Update status: Complete
        write_status(job_id, {
            "status": "complete",
            "progress": 100,
            "message": "Lineage analysis complete",
            "completed_at": datetime.now().isoformat(),
            "stats": stats
        })

    except Exception as e:
        # Update status: Error
        write_status(job_id, {
            "status": "error",
            "message": str(e),
            "errors": [str(e)],
            "completed_at": datetime.now().isoformat()
        })

        # Log error for debugging
        import traceback
        with open(f"{job_dir}/error.log", "w") as f:
            f.write(traceback.format_exc())

def write_status(job_id: str, status_dict: dict):
    """Write status to JSON file for polling."""
    status_file = Path(f"/tmp/jobs/{job_id}/status.json")
    with open(status_file, "w") as f:
        json.dump(status_dict, f, indent=2)
```

### 5.5. Frontend Implementation

#### Modified ImportDataModal Component

```typescript
// frontend/components/ImportDataModal.tsx

import React, { useState, useRef } from 'react';

type UploadMode = 'json' | 'parquet';

export const ImportDataModal = ({ isOpen, onClose, onImport }: Props) => {
    const [uploadMode, setUploadMode] = useState<UploadMode>('json');
    const [isProcessing, setIsProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const [errors, setErrors] = useState<string[]>([]);

    // File refs for Parquet upload
    const objectsFileRef = useRef<File | null>(null);
    const dependenciesFileRef = useRef<File | null>(null);
    const definitionsFileRef = useRef<File | null>(null);
    const queryLogsFileRef = useRef<File | null>(null);

    // NEW: Handle Parquet upload
    const handleParquetUpload = async () => {
        if (!objectsFileRef.current || !dependenciesFileRef.current || !definitionsFileRef.current) {
            setErrors(['Please select all required Parquet files (objects, dependencies, definitions)']);
            return;
        }

        setIsProcessing(true);
        setProgress(0);
        setStatusMessage('Uploading files...');
        setErrors([]);

        try {
            // Upload files
            const formData = new FormData();
            formData.append('objects', objectsFileRef.current);
            formData.append('dependencies', dependenciesFileRef.current);
            formData.append('definitions', definitionsFileRef.current);
            if (queryLogsFileRef.current) {
                formData.append('query_logs', queryLogsFileRef.current);
            }

            const uploadResponse = await fetch('/api/upload-parquet', {
                method: 'POST',
                body: formData
            });

            if (!uploadResponse.ok) {
                throw new Error(`Upload failed: ${uploadResponse.statusText}`);
            }

            const { job_id } = await uploadResponse.json();

            // Start polling for status
            await pollJobStatus(job_id);

        } catch (error) {
            setErrors([error.message]);
            setIsProcessing(false);
        }
    };

    // NEW: Poll for job status
    const pollJobStatus = async (job_id: string) => {
        const startTime = Date.now();

        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${job_id}`);
                const status = await response.json();

                // Update UI
                setProgress(status.progress || 0);
                setStatusMessage(status.message || 'Processing...');

                // Calculate elapsed time
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const elapsedText = `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
                setStatusMessage(`${status.message} (${elapsedText})`);

                // Check if complete
                if (status.status === 'complete') {
                    clearInterval(interval);

                    // Fetch result
                    const resultResponse = await fetch(`/api/result/${job_id}`);
                    const lineageData = await resultResponse.json();

                    // Import data (existing function)
                    onImport(lineageData);

                    // Close modal
                    setIsProcessing(false);
                    onClose();
                }

                // Check if error
                if (status.status === 'error') {
                    clearInterval(interval);
                    setErrors([status.message, ...(status.errors || [])]);
                    setIsProcessing(false);
                }

            } catch (error) {
                clearInterval(interval);
                setErrors([`Polling error: ${error.message}`]);
                setIsProcessing(false);
            }
        }, 2000); // Poll every 2 seconds
    };

    return (
        <div className="modal">
            {/* Tab selection */}
            <div className="tabs">
                <button
                    className={uploadMode === 'json' ? 'active' : ''}
                    onClick={() => setUploadMode('json')}
                >
                    Import JSON
                </button>
                <button
                    className={uploadMode === 'parquet' ? 'active' : ''}
                    onClick={() => setUploadMode('parquet')}
                >
                    Upload Parquet Files
                </button>
            </div>

            {/* Content */}
            {uploadMode === 'json' ? (
                <div>
                    {/* Existing JSON upload UI */}
                </div>
            ) : (
                <div>
                    {/* NEW: Parquet upload UI */}
                    <h3>Upload Parquet Files</h3>
                    <p>Upload the 4 Parquet files generated by the PySpark extractor:</p>

                    <div className="file-inputs">
                        <label>
                            <strong>objects.parquet</strong> (required)
                            <input
                                type="file"
                                accept=".parquet"
                                onChange={(e) => objectsFileRef.current = e.target.files?.[0] || null}
                            />
                        </label>

                        <label>
                            <strong>dependencies.parquet</strong> (required)
                            <input
                                type="file"
                                accept=".parquet"
                                onChange={(e) => dependenciesFileRef.current = e.target.files?.[0] || null}
                            />
                        </label>

                        <label>
                            <strong>definitions.parquet</strong> (required)
                            <input
                                type="file"
                                accept=".parquet"
                                onChange={(e) => definitionsFileRef.current = e.target.files?.[0] || null}
                            />
                        </label>

                        <label>
                            <strong>query_logs.parquet</strong> (optional)
                            <input
                                type="file"
                                accept=".parquet"
                                onChange={(e) => queryLogsFileRef.current = e.target.files?.[0] || null}
                            />
                        </label>
                    </div>

                    <button
                        onClick={handleParquetUpload}
                        disabled={isProcessing}
                        className="upload-button"
                    >
                        {isProcessing ? 'Processing...' : 'Upload & Parse'}
                    </button>

                    {/* Processing status */}
                    {isProcessing && (
                        <div className="processing-status">
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                            <p>{statusMessage}</p>
                            <p className="progress-text">{progress}% complete</p>
                        </div>
                    )}

                    {/* Errors */}
                    {errors.length > 0 && (
                        <div className="errors">
                            <h4>Errors:</h4>
                            <ul>
                                {errors.map((err, i) => (
                                    <li key={i}>{err}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
```

### 5.6. Docker Container Configuration

```dockerfile
# ============================================================================
# Multi-Stage Build: Frontend + Backend in Single Container
# ============================================================================

# ────────────────────────────────────────────────────────────────────────────
# Stage 1: Build Frontend
# ────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci --only=production

# Build frontend
COPY frontend/ ./
RUN npm run build

# Result: /frontend/dist/ contains React SPA

# ────────────────────────────────────────────────────────────────────────────
# Stage 2: Backend + Serve Frontend
# ────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install FastAPI and ASGI server
RUN pip install --no-cache-dir \
    fastapi==0.110.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.9

# Copy backend code
COPY lineage_v3/ ./lineage_v3/

# Copy frontend build from stage 1
COPY --from=frontend-build /frontend/dist ./static

# Create directory for job storage
RUN mkdir -p /tmp/jobs

# Copy FastAPI app
COPY docker/api_main.py ./main.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start FastAPI with static file serving
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**FastAPI App with Static Files:**

```python
# docker/api_main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# API routes (defined above in Section 5.3)
# ... (include all @app.post, @app.get routes here)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}

# Serve index.html for all non-API routes (SPA routing)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve React SPA for all routes not matched by API."""
    if full_path.startswith("api/"):
        # Let FastAPI handle API routes
        return {"error": "Not found"}

    # Serve index.html for SPA routing
    return FileResponse("static/index.html")
```

---

## 6. Feature 3: SQL Viewer

### 6.1. Overview

Add "View SQL" feature that displays DDL in a split view via a toggle button. The SQL viewer is only active in Detail View when Parquet files are uploaded (DDL included).

**Key Design Decisions:**
- **Toggle Button** (not right-click): Button appears in toolbar next to "Hide Overlays"
- **Split Screen**: 50/50 layout (graph left, SQL viewer right)
- **Click-to-View**: User clicks nodes in the graph to see their SQL in the right panel
- **Conditional Activation**: Only enabled when:
  - Data loaded via **Parquet upload** (includes DDL text)
  - **Detail View** mode is active (not Overview mode)
- **Interactive Selection**: Clicking different nodes updates the SQL viewer panel

### 6.2. User Workflow

**Prerequisites:**
- Data loaded via **Parquet upload** (includes DDL text)
- **Detail View** mode active (not Overview mode)

**Workflow:**
1. User sees toolbar with control buttons (left side):
   - "Hide Overlays" button (existing)
   - **"View SQL" button** (NEW) - appears next to Hide Overlays
2. **SQL button states:**
   - **Active** (clickable): When in Detail View + Parquet uploaded
   - **Inactive** (grayed out): When in Overview mode OR JSON imported (no DDL)
3. User clicks "View SQL" toggle button
4. Screen splits 50/50:
   - **Left side (50%)**: Graph with all objects (remains interactive)
   - **Right side (50%)**: SQL viewer panel
     - Header: "SQL Definition Viewer"
     - Message: "Click on any Stored Procedure or View to see its SQL"
     - Empty content area (syntax-highlighted placeholder)
5. User clicks on a Stored Procedure or View node in the graph
6. Node highlights (selected state)
7. Right panel updates:
   - Header shows: `{schema}.{object_name} - SQL Definition`
   - SQL content displays with syntax highlighting
   - Search box appears at top
8. User can:
   - Search for keywords (e.g., "INSERT INTO") - matches highlight in yellow
   - Click different nodes to view their SQL
   - Scroll through SQL content
9. User clicks "View SQL" button again (toggle off)
10. Split view closes, graph returns to full width

### 6.3. Frontend Implementation

#### Add DDL to DataNode Type

```typescript
// frontend/types.ts

export type DataNode = {
    id: string;
    name: string;
    schema: string;
    object_type: 'Table' | 'View' | 'Stored Procedure';
    description: string;
    data_model_type: string;
    inputs: string[];
    outputs: string[];
    ddl_text?: string | null;  // NEW: DDL definition
};
```

#### SQL Viewer Component

```typescript
// frontend/components/SqlViewer.tsx

import React, { useState, useRef, useEffect } from 'react';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';  // Dark theme
import 'prismjs/components/prism-sql';       // SQL syntax

type SqlViewerProps = {
    isOpen: boolean;
    selectedNode: {
        name: string;
        schema: string;
        ddlText: string | null;
    } | null;
};

export const SqlViewer: React.FC<SqlViewerProps> = ({
    isOpen,
    selectedNode
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [highlightedDdl, setHighlightedDdl] = useState('');
    const codeRef = useRef<HTMLPreElement>(null);

    // Syntax highlight DDL
    useEffect(() => {
        if (selectedNode?.ddlText) {
            // Use Prism.js for syntax highlighting
            const highlighted = Prism.highlight(
                selectedNode.ddlText,
                Prism.languages.sql,
                'sql'
            );
            setHighlightedDdl(highlighted);
            setSearchQuery(''); // Reset search when node changes
        }
    }, [selectedNode]);

    // Handle search
    useEffect(() => {
        if (!searchQuery || !codeRef.current) return;

        // Find all matches
        const regex = new RegExp(searchQuery, 'gi');
        let html = highlightedDdl;

        // Wrap matches in <mark> tags
        html = html.replace(regex, (match) => `<mark class="search-highlight">${match}</mark>`);

        if (codeRef.current) {
            codeRef.current.innerHTML = html;

            // Scroll to first match
            const firstMatch = codeRef.current.querySelector('.search-highlight');
            if (firstMatch) {
                firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }, [searchQuery, highlightedDdl]);

    if (!isOpen) return null;

    return (
        <div className="sql-viewer-panel">
            {/* Header */}
            <div className="sql-viewer-header">
                <h2>
                    {selectedNode
                        ? `${selectedNode.schema}.${selectedNode.name} - SQL Definition`
                        : 'SQL Definition Viewer'
                    }
                </h2>

                {/* Search box - only show when SQL is loaded */}
                {selectedNode?.ddlText && (
                    <input
                        type="text"
                        placeholder="Search SQL..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="sql-search"
                    />
                )}
            </div>

            {/* SQL content */}
            <div className="sql-viewer-content">
                {!selectedNode ? (
                    <div className="sql-viewer-empty">
                        <p>Click on any Stored Procedure or View to see its SQL definition</p>
                    </div>
                ) : selectedNode.ddlText ? (
                    <pre ref={codeRef} className="language-sql">
                        <code
                            className="language-sql"
                            dangerouslySetInnerHTML={{ __html: highlightedDdl }}
                        />
                    </pre>
                ) : (
                    <div className="sql-viewer-empty">
                        <p>No SQL definition available for this object</p>
                        <p className="hint">(Tables don't have DDL text)</p>
                    </div>
                )}
            </div>
        </div>
    );
};
```

#### Update CustomNode with Click Handler

```typescript
// frontend/components/CustomNode.tsx

import React from 'react';
import { Handle, Position } from 'reactflow';

export const CustomNode = ({ data }) => {
    const handleClick = () => {
        // Only trigger SQL viewer if it's open and node has DDL
        if (data.sqlViewerOpen && data.ddl_text) {
            data.onNodeClick({
                id: data.id,
                name: data.name,
                schema: data.schema,
                ddlText: data.ddl_text
            });
        }
    };

    return (
        <div
            className={`custom-node ${data.sqlViewerOpen && data.ddl_text ? 'sql-clickable' : ''}`}
            onClick={handleClick}
            title={data.sqlViewerOpen && data.ddl_text ? "Click to view SQL definition" : ""}
        >
            <Handle type="target" position={Position.Left} />
            <div className="node-content">
                <strong>{data.name}</strong>
                <div className="node-schema">{data.schema}</div>
            </div>
            <Handle type="source" position={Position.Right} />
        </div>
    );
};
```

#### Update App with Split View and Toggle Button

```typescript
// frontend/App.tsx

import React, { useState, useEffect } from 'react';
import { SqlViewer } from './components/SqlViewer';

export default function App() {
    // Track if data was loaded via Parquet (has DDL)
    const [hasDdlData, setHasDdlData] = useState(false);

    // Track current view mode (overview vs detail)
    const [viewMode, setViewMode] = useState<'overview' | 'detail'>('detail');

    // SQL Viewer state
    const [sqlViewerOpen, setSqlViewerOpen] = useState(false);
    const [selectedNode, setSelectedNode] = useState<{
        id: string;
        name: string;
        schema: string;
        ddlText: string | null;
    } | null>(null);

    // Check if data has DDL when loaded
    useEffect(() => {
        // After data import, check if any nodes have ddl_text
        const anyNodeHasDdl = nodes.some(node => node.data.ddl_text != null);
        setHasDdlData(anyNodeHasDdl);
    }, [nodes]);

    // Determine if SQL viewer button should be enabled
    const sqlViewerEnabled = hasDdlData && viewMode === 'detail';

    const handleToggleSqlViewer = () => {
        if (!sqlViewerEnabled) return;

        setSqlViewerOpen(!sqlViewerOpen);
        if (sqlViewerOpen) {
            // Closing viewer, clear selection
            setSelectedNode(null);
        }
    };

    const handleNodeClick = (nodeData: {
        id: string;
        name: string;
        schema: string;
        ddlText: string | null;
    }) => {
        if (sqlViewerOpen) {
            setSelectedNode(nodeData);
        }
    };

    return (
        <div className="app-container">
            {/* Toolbar */}
            <div className="toolbar">
                {/* Existing buttons */}
                <button onClick={handleHideOverlays}>
                    Hide Overlays
                </button>

                {/* NEW: SQL Viewer Toggle Button */}
                <button
                    onClick={handleToggleSqlViewer}
                    disabled={!sqlViewerEnabled}
                    className={`sql-viewer-toggle ${sqlViewerOpen ? 'active' : ''}`}
                    title={
                        !hasDdlData
                            ? 'Upload Parquet files to view SQL'
                            : viewMode !== 'detail'
                            ? 'Switch to Detail View to view SQL'
                            : sqlViewerOpen
                            ? 'Close SQL Viewer'
                            : 'View SQL Definitions'
                    }
                >
                    {sqlViewerOpen ? '✕ Close SQL' : '📄 View SQL'}
                </button>
            </div>

            {/* Main content area */}
            <div className="main-content">
                <div className={`graph-container ${sqlViewerOpen ? 'split-view' : ''}`}>
                    <ReactFlow
                        nodes={nodes.map(n => ({
                            ...n,
                            data: {
                                ...n.data,
                                sqlViewerOpen,
                                onNodeClick: handleNodeClick
                            }
                        }))}
                        edges={edges}
                    />
                </div>

                {sqlViewerOpen && (
                    <div className="sql-viewer-container">
                        <SqlViewer
                            isOpen={sqlViewerOpen}
                            selectedNode={selectedNode}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}
```

#### CSS Styling

```css
/* frontend/styles/sql-viewer.css */

/* Toolbar button styling */
.sql-viewer-toggle {
    padding: 0.5rem 1rem;
    background: #007acc;
    border: none;
    border-radius: 4px;
    color: #ffffff;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s ease;
}

.sql-viewer-toggle:hover:not(:disabled) {
    background: #005a9e;
}

.sql-viewer-toggle.active {
    background: #ff6b6b;
}

.sql-viewer-toggle:disabled {
    background: #555555;
    color: #888888;
    cursor: not-allowed;
    opacity: 0.5;
}

/* Split view layout */
.main-content {
    display: flex;
    height: calc(100vh - 60px);  /* Account for toolbar height */
    width: 100vw;
}

.graph-container {
    flex: 1;
    transition: all 0.3s ease;
}

.graph-container.split-view {
    flex: 0 0 50%;  /* 50% width when SQL viewer open */
}

.sql-viewer-container {
    flex: 0 0 50%;  /* 50% width */
    border-left: 2px solid #3e3e42;
}

/* SQL viewer panel */
.sql-viewer-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #1e1e1e;  /* Dark theme */
}

.sql-viewer-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #252526;
    border-bottom: 1px solid #3e3e42;
}

.sql-viewer-header h2 {
    flex: 1;
    margin: 0;
    color: #ffffff;
    font-size: 1.1rem;
}

.sql-search {
    width: 250px;
    padding: 0.5rem;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    background: #3c3c3c;
    color: #ffffff;
}

.sql-search:focus {
    outline: none;
    border-color: #007acc;
}

/* Empty state */
.sql-viewer-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #888888;
    text-align: center;
    padding: 2rem;
}

.sql-viewer-empty p {
    margin: 0.5rem 0;
    font-size: 16px;
}

.sql-viewer-empty .hint {
    font-size: 14px;
    color: #666666;
    font-style: italic;
}

/* SQL content */
.sql-viewer-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
}

.sql-viewer-content pre {
    margin: 0;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
    color: #d4d4d4;
}

/* Syntax highlighting (using Prism.js theme) */
.language-sql .token.comment {
    color: #6a9955;
    font-style: italic;
}

.language-sql .token.keyword {
    color: #569cd6;
    font-weight: bold;
}

.language-sql .token.string {
    color: #ce9178;
}

.language-sql .token.number {
    color: #b5cea8;
}

.language-sql .token.function {
    color: #dcdcaa;
}

.language-sql .token.operator {
    color: #d4d4d4;
}

/* Search highlighting */
.search-highlight {
    background-color: #ffd700;
    color: #000000;
    padding: 2px 4px;
    border-radius: 2px;
    font-weight: bold;
}

/* Clickable node styling (when SQL viewer is open) */
.custom-node.sql-clickable {
    cursor: pointer;
}

.custom-node.sql-clickable:hover {
    box-shadow: 0 0 8px rgba(0, 122, 204, 0.6);
    border-color: #007acc;
}

/* Scrollbar styling (webkit browsers) */
.sql-viewer-content::-webkit-scrollbar {
    width: 12px;
}

.sql-viewer-content::-webkit-scrollbar-track {
    background: #1e1e1e;
}

.sql-viewer-content::-webkit-scrollbar-thumb {
    background: #424242;
    border-radius: 6px;
}

.sql-viewer-content::-webkit-scrollbar-thumb:hover {
    background: #555555;
}
```

### 6.4. Backend Modification

**Modify `FrontendFormatter` to include DDL text:**

```python
# lineage_v3/output/frontend_formatter.py

class FrontendFormatter:
    def generate(
        self,
        internal_lineage: List[Dict[str, Any]],
        output_path: str = "lineage_output/frontend_lineage.json",
        include_ddl: bool = False  # NEW PARAMETER
    ) -> Dict[str, Any]:
        """
        Generate frontend_lineage.json from internal lineage.

        Args:
            internal_lineage: List of nodes in internal format
            output_path: Path to output JSON file
            include_ddl: If True, include DDL text in output (for SQL viewer)
        """
        frontend_nodes = []

        for node in internal_lineage:
            # ... existing transformation logic ...

            # NEW: Include DDL text if requested
            ddl_text = None
            if include_ddl and node['object_type'] in ['Stored Procedure', 'View']:
                ddl_text = self.workspace.get_object_definition(node['id'])

            frontend_node = {
                'id': node_id,
                'name': node['name'],
                'schema': node['schema'],
                'object_type': node['object_type'],
                'description': description,
                'data_model_type': data_model_type,
                'inputs': sorted(input_node_ids),
                'outputs': sorted(output_node_ids),
                'ddl_text': ddl_text  # NEW FIELD
            }

            frontend_nodes.append(frontend_node)

        # ... rest of existing code ...
```

### 6.5. Package Dependencies

```json
// frontend/package.json

{
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "reactflow": "^11.11.4",
    "prismjs": "^1.29.0"  // NEW: Syntax highlighting
  }
}
```

---

## 7. Implementation Timeline

### Week 1: PySpark Extractor (5 days)

**Day 1-2: Create PySpark Script**
- [ ] Convert Python queries to PySpark JDBC
- [ ] Implement platform detection (Synapse)
- [ ] Implement directory output (`.coalesce(1)` for single partition)
- [ ] Test connection to Synapse SQL Pool

**Day 3: Create Synapse Notebook**
- [ ] Add cell markers (# CELL N:)
- [ ] Add markdown documentation
- [ ] Add configuration section
- [ ] Test in Synapse Studio

**Day 4: Testing**
- [ ] Test on production Synapse workspace
- [ ] Verify Parquet directories (single partition, correct schema)
- [ ] Test download from ADLS

**Day 5: Documentation**
- [ ] User guide with screenshots
- [ ] Download instructions (Storage Explorer, CLI, Studio)
- [ ] Permissions requirements
- [ ] Troubleshooting guide

**Deliverable:** ✅ Working PySpark notebook for DMV extraction

### Week 2-3: Single Container (10 days)

**Day 1-2: Backend API - File Upload**
- [ ] Create FastAPI app (`lineage_v3/api/main.py`)
- [ ] Implement `POST /api/upload-parquet`
- [ ] Save files to `/tmp/jobs/{job_id}/`
- [ ] Return job ID

**Day 3-4: Backend API - Background Processing**
- [ ] Implement background task wrapper
- [ ] Integrate existing `DuckDBWorkspace` code (unchanged)
- [ ] Integrate existing `QualityAwareParser` code (unchanged)
- [ ] Integrate existing `FrontendFormatter` code (modified for DDL)
- [ ] Write status updates during processing

**Day 5: Backend API - Status & Result Endpoints**
- [ ] Implement `GET /api/status/{job_id}`
- [ ] Implement `GET /api/result/{job_id}`
- [ ] Add error handling
- [ ] Test with real Parquet files (30-120 second processing)

**Day 6-7: Frontend - Upload UI**
- [ ] Modify `ImportDataModal.tsx`
- [ ] Add "Upload Parquet Files" mode
- [ ] Add file input fields (4 files)
- [ ] Implement upload handler
- [ ] Implement polling logic (every 2 seconds)

**Day 8: Frontend - Progress Display**
- [ ] Add progress bar component
- [ ] Add status message display
- [ ] Add elapsed time display
- [ ] Add error/warning display
- [ ] Test UX during long processing

**Day 9: Docker Container**
- [ ] Create `Dockerfile` (multi-stage build)
- [ ] Configure Nginx routing (or FastAPI static serving)
- [ ] Test local build
- [ ] Optimize image size (<500 MB target)

**Day 10: Integration Testing**
- [ ] End-to-end test (upload → parse → display)
- [ ] Test with large datasets (100+ objects)
- [ ] Test error scenarios (invalid files, parsing errors)
- [ ] Test multiple concurrent users

**Deliverable:** ✅ Single container with full upload → parse → display workflow

### Week 4: SQL Viewer (5 days)

**Day 1: Backend - DDL Integration**
- [ ] Modify `FrontendFormatter` to include DDL text
- [ ] Add `include_ddl` parameter
- [ ] Test JSON output (verify DDL included)
- [ ] Verify file size (should be <5 MB total)

**Day 2-3: Frontend - SQL Viewer Component**
- [ ] Create `SqlViewer.tsx` component
- [ ] Integrate Prism.js for syntax highlighting
- [ ] Implement split view layout (50/50)
- [ ] Add search functionality
- [ ] Style like SQL editor (dark theme)

**Day 4: Frontend - Context Menu**
- [ ] Add right-click handler to `CustomNode`
- [ ] Show "View SQL Definition" option
- [ ] Connect to SQL viewer state
- [ ] Test on different object types

**Day 5: Polish & Testing**
- [ ] Add scrollbars and navigation
- [ ] Test full-text search with highlighting
- [ ] Test with long SQL (1000+ lines)
- [ ] Test mobile responsiveness
- [ ] User acceptance testing

**Deliverable:** ✅ Right-click → View SQL feature with syntax highlighting

---

## 8. Technical Specifications

### 8.1. System Requirements

**Backend Container:**
- Base Image: `python:3.12-slim`
- RAM: 2-4 GB (for DuckDB + parsing)
- CPU: 2 cores minimum
- Disk: 10 GB (for `/tmp/jobs/` + Docker layers)

**Synapse Spark Pool:**
- Size: Small (3 nodes) or Medium (5 nodes)
- Spark Version: 3.3+
- Python Version: 3.10+
- Auto-pause: 5 minutes recommended

**Client Browser:**
- Modern browser (Chrome, Firefox, Edge, Safari)
- JavaScript enabled
- LocalStorage available (for caching)

### 8.2. File Specifications

**Parquet Files:**

| File | Expected Rows | Expected Size | Schema |
|------|---------------|---------------|---------|
| `objects.parquet` | 100-1,000 | <1 MB | object_id (int), schema_name (str), object_name (str), object_type (str), create_date (timestamp), modify_date (timestamp) |
| `dependencies.parquet` | 500-5,000 | <5 MB | referencing_object_id (int), referenced_object_id (int) |
| `definitions.parquet` | 50-500 | <10 MB | object_id (int), object_name (str), schema_name (str), definition (str) |
| `query_logs.parquet` | 10,000 | <5 MB | request_id (str), command_text (str), submit_time (timestamp) |

**JSON Output:**

```typescript
// frontend_lineage.json with DDL
[
  {
    "id": "1001",
    "name": "spLoadDimCustomers",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Stored Procedure",
    "description": "Confidence: 0.85",
    "data_model_type": "Other",
    "inputs": ["2001", "2002"],
    "outputs": ["3001"],
    "ddl_text": "CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimCustomers]\nAS\nBEGIN\n    INSERT INTO DimCustomers...\nEND"
  }
]
```

**Expected Size:** 2-5 MB (with DDL text for 100 SPs)

### 8.3. API Response Times

| Endpoint | Expected Response Time | Notes |
|----------|----------------------|-------|
| `POST /api/upload-parquet` | <5 seconds | File upload + save to disk |
| `GET /api/status/{job_id}` | <100ms | Read JSON file |
| `GET /api/result/{job_id}` | <500ms | Read JSON file (2-5 MB) |
| **Background processing** | **30-120 seconds** | DuckDB load + parsing + format |

### 8.4. Polling Strategy

**Configuration:**
- Poll interval: 2 seconds
- Timeout: 300 seconds (5 minutes)
- Retry on failure: 3 times

**Optimization:**
- Exponential backoff after 1 minute (2s → 5s → 10s)
- Stop polling if browser tab hidden
- Resume polling when tab visible

---

## 9. Testing Strategy

### 9.1. Unit Tests

**Backend:**
- [ ] Test file upload handler (valid/invalid files)
- [ ] Test status file read/write
- [ ] Test background task wrapper
- [ ] Test existing Python code (regression)

**Frontend:**
- [ ] Test file input validation
- [ ] Test polling logic (complete, error, timeout)
- [ ] Test progress bar updates
- [ ] Test SQL viewer rendering

### 9.2. Integration Tests

- [ ] End-to-end: Upload Parquet → Parse → Display graph
- [ ] Error handling: Invalid Parquet files
- [ ] Error handling: Parsing failures
- [ ] Concurrent users: 2 users upload simultaneously
- [ ] Large dataset: 500+ objects
- [ ] SQL viewer: Right-click → View SQL

### 9.3. Performance Tests

- [ ] Parsing time: 30-120 seconds target
- [ ] Memory usage: <4 GB during parsing
- [ ] Frontend load time: <2 seconds
- [ ] JSON download time: <3 seconds (5 MB file)
- [ ] Container startup time: <30 seconds

### 9.4. User Acceptance Tests

- [ ] User can extract DMV data in Synapse Studio (GUI)
- [ ] User can upload Parquet files in browser
- [ ] User sees progress during parsing
- [ ] User can view SQL definitions
- [ ] User can search SQL text
- [ ] Error messages are clear and actionable

---

## 10. Deployment Guide

### 10.1. Build Docker Image

```bash
# Build locally
docker build -t vibecoding-lineage:latest .

# Test locally
docker run -p 8000:8000 vibecoding-lineage:latest

# Open browser: http://localhost:8000

# Push to Azure Container Registry
az acr login --name myregistry
docker tag vibecoding-lineage:latest myregistry.azurecr.io/lineage:v3.0
docker push myregistry.azurecr.io/lineage:v3.0
```

### 10.2. Deploy to Azure Web App

```bash
# Create Azure Web App (Linux container)
az webapp create \
  --resource-group lineage-rg \
  --plan lineage-plan \
  --name vibecoding-lineage \
  --deployment-container-image-name myregistry.azurecr.io/lineage:v3.0

# Configure environment
az webapp config appsettings set \
  --resource-group lineage-rg \
  --name vibecoding-lineage \
  --settings WEBSITES_PORT=8000

# Configure container settings
az webapp config container set \
  --name vibecoding-lineage \
  --resource-group lineage-rg \
  --docker-custom-image-name myregistry.azurecr.io/lineage:v3.0 \
  --docker-registry-server-url https://myregistry.azurecr.io

# Scale up (if needed)
az appservice plan update \
  --name lineage-plan \
  --resource-group lineage-rg \
  --sku B2  # 2 cores, 3.5 GB RAM
```

### 10.3. Environment Configuration

**Environment Variables:**
```bash
# Container settings
WEBSITES_PORT=8000
WEBSITES_CONTAINER_START_TIME_LIMIT=600

# Cleanup settings (optional)
JOB_CLEANUP_INTERVAL_MINUTES=60
JOB_RETENTION_HOURS=1

# Logging
LOG_LEVEL=INFO
```

### 10.4. Health Monitoring

**Health Check Endpoint:**
```bash
# Test health
curl https://vibecoding-lineage.azurewebsites.net/health

# Response:
{
  "status": "healthy",
  "version": "3.0",
  "uptime_seconds": 3600
}
```

**Azure Monitoring:**
- Enable Application Insights
- Set up alerts for:
  - Container restart
  - High memory usage (>80%)
  - Response time >5 seconds
  - Error rate >5%

---

## 11. Critical Review & Risk Assessment

### 11.1. Architecture Review

✅ **APPROVED Design Principles:**

1. **Existing Python Code Unchanged**
   - Core parsing logic runs as-is
   - Only wrapped in web API
   - Low risk of introducing bugs

2. **Server-Side Processing**
   - Parquet parsing in container, not browser
   - No WASM dependencies
   - Standard Python environment

3. **Simple Polling (Not WebSocket)**
   - 2-second polling is acceptable for 30-120s jobs
   - No complex WebSocket infrastructure
   - Easy to implement and debug

4. **Ephemeral Job Storage**
   - `/tmp/jobs/` lost on restart (acceptable)
   - Cleanup after 1 hour
   - No persistent storage complexity

5. **DDL Included in JSON**
   - Each SP <100 KB DDL
   - Total JSON <5 MB (manageable)
   - No lazy-loading complexity

### 11.2. Risk Assessment

#### Risk 1: Container Memory (MEDIUM)

**Risk:** Concurrent users exhaust container memory

**Analysis:**
- Each job needs ~500 MB RAM (DuckDB workspace)
- 4 GB container = ~6 concurrent users
- 10 users = 5 GB = Container crashes

**Mitigation:**
- [ ] Implement job queue (max 3 concurrent)
- [ ] Add memory monitoring
- [ ] Scale to B3 (8 GB RAM) if needed

**Likelihood:** ⚠️ Medium (depends on user load)

**Impact:** 🔴 High (container crash)

**Verdict:** ⚠️ **IMPLEMENT JOB QUEUE**

#### Risk 2: Parsing Timeout (LOW)

**Risk:** Parsing takes >300 seconds, user gives up

**Analysis:**
- Current: 30-120 seconds typical
- Worst case: 200 seconds (very large dataset)
- 300 second timeout is safe

**Mitigation:**
- [ ] Display "This may take 2-3 minutes" message
- [ ] Show elapsed time during parsing
- [ ] Add "Cancel Job" button (optional)

**Likelihood:** ✅ Low (tested range is 30-120s)

**Impact:** ⚠️ Medium (user frustration)

**Verdict:** ✅ **ACCEPTABLE (with clear messaging)**

#### Risk 3: File Size (LOW)

**Risk:** DDL text makes JSON file too large (>10 MB)

**Analysis:**
- 100 SPs × 30 KB avg = 3 MB
- 500 SPs × 30 KB avg = 15 MB ⚠️
- Worst case: 20 MB (still downloadable in <5s on 4G)

**Mitigation:**
- [ ] Monitor file sizes in production
- [ ] Add lazy-loading if >10 MB (future enhancement)
- [ ] Compress JSON with gzip (browser auto-decompresses)

**Likelihood:** ✅ Low (typical datasets <200 SPs)

**Impact:** ⚠️ Medium (slow frontend load)

**Verdict:** ✅ **ACCEPTABLE (monitor in production)**

#### Risk 4: PySpark Costs (LOW)

**Risk:** Users forget to pause Spark pool, costs increase

**Analysis:**
- Spark pool cost: ~$0.20/hour (Small pool)
- Extraction time: 5-10 minutes = $0.02
- If user forgets to pause: $5/day = $150/month

**Mitigation:**
- [ ] Enable auto-pause (5 minutes) in documentation
- [ ] Add warning in notebook: "Ensure auto-pause is enabled"
- [ ] Document pool selection (Small = cheapest)

**Likelihood:** ⚠️ Medium (users forget)

**Impact:** ⚠️ Medium (increased costs)

**Verdict:** ✅ **ACCEPTABLE (user education + auto-pause)**

#### Risk 5: Single Container Failure (MEDIUM)

**Risk:** Container crashes, all active jobs lost

**Analysis:**
- `/tmp/jobs/` is ephemeral
- If container restarts, jobs lost
- Users must re-upload and restart

**Mitigation:**
- [ ] Add job persistence to Azure Blob (future enhancement)
- [ ] For now: Clear error message "Job lost due to system restart"
- [ ] Users can re-upload quickly (files are local)

**Likelihood:** ⚠️ Medium (container restarts happen)

**Impact:** ⚠️ Medium (user must re-upload)

**Verdict:** ⚠️ **ACCEPTABLE (document limitation, add persistence in v3.1)**

### 11.3. Overall Assessment

**Feasibility:** ✅ **HIGH** (all features are achievable)

**Complexity:** ✅ **MEDIUM** (no major architectural changes)

**Timeline:** ✅ **REALISTIC** (4 weeks is achievable)

**Risk Level:** ✅ **LOW-MEDIUM** (mitigations in place)

**ROI:** ✅ **HIGH** (eliminates CLI step, better UX)

### 11.4. Go/No-Go Decision

✅ **GO - APPROVED FOR IMPLEMENTATION**

**Justification:**
1. All features are technically feasible
2. Existing Python code runs unchanged (low risk)
3. 4-week timeline is realistic
4. Risks are manageable with documented mitigations
5. User experience significantly improved

**Contingencies:**
- If Week 2 testing shows memory issues → Implement job queue immediately
- If JSON file size >10 MB → Add gzip compression
- If parsing >300 seconds → Increase timeout to 600 seconds
- If Spark costs are concern → Document auto-pause setup clearly

---

## 12. Appendix

### 12.1. Configuration Decisions Summary

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Q1: Status Updates** | Poll every 2 seconds | Simple, acceptable latency |
| **Q2: Job Storage** | `/tmp/jobs/` (ephemeral) | Simple, lost on restart OK |
| **Q3: DDL Strategy** | Include in JSON | Each SP <100 KB, total <5 MB OK |
| **Q4: SQL Formatting** | Syntax highlighting (Prism.js) | Professional appearance, read-only |

### 12.2. Success Metrics

**Operational Metrics:**
- [ ] Parsing success rate >95%
- [ ] Average parsing time <90 seconds
- [ ] Container memory usage <80%
- [ ] Error rate <5%

**User Metrics:**
- [ ] User can extract DMV data without CLI
- [ ] User can upload Parquet files in browser
- [ ] User sees progress during parsing
- [ ] User can view SQL definitions

**Business Metrics:**
- [ ] Reduce onboarding time (no Python setup)
- [ ] Increase adoption (GUI-based workflow)
- [ ] Reduce support requests (clear error messages)

### 12.3. Future Enhancements (v3.1)

**Not in Scope for v3.0:**
- [ ] Job persistence to Azure Blob
- [ ] WebSocket real-time updates
- [ ] Databricks support (Synapse only for v3.0)
- [ ] DDL lazy-loading (only if JSON >10 MB)
- [ ] Job queue with max concurrency
- [ ] User authentication/multi-tenancy
- [ ] Advanced SQL editor features (edit DDL, save changes)

**Prioritization:**
1. **High:** Job queue (if memory issues)
2. **Medium:** Job persistence (if users complain about lost jobs)
3. **Low:** WebSocket updates (polling works fine)
4. **Low:** Databricks support (if requested)

---

## 13. Approval & Sign-Off

**Specification Version:** 3.0 FINAL

**Approved By:**
- [ ] Vibecoding Team Lead
- [ ] Technical Architect
- [ ] Product Owner

**Approval Date:** 2025-10-27

**Implementation Start Date:** TBD

**Target Completion Date:** +4 weeks from start

---

**Document Status:** ✅ **FINAL - READY FOR IMPLEMENTATION**

**Next Steps:**
1. Get stakeholder sign-off
2. Set up development environment
3. Begin Week 1: PySpark extractor implementation
4. Daily standups to track progress
5. Weekly demos to stakeholders

---

**END OF SPECIFICATION**
