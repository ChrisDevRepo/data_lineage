#!/usr/bin/env python3
"""
DuckDB Workspace Manager
========================

Manages the persistent DuckDB database for lineage analysis.

This module provides:
1. DuckDB connection management with persistent workspace
2. Parquet ingestion into DuckDB tables
3. Incremental load metadata tracking
4. Query interface for DMV data access

Author: Vibecoding Team
Version: 3.0.0
Phase: 3 (Core Engine)
"""

import duckdb
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class DuckDBWorkspace:
    """
    DuckDB workspace for lineage analysis.

    The workspace maintains:
    - Persistent DuckDB database file
    - Tables for objects, dependencies, definitions, query_logs
    - Metadata table for incremental load tracking
    - Lineage results table

    Schema Design:
    - objects: All database objects (tables, views, procedures)
    - dependencies: DMV dependencies (high confidence)
    - definitions: DDL text for parsing
    - query_logs: Optional runtime execution logs
    - lineage_metadata: Incremental load tracking
    - lineage_results: Final merged lineage graph
    """

    # Default workspace location
    DEFAULT_WORKSPACE_PATH = "lineage_workspace.duckdb"

    # Schema for lineage_metadata table (incremental load tracking)
    SCHEMA_LINEAGE_METADATA = """
        CREATE TABLE IF NOT EXISTS lineage_metadata (
            object_id INTEGER PRIMARY KEY,
            last_parsed_modify_date TIMESTAMP,
            last_parsed_at TIMESTAMP,
            primary_source TEXT,
            confidence REAL,
            inputs TEXT,  -- JSON array of integer object_ids
            outputs TEXT  -- JSON array of integer object_ids
        )
    """

    # Schema for lineage_results table (final graph)
    SCHEMA_LINEAGE_RESULTS = """
        CREATE TABLE IF NOT EXISTS lineage_results (
            object_id INTEGER PRIMARY KEY,
            object_name TEXT,
            schema_name TEXT,
            object_type TEXT,
            inputs TEXT,  -- JSON array of integer object_ids
            outputs TEXT,  -- JSON array of integer object_ids
            primary_source TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    # Schema for parser comparison logs
    SCHEMA_PARSER_COMPARISON = """
        CREATE TABLE IF NOT EXISTS parser_comparison_log (
            object_id INTEGER,
            object_name TEXT,
            schema_name TEXT,
            object_type TEXT,
            parse_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Regex baseline (expected counts)
            regex_sources_expected INTEGER,
            regex_targets_expected INTEGER,

            -- SQLGlot parser results
            sqlglot_sources_found INTEGER,
            sqlglot_targets_found INTEGER,
            sqlglot_confidence REAL,
            sqlglot_quality_match REAL,

            -- SQLLineage parser results (if dual-parser used)
            sqllineage_sources_found INTEGER,
            sqllineage_targets_found INTEGER,
            sqllineage_quality_match REAL,

            -- Dual-parser decision
            dual_parser_agreement REAL,
            dual_parser_decision TEXT,

            -- Final result
            final_sources_count INTEGER,
            final_targets_count INTEGER,
            final_confidence REAL,
            final_source TEXT,  -- 'sqlglot', 'sqllineage', 'dual_parser', 'ai'

            -- AI fallback (if used)
            ai_used BOOLEAN DEFAULT FALSE,
            ai_sources_found INTEGER,
            ai_targets_found INTEGER,
            ai_confidence REAL,

            PRIMARY KEY (object_id, parse_timestamp)
        )
    """

    def __init__(self, workspace_path: Optional[str] = None, read_only: bool = False):
        """
        Initialize DuckDB workspace.

        Args:
            workspace_path: Path to DuckDB database file (default: lineage_workspace.duckdb)
            read_only: Open database in read-only mode
        """
        self.workspace_path = Path(workspace_path or self.DEFAULT_WORKSPACE_PATH)
        self.read_only = read_only
        self.connection: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Connect to DuckDB workspace.

        Creates persistent database if it doesn't exist.

        Returns:
            DuckDB connection object
        """
        if self.connection:
            return self.connection

        # Create parent directory if needed
        self.workspace_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to persistent database
        self.connection = duckdb.connect(
            str(self.workspace_path),
            read_only=self.read_only
        )

        # Initialize schema
        if not self.read_only:
            self._initialize_schema()

        return self.connection

    def disconnect(self):
        """Close DuckDB connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def _initialize_schema(self):
        """Initialize workspace schema (metadata and results tables)."""
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        # Create lineage_metadata table
        self.connection.execute(self.SCHEMA_LINEAGE_METADATA)

        # Create lineage_results table
        self.connection.execute(self.SCHEMA_LINEAGE_RESULTS)

        # Create parser_comparison_log table
        self.connection.execute(self.SCHEMA_PARSER_COMPARISON)

    def load_parquet(
        self,
        parquet_dir: Path,
        full_refresh: bool = False
    ) -> Dict[str, int]:
        """
        Load Parquet files into DuckDB tables.

        Loads the 4 required Parquet files:
        1. objects.parquet → objects table
        2. dependencies.parquet → dependencies table
        3. definitions.parquet → definitions table
        4. query_logs.parquet → query_logs table (optional)

        Args:
            parquet_dir: Directory containing Parquet files
            full_refresh: If True, drop existing tables before loading

        Returns:
            Dictionary mapping table name to row count

        Raises:
            FileNotFoundError: If required Parquet files missing
            RuntimeError: If loading fails
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        parquet_dir = Path(parquet_dir)
        if not parquet_dir.exists():
            raise FileNotFoundError(f"Parquet directory not found: {parquet_dir}")

        row_counts = {}

        # Required Parquet files
        required_files = {
            'objects': 'objects.parquet',
            'dependencies': 'dependencies.parquet',
            'definitions': 'definitions.parquet'
        }

        # Optional files
        optional_files = {
            'query_logs': 'query_logs.parquet'
        }

        # Load required files
        for table_name, filename in required_files.items():
            file_path = parquet_dir / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Required file not found: {file_path}")

            row_count = self._load_parquet_file(
                file_path,
                table_name,
                full_refresh
            )
            row_counts[table_name] = row_count

        # Load optional files
        for table_name, filename in optional_files.items():
            file_path = parquet_dir / filename
            if file_path.exists():
                row_count = self._load_parquet_file(
                    file_path,
                    table_name,
                    full_refresh
                )
                row_counts[table_name] = row_count
            else:
                row_counts[table_name] = 0  # Mark as skipped

        return row_counts

    def _load_parquet_file(
        self,
        file_path: Path,
        table_name: str,
        replace: bool = False
    ) -> int:
        """
        Load a single Parquet file into DuckDB table.

        Args:
            file_path: Path to Parquet file
            table_name: Target table name in DuckDB
            replace: If True, replace existing table

        Returns:
            Number of rows loaded
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        # Drop table if replace requested
        if replace:
            self.connection.execute(f"DROP TABLE IF EXISTS {table_name}")

        # Load Parquet file
        # DuckDB can read Parquet directly without pandas
        self.connection.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_parquet('{file_path}')
        """)

        # Get row count
        result = self.connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()

        return result[0] if result else 0

    def get_objects_to_parse(
        self,
        full_refresh: bool = False,
        confidence_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Get list of objects that need parsing.

        Uses incremental load logic:
        - If full_refresh=True, return all objects
        - Otherwise, return only objects that:
          1. Don't exist in lineage_metadata, OR
          2. Have been modified since last parse, OR
          3. Have confidence < threshold

        Args:
            full_refresh: If True, ignore metadata and return all objects
            confidence_threshold: Skip objects with confidence >= this value

        Returns:
            List of object dictionaries with fields:
            - object_id
            - schema_name
            - object_name
            - object_type
            - modify_date
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        if full_refresh:
            # Return all objects
            query = """
                SELECT
                    object_id,
                    schema_name,
                    object_name,
                    object_type,
                    modify_date
                FROM objects
                ORDER BY schema_name, object_name
            """
        else:
            # Return only objects needing update
            query = f"""
                SELECT
                    o.object_id,
                    o.schema_name,
                    o.object_name,
                    o.object_type,
                    o.modify_date
                FROM objects o
                LEFT JOIN lineage_metadata m
                    ON o.object_id = m.object_id
                WHERE
                    -- Object not in metadata (never parsed)
                    m.object_id IS NULL
                    -- OR object modified since last parse
                    OR o.modify_date > m.last_parsed_modify_date
                    -- OR confidence below threshold (needs re-parsing)
                    OR m.confidence < {confidence_threshold}
                ORDER BY o.schema_name, o.object_name
            """

        results = self.connection.execute(query).fetchall()

        # Convert to list of dicts
        columns = ['object_id', 'schema_name', 'object_name', 'object_type', 'modify_date']
        return [dict(zip(columns, row)) for row in results]

    def get_dmv_dependencies(self) -> List[Dict[str, Any]]:
        """
        Get all DMV dependencies (baseline - confidence 1.0).

        Returns:
            List of dependency dictionaries with fields:
            - referencing_object_id
            - referenced_object_id
            - source: 'dmv'
            - confidence: 1.0
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        query = """
            SELECT
                referencing_object_id,
                referenced_object_id,
                'dmv' AS source,
                1.0 AS confidence
            FROM dependencies
            WHERE referencing_object_id IS NOT NULL
                AND referenced_object_id IS NOT NULL
        """

        results = self.connection.execute(query).fetchall()

        columns = ['referencing_object_id', 'referenced_object_id', 'source', 'confidence']
        return [dict(zip(columns, row)) for row in results]

    def get_object_definition(self, object_id: int) -> Optional[str]:
        """
        Get DDL definition text for an object.

        Args:
            object_id: Object ID to retrieve

        Returns:
            DDL definition text, or None if not found
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        query = """
            SELECT definition
            FROM definitions
            WHERE object_id = ?
        """

        result = self.connection.execute(query, [object_id]).fetchone()
        return result[0] if result else None

    def resolve_table_names_to_ids(
        self,
        table_names: List[str]
    ) -> Dict[str, Optional[int]]:
        """
        Resolve table names (schema.table format) to object_ids.

        Args:
            table_names: List of table names in format "schema.table"

        Returns:
            Dictionary mapping table_name → object_id (or None if not found)
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        if not table_names:
            return {}

        # Parse table names into schema and object parts
        lookup = {}
        for name in table_names:
            parts = name.split('.')
            if len(parts) == 2:
                schema, obj = parts
                lookup[name] = (schema, obj)
            elif len(parts) == 1:
                # Assume dbo schema if not specified
                lookup[name] = ('dbo', parts[0])

        # Build WHERE clause for batch lookup
        conditions = []
        for schema, obj in lookup.values():
            conditions.append(
                f"(schema_name = '{schema}' AND object_name = '{obj}')"
            )

        if not conditions:
            return {}

        where_clause = ' OR '.join(conditions)

        query = f"""
            SELECT
                schema_name || '.' || object_name AS full_name,
                object_id
            FROM objects
            WHERE {where_clause}
        """

        results = self.connection.execute(query).fetchall()

        # Build result map
        result_map = {row[0]: row[1] for row in results}

        # Return with original input keys (handle missing values)
        return {name: result_map.get(name) for name in table_names}

    def update_metadata(
        self,
        object_id: int,
        modify_date: datetime,
        primary_source: str,
        confidence: float,
        inputs: List[int],
        outputs: List[int]
    ):
        """
        Update lineage_metadata for an object.

        Args:
            object_id: Object ID
            modify_date: Modification date from objects.parquet
            primary_source: Source with highest confidence (dmv, query_log, parser, ai)
            confidence: Confidence score (0.0-1.0)
            inputs: List of input object_ids
            outputs: List of output object_ids
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        # Convert lists to JSON strings
        import json
        inputs_json = json.dumps(inputs)
        outputs_json = json.dumps(outputs)

        query = """
            INSERT OR REPLACE INTO lineage_metadata (
                object_id,
                last_parsed_modify_date,
                last_parsed_at,
                primary_source,
                confidence,
                inputs,
                outputs
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        self.connection.execute(query, [
            object_id,
            modify_date,
            datetime.now(),
            primary_source,
            confidence,
            inputs_json,
            outputs_json
        ])

    def query(self, sql: str, params: Optional[List[Any]] = None) -> List[tuple]:
        """
        Execute arbitrary SQL query.

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            List of result tuples
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        if params:
            return self.connection.execute(sql, params).fetchall()
        else:
            return self.connection.execute(sql).fetchall()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get workspace statistics.

        Returns:
            Dictionary with table row counts and metadata stats
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        stats = {}

        # Table row counts
        for table in ['objects', 'dependencies', 'definitions', 'query_logs',
                     'lineage_metadata', 'lineage_results']:
            try:
                result = self.connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()
                stats[f"{table}_count"] = result[0] if result else 0
            except:
                stats[f"{table}_count"] = 0

        # Metadata stats
        try:
            result = self.connection.execute("""
                SELECT
                    primary_source,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM lineage_metadata
                GROUP BY primary_source
            """).fetchall()

            stats['source_breakdown'] = {
                row[0]: {'count': row[1], 'avg_confidence': row[2]}
                for row in result
            }
        except:
            stats['source_breakdown'] = {}

        return stats

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
