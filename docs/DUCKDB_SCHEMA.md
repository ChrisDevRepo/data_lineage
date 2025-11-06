# DuckDB Workspace Schema Documentation

**File:** `lineage_workspace.duckdb` (default location)
**Version:** 3.7.0
**Date:** 2025-11-02

## Overview

The DuckDB workspace is a persistent file-based database that stores:
1. **Input Data** - Loaded from Parquet snapshots
2. **Metadata** - Incremental load tracking, parse results
3. **Results** - Final lineage graph exported to JSON

## Data Flow Architecture

**IMPORTANT:** Understanding where dependencies are stored:

```
DMV Dependencies (Views, Functions)
└─> dependencies table (confidence: 1.0)
    └─> Used for Views and Functions only

Parser Dependencies (Stored Procedures)
└─> lineage_metadata table (confidence: 0.5-0.95)
    └─> Exported to JSON files
    └─> NOT inserted into dependencies table (by design)

Query Log Validation
└─> query_logs table → validation only
    └─> Boosts confidence of parsed results
```

**Key Insight for Testing:**
- When checking for isolated objects, query **BOTH** `dependencies` AND `lineage_metadata`
- Example: `test_isolated_objects.py` Test 3 checks both sources (fixed in v3.7.0)

## Database Structure

```
lineage_workspace.duckdb
│
├── Input Tables (from Parquet files)
│   ├── objects          - All database objects catalog
│   ├── dependencies     - DMV dependencies (confidence 1.0)
│   ├── definitions      - DDL text for parsing
│   ├── query_logs       - Optional runtime execution logs
│   └── table_columns    - Optional table column metadata
│
├── Views (generated, managed by parser)
│   └── unified_ddl      - Union of real DDL + generated CREATE TABLE statements
│
├── Search Tables (managed by parser)
│   └── unified_ddl_materialized - Materialized view for full-text search
│
└── Metadata Tables (persistent, managed by parser)
    ├── lineage_metadata - Incremental load tracking
    └── lineage_results  - Final merged lineage graph
```

---

## Input Tables (Loaded from Parquet)

These tables are loaded from Parquet snapshots created by the Production Extractor.

### 1. `objects` Table

**Source:** `objects.parquet`
**Purpose:** Authoritative catalog of all database objects (tables, views, stored procedures)
**Primary Key:** `object_id`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `object_id` | INTEGER | Unique object identifier from sys.objects | 1001 |
| `schema_name` | TEXT | Schema name | "CONSUMPTION_FINANCE" |
| `object_name` | TEXT | Object name | "DimCustomers" |
| `type_code` | TEXT | Single-char type code | "U" (Table), "V" (View), "P" (Procedure) |
| `object_type` | TEXT | Human-readable type | "Table", "View", "Stored Procedure" |
| `create_date` | TIMESTAMP | Object creation date | 2024-01-01 10:30:00 |
| `modify_date` | TIMESTAMP | Last modification date (used for incremental load) | 2024-02-15 14:22:00 |
| `full_type_description` | TEXT | Detailed type description from sys.objects | "USER_TABLE", "SQL_STORED_PROCEDURE" |

**Sample Row:**
```sql
object_id: 1001
schema_name: CONSUMPTION_FINANCE
object_name: DimCustomers
type_code: U
object_type: Table
create_date: 2024-01-01 10:30:00
modify_date: 2024-02-15 14:22:00
full_type_description: USER_TABLE
```

**Typical Row Count:** 1,000 - 100,000 objects (depends on warehouse size)

---

### 2. `dependencies` Table

**Source:** `dependencies.parquet`
**Purpose:** DMV-based dependencies (highest confidence source)
**Primary Key:** None (composite: referencing_object_id + referenced_object_id)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `referencing_object_id` | INTEGER | Object that references another | 2001 (FactSales) |
| `referenced_object_id` | INTEGER | Object being referenced | 1001 (DimCustomers) |
| `referenced_schema_name` | TEXT | Schema of referenced object | "CONSUMPTION_FINANCE" |
| `referenced_entity_name` | TEXT | Name of referenced object | "DimCustomers" |
| `referenced_database_name` | TEXT | Database name (usually NULL for same DB) | NULL |
| `is_ambiguous` | BOOLEAN | DMV flag: ambiguous reference | false |
| `is_schema_bound_reference` | BOOLEAN | DMV flag: schema-bound | false |
| `is_caller_dependent` | BOOLEAN | DMV flag: caller-dependent | false |
| `referencing_class_desc` | TEXT | Type of referencing entity | "OBJECT_OR_COLUMN" |
| `referenced_class_desc` | TEXT | Type of referenced entity | "OBJECT_OR_COLUMN" |
| `referencing_type` | TEXT | Type description of referencing object | "SQL_STORED_PROCEDURE" |
| `referenced_type` | TEXT | Type description of referenced object | "USER_TABLE" |

**Sample Row:**
```sql
referencing_object_id: 2001
referenced_object_id: 1001
referenced_schema_name: CONSUMPTION_FINANCE
referenced_entity_name: DimCustomers
referenced_database_name: NULL
is_ambiguous: false
is_schema_bound_reference: false
is_caller_dependent: false
referencing_class_desc: OBJECT_OR_COLUMN
referenced_class_desc: OBJECT_OR_COLUMN
referencing_type: SQL_STORED_PROCEDURE
referenced_type: USER_TABLE
```

**Interpretation:**
- Object 2001 (a stored procedure) references object 1001 (DimCustomers table)
- This is a DMV-confirmed dependency (confidence 1.0)

**Typical Row Count:** 5,000 - 500,000 dependencies

---

### 3. `definitions` Table

**Source:** `definitions.parquet`
**Purpose:** DDL text for parsing (used when DMV dependencies are incomplete)
**Primary Key:** `object_id`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `object_id` | INTEGER | Object identifier | 2001 |
| `object_name` | TEXT | Object name | "spLoadDimCustomers" |
| `schema_name` | TEXT | Schema name | "CONSUMPTION_FINANCE" |
| `object_type` | TEXT | Object type | "SQL_STORED_PROCEDURE" |
| `definition` | TEXT | Full DDL text (can be very large) | "CREATE PROCEDURE..." |
| `uses_ansi_nulls` | BOOLEAN | ANSI NULLS setting | true |
| `uses_quoted_identifier` | BOOLEAN | Quoted identifier setting | true |
| `is_schema_bound` | BOOLEAN | Schema-bound flag | false |
| `create_date` | TIMESTAMP | Creation date | 2024-01-01 10:30:00 |
| `modify_date` | TIMESTAMP | Last modification date | 2024-02-15 14:22:00 |

**Sample Row:**
```sql
object_id: 2001
object_name: spLoadDimCustomers
schema_name: CONSUMPTION_FINANCE
object_type: SQL_STORED_PROCEDURE
definition: "CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadDimCustomers]
             AS
             BEGIN
               INSERT INTO DimCustomers
               SELECT * FROM STAGING_CADENCE.RawCustomers
             END"
uses_ansi_nulls: true
uses_quoted_identifier: true
is_schema_bound: false
create_date: 2024-01-01 10:30:00
modify_date: 2024-02-15 14:22:00
```

**Typical Row Count:** 500 - 50,000 objects (only objects with DDL)

**Important Notes:**
- `definition` column can be **very large** (up to 4MB for complex stored procedures)
- Used for SQLGlot parsing when DMV dependencies are missing
- Not all objects have definitions (tables don't have DDL in sys.sql_modules)

---

### 4. `query_logs` Table

**Source:** `query_logs.parquet`
**Purpose:** Runtime execution logs for validation and discovery (confidence 0.9)
**Primary Key:** `request_id`
**Optional:** This table may not exist if query logs were skipped

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `request_id` | TEXT | Unique request identifier | "QID123456" |
| `session_id` | TEXT | Session identifier | "SID789" |
| `submit_time` | TIMESTAMP | When query was submitted | 2024-02-15 10:30:00 |
| `start_time` | TIMESTAMP | When query started executing | 2024-02-15 10:30:01 |
| `end_time` | TIMESTAMP | When query completed | 2024-02-15 10:30:05 |
| `status` | TEXT | Query status | "Completed", "Failed" |
| `command` | TEXT | SQL command type | "INSERT...SELECT", "UPDATE" |
| `total_elapsed_time` | INTEGER | Elapsed time in milliseconds | 4000 |
| `label` | TEXT | Query label (optional) | "ETL_Load" |
| `command_text` | TEXT | First 4000 chars of SQL | "INSERT INTO FactSales..." |

**Sample Row:**
```sql
request_id: QID123456
session_id: SID789
submit_time: 2024-02-15 10:30:00
start_time: 2024-02-15 10:30:01
end_time: 2024-02-15 10:30:05
status: Completed
command: INSERT...SELECT
total_elapsed_time: 4000
label: ETL_Load
command_text: "INSERT INTO FactSales SELECT * FROM STAGING_CADENCE.SalesData"
```

**Important Limitations:**
- DMV retains only ~10,000 most recent queries
- Query text truncated to 4000 characters
- Only includes queries from last 7 days (extractor default)
- **This table is OPTIONAL** - parser works without it

**Typical Row Count:** 0 - 10,000 queries (or 0 if skipped)

---

### 5. `table_columns` Table

**Source:** `table_columns.parquet`
**Purpose:** Table column metadata for generating CREATE TABLE DDL statements
**Primary Key:** None (composite: schema_name + table_name + column_id)
**Optional:** This table may not exist if table column metadata was skipped

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `schema_name` | TEXT | Schema name | "CONSUMPTION_PRIMA" |
| `table_name` | TEXT | Table name | "FeasibilityContacts" |
| `column_name` | TEXT | Column name | "RECORD_ID" |
| `column_id` | INTEGER | Column ordinal position | 1 |
| `data_type` | TEXT | SQL Server data type | "int", "varchar", "datetime" |
| `max_length` | INTEGER | Maximum length for char/varchar types | 255, -1 (MAX) |
| `precision` | INTEGER | Precision for numeric types | 18 |
| `scale` | INTEGER | Scale for numeric types | 2 |
| `is_nullable` | BOOLEAN | NULL allowed | true, false |
| `correct_object_id` | INTEGER | Resolved object_id from objects table | 1275862257 |

**Sample Row:**
```sql
schema_name: CONSUMPTION_PRIMA
table_name: FeasibilityContacts
column_name: RECORD_ID
column_id: 1
data_type: int
max_length: NULL
precision: 10
scale: 0
is_nullable: true
correct_object_id: 1275862257
```

**Important Notes:**
- Used to generate CREATE TABLE statements for full-text search
- `correct_object_id` is auto-populated by joining with `objects` table
- Handles object_id changes between extractions
- **This table is OPTIONAL** - unified_ddl view works without it (fallback DDL)

**Typical Row Count:** 0 - 500,000 columns (10-50 columns per table)

---

## Views (Generated, Managed by Parser)

These views are automatically created by the parser to provide unified access to DDL.

### 6. `unified_ddl` View

**Purpose:** Union of real DDL (SPs/Views) + generated CREATE TABLE statements
**Managed By:** `DuckDBWorkspace.create_unified_ddl_view()`
**Used For:** Full-text search, DDL retrieval

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `object_id` | INTEGER | Object identifier | 1275862257 |
| `schema_name` | TEXT | Schema name | "CONSUMPTION_PRIMA" |
| `object_name` | TEXT | Object name | "FeasibilityContacts" |
| `object_type` | TEXT | Object type | "Table", "Stored Procedure", "View" |
| `ddl_text` | TEXT | DDL statement (real or generated) | "CREATE TABLE..." |

**View Definition:**
```sql
CREATE OR REPLACE VIEW unified_ddl AS
-- Part 1: Real DDL from definitions (Stored Procedures & Views)
SELECT object_id, schema_name, object_name, object_type, definition as ddl_text
FROM definitions d JOIN objects o ON d.object_id = o.object_id
WHERE o.object_type IN ('Stored Procedure', 'View')

UNION ALL

-- Part 2: Generated CREATE TABLE DDL from table_columns (if available)
SELECT correct_object_id, schema_name, table_name, 'Table',
       'CREATE TABLE [schema].[table] (' || column_definitions || ');'
FROM table_columns WHERE correct_object_id IS NOT NULL
GROUP BY correct_object_id, schema_name, table_name

UNION ALL

-- Part 3: Fallback CREATE TABLE for tables without column metadata
SELECT object_id, schema_name, object_name, 'Table',
       'CREATE TABLE [schema].[table] (/* Column info not available */);'
FROM objects WHERE object_type = 'Table'
AND NOT EXISTS (SELECT 1 FROM table_columns WHERE correct_object_id = object_id)
```

**Sample Row:**
```sql
object_id: 1275862257
schema_name: CONSUMPTION_PRIMA
object_name: FeasibilityContacts
object_type: Table
ddl_text: "CREATE TABLE [CONSUMPTION_PRIMA].[FeasibilityContacts] (
    [RECORD_ID] int NULL,
    [CONTACT_DATE] datetime NULL,
    [CONTACT_ORIGINATOR] int NULL,
    ...
);"
```

**Typical Row Count:** Same as total objects (tables + SPs + views)

---

## Search Tables (Managed by Parser)

These tables are automatically created and maintained for full-text search functionality.

### 7. `unified_ddl_materialized` Table

**Purpose:** Materialized copy of unified_ddl view for full-text search indexing
**Managed By:** `DuckDBWorkspace.create_fts_index()`
**Used For:** Full-text search via BM25 ranking

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `object_id` | INTEGER | Object identifier | 1275862257 |
| `schema_name` | TEXT | Schema name | "CONSUMPTION_PRIMA" |
| `object_name` | TEXT | Object name | "FeasibilityContacts" |
| `object_type` | TEXT | Object type | "Table" |
| `ddl_text` | TEXT | DDL statement (real or generated) | "CREATE TABLE..." |

**Full-Text Search Index:**
- **Index Name:** `fts_main_unified_ddl_materialized`
- **Indexed Columns:** `object_name`, `ddl_text`
- **Key Column:** `object_id`
- **Features:** BM25 ranking, stemming, phrase search, wildcards, boolean operators

**Creation:**
```sql
-- Step 1: Materialize the view (FTS can't index views)
CREATE OR REPLACE TABLE unified_ddl_materialized AS
SELECT * FROM unified_ddl;

-- Step 2: Create FTS index
PRAGMA create_fts_index(
    'unified_ddl_materialized',
    'object_id',
    'object_name',
    'ddl_text',
    overwrite=1
);
```

**Search Query Example:**
```sql
SELECT
    object_id::TEXT as id,
    object_name as name,
    object_type as type,
    schema_name as schema,
    fts_main_unified_ddl_materialized.match_bm25(object_id, 'FeasibilityContacts') as score,
    substr(ddl_text, 1, 150) as snippet
FROM unified_ddl_materialized
WHERE fts_main_unified_ddl_materialized.match_bm25(object_id, 'FeasibilityContacts') IS NOT NULL
ORDER BY score DESC
LIMIT 100;
```

**Sample Row:**
```sql
object_id: 1275862257
schema_name: CONSUMPTION_PRIMA
object_name: FeasibilityContacts
object_type: Table
ddl_text: "CREATE TABLE [CONSUMPTION_PRIMA].[FeasibilityContacts] (
    [RECORD_ID] int NULL,
    [CONTACT_DATE] datetime NULL,
    ...
);"
```

**Important Notes:**
- Rebuilt whenever Parquet files are uploaded
- Includes ALL object types: Tables, Stored Procedures, Views
- Tables show generated CREATE TABLE statements (not available in definitions table)
- Used by `/api/search-ddl` endpoint

**Typical Row Count:** Same as total objects (tables + SPs + views)

---

## Metadata Tables (Persistent, Managed by Parser)

These tables are created and managed by the lineage parser to track progress and results.

### 8. `lineage_metadata` Table

**Purpose:** Incremental load tracking - stores last parsed state for each object
**Primary Key:** `object_id`
**Managed By:** `DuckDBWorkspace.update_metadata()`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `object_id` | INTEGER | Object identifier (FK to objects.object_id) | 1001 |
| `last_parsed_modify_date` | TIMESTAMP | modify_date when object was last parsed | 2024-02-15 14:22:00 |
| `last_parsed_at` | TIMESTAMP | When parser last analyzed this object | 2024-02-20 09:15:00 |
| `primary_source` | TEXT | Source with highest confidence | "dmv", "query_log", "parser" |
| `confidence` | REAL | Confidence score (0.0-1.0) | 1.0 |
| `inputs` | TEXT | JSON array of input object_ids | "[1002, 1003]" |
| `outputs` | TEXT | JSON array of output object_ids | "[2001]" |

**Schema Definition:**
```sql
CREATE TABLE IF NOT EXISTS lineage_metadata (
    object_id INTEGER PRIMARY KEY,
    last_parsed_modify_date TIMESTAMP,
    last_parsed_at TIMESTAMP,
    primary_source TEXT,
    confidence REAL,
    inputs TEXT,   -- JSON array of integer object_ids
    outputs TEXT   -- JSON array of integer object_ids
)
```

**Sample Row:**
```sql
object_id: 1001
last_parsed_modify_date: 2024-02-15 14:22:00
last_parsed_at: 2024-02-20 09:15:00
primary_source: dmv
confidence: 1.0
inputs: "[1002, 1003]"
outputs: "[2001, 2002]"
```

**Interpretation:**
- Object 1001 was last parsed on 2024-02-20
- It was last modified on 2024-02-15 (from objects.modify_date)
- Dependencies found via DMV (confidence 1.0)
- It reads from objects 1002 and 1003
- It writes to objects 2001 and 2002

**Usage in Incremental Load:**
```python
# Skip if:
objects.modify_date <= lineage_metadata.last_parsed_modify_date
AND lineage_metadata.confidence >= 0.85

# Re-parse if:
objects.modify_date > lineage_metadata.last_parsed_modify_date
OR lineage_metadata.confidence < 0.85
OR object_id NOT IN lineage_metadata
```

**Typical Row Count:** Same as parsed objects (grows over time)

---

### 9. `lineage_results` Table

**Purpose:** Final merged lineage graph (all sources combined)
**Primary Key:** `object_id`
**Status:** Future implementation (Phase 7)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `object_id` | INTEGER | Object identifier (FK to objects.object_id) | 1001 |
| `object_name` | TEXT | Object name (denormalized for performance) | "DimCustomers" |
| `schema_name` | TEXT | Schema name (denormalized) | "CONSUMPTION_FINANCE" |
| `object_type` | TEXT | Object type (denormalized) | "Table" |
| `inputs` | TEXT | JSON array of input object_ids | "[1002, 1003]" |
| `outputs` | TEXT | JSON array of output object_ids | "[2001, 2002]" |
| `primary_source` | TEXT | Source with highest confidence | "dmv" |
| `confidence` | REAL | Final confidence score (0.0-1.0) | 1.0 |
| `created_at` | TIMESTAMP | When lineage was first created | 2024-02-20 09:15:00 |
| `updated_at` | TIMESTAMP | Last update timestamp | 2024-02-20 09:15:00 |

**Schema Definition:**
```sql
CREATE TABLE IF NOT EXISTS lineage_results (
    object_id INTEGER PRIMARY KEY,
    object_name TEXT,
    schema_name TEXT,
    object_type TEXT,
    inputs TEXT,   -- JSON array of integer object_ids
    outputs TEXT,  -- JSON array of integer object_ids
    primary_source TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Sample Row:**
```sql
object_id: 2001
object_name: spLoadDimCustomers
schema_name: CONSUMPTION_FINANCE
object_type: Stored Procedure
inputs: "[1003, 3001]"          -- Reads from DimCustomers, StageTable
outputs: "[1001]"                -- Writes to FactSales
primary_source: dmv
confidence: 1.0
created_at: 2024-02-20 09:15:00
updated_at: 2024-02-20 09:15:00
```

**Typical Row Count:** Same as total objects analyzed

---

## Confidence Scoring Model

Each dependency source has a fixed confidence score:

| Source | Confidence | Table with Evidence |
|--------|-----------|---------------------|
| **DMV** | 1.0 | `dependencies` table |
| **Query Log** | 0.95 | `query_logs` table (validation) |
| **Parser (SQLGlot High)** | 0.85 | Parsed from `definitions` table (high agreement) |
| **Parser (SQLGlot Medium)** | 0.75 | Parsed from `definitions` table (partial agreement) |
| **Parser (SQLGlot Low)** | 0.50 | Parsed from `definitions` table (low agreement) |

**Merging Logic:**
When multiple sources confirm the same dependency, use `MAX(confidence)`.

---

## Data Flow Through Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Load Parquet Files                                     │
├─────────────────────────────────────────────────────────────────┤
│ objects.parquet      → objects table                            │
│ dependencies.parquet → dependencies table                       │
│ definitions.parquet  → definitions table                        │
│ query_logs.parquet   → query_logs table (optional)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Build Baseline (DMV)                                   │
├─────────────────────────────────────────────────────────────────┤
│ SELECT referencing_object_id, referenced_object_id              │
│ FROM dependencies                                               │
│ → Confidence: 1.0                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Enhance from Query Logs (Optional)                     │
├─────────────────────────────────────────────────────────────────┤
│ Parse command_text from query_logs                              │
│ Extract table references                                        │
│ → Confidence: 0.9                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Detect Gaps                                            │
├─────────────────────────────────────────────────────────────────┤
│ Find objects with no dependencies in lineage_metadata           │
│ → List of object_ids needing parsing                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Parse DDL (SQLGlot with Quality Scoring)               │
├─────────────────────────────────────────────────────────────────┤
│ For each gap: SELECT definition FROM definitions                │
│ Parse with SQLGlot AST + Regex baseline comparison              │
│ → Confidence: 0.85 (high) / 0.75 (medium) / 0.50 (low)         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Merge & Update Metadata                                │
├─────────────────────────────────────────────────────────────────┤
│ INSERT/UPDATE lineage_metadata                                  │
│ INSERT/UPDATE lineage_results                                   │
│ → Final confidence = MAX(all sources)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Generate JSON Output                                   │
├─────────────────────────────────────────────────────────────────┤
│ SELECT * FROM lineage_results                                   │
│ → lineage.json (internal format)                                │
│ → frontend_lineage.json (string node IDs)                       │
│ → lineage_summary.json (statistics)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Common Queries

### Get all dependencies for an object
```sql
SELECT
    d.referencing_object_id,
    d.referenced_object_id,
    o1.schema_name || '.' || o1.object_name AS referencing_object,
    o2.schema_name || '.' || o2.object_name AS referenced_object
FROM dependencies d
JOIN objects o1 ON d.referencing_object_id = o1.object_id
JOIN objects o2 ON d.referenced_object_id = o2.object_id
WHERE d.referencing_object_id = 2001;
```

### Get objects needing parse (incremental logic)
```sql
SELECT
    o.object_id,
    o.schema_name,
    o.object_name,
    o.object_type,
    o.modify_date
FROM objects o
LEFT JOIN lineage_metadata m ON o.object_id = m.object_id
WHERE
    m.object_id IS NULL  -- Never parsed
    OR o.modify_date > m.last_parsed_modify_date  -- Modified since last parse
    OR m.confidence < 0.85  -- Low confidence
ORDER BY o.schema_name, o.object_name;
```

### Get lineage coverage statistics
```sql
SELECT
    primary_source,
    COUNT(*) as object_count,
    AVG(confidence) as avg_confidence
FROM lineage_metadata
GROUP BY primary_source;
```

### Find objects with no dependencies (gaps)
```sql
SELECT
    o.object_id,
    o.schema_name || '.' || o.object_name AS full_name,
    o.object_type
FROM objects o
LEFT JOIN dependencies d ON o.object_id = d.referencing_object_id
WHERE d.referencing_object_id IS NULL
  AND o.object_type = 'Stored Procedure';
```

---

## Storage & Performance

### File Size Estimates

| Table/View | Row Count | Est. Size |
|-------|-----------|-----------|
| `objects` | 10,000 | ~2 MB |
| `dependencies` | 50,000 | ~10 MB |
| `definitions` | 5,000 | ~50 MB (large DDL text) |
| `query_logs` | 10,000 | ~20 MB |
| `table_columns` | 100,000 | ~5 MB |
| `unified_ddl_materialized` | 10,000 | ~55 MB (includes generated DDL) |
| `lineage_metadata` | 10,000 | ~2 MB |
| `lineage_results` | 10,000 | ~2 MB |
| **Total** | | **~146 MB** |

**Actual workspace file size:** ~150-200 MB (includes DuckDB metadata + FTS index)

### Performance Characteristics

- **Parquet Load:** ~5 seconds for 10,000 objects
- **Incremental Query:** <1 second (indexed on object_id)
- **Name Resolution:** <100ms for 1,000 table names (batch query)
- **Metadata Update:** <10ms per object
- **FTS Index Creation:** ~1-2 seconds for 10,000 objects
- **Full-Text Search:** <100ms for typical queries (BM25 ranking)

---

## Schema Versioning

**Current Version:** 3.1.0

**Schema Changes:**
- v3.1.0 (2025-11-02): Added full-text search with unified_ddl_materialized table
- v3.0.0 (2025-10-26): Initial schema with incremental load support

**Future Changes:**
- Add indexes on frequently queried columns
- Add computed columns for common joins

---

## See Also

- [lineage_specs.md](../lineage_specs.md) - Full specification
- [lineage_v3/core/README.md](../lineage_v3/core/README.md) - Core engine documentation
- [lineage_v3/core/duckdb_workspace.py](../lineage_v3/core/duckdb_workspace.py) - Implementation
