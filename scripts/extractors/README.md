# Database Metadata Extractors

This directory contains standalone Python scripts for extracting metadata from various database systems and exporting it to Parquet format for use with the Data Lineage Visualizer.

## Available Extractors

### Azure Synapse Analytics / SQL Server
**Script:** `synapse_dmv_extractor.py`

Extracts metadata using Dynamic Management Views (DMVs) from Azure Synapse, SQL Server, or Azure SQL Database.

**⚠️ IMPORTANT:** This script is provided as a **helper tool for Synapse administrators**. It is designed to be run **inside Azure Synapse** (e.g., via Synapse notebooks or Spark pools) where ODBC connectivity is already configured.

**The Data Lineage Visualizer application itself does NOT require ODBC or any database connectivity.** It only uses DuckDB internally for processing the exported Parquet files.

**Requirements (inside Synapse environment):**
```bash
pip install pyodbc pandas pyarrow python-dotenv
```

**Microsoft ODBC Driver 18 for SQL Server** (typically pre-installed in Synapse environments)

**Usage:**
```bash
# Using .env file (recommended)
python synapse_dmv_extractor.py --output output/

# Using command-line credentials
python synapse_dmv_extractor.py \
    --server yourserver.sql.azuresynapse.net \
    --database yourdatabase \
    --username youruser \
    --password yourpassword \
    --output output/
```

**Environment Variables (.env file):**
```env
SYNAPSE_SERVER=yourserver.sql.azuresynapse.net
SYNAPSE_DATABASE=yourdatabase
SYNAPSE_USERNAME=youruser
SYNAPSE_PASSWORD=yourpassword
```

## Output Files

All extractors generate Parquet files with the following **generic column names** (not database-specific):

### Required Files

1. **objects.parquet**
   - Required columns: `object_id`, `schema_name`, `object_name`, `object_type`
   - Contains all database objects (tables, views, stored procedures, functions)

2. **dependencies.parquet**
   - Required columns: `referencing_object_id`, `referenced_object_id`
   - Contains object dependencies (which objects reference which other objects)

3. **definitions.parquet**
   - Required columns: `object_id`, `definition`
   - Contains DDL text/source code for objects

### Optional Files

4. **table_columns.parquet**
   - Detected columns: `column_name`, `data_type`
   - Contains table/view column metadata

5. **query_logs.parquet**
   - Detected columns: `request_id` or `command`
   - Contains historical query execution logs

## Column Name Specification

The Data Lineage Visualizer validates files by **inspecting column names inside the Parquet files**, not by filename. This means:

- ✅ **Any filename works** - You can use `spark_export_001.parquet`, `objects_20250112.parquet`, etc.
- ✅ **Database-agnostic** - Works with Synapse, PostgreSQL, Oracle, Snowflake, etc.
- ✅ **Case-insensitive** - Column names are matched case-insensitively
- ⚠️ **Column names must match** - The actual column names inside the Parquet file must match the specification above

## Future Extractors

Planned extractors for other databases:
- `postgres_extractor.py` - PostgreSQL metadata from information_schema
- `oracle_extractor.py` - Oracle metadata from DBA_* views
- `snowflake_extractor.py` - Snowflake metadata using INFORMATION_SCHEMA
- `redshift_extractor.py` - Amazon Redshift metadata

## Contributing

To add a new extractor:

1. Create a Python script following the naming pattern `{database}_extractor.py`
2. Use the generic column names specified above
3. Export to Parquet format using pandas/pyarrow
4. Include usage documentation in comments
5. Add entry to this README

## Support

For issues or questions:
- Check the main documentation in `/docs/`
- See `/docs/SETUP.md` for installation help
- See `/docs/USAGE.md` for troubleshooting
