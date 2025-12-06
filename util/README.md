# Universal SQL Metadata Extractor

A portable, standalone utility to export Microsoft SQL Server metadata to Parquet files for Data Lineage analysis.

## Purpose
This tool allows DBAs to extract necessary metadata (Tables, Views, Stored Procedures, Dependencies) from a SQL Server environment **without installing the full Data Lineage application**. The output Parquet files can then be imported into the visualizer.

## Features
- **Zero Application Dependencies**: Only requires Python and a few standard libraries.
- **Security Friendly**: Full control over the queries (visible in the script).
- **Read-Only**: Performs `SELECT` operations only.
- **Optimized Output**: Saves data in compressed Parquet format (small file size).

## Requirements
- Python 3.10+
- Microsoft ODBC Driver 18 for SQL Server
- Pip packages: `pyodbc`, `pandas`, `pyarrow`

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install pyodbc pandas pyarrow
   ```

2. **Run the Extractor**:
   ```bash
   # Using arguments
   python universal_sql_extractor.py --server "MyServer" --database "MyDB" --username "sa" --password "secret"

   # Using Environment Variables
   export MSSQL_SERVER="MyServer"
   export MSSQL_DATABASE="MyDB"
   export MSSQL_USERNAME="sa"
   export MSSQL_PASSWORD="secret"
   python universal_sql_extractor.py
   ```

3. **Check Output**:
   The script creates a `parquet_snapshots` folder containing:
   - `objects.parquet`
   - `definitions.parquet`
   - `dependencies.parquet`
   - `table_columns.parquet`
   - `query_logs.parquet`

4. **Import**:
   Take these files and upload them to the Lineage Visualizer.

## Configuration
The SQL queries used for extraction are strictly defined at the top of the `universal_sql_extractor.py` script. 
DBAs can review and modify these queries directly in the file if specific schema filters or permissions are required.

## Troubleshooting
- **Connection Error**: Ensure the ODBC Driver 18 is installed.
- **Self-Signed Certs**: Use the `--trust-cert` flag if you encounter SSL errors locally.
