"""
Synapse PySpark DMV Extractor - v3.0

Extracts DMV metadata from Azure Synapse Dedicated SQL Pool and saves to Parquet files.
Designed to run as a Synapse Spark Job (not a notebook).

Usage:
    spark-submit synapse_pyspark_dmv_extractor.py

Requirements:
    - shared_utils.process_spark_base wheel installed
    - Synapse Spark pool with access to SQL pool
    - ADLS Gen2 storage account

Output:
    - objects.parquet
    - dependencies.parquet
    - definitions.parquet
    - query_logs.parquet (optional)
"""

from shared_utils.process_spark_base import ProcessSparkBase
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

SERVER = "your-synapse-workspace.sql.azuresynapse.net"
DATABASE = "YourDatabase"
TEMP_FOLDER = "abfss://lineage@yourstorage.dfs.core.windows.net/temp"
OUTPUT_PATH = "abfss://lineage@yourstorage.dfs.core.windows.net/parquet_snapshots/"

# Set to True to skip query logs (if no VIEW SERVER STATE permission)
SKIP_QUERY_LOGS = False

# ============================================================================
# SQL QUERIES
# ============================================================================

# Schemas to include (based on production data warehouse structure)
INCLUDED_SCHEMAS = [
    'CONSUMPTION_FINANCE',
    'CONSUMPTION_POWERBI',
    'CONSUMPTION_PRIMA',
    'STAGING_FINANCE_COGNOS',
    'STAGING_FINANCE_FILE',
    'ADMIN',
    'dbo'
]

QUERY_OBJECTS = """
    SELECT
        o.object_id,
        s.name AS schema_name,
        o.name AS object_name,
        CASE o.type
            WHEN 'U' THEN 'Table'
            WHEN 'V' THEN 'View'
            WHEN 'P' THEN 'Stored Procedure'
        END AS object_type,
        o.create_date,
        o.modify_date
    FROM sys.objects o
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    WHERE o.type IN ('U', 'V', 'P')
        AND o.is_ms_shipped = 0
        AND s.name IN ('CONSUMPTION_FINANCE', 'CONSUMPTION_POWERBI', 'CONSUMPTION_PRIMA',
                       'STAGING_FINANCE_COGNOS', 'STAGING_FINANCE_FILE', 'ADMIN', 'dbo')
    ORDER BY s.name, o.name
"""

QUERY_DEPENDENCIES = """
    SELECT
        d.referencing_id AS referencing_object_id,
        d.referenced_id AS referenced_object_id,
        d.referenced_schema_name,
        d.referenced_entity_name
    FROM sys.sql_expression_dependencies d
    WHERE d.referencing_id IS NOT NULL
        AND d.referenced_id IS NOT NULL
"""

QUERY_DEFINITIONS = """
    SELECT
        m.object_id,
        o.name AS object_name,
        s.name AS schema_name,
        m.definition
    FROM sys.sql_modules m
    JOIN sys.objects o ON m.object_id = o.object_id
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    WHERE o.is_ms_shipped = 0
        AND s.name IN ('CONSUMPTION_FINANCE', 'CONSUMPTION_POWERBI', 'CONSUMPTION_PRIMA',
                       'STAGING_FINANCE_COGNOS', 'STAGING_FINANCE_FILE', 'ADMIN', 'dbo')
"""

QUERY_LOGS = """
    SELECT TOP 10000
        r.request_id,
        r.session_id,
        r.submit_time,
        SUBSTRING(r.command, 1, 4000) AS command_text
    FROM sys.dm_pdw_exec_requests r
    WHERE r.submit_time >= DATEADD(day, -7, GETDATE())
        AND r.command IS NOT NULL
    ORDER BY r.submit_time DESC
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_to_parquet(utils, query, output_filename, description):
    """Extract data from DWH and save as single Parquet file."""
    print(f"\n{'='*60}")
    print(f"Extracting {description}...")
    print(f"{'='*60}")

    try:
        df = utils.read_dwh(query)
        row_count = df.count()
        print(f"✅ Query executed: {row_count:,} rows")

        output_path = f"{OUTPUT_PATH}{output_filename}"
        df.coalesce(1).write.mode("overwrite").parquet(output_path)

        print(f"✅ Saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main extraction process"""
    print(f"\n{'='*80}")
    print("SYNAPSE PYSPARK DMV EXTRACTOR - v3.0")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server: {SERVER} | Database: {DATABASE}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"{'='*80}")

    try:
        utils = ProcessSparkBase(SERVER=SERVER, DATABASE=DATABASE, TEMP_FOLDER=TEMP_FOLDER)
        print("✅ Connected to DWH")

        extract_to_parquet(utils, QUERY_OBJECTS, "objects.parquet", "objects")
        extract_to_parquet(utils, QUERY_DEPENDENCIES, "dependencies.parquet", "dependencies")
        extract_to_parquet(utils, QUERY_DEFINITIONS, "definitions.parquet", "definitions")

        if not SKIP_QUERY_LOGS:
            try:
                extract_to_parquet(utils, QUERY_LOGS, "query_logs.parquet", "query logs")
            except Exception as e:
                print(f"⚠️  Query logs skipped: {str(e)}")

        print(f"\n{'='*80}")
        print("✅ EXTRACTION COMPLETE")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Location: {OUTPUT_PATH}")
        print(f"{'='*80}\n")
        return 0

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ EXTRACTION FAILED: {str(e)}")
        print(f"{'='*80}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
