# Data Contracts and Interface Specifications

**Complete reference for all data interfaces, schemas, and API contracts**

> **Context:** This document combines interface specifications (DMV, Parquet, JSON, YAML) with detailed data contracts (Parquet schemas, JSON formats, REST API endpoints).

---

## Table of Contents

- [Overview](#overview)
- [Interface 1: DMV (Database Metadata Queries)](#interface-1-dmv-database-metadata-queries)
- [Interface 2: Parquet (Data Storage Format)](#interface-2-parquet-data-storage-format)
- [Interface 3: JSON (API Output Format)](#interface-3-json-api-output-format)
- [Interface 4: YAML (SQL Cleaning Rules)](#interface-4-yaml-sql-cleaning-rules)
- [REST API Endpoints](#rest-api-endpoints)

---

## Overview

The Data Lineage Visualizer defines **4 core interfaces** that enable modularity and extensibility:

1. **DMV Interface** - Database metadata extraction queries
2. **Parquet Interface** - Standardized file storage format
3. **JSON Interface** - Frontend visualization data format
4. **YAML Interface** - SQL cleaning and extraction rules

These interfaces allow you to:
- Add support for new SQL dialects by implementing the DMV and YAML interfaces
- Integrate with external data sources via the Parquet interface
- Build custom visualizations using the JSON interface

---

## Interface 1: DMV (Database Metadata Queries)

### Contract Purpose

Defines what **database metadata queries must return** when extracting objects and definitions.

### Folder Structure

```
engine/
├── dialects/
│   ├── base.py                    # Abstract base class (interface contract)
│   └── tsql.py                    # T-SQL implementation
│
└── connectors/queries/
    └── tsql/
        └── metadata.yaml          # 5 T-SQL metadata extraction queries
```

### Required Query: objects_query

**Contract:**
```python
"""
Must return DataFrame with these columns:

Column Name          | Type       | Required | Description
---------------------|------------|----------|---------------------------
database_object_id   | int64      | ✅       | Unique object identifier
schema_name          | string     | ✅       | Database schema/namespace
object_name          | string     | ✅       | Object name (table/view/proc)
object_type          | string     | ✅       | Type (PROCEDURE, VIEW, TABLE, FUNCTION)
created_at           | datetime64 | ⬜       | Creation timestamp
modified_at          | datetime64 | ⬜       | Last modification timestamp
"""
```

**Example (T-SQL):**
```sql
SELECT
    o.object_id as database_object_id,
    SCHEMA_NAME(o.schema_id) as schema_name,
    o.name as object_name,
    o.type_desc as object_type,
    o.create_date as created_at,
    o.modify_date as modified_at
FROM sys.objects o
WHERE o.type IN ('P', 'V', 'FN', 'IF', 'TF')
  AND o.is_ms_shipped = 0
```

### Required Query: definitions_query

**Contract:**
```python
"""
Must return DataFrame with these columns:

Column Name          | Type       | Required | Description
---------------------|------------|----------|---------------------------
database_object_id   | int64      | ✅       | Matches objects_query.database_object_id
sql_code             | string     | ✅       | Full SQL source code (CREATE statement)
"""
```

**Example (T-SQL):**
```sql
SELECT
    sm.object_id as database_object_id,
    sm.definition as sql_code
FROM sys.sql_modules sm
WHERE sm.definition IS NOT NULL
```

---

## Interface 2: Parquet (Data Storage Format)

### Contract Purpose

Defines the **exact schema** for Parquet files that store database metadata.

**5 Parquet Files: 3 Required, 2 Optional**

### Location

- **Validation:** `engine/core/validation.py` (PARQUET_SCHEMAS)
- **Import:** `engine/core/duckdb_workspace.py` (load_parquet_files method)

---

### 1. objects.parquet (REQUIRED)

**Purpose:** List of all database objects (tables, views, stored procedures, functions)

**Schema Contract:**
```python
{
    "object_id": "int64",          # REQUIRED - Unique identifier (PRIMARY KEY)
    "schema_name": "string",        # REQUIRED - Database schema name
    "object_name": "string",        # REQUIRED - Object name
    "object_type": "string",        # REQUIRED - Friendly name: Table, View, Stored Procedure, Function
    "create_date": "datetime64",    # OPTIONAL - Creation timestamp
    "modify_date": "datetime64"     # OPTIONAL - Last modification timestamp
}
```

**Constraints:**
- `object_id` must be unique across all objects
- `object_type` values: `Table`, `View`, `Stored Procedure`, `Function`
- No NULL values in REQUIRED columns

**Code Reference:** `engine/core/validation.py:23`

---

### 2. definitions.parquet (REQUIRED)

**Purpose:** DDL source code for stored procedures, views, and functions

**Schema Contract:**
```python
{
    "object_id": "int64",          # REQUIRED - FOREIGN KEY → objects.object_id
    "definition": "string"          # REQUIRED - Full SQL source code (DDL)
}
```

**Constraints:**
- Every `object_id` must exist in `objects.parquet`
- `definition` must contain complete CREATE statement
- Include all comments (used for `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints)
- SQL validity checked by parser, not at import

**Code Reference:** `engine/core/validation.py:24`

---

### 3. dependencies.parquet (REQUIRED)

**Purpose:** Native database dependency tracking (cross-referenced with parser results)

**Schema Contract:**
```python
{
    "referencing_object_id": "int64",    # REQUIRED - Source object ID (SP/view)
    "referenced_object_id": "int64",     # REQUIRED - Target object ID (table/view)
    "referenced_schema_name": "string",  # REQUIRED - Schema of referenced object
    "referenced_entity_name": "string"   # REQUIRED - Name of referenced object
}
```

**Constraints:**
- `referencing_object_id` should exist in `objects.parquet`
- `referenced_object_id` should exist in `objects.parquet`
- This file provides validation data - parser extracts dependencies independently

**Note:** If your database doesn't track dependencies natively, provide an empty Parquet file with the correct schema.

**Code Reference:** `engine/core/validation.py:25`

---

### 4. query_logs.parquet (OPTIONAL)

**Purpose:** Query execution logs for validation and runtime analysis

**Schema Contract:**
```python
{
    "command_text": "string"        # REQUIRED - SQL command text
}
```

**Note:** The file must contain **only** the `command_text` column. Additional columns are not supported.

**Usage:** Validates parser results against actual query execution patterns

**Code Reference:** `engine/core/duckdb_workspace.py:528`

---

### 5. table_columns.parquet (OPTIONAL)

**Purpose:** Table schema metadata for generating CREATE TABLE statements

**Schema Contract:**
```python
{
    "object_id": "int64",          # REQUIRED - FOREIGN KEY → objects.object_id
    "schema_name": "string",        # REQUIRED - Schema name
    "table_name": "string",         # REQUIRED - Table name
    "column_name": "string",        # REQUIRED - Column name
    "data_type": "string",          # REQUIRED - SQL data type
    "ordinal_position": "int32",    # OPTIONAL - Column order (1, 2, 3...)
    "is_nullable": "boolean"        # OPTIONAL - Nullable flag
}
```

**Note:** The 5 **REQUIRED** columns must all be present. Optional columns enhance functionality but are not mandatory.

**Usage:** Enables CREATE TABLE DDL generation for search functionality

**Code Reference:** `engine/core/duckdb_workspace.py:530`

---

## Interface 3: JSON (API Output Format)

### Contract Purpose

Defines the **frontend lineage node format** returned by the API and consumed by the frontend graph visualization.

**This is the EXTERNAL data contract - what you must provide to the frontend.**

### Location

- **Generation:** `engine/output/frontend_formatter.py`
- **Consumers:** `frontend/components/LineageGraph.tsx`
- **Validation:** `engine/core/validation.py` (validate_lineage_json)

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

## Interface 4: YAML (SQL Cleaning Rules)

### Contract Purpose

Defines the **structure of YAML rules** used to clean and normalize dialect-specific SQL before parsing.

### Folder Structure

```
engine/rules/
├── README.md                      # Rule system documentation
├── YAML_STRUCTURE.md              # Complete YAML schema reference
├── TEMPLATE.yaml                  # Template for creating new rules
├── rule_loader.py                 # Rule validation and loading logic
│
├── defaults/                      # ⭐ DEFAULT RULES (for resetting)
│   ├── 05_extract_sources_ansi.yaml
│   ├── 06_extract_targets_ansi.yaml
│   └── 10_comment_removal.yaml
│
├── tsql/                          # T-SQL specific rules
│   ├── 07_extract_sources_tsql_apply.yaml
│   ├── 08_extract_sp_calls_tsql.yaml
│   └── 10_extract_targets_tsql.yaml
```

**Rule Loading Strategy:**
1. **Load dialect-specific rules** from `engine/rules/{dialect}/` (e.g., `tsql/`)
2. **Merge with default rules** from `engine/rules/defaults/`
3. **Apply in priority order** (lower number = higher priority)

**Default Rules (Reset Source):**
- **Location:** `engine/rules/defaults/`
- **Purpose:** ANSI-compliant patterns that work across all SQL dialects
- **Usage:** Used as fallback when no dialect-specific rule exists

**Code Reference:** `engine/rules/rule_loader.py`

### YAML Rule Schema Contract

**Minimal Required Fields:**
```yaml
name: string                # Unique rule name (within dialect)
description: string         # Human-readable description
dialect: string             # Dialect name (tsql)
enabled: boolean            # Whether rule is active
priority: integer           # Execution order (10, 20, 30...)
pattern: string             # Regex pattern to match
replacement: string         # Replacement string (can use \1, \2 for capture groups)
```

**Optional Fields:**
```yaml
category: string            # Category: cleaning, extraction, normalization
examples:                   # Test cases
  - before: string
    after: string
    description: string
```

**Example:**
```yaml
name: remove_go_batch_separator
description: Remove GO batch separators from T-SQL
dialect: tsql
enabled: true
priority: 10
category: cleaning
pattern: '^\s*GO\s*$'
replacement: ''
flags:
  - IGNORECASE
  - MULTILINE
examples:
  - before: |
      CREATE PROCEDURE test
      AS
      BEGIN
        SELECT 1
      END
      GO
    after: |
      CREATE PROCEDURE test
      AS
      BEGIN
        SELECT 1
      END
    description: "Removes GO batch separator"
```

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

**Key Endpoints:**

### Parquet Upload
- `POST /api/upload/parquet` - Upload 3-5 Parquet files
- `GET /api/upload/status/{job_id}` - Check upload status

### Lineage Data
- `GET /api/lineage` - Get full lineage graph
- `GET /api/lineage/export` - Export lineage as JSON

### Database Direct
- `POST /api/database/import` - Import directly from database
- `GET /api/database/status` - Check import status

### Search & Utilities
- `GET /api/search` - Full-text search across DDL
- `GET /api/health` - Health check endpoint

---

## References

- **ARCHITECTURE.md** - System design and parser internals
- **CONFIGURATION.md** - Environment variables and database setup
- **DEVELOPMENT_SETUP.md** - Development environment configuration
- **BaseDialect** (`engine/dialects/base.py`) - Abstract interface definition
- **YAML Structure** (`engine/rules/YAML_STRUCTURE.md`) - YAML rule reference

---

## SQL Comment Hints

The parser supports special SQL comments to manually override parsed dependencies when automatic extraction fails or needs correction.

### Syntax

Add these comments **anywhere** in your SQL definition:

```sql
-- @LINEAGE_INPUTS: schema.table1, schema.table2, schema.table3
-- @LINEAGE_OUTPUTS: schema.output_table
```

### Example

```sql
CREATE PROCEDURE dbo.MyComplexProcedure
AS
BEGIN
    -- Parser may miss dynamic SQL dependencies
    -- @LINEAGE_INPUTS: dbo.SourceTable1, dbo.SourceTable2
    -- @LINEAGE_OUTPUTS: dbo.TargetTable

    DECLARE @sql NVARCHAR(MAX);
    SET @sql = 'SELECT * FROM dbo.SourceTable1';
    EXEC sp_executesql @sql;
END
```

### Use Cases

- **Dynamic SQL:** Parser cannot extract table names from string concatenation
- **Complex Patterns:** Unusual SQL patterns not covered by YAML rules
- **Manual Overrides:** Force specific dependencies for business logic reasons
- **External References:** Document dependencies to external systems

### Behavior

1. Parser first extracts dependencies using YAML rules
2. If `@LINEAGE_INPUTS` or `@LINEAGE_OUTPUTS` comments are found:
   - **Replace** automatic extraction with manual hints
   - Validate hint tables against metadata catalog
   - Only catalog-validated tables are included

**Note:** Comments must include complete two-part names (`schema.table`). Single-part names are not supported.

---

**Last Updated:** 2025-01-23
**Status:** Production-ready
