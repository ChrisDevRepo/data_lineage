# Technical Reference

Technical specifications, architecture, and schema documentation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  React + React Flow + Monaco Editor                         │
│  - Graph visualization with D3 layout                        │
│  - Interactive filtering and search                          │
│  - DDL viewer with syntax highlighting                       │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/JSON
┌────────────────▼────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  - Serves frontend_lineage.json                             │
│  - On-demand DDL fetching from DuckDB                       │
│  - Parquet file upload processing                           │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    Parser (v4.2.0)                           │
│  Regex → SQLGlot → Rule Engine → Confidence                 │
│  - Extracts table dependencies from SQL                      │
│  - Calculates confidence scores                             │
│  - Detects parse failures and reasons                       │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    DuckDB Workspace                          │
│  - Persistent storage for parsed lineage                    │
│  - Incremental parsing support                              │
│  - Full-text search indexes                                 │
└─────────────────────────────────────────────────────────────┘
```

## Parser Specification (v4.2.0)

### Parsing Strategy

**Phase 1: Regex Baseline**
- Extract table names from SELECT/INSERT/UPDATE/DELETE
- Pattern matching for common SQL structures
- Fast but can miss complex cases

**Phase 2: SQLGlot AST**
- Parse SQL into Abstract Syntax Tree
- Walk AST to find table references
- Handles complex queries (CTEs, subqueries)

**Phase 3: Rule Engine**
- Apply SQL cleaning rules (temp tables, variables)
- Resolve schema qualifications
- Validate against object catalog

**Phase 4: Confidence Calculation**
- Compare found tables vs expected (smoke test)
- Assign discrete confidence score (0, 75, 85, 100)
- Generate actionable guidance

### Performance

- **Accuracy:** 95.5% overall (729/763 objects)
- **Stored Procedures:** 97.0% (196/202 SPs)
- **Speed:** ~350 SPs in <30 seconds
- **Incremental mode:** 50-90% faster

### Confidence Model (v2.1.0)

**Formula:**
```python
completeness = (found_tables / expected_tables) * 100

if completeness >= 90:   confidence = 100
elif completeness >= 70: confidence = 85
elif completeness >= 50: confidence = 75
else:                    confidence = 0
```

**Special cases:**
- Orchestrators (expected=0) → 100%
- Parse failures → 0%

**Fields:**
- `confidence`: 0 | 75 | 85 | 100
- `parse_failure_reason`: Error description (if failed)
- `expected_count`: Expected table count from smoke test
- `found_count`: Actual tables found by parser

## DuckDB Schema

### Core Tables

**objects**
```sql
CREATE TABLE objects (
    object_id BIGINT PRIMARY KEY,
    schema_name VARCHAR,
    object_name VARCHAR,
    object_type VARCHAR  -- 'Table', 'View', 'Stored Procedure'
);
```

**dependencies**
```sql
CREATE TABLE dependencies (
    referencing_id BIGINT,
    referenced_schema VARCHAR,
    referenced_name VARCHAR,
    dependency_type VARCHAR  -- 'SELECT', 'INSERT', 'UPDATE', etc.
);
```

**definitions**
```sql
CREATE TABLE definitions (
    object_id BIGINT,
    definition TEXT,  -- DDL text
    schema_name VARCHAR,
    object_name VARCHAR
);
```

**lineage_metadata**
```sql
CREATE TABLE lineage_metadata (
    object_id BIGINT PRIMARY KEY,
    confidence REAL,
    primary_source VARCHAR,
    parse_failure_reason VARCHAR,      -- v4.2.0
    expected_count INTEGER,            -- v4.2.0
    found_count INTEGER,               -- v4.2.0
    last_updated TIMESTAMP
);
```

### Optional Tables

**table_columns** (for table DDL generation)
```sql
CREATE TABLE table_columns (
    schema_name VARCHAR,
    table_name VARCHAR,
    column_name VARCHAR,
    data_type VARCHAR,
    max_length INTEGER,
    precision INTEGER,
    scale INTEGER,
    is_nullable BOOLEAN
);
```

**query_logs** (runtime validation)
```sql
CREATE TABLE query_logs (
    object_name VARCHAR,
    referenced_objects VARCHAR,  -- JSON array
    execution_count INTEGER,
    last_executed TIMESTAMP
);
```

## API Endpoints

### GET /api/latest-data
Returns frontend_lineage.json for graph visualization.

**Response:**
```json
[{
  "id": "node_1",
  "name": "spLoadCustomers",
  "schema": "dbo",
  "object_type": "Stored Procedure",
  "description": "✅ Good quality (score 0.85)",
  "data_model_type": "Other",
  "inputs": ["node_2", "node_3"],
  "outputs": ["node_4"],
  "confidence": 0.85
}]
```

### GET /api/ddl/{object_id}
Fetch DDL for specific object (on-demand).

**Response:**
```json
{
  "object_id": "123",
  "ddl_text": "CREATE PROCEDURE..."
}
```

### POST /api/upload-parquet
Upload Parquet files for parsing.

**Request:** Multipart form with 3-5 Parquet files
**Response:**
```json
{
  "job_id": "abc123",
  "status": "processing"
}
```

### GET /api/job/{job_id}
Check parsing job status.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "stats": {
    "total_objects": 349,
    "high_confidence": 196,
    "medium_confidence": 138,
    "low_confidence": 15
  }
}
```

## Frontend Data Format

**frontend_lineage.json structure:**
```json
{
  "id": "unique_node_id",
  "name": "ObjectName",
  "schema": "SchemaName",
  "object_type": "Stored Procedure|Table|View",
  "description": "Confidence info + guidance",
  "data_model_type": "Dimension|Fact|Other",
  "inputs": ["id1", "id2"],
  "outputs": ["id3"],
  "confidence": 0.85,
  "confidence_breakdown": { /* v2.0.0 details */ }
}
```

See [CLAUDE.md](../CLAUDE.md) for current project status and quick reference.
