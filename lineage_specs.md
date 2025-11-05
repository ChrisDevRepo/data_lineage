# Data Lineage Parser Specification

**Version:** 3.1
**Parser Version:** v3.8.0 (Production)
**Last Updated:** 2025-11-02

## 1. Objective

Extract table-level lineage from **Azure Synapse Dedicated SQL Pool** metadata using offline Parquet snapshots.

**Core Principles:**
- **Offline Operation:** No direct Synapse connection - consumes pre-exported Parquet files
- **DMV-First:** System metadata (`sys.sql_expression_dependencies`) is authoritative
- **Object-Level Only:** No column-level lineage
- **File-Based:** Parquet input → JSON output

---

## 2. Input: Parquet Files

**File Detection:** Auto-detected by **schema** (column names), not filename. Any filename works.

### Required Files (3)

| Source DMVs | Expected Columns | Purpose |
|-------------|------------------|---------|
| `sys.objects`, `sys.schemas` | `object_id`, `schema_name`, `object_name`, `object_type`, `modify_date` | Object catalog |
| `sys.sql_expression_dependencies` | `referencing_object_id`, `referenced_object_id` | DMV dependencies (confidence: 1.0) |
| `sys.sql_modules` | `object_id`, `definition` | DDL text for parsing |

### Optional Files (2)

| Source DMVs | Expected Columns | Purpose |
|-------------|------------------|---------|
| `sys.dm_pdw_exec_requests` | Runtime query text | Validation/confidence boosting (0.85 → 0.95) |
| `sys.tables`, `sys.columns`, `sys.types` | Table column metadata | DDL generation for SQL Viewer |

---

## 3. Architecture

```
Parquet Files → DuckDB Workspace (persistent)
                      ↓
         DMV Dependencies (confidence: 1.0)
                      +
         SQLGlot Parser (confidence: 0.85/0.50)
                      +
         AI Fallback (confidence: 0.85-0.95)
                      ↓
         Query Log Validation (boost to 0.95)
                      ↓
         JSON Output (lineage.json, frontend_lineage.json)
```

**Components:**
1. **DuckDB Workspace** - Persistent database (`lineage_workspace.duckdb`)
2. **QualityAwareParser** - SQLGlot-based T-SQL parser with regex fallback
3. **AIDisambiguator** - Azure OpenAI (direct API, gpt-4.1-nano) for complex SPs
4. **QueryLogValidator** - Cross-validates parsed results with runtime execution

---

## 4. Parsing Logic

### Step 1: DMV Baseline (Confidence: 1.0)
Load `dependencies.parquet` → Create primary lineage from system metadata

### Step 2: SQLGlot Parsing + Selective Merge (Confidence: 0.85 or 0.50)
For stored procedures:
- Parse DDL using SQLGlot AST traversal
- Extract table references (FROM, JOIN, INSERT, UPDATE, MERGE, TRUNCATE)
- **NEW in v3.8.0:** Extract SP-to-SP dependencies via regex (EXEC statements)
  - SQLGlot treats `EXEC` as Command expressions (can't extract dependencies semantically)
  - Regex pattern: `\bEXEC(?:UTE)?\s+\[?(\w+)\]?\.\[?(\w+)\]?`
  - **Selective Merge Strategy:**
    - Tables/Views: Use SQLGlot only (accurate AST parsing)
    - Stored Procedures: Add from regex if missing (SQLGlot can't handle EXEC)
  - **Utility SP Filtering:** Exclude non-data-lineage SPs from tracking
    - **Logging SPs:** `LogMessage`, `LogError`, `LogInfo`, `LogWarning` (administrative only)
    - **Utility SPs:** `spLastRowCount` (queries system DMVs, no data flow)
    - **Why Filtered:** Would add ~682 noise edges to lineage graph
    - **Implementation:** Case-insensitive filter in `EXCLUDED_UTILITY_SPS` constant
    - **Example:** `EXEC LogMessage @msg` → Not tracked as dependency
- Resolve table/SP names to `object_id` via DuckDB lookup
- Assign confidence: 0.85 (successful parse) or 0.50 (regex fallback)

### Step 3: AI Fallback (Confidence: 0.85-0.95)
**Trigger:** Low confidence (<0.85) or failed SQLGlot parse

**Implementation:**
- Direct Azure OpenAI API call (no agent framework)
- Model: `gpt-4.1-nano` (Azure AI Foundry)
- Few-shot prompt with production examples
- 3-layer validation:
  1. Catalog validation (extracted tables exist in `objects.parquet`)
  2. Schema consistency (tables belong to expected schemas)
  3. Query log validation (tables appear in runtime queries)

**Output:** Returns `object_id` arrays with confidence score (0.85-0.95)

### Step 4: Query Log Validation (Boost: 0.85 → 0.95)
Cross-validate high-confidence parses (≥0.85) with runtime query logs:
- Match parsed table dependencies against actual DML execution
- If confirmed: Boost confidence from 0.85 → 0.95

### Step 5: Bidirectional Graph
Populate reverse dependencies:
- SP reads Table → Add SP to Table's `outputs`
- SP writes Table → Add SP to Table's `inputs`

---

## 5. Incremental Mode

**Default:** Incremental mode (re-parse only modified/new objects)

**Trigger Conditions:**
1. Object modified (`modify_date` changed)
2. Never parsed before (new object)
3. Low confidence (<0.85, needs improvement)

**CLI:**
```bash
# Incremental (default)
python lineage_v3/main.py run --parquet parquet_snapshots/

# Full refresh
python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

**API:**
```bash
# Incremental
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" -F "files=@..."

# Full refresh
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=false" -F "files=@..."
```

---

## 6. Output Artifacts

### lineage.json (Internal Format)
Integer `object_id` for processing:
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

### frontend_lineage.json (Frontend Format)
String IDs for React Flow:
```json
{
  "id": "1986106116",
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "description": "Confidence: 1.00",
  "data_model_type": "Dimension",
  "inputs": ["46623209"],
  "outputs": ["350624292"]
}
```

**Note:** `ddl_text` field is **conditionally included**:
- CLI output: Embedded in `frontend_lineage.json` (default)
- API output: Fetched on-demand via `/api/ddl/{object_id}` for scalability

---

## 7. Confidence Model

| Source | Confidence | Applied To |
|--------|-----------|------------|
| DMV | 1.0 | Views, Functions |
| Query Log | 0.95 | Validated SPs |
| AI (Validated) | 0.85-0.95 | Complex SPs (3-layer validation) |
| SQLGlot Parser | 0.85 | Successfully parsed SPs |
| Regex Fallback | 0.50 | Failed SQLGlot parses |

---

## 8. Out of Scope

- Column-level lineage
- Dynamic SQL (`EXEC(@sql)`)
- User-Defined Functions
- Triggers
- Serverless SQL Pools
- Temp tables (#temp)
- **Utility/Logging SPs:** Intentionally excluded from lineage (see Step 2)
  - `LogMessage`, `LogError`, `LogInfo`, `LogWarning`
  - `spLastRowCount`
  - Custom utility SPs can be added to `EXCLUDED_UTILITY_SPS`

---