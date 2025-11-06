# PySpark DMV Extractor

**Status:** ✅ Production Ready

Standalone PySpark script for extracting DMV metadata from Azure Synapse Dedicated SQL Pool.

## Files

- `synapse_pyspark_dmv_extractor.py` - Main extraction script

## Configuration

Edit configuration section in script:

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

**Prerequisites:**
1. Azure Synapse Workspace with Spark pool
2. `shared_utils.process_spark_base` wheel installed on Spark pool
3. ADLS Gen2 storage account with write permissions

**Steps:**
1. Upload `synapse_pyspark_dmv_extractor.py` to Synapse Studio
2. Create new Spark Job definition
3. Configure script file path and Spark pool
4. Run job
5. Download Parquet files from OUTPUT_PATH

## Usage Workflow

```
Synapse Studio → Run PySpark Extractor
     ↓
Download Parquet files from ADLS
     ↓
Upload to v3.0 web application
     ↓
View lineage graph + SQL definitions
```

## Troubleshooting

**"shared_utils.process_spark_base not found"**
- Install wheel on Spark pool (Packages tab)

**"Permission denied on OUTPUT_PATH"**
- Verify ADLS Gen2 path is correct
- Check Spark pool managed identity has Storage Blob Data Contributor role

**"Cannot connect to SERVER"**
- Verify SQL pool endpoint
- Check firewall rules allow Spark pool access

**Query logs failed but continuing:**
- Expected if no VIEW SERVER STATE permission
- Set `SKIP_QUERY_LOGS = True` to suppress warning

---

**Last Updated:** 2025-10-27
