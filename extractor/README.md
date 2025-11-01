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


## Reference

See [docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md) - Section 4 (Feature 1: PySpark DMV Extractor)

---

**Last Updated:** 2025-10-27
**Status:** ✅ Production Ready - Week 1 Complete
