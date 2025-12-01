# Data Specifications

---

## Table of Contents

### Import Interfaces
- [Import Interface 1: Parquet Files](#import-interface-1-parquet-files)
- [Import Interface 2: Database Direct (DMV Queries)](#import-interface-2-database-direct-dmv-queries)
- [Import Interface 3: JSON Import](#import-interface-3-json-import)

### Configuration Interfaces
- [Configuration Interface 1: DMV Query Definitions (YAML)](#configuration-interface-1-dmv-query-definitions-yaml)
- [Configuration Interface 2: SQL Cleaning Rules (YAML)](#configuration-interface-2-sql-cleaning-rules-yaml)

### Additional Documentation
- [SQL Comment Hints](#sql-comment-hints)
- [References](#references)

---

## Overview

The Data Lineage Visualizer defines **5 interfaces** organized in 2 categories:

### Import Interfaces

1. **Parquet Files** - Upload 3-5 Parquet files with database metadata
2. **Database Direct** - Connection string to SQL Server/Azure SQL/Synapse/Fabric
3. **JSON Import** - Upload or paste lineage JSON (max 10MB)

### Configuration Interfaces

1. **DMV Query Definitions (YAML)** - SQL queries for metadata extraction from databases
2. **SQL Cleaning Rules (YAML)** - Regex patterns for SQL preprocessing and dependency extraction

**Extensibility:**
- Add support for new SQL dialects by creating DMV Query Definitions and SQL Cleaning Rules (YAML files)
- Integrate with external data sources by providing Parquet files in the correct schema

---

## Import Interface 1: Parquet Files

### Purpose

Upload 3-5 Parquet files containing database metadata exported from SQL Server DMVs or similar sources.

### File 1: objects.parquet (REQUIRED)

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

### File 2: definitions.parquet (REQUIRED)

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

---

### File 3: dependencies.parquet (REQUIRED)

**Purpose:** Native database dependency tracking

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

---

### File 4: query_logs.parquet (OPTIONAL)

**Purpose:** Query execution logs for validation and runtime analysis

**Schema Contract:**
```python
{
    "command_text": "string"        # REQUIRED - SQL command text
}
```

**Note:** The file must contain **only** the `command_text` column. Additional columns are not supported.

**Usage:** Validates parser results against actual query execution patterns

---

### File 5: table_columns.parquet (OPTIONAL)

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

**Usage:** Enables CREATE TABLE DDL generation for search functionality

---

## Import Interface 2: Database Direct (DMV Queries)

### Purpose

Connect directly to SQL Server/Azure SQL/Synapse/Fabric and query Dynamic Management Views (DMVs) to extract metadata at runtime.

### Location

- **Query Definitions:** `engine/connectors/queries/tsql/metadata.yaml` (YAML format)

### Query Contract

The YAML file must define the same DMV queries that are defined in the import specification for the Parquet files.

**Required Queries:**
1. `list_objects` - Returns all database objects (tables, views, procedures, functions)
2. `list_object_definitions` - Returns DDL source code for objects

**Optional Queries:**
3. `list_stored_procedures` - Filter for stored procedures only
4. `list_dependencies` - Native database dependency tracking
5. `list_table_columns` - Table schema metadata

### Output Format

Database Direct import converts DMV query results to the same Parquet schema as Import Interface 1, then ingests into DuckDB workspace.

---

## Import Interface 3: JSON Import

### Purpose

Upload or paste lineage JSON directly into the application for quick visualization without processing.

**Use Cases:**
- Import pre-generated lineage data from external tools
- Quick testing with sample data

### JSON Format

The JSON must be an array of node objects with the following structure:

```json
[
  {
    "id": "1986106116",
    "name": "spLoadFactSales",
    "schema": "CONSUMPTION_FINANCE",
    "object_type": "Stored Procedure",
    "inputs": ["101", "102", "103"],
    "outputs": ["201"]
  }
]
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique object identifier (**must be string**) |
| `name` | string | Object name |
| `schema` | string | Database schema name |
| `object_type` | string | `Table`, `View`, `Stored Procedure`, or `Function` |
| `inputs` | string[] | Array of input node IDs (**strings**, not integers) |
| `outputs` | string[] | Array of output node IDs (**strings**, not integers) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable description |
| `data_model_type` | string | Classification: `Dimension`, `Fact`, `Lookup`, or `Other` |
| `ddl_text` | string | Full DDL text (CREATE statement) |


### Validation

The system validates:
- JSON syntax (must be valid JSON)
- Array structure (must be array of objects)
- Required fields (all required fields must be present)
- Data types (strings, arrays, booleans must match specification)
- File size (max 10MB)

---

## Configuration Interface 1: DMV Query Definitions (YAML)

### Purpose

YAML configuration files that define SQL queries for extracting database metadata from DMVs.

**This interface defines HOW to query databases for Import Interface 2 (Database Direct).**

### Location

```
engine/connectors/queries/
└── tsql/
    └── metadata.yaml          # T-SQL DMV queries
```

### YAML Structure

Each query must have:
- `name` - Unique query identifier
- `description` - Human-readable description
- `sql` - The SQL query string
- `returns` - Expected DataFrame schema

### Required Queries

The YAML file must define the same DMV queries that are defined in the import specification for the Parquet files.

### Example (T-SQL metadata.yaml)

```yaml
queries:
  list_objects:
    name: "List Database Objects"
    description: "Get all user-defined objects"
    sql: |
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

## Configuration Interface 2: SQL Cleaning Rules (YAML)

### Purpose

YAML regex patterns for SQL preprocessing and dependency extraction. Rules clean SQL syntax and extract table references before catalog validation.

**This interface enables dialect-specific SQL parsing without code changes.**

### Folder Structure

```
engine/rules/
├── README.md                      # Rule system documentation
├── YAML_STRUCTURE.md              # Complete YAML schema reference
├── TEMPLATE.yaml                  # Template for creating new rules
├── rule_loader.py                 # Rule validation and loading logic
│
├── defaults/                      # DEFAULT RULES
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

## References

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and parser internals
- [CONFIGURATION.md](CONFIGURATION.md) - Environment variables and database setup
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development environment and YAML rule configuration
- `engine/rules/YAML_STRUCTURE.md` - Complete YAML rule schema reference

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
