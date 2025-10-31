# Vibecoding — Data Lineage Parser Specification

**Specification Version:** 2.1
**Parser Version:** 2.0
**Date:** 2025-10-26
**Status:** Updated with frontend compatibility, incremental load support, and Microsoft Agent Framework integration

**Note:** This specification (v2.1) describes the Vibecoding Lineage Parser v2.0. The folder name `lineage_v3` refers to the third iteration of development, but the product version is v2.0.

## 1. Objective

To extract table-level data lineage from **Azure Synapse Dedicated SQL Pool** metadata. The system consumes offline Parquet snapshots and produces JSON-based node/edge lists representing object dependencies.

**Core Principles:**

* **Offline Operation:** The parser *must not* connect to Synapse. It consumes pre-exported Parquet snapshots.

* **DMV-First Model:** Synapse metadata (`sys.sql_expression_dependencies`) is the authoritative source. Query logs and parsing are used *only* to fill documented gaps.

* **JSON-Only Output:** All artifacts *must* be JSON, optimized for machine-to-machine consumption (e.g., by a frontend application).

* **Object-Level Only:** The system *must not* process or infer column-level lineage.

---

## 2. System Architecture

The system is a file-based batch processor. Its boundary is defined by Parquet files as input and JSON files as output.

```
[External] --> Helper Extractor --> (Input Interface)
                                        |
+---------------------------------------+
|         PARSER SYSTEM      |
|                                       |
|  1. Core Engine (DuckDB)              |
|     - Ingests Parquet snapshots       |
|     - Merges DMV & Log sources        |
|     - Detects unresolved gaps         |
|                                       |
|  2. Parser Extension (SQLGlot)        |
|     - Parses DDL for gap-filling      |
|                                       |
|  3. AI Fallback (Microsoft Agent      |
|     Framework)                        |
|     - Resolves remaining complex SPs  |
|                                       |
+---------------------------------------+
                |
                v
       (Output Interface) --> lineage.json, lineage_summary.json
                |
                v
       Frontend Adapter --> frontend_lineage.json
                |
                v --> [External] React Flow Frontend Consumer
```

---

## 3. Input Interface: Parquet Snapshots

The system *must* read the following Parquet files. The `Helper Extractor` component is responsible for their generation.

### 3.1. Required Files (3)

| File | Source DMV(s) | Purpose |
| :--- | :--- | :--- |
| `objects.parquet` | `sys.objects`, `sys.schemas` | Authoritative catalog of all objects (schema, name, type, **object_id**). |
| `dependencies.parquet` | `sys.sql_expression_dependencies` | The primary, high-confidence dependency links (using **object_id**). |
| `definitions.parquet` | `sys.sql_modules` | The DDL text (e.g., `CREATE PROC...`, `CREATE VIEW...`) for parsing stored procedures and views. |

### 3.2. Optional Files (2)

| File | Source DMV(s) | Purpose |
| :--- | :--- | :--- |
| `query_logs.parquet` | `sys.dm_pdw_exec_requests` | **OPTIONAL.** Runtime execution text for validation and discovery. *Note: DMV retains only ~10,000 recent queries - use sparingly.* |
| `table_columns.parquet` | `sys.tables`, `sys.columns`, `sys.types` | **OPTIONAL.** Table column metadata for DDL generation. Enables CREATE TABLE statement reconstruction for SQL Viewer feature. |

**Table Columns Schema:**

The `table_columns.parquet` file (if provided) must contain:
- `object_id` (int) - Links to objects.parquet
- `schema_name` (string)
- `table_name` (string)
- `column_name` (string)
- `data_type` (string) - SQL Server data type name
- `max_length` (int) - Maximum length for string types (-1 for MAX)
- `precision` (int) - Precision for numeric types
- `scale` (int) - Scale for numeric types
- `is_nullable` (bool)
- `column_id` (int) - Column ordinal position

**Incremental Load Support:**

The `objects.parquet` file includes `create_date` and `modify_date` timestamps. The parser *may* use `modify_date` to skip re-parsing objects that haven't changed since the last run (see Section 10).

---

## 4. Core Engine & Parser Design

### 4.1. Workspace: DuckDB

DuckDB is the required in-memory engine. It will be used to:

* Load all Parquet files into relational tables.
* Join `objects`, `dependencies`, and `query_logs` to create a baseline lineage set using `object_id`.
* Execute validation queries to identify objects (especially Stored Procedures) present in `definitions` or `query_logs` but missing from `dependencies`.

### 4.2. Parser: SQLGlot

SQLGlot is the required SQL parser. It is the optimal choice due to its robust T-SQL dialect support and full AST (Abstract Syntax Tree) access.

* **Usage:** SQLGlot will parse the DDL text from `definitions.parquet` for objects identified as gaps.
* **Logic:** The AST will be traversed to extract source (e.g., `FROM`, `JOIN`) and target (e.g., `INTO`, `UPDATE`) table references, which will be strings (e.g., `schema.table`).
* **Resolution:** These extracted string references *must* be resolved back to their integer `object_id` by joining against the `objects.parquet` data loaded in DuckDB.

---

## 5. Lineage Construction Logic
## 5. Lineage Construction Logic

The system must execute the following steps in order:

1.  **Ingest:** Load all `.parquet` snapshots into DuckDB tables.
2.  **Build Baseline (DMV):** Create the primary lineage set from `objects` and `dependencies` using `object_id`. Assign `provenance` as "dmv" and `confidence` as 1.0.
3.  **Detect Gaps:** Identify any Stored Procedures that have a `definition` but no resolved inputs or outputs.
4.  **Run Parser (Dual Parser):** For all Stored Procedures, parse DDL from `definitions.parquet`. Resolve extracted table names to `object_id`s. Assign `provenance` as "parser" or "dual_parser" and `confidence` as 0.85 (high-quality parse) or 0.50 (low-quality parse).
5.  **Query Log Validation (NEW - v3.4.0):** Cross-validate high-confidence parsed SPs (≥0.85) with runtime execution evidence.
    * Load DML queries from `query_logs.parquet` (INSERT/UPDATE/MERGE only).
    * For each high-confidence SP, match its parsed table dependencies against query log entries.
    * If matching queries found: Boost confidence from 0.85 → 0.95.
    * Assign `validation_source` as "query_log" in provenance.
    * **Note:** This is validation only - no new lineage objects created.
6.  **Run AI Fallback:** For any low-confidence SPs (confidence < 0.85), invoke the AI Fallback Framework. Assign `provenance` as "ai" and `confidence` as 0.7. **(DEFERRED - Phase 5)**
7.  **Bidirectional Graph (Reverse Lookup):** Populate reverse dependencies for Tables/Views.
    * For each SP/View that reads from a Table → Add SP/View to Table's `outputs`.
    * For each SP that writes to a Table → Add SP to Table's `inputs`.
    * This ensures React Flow can render edges in both directions.
8.  **Emit Artifacts:** Generate the final `lineage.json`, `frontend_lineage.json`, and `lineage_summary.json` files.
    * This ensures React Flow can render edges in both directions.
8.  **Emit Artifacts:** Generate the final `lineage.json`, `frontend_lineage.json`, and `lineage_summary.json` files.

---

## 6. AI Fallback Framework (Microsoft Agent Framework)

This subsystem is invoked *only* for Stored Procedures that remain unresolved after Step 5.

**Implementation:** Uses [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (python-1.0.0b251016 or later) for multi-agent orchestration.

### 6.1. Installation

```bash
pip install agent-framework --pre
```

### 6.2. Agent Architecture

* **Trigger:** Unresolved SP DDL from `definitions.parquet`.
* **Framework:** Multi-agent workflow using Microsoft Agent Framework graph-based orchestration
* **Agents:** The system must implement three specialized agents:
    1.  **ParserAgent:** Extracts potential table dependencies (as strings) from the raw SQL text using Azure AI Foundry LLM.
    2.  **ValidatorAgent:** Cross-references the extracted tables against `objects.parquet` data loaded in DuckDB to find their `object_id` and ensure they are valid.
    3.  **ResolverAgent:** Consolidates valid results from both agents and assigns a final confidence score based on validation success rate.

### 6.3. Agent Workflow

```
[Unresolved SP DDL] → ParserAgent → [Extracted Tables]
                                          ↓
                         ValidatorAgent (DuckDB Query)
                                          ↓
                         ResolverAgent → [object_ids + confidence]
```

### 6.4. Output Contract

The AI output *must* adhere to this JSON structure:

```json
{ "source": "ai", "inputs": [23456], "outputs": [45678], "confidence": 0.7 }
```

**Confidence Calculation:**
- If all extracted tables are validated: `confidence = 0.7`
- If partial validation (50-99%): `confidence = 0.5`
- If low validation (<50%): `confidence = 0.3`

---

## 7. Output Artifacts & JSON Schemas

The system must produce two distinct JSON files in an `/output/` directory.

### 7.1. Artifacts

| File | Purpose | Format |
| :--- | :--- | :--- |
| `lineage.json` | **Primary Output.** Full lineage node array for machine consumption (frontend). | JSON |
| `lineage_summary.json` | **Secondary Output.** Aggregate counts and coverage stats for the frontend. | JSON |

### 7.2. Summary JSON Schema

The `lineage_summary.json` file *must* be a single JSON object adhering to the following schema.

```json
{
  "total_objects": 2500,
  "coverage_percent": 0.95,
  "unresolved_objects": 125,
  "confidence_counts": {
    "dmv": 1800,
    "query_log": 300,
    "parser": 200,
    "ai": 75
  },
  "object_type_counts": {
    "Table": 1500,
    "View": 850,
    "Stored Procedure": 150
  }
}
```

### 7.3. Lineage JSON Schema

The `lineage.json` file *must* be a JSON array where each object (node) adheres to the following schema.

```json
{
  "id": 1001,
  "name": "object_name",
  "schema": "schema",
  "object_type": "Table|View|Stored Procedure",
  "inputs": [2002, 2003],
  "outputs": [3004],
  "provenance": {
    "primary_source": "dmv|query_log|parser|ai",
    "confidence": 0.0-1.0
  }
}
```

**Schema Rules:**

* `id` *must* be the integer `object_id` from `sys.objects`.
* `inputs` *must* be an array of integer `object_id`s representing the sources (tables/views this object reads from).
* `outputs` *must* be an array of integer `object_id`s representing the targets (tables this object writes to - only applicable for Stored Procedures).
* `inputs` and `outputs` *must* be empty arrays (`[]`) if no dependencies exist, never `null`.
* `provenance.primary_source` *must* be the source with the highest confidence score.
* `provenance.confidence` *must* be a float between 0.0 and 1.0.

**Bidirectional Graph Model:**

For proper graph visualization, the lineage must form bidirectional relationships:

* **Stored Procedures:**
  - `inputs`: Tables/Views it reads from (FROM, JOIN clauses)
  - `outputs`: Tables it writes to (INSERT, UPDATE, MERGE, TRUNCATE)

* **Tables:**
  - `inputs`: Stored Procedures that write to this table
  - `outputs`: Stored Procedures/Views that read from this table (**populated by reverse lookup**)

* **Views:**
  - `inputs`: Tables/Views it reads from
  - `outputs`: Stored Procedures/Views that read from this view (**populated by reverse lookup**)

---

## 8. Confidence Model

Confidence scores are static and *must* be assigned based on the source of the lineage data.

| Source | Confidence | Description |
| :--- | :--- | :--- |
| DMV | **1.0** | Authoritative system metadata. |
| Query Log | **0.9** | Confirmed runtime execution. |
| Parser (SQLGlot) | **0.85** | High-confidence static analysis. |
| AI | **0.7** | Fallback estimation; advisory. |

**Merging Logic:** When merging sources (e.g., a DMV link validated by a Query Log), the `confidence` *must* be the highest value (1.0 in this case). The `provenance.primary_source` field should reflect the source with the highest confidence.

---

## 9. Constraints & Performance

### 9.1. Hard Constraints (Out of Scope)

The parser *must not* attempt to process the following:

* **Column-Level Lineage**
* **Dynamic SQL** (e.g., `EXEC(@sql)`)
* **User Defined Functions (UDFs)**
* **Triggers**
* **Serverless** SQL Pools

Additionally:
* The parser *must not* have network access to Synapse.
* AI-derived results are *advisory* and must be assigned a lower confidence than other methods.

### 9.2. Performance Targets

The system's effectiveness will be measured against these coverage targets.

| Object Type | Primary Source(s) | Target Confidence |
| :--- | :--- | :--- |
| Tables | DMV | 1.0 |
| Views | DMV + Logs | 1.0 |
| Stored Procedures | DMV + Parser + AI | 0.7 - 1.0 |

**Overall Target:** The system must achieve ≥90% table-level lineage coverage across datasets.

---

## 10. Frontend Compatibility Layer

The React Flow frontend requires string-based node IDs and additional metadata fields not present in the internal `lineage.json` format.

### 10.1. Frontend Output Format

A separate `frontend_lineage.json` file *must* be generated with the following schema:

```json
{
  "id": "1986106116",
  "name": "object_name",
  "schema": "schema",
  "object_type": "Table|View|Stored Procedure",
  "description": "Confidence: 0.85",
  "data_model_type": "Dimension|Fact|Other|Lookup",
  "inputs": ["46623209", "350624292"],
  "outputs": ["366624349"]
}
```

**Note:** IDs are string-cast database `object_id` values (e.g., `"1986106116"`), NOT sequential `"node_0"` format. This preserves traceability to `sys.objects.object_id`.

### 10.2. Transformation Rules

| Internal Field | Frontend Field | Transformation |
| :--- | :--- | :--- |
| `id` (integer) | `id` (string) | Cast `object_id` to string (e.g., `1986106116` → `"1986106116"`) |
| `provenance` | `description` | Format confidence: `"Confidence: 0.85"` or `"Confidence: 1.00"` |
| *(inferred)* | `data_model_type` | Classify based on name prefix:<br>• `Dim*` → `"Dimension"`<br>• `Fact*` → `"Fact"`<br>• `Lookup*` → `"Lookup"`<br>• Other → `"Other"` |
| `inputs` (int[]) | `inputs` (string[]) | Cast each object_id to string |
| `outputs` (int[]) | `outputs` (string[]) | Cast each object_id to string |

### 10.3. Validation

The frontend adapter *must* validate that:
- All node IDs are unique strings
- All references in `inputs`/`outputs` exist in the node list
- No duplicate node IDs after transformation
- `object_type` values match enum: `"Table"`, `"View"`, `"Stored Procedure"`

---

## 11. Incremental Load Support

To optimize performance on large datasets, the parser *should* support incremental parsing based on object modification timestamps.

### 11.1. Metadata Tracking

The DuckDB workspace *must* maintain a `lineage_metadata` table:

```sql
CREATE TABLE IF NOT EXISTS lineage_metadata (
    object_id INTEGER PRIMARY KEY,
    last_parsed_modify_date TIMESTAMP,
    last_parsed_at TIMESTAMP,
    primary_source TEXT,
    confidence REAL
);
```

### 11.2. Incremental Logic

**Before parsing an object:**

1. Check if `object_id` exists in `lineage_metadata`
2. Compare `modify_date` from `objects.parquet` with `last_parsed_modify_date`
3. If `modify_date <= last_parsed_modify_date` AND confidence >= 0.85:
   - **Skip parsing** (object hasn't changed)
   - Reuse existing lineage from metadata
4. Otherwise:
   - **Parse object** and update metadata

### 11.3. CLI Flags

The parser *must* support two modes:

```bash
# Incremental mode (default) - skips unchanged objects
python main.py run --parquet parquet_snapshots/

# Full refresh mode - re-parses all objects
python main.py run --parquet parquet_snapshots/ --full-refresh
```

**Use Cases:**
- **Incremental**: Daily/weekly updates where most objects haven't changed
- **Full Refresh**: Initial load, major schema migrations, or confidence score recalibration

---

## 12. Version History

| Version | Date | Changes |
| :--- | :--- | :--- |
| **2.1** | 2025-10-26 | • Added Microsoft Agent Framework integration<br>• Simplified provenance schema (removed `sources` array)<br>• Added bidirectional graph documentation<br>• Added frontend compatibility layer (Section 10)<br>• Added incremental load support (Section 11)<br>• Documented query log DMV limitations |
| **2.0** | 2025-10-24 | Initial specification with DuckDB, SQLGlot, and AI fallback |
