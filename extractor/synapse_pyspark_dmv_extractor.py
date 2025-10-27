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
    """
    Extract data from DWH using shared_utils and save as single Parquet file.

    Args:
        utils: ProcessSparkBase instance
        query: SQL query string
        output_filename: Output file name (e.g., "objects.parquet")
        description: Human-readable description for logging
    """
    print(f"\n{'='*60}")
    print(f"Extracting {description}...")
    print(f"{'='*60}")

    try:
        # Read from DWH using shared_utils
        df = utils.read_dwh(query)

        # Get row count for logging
        row_count = df.count()
        print(f"✅ Query executed successfully: {row_count:,} rows retrieved")

        # Convert to pandas for single-file write (DMV data is small)
        print(f"Converting to pandas for single-file output...")
        pdf = df.toPandas()

        # Save to temp file
        temp_path = f"/tmp/{output_filename}"
        print(f"Writing to temporary file: {temp_path}")
        pdf.to_parquet(temp_path, index=False, engine='pyarrow', compression='snappy')

        # Upload to ADLS
        output_full_path = f"{OUTPUT_PATH}{output_filename}"
        print(f"Uploading to ADLS: {output_full_path}")

        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()

        # Use mssparkutils for file operations (Synapse-specific)
        from notebookutils import mssparkutils
        mssparkutils.fs.cp(f"file://{temp_path}", output_full_path, True)

        # Clean up temp file
        import os
        os.remove(temp_path)

        print(f"✅ {description.capitalize()} saved successfully!")
        print(f"   Location: {output_full_path}")
        print(f"   Rows: {row_count:,}")
        print(f"   Size: ~{len(pdf):,} bytes (uncompressed)")

    except Exception as e:
        print(f"❌ Error extracting {description}: {str(e)}")
        raise

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main extraction process"""

    print("\n" + "="*80)
    print("  SYNAPSE PYSPARK DMV EXTRACTOR - v3.0")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nConfiguration:")
    print(f"  Server: {SERVER}")
    print(f"  Database: {DATABASE}")
    print(f"  Temp Folder: {TEMP_FOLDER}")
    print(f"  Output Path: {OUTPUT_PATH}")
    print(f"  Skip Query Logs: {SKIP_QUERY_LOGS}")
    print("="*80)

    try:
        # Initialize ProcessSparkBase
        print("\n📦 Initializing ProcessSparkBase...")
        utils = ProcessSparkBase(
            SERVER=SERVER,
            DATABASE=DATABASE,
            TEMP_FOLDER=TEMP_FOLDER
        )
        print("✅ ProcessSparkBase initialized successfully")

        # Extract objects (Tables, Views, Stored Procedures)
        extract_to_parquet(
            utils,
            QUERY_OBJECTS,
            "objects.parquet",
            "objects (tables, views, stored procedures)"
        )

        # Extract dependencies (DMV relationships)
        extract_to_parquet(
            utils,
            QUERY_DEPENDENCIES,
            "dependencies.parquet",
            "dependencies (DMV relationships)"
        )

        # Extract definitions (DDL text)
        extract_to_parquet(
            utils,
            QUERY_DEFINITIONS,
            "definitions.parquet",
            "definitions (DDL text)"
        )

        # Extract query logs (optional)
        if not SKIP_QUERY_LOGS:
            try:
                extract_to_parquet(
                    utils,
                    QUERY_LOGS,
                    "query_logs.parquet",
                    "query logs (execution history)"
                )
            except Exception as e:
                print(f"\n⚠️  Warning: Query log extraction failed: {str(e)}")
                print("    This is optional - continuing without query logs")
        else:
            print("\n⏭️  Skipping query logs (SKIP_QUERY_LOGS = True)")

        # Summary
        print("\n" + "="*80)
        print("  ✅ EXTRACTION COMPLETE!")
        print("="*80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nOutput files saved to:")
        print(f"  {OUTPUT_PATH}")
        print(f"\nFiles generated:")
        print(f"  1. objects.parquet       - Tables, Views, Stored Procedures")
        print(f"  2. dependencies.parquet  - DMV relationships")
        print(f"  3. definitions.parquet   - DDL text")
        if not SKIP_QUERY_LOGS:
            print(f"  4. query_logs.parquet    - Query execution history")
        print("\n📥 Download these files from ADLS to your local machine")
        print("📤 Then upload to the web application for lineage analysis")
        print("="*80 + "\n")

        return 0

    except Exception as e:
        print("\n" + "="*80)
        print("  ❌ EXTRACTION FAILED!")
        print("="*80)
        print(f"Error: {str(e)}")
        print("\nPlease check:")
        print("  1. SERVER and DATABASE configuration are correct")
        print("  2. Spark pool has access to SQL pool")
        print("  3. TEMP_FOLDER and OUTPUT_PATH exist and are writable")
        print("  4. shared_utils.process_spark_base wheel is installed")
        print("="*80 + "\n")

        import traceback
        traceback.print_exc()

        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
