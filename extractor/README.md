# PySpark DMV Extractor

**Status:** ✅ **Week 1 Complete** - Ready for deployment

## Overview

Standalone Python script for extracting DMV metadata from Azure Synapse Dedicated SQL Pool.

**Replaces:** `lineage_v3/extractor/synapse_dmv_extractor.py` (Python + ODBC)

**New Approach:**
- Uses `shared_utils.process_spark_base` wheel (no JDBC/ODBC)
- Runs as Synapse Spark Job (not notebook)
- Directory output with single partition per table (DuckDB compatible)

## Files

- `synapse_pyspark_dmv_extractor.py` - Standalone Python script for Spark Job

## Configuration

Edit the configuration section in the script:

```python
SERVER = "your-synapse-workspace.sql.azuresynapse.net"
DATABASE = "YourDatabase"
TEMP_FOLDER = "abfss://lineage@yourstorage.dfs.core.windows.net/temp"
OUTPUT_PATH = "abfss://lineage@yourstorage.dfs.core.windows.net/parquet_snapshots/"
SKIP_QUERY_LOGS = False  # Set True if no VIEW SERVER STATE permission
```

**Schemas Extracted (Hardcoded):**
- CONSUMPTION_FINANCE
- CONSUMPTION_POWERBI
- CONSUMPTION_PRIMA
- STAGING_FINANCE_COGNOS
- STAGING_FINANCE_FILE
- ADMIN
- dbo

## Deployment

### Prerequisites
1. Azure Synapse Workspace with Spark pool
2. `shared_utils.process_spark_base` wheel installed on Spark pool
3. ADLS Gen2 storage account with write permissions

### Steps

**1. Upload script to Synapse:**
```bash
# Via Azure Portal:
Synapse Studio → Develop → Spark job definitions → Upload Python file
```

**2. Create Spark Job Definition:**
- Name: `DMV_Extractor`
- Main definition file: `synapse_pyspark_dmv_extractor.py`
- Spark pool: (Select your pool)
- Executors: 2 (default)
- Executor size: Small (4 vCPU, 28 GB memory)

**3. Run the job:**
- Click "Submit" in Synapse Studio
- Monitor progress in "Monitor" → "Spark applications"
- Expected runtime: 2-5 minutes

## Output Files

All files saved to `OUTPUT_PATH` as **directories** (Spark native format):

| Directory | Content | Typical Size | Notes |
|-----------|---------|--------------|-------|
| `objects.parquet/` | Tables, Views, Stored Procedures | ~100-500 rows | Full metadata |
| `dependencies.parquet/` | DMV relationships (Views only) | ~50-200 rows | From sys.sql_expression_dependencies |
| `definitions.parquet/` | DDL text | ~100-500 rows | Stored procedures + views source code |
| `query_logs.parquet/` | Query execution history (optional) | ~285 rows | ✨ **Optimized**: DISTINCT DML only (97% reduction) |

**Directory Structure:**
```
OUTPUT_PATH/
├── objects.parquet/
│   ├── _SUCCESS
│   └── part-00000-abc123.snappy.parquet  ← Single partition
├── dependencies.parquet/
│   ├── _SUCCESS
│   └── part-00000-def456.snappy.parquet
├── definitions.parquet/
│   ├── _SUCCESS
│   └── part-00000-ghi789.snappy.parquet
└── query_logs.parquet/
    ├── _SUCCESS
    └── part-00000-jkl012.snappy.parquet
```

**Notes:**
- Each directory contains a single `part-*.parquet` file (via `.coalesce(1)`)
- DuckDB reads these directories natively (no conversion needed)
- `dependencies.parquet` captures View dependencies only (SPs parsed from DDL)

### Query Logs Optimization (Week 2-3)

The `query_logs.parquet` extract is heavily optimized for data lineage:

**SQL Query:**
```sql
SELECT DISTINCT
    SUBSTRING(r.command, 1, 4000) AS command_text
FROM sys.dm_pdw_exec_requests r
WHERE r.submit_time >= DATEADD(day, -21, GETDATE())  -- Last 3 weeks
    AND r.status = 'Completed'
    AND (
        r.command LIKE 'SELECT %'    -- Read dependencies
        OR r.command LIKE 'INSERT %' -- Write dependencies
        OR r.command LIKE 'UPDATE %' -- Read + Write
        OR r.command LIKE 'MERGE %'  -- Upsert operations
    )
```

**Optimization Results:**
- **Before:** 9,991 rows with 93% duplicates, all operations
- **After:** ~285 rows (97.1% reduction), only DML operations
- **File size:** 170KB → ~5KB
- **Only 1 column:** `command_text` (removed request_id, session_id, submit_time)

**What's Included:**
- ✅ SELECT - Shows table read dependencies
- ✅ INSERT - Shows table write dependencies
- ✅ UPDATE - Shows read + write dependencies
- ✅ MERGE - Shows upsert dependencies

**What's Excluded (not useful for lineage):**
- ❌ DELETE, TRUNCATE - No data flow information
- ❌ SET, DECLARE, BEGIN, COMMIT - Session management
- ❌ EXEC sp_executesql - Dynamic SQL wrappers
- ❌ CREATE/DROP EXTERNAL TABLE - Spark connector internals

## Usage Workflow

```
1. Run PySpark Extractor in Synapse Studio
   ↓
2. Download Parquet files from ADLS to local machine
   ↓
3. Upload Parquet files to v3.0 web application
   ↓
4. Web app processes lineage in background
   ↓
5. View interactive lineage graph + SQL definitions
```

## Troubleshooting

**Error: "shared_utils.process_spark_base not found"**
- Ensure wheel is installed on Spark pool
- Check Spark pool configuration → Packages

**Error: "Permission denied on OUTPUT_PATH"**
- Verify ADLS Gen2 path is correct
- Check Spark pool managed identity has Storage Blob Data Contributor role

**Error: "Cannot connect to SERVER"**
- Verify Synapse SQL pool endpoint is correct
- Check Spark pool can access SQL pool (firewall rules)

**Query logs failed but continuing:**
- This is expected if no VIEW SERVER STATE permission
- Set `SKIP_QUERY_LOGS = True` to suppress warning

## Technical Details

**Spark Operations:**
- `utils.read_dwh(query)` → Returns Spark DataFrame
- `df.coalesce(1)` → Reduces to single partition
- `.write.parquet(path)` → Creates directory with single part file
  - Example: `objects.parquet/part-00000-{uuid}.snappy.parquet`

**Memory Usage:**
- DMV queries return small datasets (<1000 rows typically)
- Safe to use `coalesce(1)` without memory issues
- Executor size: Small (4 vCPU, 28 GB) is sufficient

## Reference

See [docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md) - Section 4 (Feature 1: PySpark DMV Extractor)

---

**Last Updated:** 2025-10-27
**Status:** ✅ Production Ready - Week 1 Complete
