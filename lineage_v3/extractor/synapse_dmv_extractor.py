#!/usr/bin/env python3
"""
Synapse DMV Extractor - Production Tool
========================================

Standalone utility to export Azure Synapse metadata (DMVs) to Parquet files.

This script is designed for external users who need to generate Parquet snapshots
of their Synapse metadata for use with the Vibecoding Lineage Parser v2.0.

Requirements:
    - Python >= 3.10
    - Microsoft ODBC Driver 18 for SQL Server
    - pyodbc
    - pandas
    - pyarrow

Installation:
    pip install pyodbc pandas pyarrow python-dotenv

Usage:
    # Using environment variables from .env file
    python synapse_dmv_extractor.py --output parquet_snapshots/

    # Using command-line credentials (not recommended for production)
    python synapse_dmv_extractor.py \\
        --server yourserver.sql.azuresynapse.net \\
        --database yourdatabase \\
        --username youruser \\
        --password yourpassword \\
        --output parquet_snapshots/

Output Files:
    - objects.parquet: All database objects (tables, views, procedures)
    - dependencies.parquet: Object dependencies from sys.sql_expression_dependencies
    - definitions.parquet: DDL definitions from sys.sql_modules
    - query_logs.parquet: Recent query execution logs (optional)

Author: Vibecoding
Version: 1.0.0
Parser Version: 2.0
Date: 2025-10-26
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import pyodbc
import pandas as pd

# Optional: Load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class SynapseDMVExtractor:
    """Extract Synapse DMV metadata to Parquet files."""

    # DMV Query Definitions
    # These queries are optimized for Azure Synapse Dedicated SQL Pool

    QUERY_OBJECTS = """
        SELECT
            o.object_id,
            s.name AS schema_name,
            o.name AS object_name,
            o.type AS type_code,
            CASE o.type
                WHEN 'U' THEN 'Table'
                WHEN 'V' THEN 'View'
                WHEN 'P' THEN 'Stored Procedure'
                WHEN 'TF' THEN 'Function'
                WHEN 'IF' THEN 'Function'
                WHEN 'FN' THEN 'Function'
                ELSE o.type_desc
            END AS object_type,
            o.create_date,
            o.modify_date,
            o.type_desc AS full_type_description
        FROM sys.objects o
        JOIN sys.schemas s ON o.schema_id = s.schema_id
        WHERE o.type IN ('U', 'V', 'P', 'TF', 'IF', 'FN')
            AND o.is_ms_shipped = 0
        ORDER BY s.name, o.name
    """

    QUERY_DEPENDENCIES = """
        SELECT
            d.referencing_id AS referencing_object_id,
            d.referenced_id AS referenced_object_id,
            d.referenced_schema_name,
            d.referenced_entity_name,
            d.referenced_database_name,
            d.is_ambiguous,
            d.is_schema_bound_reference,
            d.is_caller_dependent,
            d.referencing_class_desc,
            d.referenced_class_desc,
            o1.type_desc AS referencing_type,
            o2.type_desc AS referenced_type
        FROM sys.sql_expression_dependencies d
        JOIN sys.objects o1 ON d.referencing_id = o1.object_id
        LEFT JOIN sys.objects o2 ON d.referenced_id = o2.object_id
        WHERE d.referencing_id IS NOT NULL
            AND o1.is_ms_shipped = 0
        ORDER BY d.referencing_id, d.referenced_id
    """

    QUERY_DEFINITIONS = """
        SELECT
            m.object_id,
            o.name AS object_name,
            s.name AS schema_name,
            o.type_desc AS object_type,
            m.definition,
            m.uses_ansi_nulls,
            m.uses_quoted_identifier,
            m.is_schema_bound,
            o.create_date,
            o.modify_date
        FROM sys.sql_modules m
        JOIN sys.objects o ON m.object_id = o.object_id
        JOIN sys.schemas s ON o.schema_id = s.schema_id
        WHERE o.is_ms_shipped = 0
        ORDER BY s.name, o.name
    """

    QUERY_LOGS = """
        SELECT TOP 10000
            r.request_id,
            r.session_id,
            r.submit_time,
            r.start_time,
            r.end_time,
            r.status,
            r.command,
            r.total_elapsed_time,
            r.[label],
            SUBSTRING(r.command, 1, 4000) AS command_text
        FROM sys.dm_pdw_exec_requests r
        WHERE r.command IS NOT NULL
            AND r.command NOT LIKE '%sys.dm_pdw_exec_requests%'
            AND r.status IN ('Completed', 'Failed')
            AND r.submit_time >= DATEADD(day, -7, GETDATE())
            AND (
                r.[label] IS NOT NULL  -- Has label (ETL process marker)
                OR r.command LIKE 'EXEC %'  -- Stored procedure execution
                OR r.command LIKE 'EXECUTE %'  -- Stored procedure execution
                OR r.command LIKE 'INSERT %'  -- DML operations
                OR r.command LIKE 'UPDATE %'
                OR r.command LIKE 'DELETE %'
                OR r.command LIKE 'MERGE %'
                OR r.command LIKE 'TRUNCATE %'
                OR r.command LIKE 'CREATE %'  -- DDL operations
                OR r.command LIKE 'ALTER %'
                OR r.command LIKE 'DROP %'
            )
            AND r.command NOT LIKE 'SELECT %'  -- Exclude ad-hoc SELECT queries
            AND r.command NOT LIKE 'WITH %'  -- Exclude ad-hoc CTE queries
        ORDER BY r.submit_time DESC
    """

    def __init__(
        self,
        server: str,
        database: str,
        username: str,
        password: str,
        output_dir: str = "parquet_snapshots",
        skip_query_logs: bool = False
    ):
        """
        Initialize the extractor.

        Args:
            server: Azure Synapse server name (e.g., yourserver.sql.azuresynapse.net)
            database: Database name
            username: SQL authentication username
            password: SQL authentication password
            output_dir: Directory to save Parquet files
            skip_query_logs: Skip extracting query logs (useful if DMV access restricted)
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.output_dir = Path(output_dir)
        self.skip_query_logs = skip_query_logs
        self.connection = None

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> pyodbc.Connection:
        """
        Establish connection to Synapse.

        Returns:
            pyodbc.Connection object

        Raises:
            pyodbc.Error: If connection fails
        """
        if self.connection:
            return self.connection

        # Build connection string for Azure Synapse
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )

        try:
            print(f"[INFO] Connecting to {self.server}...")
            self.connection = pyodbc.connect(conn_str)
            print(f"[SUCCESS] Connected to database: {self.database}")
            return self.connection
        except pyodbc.Error as e:
            print(f"[ERROR] Connection failed: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("[INFO] Disconnected from Synapse")

    def extract_to_dataframe(self, query: str, description: str) -> pd.DataFrame:
        """
        Execute query and return results as pandas DataFrame.

        Args:
            query: SQL query to execute
            description: Description of the query for logging

        Returns:
            pandas DataFrame with query results
        """
        print(f"[INFO] Extracting {description}...")
        start_time = datetime.now()

        try:
            conn = self.connect()
            df = pd.read_sql(query, conn)
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"[SUCCESS] Extracted {len(df):,} rows in {elapsed:.2f}s")
            return df
        except Exception as e:
            print(f"[ERROR] Failed to extract {description}: {e}")
            raise

    def save_to_parquet(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Save DataFrame to Parquet file.

        Args:
            df: DataFrame to save
            filename: Output filename (without path)

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename
        print(f"[INFO] Saving to {output_path}...")

        try:
            df.to_parquet(
                output_path,
                engine='pyarrow',
                compression='snappy',
                index=False
            )
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"[SUCCESS] Saved {filename} ({file_size:.2f} KB)")
            return output_path
        except Exception as e:
            print(f"[ERROR] Failed to save {filename}: {e}")
            raise

    def extract_all(self) -> Dict[str, Path]:
        """
        Extract all DMV data and save to Parquet files.

        Returns:
            Dictionary mapping file type to output path

        Raises:
            Exception: If any extraction fails
        """
        print("=" * 70)
        print("Synapse DMV Extractor")
        print("=" * 70)
        print(f"Server: {self.server}")
        print(f"Database: {self.database}")
        print(f"Output Directory: {self.output_dir}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        output_files = {}

        try:
            # 1. Extract Objects
            df_objects = self.extract_to_dataframe(
                self.QUERY_OBJECTS,
                "database objects (tables, views, procedures)"
            )
            output_files['objects'] = self.save_to_parquet(df_objects, 'objects.parquet')
            print()

            # 2. Extract Dependencies
            df_deps = self.extract_to_dataframe(
                self.QUERY_DEPENDENCIES,
                "object dependencies"
            )
            output_files['dependencies'] = self.save_to_parquet(df_deps, 'dependencies.parquet')
            print()

            # 3. Extract Definitions
            df_defs = self.extract_to_dataframe(
                self.QUERY_DEFINITIONS,
                "object definitions (DDL)"
            )
            output_files['definitions'] = self.save_to_parquet(df_defs, 'definitions.parquet')
            print()

            # 4. Extract Query Logs (optional)
            if not self.skip_query_logs:
                try:
                    df_logs = self.extract_to_dataframe(
                        self.QUERY_LOGS,
                        "query execution logs (last 7 days, max 10,000)"
                    )
                    output_files['query_logs'] = self.save_to_parquet(df_logs, 'query_logs.parquet')
                    print()
                except Exception as e:
                    print(f"[WARNING] Query logs extraction failed (skipping): {e}")
                    print("[INFO] You can use --skip-query-logs to suppress this warning")
                    print()
            else:
                print("[INFO] Skipping query logs extraction (--skip-query-logs)")
                print()

            # Summary
            print("=" * 70)
            print("Extraction Complete!")
            print("=" * 70)
            print("\nGenerated Files:")
            for file_type, path in output_files.items():
                print(f"  - {file_type}: {path}")
            print("\nNext Steps:")
            print(f"  Run lineage parser: python lineage_v3/main.py run --parquet {self.output_dir}")
            print("=" * 70)

            return output_files

        except Exception as e:
            print(f"\n[ERROR] Extraction failed: {e}")
            raise
        finally:
            self.disconnect()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract Azure Synapse metadata (DMVs) to Parquet files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using .env file credentials
  python synapse_dmv_extractor.py --output parquet_snapshots/

  # Using command-line credentials
  python synapse_dmv_extractor.py \\
      --server yourserver.sql.azuresynapse.net \\
      --database yourdatabase \\
      --username youruser \\
      --password yourpassword \\
      --output parquet_snapshots/

  # Skip query logs (if DMV access restricted)
  python synapse_dmv_extractor.py --skip-query-logs

Environment Variables (.env file):
  SYNAPSE_SERVER=yourserver.sql.azuresynapse.net
  SYNAPSE_DATABASE=yourdatabase
  SYNAPSE_USERNAME=youruser
  SYNAPSE_PASSWORD=yourpassword
        """
    )

    # Connection parameters
    parser.add_argument(
        '--server',
        type=str,
        help='Azure Synapse server (e.g., yourserver.sql.azuresynapse.net)'
    )
    parser.add_argument(
        '--database',
        type=str,
        help='Database name'
    )
    parser.add_argument(
        '--username',
        type=str,
        help='SQL authentication username'
    )
    parser.add_argument(
        '--password',
        type=str,
        help='SQL authentication password'
    )

    # Output parameters
    parser.add_argument(
        '--output',
        type=str,
        default='parquet_snapshots',
        help='Output directory for Parquet files (default: parquet_snapshots)'
    )
    parser.add_argument(
        '--skip-query-logs',
        action='store_true',
        help='Skip extracting query logs (useful if DMV access restricted)'
    )

    # Environment file
    parser.add_argument(
        '--env-file',
        type=str,
        default='.env',
        help='Path to .env file (default: .env)'
    )

    args = parser.parse_args()

    # Load credentials from .env file if available
    env_loaded = False
    if DOTENV_AVAILABLE and Path(args.env_file).exists():
        load_dotenv(args.env_file)
        env_loaded = True
        print(f"[INFO] Loaded credentials from {args.env_file}")

    # Get credentials from args or environment
    server = args.server or os.getenv('SYNAPSE_SERVER')
    database = args.database or os.getenv('SYNAPSE_DATABASE')
    username = args.username or os.getenv('SYNAPSE_USERNAME')
    password = args.password or os.getenv('SYNAPSE_PASSWORD')

    # Validate credentials
    missing = []
    if not server:
        missing.append('--server or SYNAPSE_SERVER')
    if not database:
        missing.append('--database or SYNAPSE_DATABASE')
    if not username:
        missing.append('--username or SYNAPSE_USERNAME')
    if not password:
        missing.append('--password or SYNAPSE_PASSWORD')

    if missing:
        print("[ERROR] Missing required credentials:")
        for item in missing:
            print(f"  - {item}")
        print("\nProvide credentials via command-line arguments or .env file")
        print("Run with --help for usage examples")
        return 1

    try:
        # Initialize extractor
        extractor = SynapseDMVExtractor(
            server=server,
            database=database,
            username=username,
            password=password,
            output_dir=args.output,
            skip_query_logs=args.skip_query_logs
        )

        # Extract all DMVs
        extractor.extract_all()
        return 0

    except KeyboardInterrupt:
        print("\n[INFO] Extraction cancelled by user")
        return 130
    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
