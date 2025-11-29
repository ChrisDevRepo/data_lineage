# Data Contracts Reference

**Parquet schemas, JSON formats, and REST API endpoints**

> **Context:** This document defines INTERFACE 2 (Parquet) and INTERFACE 3 (JSON) contracts. For complete specification of all 4 interfaces (DMV, Parquet, JSON, YAML), see [INTERFACE_CONTRACTS.md](INTERFACE_CONTRACTS.md).

---

## Table of Contents

- [Parquet File Specifications](#parquet-file-specifications)
- [JSON Data Formats](#json-data-formats)
- [REST API Endpoints](#rest-api-endpoints)
- [Database Metadata Requirements](#database-metadata-requirements)

---

## Parquet File Specifications

### Overview

The application accepts 3-5 Parquet files containing database metadata:

| File | Required | Description |
|------|----------|-------------|
| `objects.parquet` | ✅ Yes | Database objects (tables, views, SPs) |
| `definitions.parquet` | ✅ Yes | Object DDL definitions |
| `dependencies.parquet` | ✅ Yes | SQL expression dependencies |
| `query_logs.parquet` | ⬜ Optional | Query execution logs (validation) |
| `table_columns.parquet` | ⬜ Optional | Table schema metadata |

---

### 1. objects.parquet

**Purpose:** List of all database objects (tables, views, stored procedures, functions)

**Schema:**

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `object_id` | int64 | ✅ | Unique object identifier |
| `schema_name` | string | ✅ | Database schema name |
| `object_name` | string | ✅ | Object name (table/view/SP) |
| `object_type` | string | ✅ | **Friendly name**: `Table`, `View`, `Stored Procedure`, or `Function` |
| `create_date` | timestamp | ⬜ | Creation timestamp |
| `modify_date` | timestamp | ⬜ | Last modification timestamp |

**DMV Queries:** See `engine/extractor/synapse_dmv_extractor.py`

---

### 2. definitions.parquet

**Purpose:** DDL source code for stored procedures, views, and functions

**Schema:**

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `object_id` | int64 | ✅ | Matches `objects.object_id` |
| `definition` | string | ✅ | Full SQL source code (DDL) |

**DMV Queries:** See `engine/extractor/synapse_dmv_extractor.py`

**Important:**
- Definitions must be complete CREATE statements
- Include all comments (used for `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints)

---

### 3. dependencies.parquet

**Purpose:** SQL Server's native dependency tracking (cross-referenced with parser results)

**Schema:**

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `referencing_object_id` | int64 | ✅ | Object ID of source (SP/view) |
| `referenced_object_id` | int64 | ✅ | Object ID of target (table/view) |
| `referenced_schema_name` | string | ✅ | Schema of referenced object |
| `referenced_entity_name` | string | ✅ | Name of referenced object |

**DMV Queries:** See `engine/extractor/synapse_dmv_extractor.py`

**Note:** Parser extracts dependencies independently - this file provides validation data.

---

### 4. query_logs.parquet (Optional)

**Purpose:** Validate parser results against actual query execution

**Schema:**

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `command_text` | string | ✅ | SQL command text |

**Important:** The file must contain **only** the `command_text` column. No other columns are supported by the current implementation.

**DMV Queries:** See `engine/extractor/synapse_dmv_extractor.py`

---

### 5. table_columns.parquet

**Purpose:** Generate CREATE TABLE statements for search functionality

**Schema:**

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `object_id` | int64 | ✅ | Table object_id (foreign key to objects.object_id) |
| `schema_name` | string | ✅ | Schema name of the table |
| `table_name` | string | ✅ | Name of the table |
| `column_name` | string | ✅ | Column name |
| `data_type` | string | ✅ | SQL data type |
| `ordinal_position` | int32 | ⬜ | Column order (1, 2, 3...) |
| `is_nullable` | boolean | ⬜ | Nullable flag |

**Important:** The 5 **REQUIRED** columns (`object_id`, `schema_name`, `table_name`, `column_name`, `data_type`) must all be present. The optional columns enhance functionality but are not mandatory.

**DMV Queries:** See `engine/extractor/synapse_dmv_extractor.py`

---

## JSON Data Formats

### Frontend Lineage Format

**File:** `data/latest_frontend_lineage.json`

**Purpose:** Interactive graph visualization data

**Structure:**

```json
[
  {
    "id": "1986106116",
    "name": "spLoadFactSales",
    "object_type": "Stored Procedure",
    "schema": "CONSUMPTION_FINANCE",
    "parse_success": true,
    "data_model_type": "Fact",
    "node_symbol": "diamond",
    "inputs": ["101", "102", "103"],
    "outputs": ["201"],
    "ddl_text": "CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadFactSales] AS...",
    "description": "Parse Success: True"
  }
]
```

**Field Reference:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique object identifier (stringified object_id from database) |
| `name` | string | Display name (object_name) |
| `object_type` | string | Object type: `Table`, `View`, `Stored Procedure`, `Function` |
| `schema` | string | Database schema |
| `parse_success` | boolean | Parser completed without errors |
| `data_model_type` | string | Classification: `Dimension`, `Fact`, `Other` |
| `node_symbol` | string | Visualization symbol: `circle`, `diamond`, `square` |
| `inputs` | string[] | Array of input node IDs (sources) - **strings**, not integers |
| `outputs` | string[] | Array of output node IDs (targets) - **strings**, not integers |
| `ddl_text` | string | Full DDL (optional, only when include_ddl=true) |
| `description` | string | Human-readable summary with parse details |

---

## REST API Endpoints

**Base URL:** `http://localhost:8000`

**Complete API Documentation:** http://localhost:8000/docs (Swagger UI with interactive API testing)

The application provides a comprehensive REST API for:
- Uploading Parquet files
- Job status monitoring
- Retrieving lineage results
- Full-text DDL search
- Database direct connection (optional)
- Developer/debug endpoints

---

**See Also:**
- [QUICKSTART.md](../QUICKSTART.md) - Upload Parquet files via UI
- [CONFIGURATION.md](CONFIGURATION.md) - Database direct connection setup
- [ARCHITECTURE.md](ARCHITECTURE.md) - How parser processes metadata
