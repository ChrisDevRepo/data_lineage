# Interface Contracts Specification

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

**Query Storage (Optional - Advanced Usage):**
- **Location:** `engine/connectors/queries/{dialect}/metadata.yaml`
- **Contains:** 5 named queries for advanced database operations:
  1. `list_stored_procedures` - Get all procedures with metadata
  2. `list_tables` - Get all tables with column info
  3. `list_views` - Get all views with DDL
  4. `list_functions` - Get all functions (scalar, table-valued)
  5. `list_dependencies` - Get object dependencies
- **Usage:** For incremental refresh and advanced metadata operations
- **Code Reference:** `engine/connectors/queries/tsql/metadata.yaml:1-205`

### Core Query Contract (Required)

**Location:** `engine/dialects/base.py` - Abstract properties that MUST be implemented

### Required Query: `objects_query`

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

### Required Query: `definitions_query`

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

- **Specification:** `docs/DATA_CONTRACTS.md` (Parquet File Specifications section)
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

**Code Reference:** `engine/core/validation.py:23` - Validates: `object_id`, `schema_name`, `object_name`, `object_type`

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

**Code Reference:** `engine/core/validation.py:24` - Validates: `object_id`, `definition`

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

**Note:** If your database doesn't track dependencies natively (like SQL Server's `sys.sql_expression_dependencies`), provide an empty Parquet file with the correct schema.

**Code Reference:** `engine/core/validation.py:25` - Validates all 4 columns

---

### 4. query_logs.parquet (OPTIONAL)

**Purpose:** Query execution logs for validation and runtime analysis

**Schema Contract:**
```python
{
    "command_text": "string"        # REQUIRED - SQL command text
}
```

**Note:** The file must contain **only** the `command_text` column. Additional columns are not supported by the current implementation.

**Usage:** Validates parser results against actual query execution patterns

**Code Reference:** `engine/core/duckdb_workspace.py:528` - Detection: `command_text` column

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

**Note:** The 5 **REQUIRED** columns (`object_id`, `schema_name`, `table_name`, `column_name`, `data_type`) must all be present. Optional columns (`ordinal_position`, `is_nullable`) enhance functionality but are not mandatory.

**Usage:** Enables CREATE TABLE DDL generation for search functionality

**Code Reference:** `engine/core/duckdb_workspace.py:530` - Detection: validates 5 required columns

---

## Interface 3: JSON (API Output Format)

### Contract Purpose

Defines the **frontend lineage node format** returned by the API and consumed by the frontend graph visualization.

**This is the EXTERNAL data contract - what you must provide to the frontend.**

### Location

- **Generation:** `engine/output/frontend_formatter.py`
- **Specification:** `docs/DATA_CONTRACTS.md` (Frontend Lineage Format section)
- **Consumers:** `frontend/components/LineageGraph.tsx`
- **Validation:** `engine/core/validation.py` (validate_lineage_json)


## Interface 4: YAML Regex (SQL Cleaning Rules)

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
- **Reset:** Developer Panel "Reset Rules to Defaults" restores from this folder
- **Count:** 3 default rules (comment removal, basic extraction)

**Code Reference:** `engine/rules/rule_loader.py` (loads and validates all rules)

### Location Details

- **Specification:** `engine/rules/TEMPLATE.yaml` (rule template)
- **Validation:** `engine/rules/rule_loader.py:20-80` (JSON Schema validation)
- **Storage:** `engine/rules/{dialect}/` (dialect-specific) + `engine/rules/defaults/` (fallback)
- **Template:** `engine/rules/TEMPLATE.yaml` (copy to create new rules)

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

- **DATA_CONTRACTS.md** - Detailed Parquet and JSON schemas
- **BaseDialect** (`engine/dialects/base.py`) - Abstract interface definition
- **YAML Structure** (`engine/rules/YAML_STRUCTURE.md`) - YAML rule reference
