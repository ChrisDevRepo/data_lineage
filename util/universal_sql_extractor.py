#!/usr/bin/env python3
"""
Universal SQL Extractor
=======================

Generic utility to export Microsoft SQL Server metadata to Parquet files
for Data Lineage analysis.

Features:
- Extracts Objects (Tables, Views, Procedures, Functions)
- Extracts Dependencies (SQL & DMV based)
- Exports to optimized Parquet format
- Portable: Single script, minimal dependencies

Configuration:
All SQL queries are defined below in the CONSTANTS section.
You can adjust them to fit your specific database permissions.

Author: Vibecoding
Version: 1.1.0
"""

import argparse
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import pyodbc
import pandas as pd

# Optional: Load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# Default Connection Settings (Override with Env Vars or Args)
DEFAULT_CONFIG = {
    'output_dir': 'parquet_snapshots',
    'connection_timeout': 30,
    'encrypt': 'yes',
    'trust_cert': 'no'  # Set to 'yes' for self-signed certs (e.g. local dev)
}

# SQL Queries Definition
# These queries are used to extract metadata from the database.
# You can modify them here if you need to filter specific schemas or objects.
SQL_QUERIES = {
    # 1. Extract Objects (Tables, Views, Procedures, Functions)
    'extract_objects': """
        SELECT
            s.name AS schema_name,
            o.name AS object_name,
            o.object_id,
            CASE
                WHEN o.type = 'U' THEN 'Table'
                WHEN o.type = 'V' THEN 'View'
                WHEN o.type = 'P' THEN 'Stored Procedure'
                WHEN o.type IN ('FN', 'IF', 'TF', 'FS', 'FT') THEN 'Function'
                ELSE 'Other'
            END AS object_type,
            o.create_date,
            o.modify_date
        FROM sys.objects o
        JOIN sys.schemas s ON o.schema_id = s.schema_id
        WHERE o.type IN ('U', 'V', 'P', 'FN', 'IF', 'TF', 'FS', 'FT')
          AND s.name NOT IN ('sys', 'INFORMATION_SCHEMA', 'guest', 'tempdb')
    """,

    # 2. Extract Dependencies
    'extract_dependencies': """
        SELECT
            d.referencing_id AS referencing_object_id,
            d.referenced_id AS referenced_object_id,
            s1.name AS referencing_schema_name,
            o1.name AS referencing_entity_name,
            s2.name AS referenced_schema_name,
            o2.name AS referenced_entity_name
        FROM sys.sql_expression_dependencies d
        JOIN sys.objects o1 ON d.referencing_id = o1.object_id
        JOIN sys.schemas s1 ON o1.schema_id = s1.schema_id
        LEFT JOIN sys.objects o2 ON d.referenced_id = o2.object_id
        LEFT JOIN sys.schemas s2 ON o2.schema_id = s2.schema_id
        WHERE d.referenced_id IS NOT NULL
          AND s1.name NOT IN ('sys', 'INFORMATION_SCHEMA')
    """,

    # 3. Extract Definitions
    'extract_definitions': """
        SELECT
            m.object_id,
            m.definition
        FROM sys.sql_modules m
        JOIN sys.objects o ON m.object_id = o.object_id
        JOIN sys.schemas s ON o.schema_id = s.schema_id
        WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
    """,

    # 4. Extract Query Logs
    'extract_query_logs': """
        SELECT TOP 5000
            r.request_id,
            r.session_id,
            r.start_time as submit_time,
            r.start_time,
            r.status,
            r.command,
            r.total_elapsed_time,
            t.text as command_text
        FROM sys.dm_exec_requests r
        CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
        WHERE r.session_id > 50
          AND r.command NOT IN ('AWAITING COMMAND', 'SLEEP_TASK', 'WAITFOR')
          AND t.text IS NOT NULL
        ORDER BY r.start_time DESC
    """,

    # 5. Extract Table Columns (Required for DDL)
    'list_table_columns': """
        SELECT
            c.object_id AS correct_object_id,
            s.name AS schema_name,
            t.name AS table_name,
            c.name AS column_name,
            c.column_id,
            y.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable
        FROM sys.columns c
        JOIN sys.tables t ON c.object_id = t.object_id
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        JOIN sys.types y ON c.user_type_id = y.user_type_id
        WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
    """
}


class UniversalSQLExtractor:
    """Extract Metadata using internal query definitions."""

    def __init__(
        self,
        server: str,
        database: str,
        username: str,
        password: str,
        output_dir: str = "parquet_snapshots",
        trust_cert: bool = False
    ):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.output_dir = Path(output_dir)
        self.trust_cert = trust_cert
        self.connection = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> pyodbc.Connection:
        """Establish database connection."""
        if self.connection:
            return self.connection

        # Build connection string
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt={DEFAULT_CONFIG['encrypt']};"
            f"TrustServerCertificate={'yes' if self.trust_cert else 'no'};"
            f"Connection Timeout={DEFAULT_CONFIG['connection_timeout']};"
        )

        try:
            # print(f"[INFO] Connecting to {self.server}...") 
            self.connection = pyodbc.connect(conn_str)
            print(f"[SUCCESS] Connected to database: {self.database}")
            return self.connection
        except pyodbc.Error as e:
            print(f"[ERROR] Connection failed: {e}")
            raise

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def extract_to_dataframe(self, query_id: str, desc: str) -> pd.DataFrame:
        if query_id not in SQL_QUERIES:
            return pd.DataFrame()

        print(f"[INFO] Extracting {desc}...")
        start_time = datetime.now()
        sql = SQL_QUERIES[query_id]

        try:
            conn = self.connect()
            df = pd.read_sql(sql, conn)
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"[SUCCESS] Extracted {len(df):,} rows in {elapsed:.2f}s")
            return df
        except Exception as e:
            print(f"[ERROR] Failed to extract {desc}: {e}")
            return pd.DataFrame()



    def save_to_parquet(self, df: pd.DataFrame, filename: str) -> Path:
        if df.empty:
            print(f"[SKIP] Skipping {filename} (empty results)")
            return None

        output_path = self.output_dir / filename
        try:
            df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)
            file_size = output_path.stat().st_size / 1024
            print(f"[SUCCESS] Saved {filename} ({file_size:.2f} KB)")
            return output_path
        except Exception as e:
            print(f"[ERROR] Failed to save {filename}: {e}")
            raise

    def extract_all(self):
        print("=" * 70)
        print("Universal SQL Extractor")
        print("=" * 70)

        try:
            # 1. Objects (Tables + Views + Procedures + Functions)
            df_objects = self.extract_to_dataframe('extract_objects', "database objects")
            self.save_to_parquet(df_objects, 'objects.parquet')

            # 2. Dependencies
            df_deps = self.extract_to_dataframe('extract_dependencies', "dependencies")
            self.save_to_parquet(df_deps, 'dependencies.parquet')

            # 3. Definitions
            df_defs = self.extract_to_dataframe('extract_definitions', "definitions")
            self.save_to_parquet(df_defs, 'definitions.parquet')

            # 4. Table Columns
            df_cols = self.extract_to_dataframe('list_table_columns', "table columns")
            self.save_to_parquet(df_cols, 'table_columns.parquet')

            # 5. Query Logs
            df_logs = self.extract_to_dataframe('extract_query_logs', "query logs")
            self.save_to_parquet(df_logs, 'query_logs.parquet')

        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Universal SQL Metadata Extractor")
    parser.add_argument('--server', help='Server address')
    parser.add_argument('--database', help='Database name')
    parser.add_argument('--username', help='Username')
    parser.add_argument('--password', help='Password')
    parser.add_argument('--output', default='snapshot', help='Output directory')
    parser.add_argument('--env-file', help='Path to .env file')
    parser.add_argument('--trust-cert', action='store_true', help='Trust server certificate (for local dev)')

    args = parser.parse_args()

    # Load .env
    if DOTENV_AVAILABLE:
        if args.env_file:
            if Path(args.env_file).exists():
                load_dotenv(args.env_file)
            else:
                print(f"[WARNING] Specified env file not found: {args.env_file}")
        else:
            # Try to load from current directory or parent directories (standard behavior)
            load_dotenv()
            
            # Also try looking in the script's directory if different from cwd
            script_dir = Path(__file__).resolve().parent
            script_env = script_dir / '.env'
            if script_env.exists() and script_dir != Path.cwd():
                load_dotenv(script_env)

    # Generic MSSQL variables
    server = args.server or os.getenv('MSSQL_SERVER') or os.getenv('DB_SERVER')
    database = args.database or os.getenv('MSSQL_DATABASE') or os.getenv('DB_NAME')
    username = args.username or os.getenv('MSSQL_USERNAME') or os.getenv('DB_USER')
    password = args.password or os.getenv('MSSQL_PASSWORD') or os.getenv('DB_PASSWORD')

    # Parse DB_CONNECTION_STRING
    conn_str = os.getenv('DB_CONNECTION_STRING')
    if conn_str and not (server and database and username and password):
        try:
            parts = {p.split('=')[0].strip().upper(): p.split('=', 1)[1].strip() for p in conn_str.split(';') if '=' in p}
            server = server or parts.get('SERVER')
            database = database or parts.get('DATABASE')
            username = username or parts.get('UID')
            password = password or parts.get('PWD')
        except Exception as e:
            print(f"[WARNING] Failed to parse DB_CONNECTION_STRING: {e}")

    # Fallback for localhost
    if not server:
         server = 'localhost'

    if not all([server, database, username, password]):
        print("Missing credentials. Provide via args or .env (MSSQL_*, DB_*)")
        return 1

    extractor = UniversalSQLExtractor(
        server=server,
        database=database,
        username=username,
        password=password,
        output_dir=args.output,
        trust_cert=args.trust_cert
    )
    extractor.extract_all()

if __name__ == '__main__':
    sys.exit(main())
