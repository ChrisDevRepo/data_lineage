#!/usr/bin/env python3
"""
DuckDB Workspace Manager
========================

Manages the persistent DuckDB database for lineage analysis.

This module provides:
1. DuckDB connection management with persistent workspace
2. Parquet ingestion into DuckDB tables with schema auto-detection
3. Incremental load metadata tracking
4. Query interface for DMV data access
5. Full-text search (FTS) on DDL definitions

Features:
- Automatic schema creation and validation
- MERGE support for incremental updates
- BM25 relevance ranking for text search
- Context manager for safe connection handling

Version: 4.0.3
"""

import duckdb
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


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

            -- Final result
            final_sources_count INTEGER,
            final_targets_count INTEGER,
            final_confidence REAL,
            final_source TEXT,  -- 'sqlglot', 'regex', 'ai', 'query_log'

            -- AI disambiguation (if used)
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

    def load_parquet_from_mappings(
        self,
        file_mappings: Dict[str, Path],
        full_refresh: bool = False
    ) -> Dict[str, int]:
        """
        Load Parquet files into DuckDB tables using file mappings.

        Works with any filenames - loads files directly by their actual paths.

        Args:
            file_mappings: Dict mapping table_name -> filepath
                Expected keys: 'objects', 'dependencies', 'definitions', 'query_logs' (optional)
            full_refresh: If True, drop existing tables before loading

        Returns:
            Dictionary mapping table name to row count

        Raises:
            KeyError: If required file mappings missing
            RuntimeError: If loading fails
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        row_counts = {}

        # Required table types
        required_tables = ['objects', 'dependencies', 'definitions']

        # Optional table types
        optional_tables = ['query_logs', 'table_columns']

        # Check for missing required files
        for table_name in required_tables:
            if table_name not in file_mappings:
                raise KeyError(f"Missing required file mapping: '{table_name}'")

        # Load required files
        for table_name in required_tables:
            file_path = file_mappings[table_name]
            row_count = self._load_parquet_file(
                file_path,
                table_name,
                full_refresh
            )
            row_counts[table_name] = row_count

        # Load optional files if provided
        for table_name in optional_tables:
            if table_name in file_mappings:
                file_path = file_mappings[table_name]
                row_count = self._load_parquet_file(
                    file_path,
                    table_name,
                    full_refresh
                )
                row_counts[table_name] = row_count
            else:
                row_counts[table_name] = 0  # Mark as skipped

        # Create unified_ddl view after loading all Parquet files
        self.create_unified_ddl_view()

        # Create FTS index for full-text search in Detail Search feature
        self.create_fts_index()

        # Clear orphaned metadata (objects removed since last upload)
        # CRITICAL: Prevents stale confidence stats from old uploads
        deleted = self.clear_orphaned_metadata()
        if deleted > 0:
            logger.info(f"Cache cleanup: Removed {deleted} orphaned metadata entries")

        return row_counts

    def load_parquet(
        self,
        parquet_dir: Path,
        full_refresh: bool = False
    ) -> Dict[str, int]:
        """
        Load Parquet files into DuckDB tables (legacy method for CLI).

        Loads the 4 required Parquet files by fixed names:
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
            'query_logs': 'query_logs.parquet',
            'table_columns': 'table_columns.parquet'
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

        # Create unified_ddl view after loading all Parquet files
        self.create_unified_ddl_view()

        # Create FTS index for full-text search in Detail Search feature
        self.create_fts_index()

        # Clear orphaned metadata (objects removed since last upload)
        # CRITICAL: Prevents stale confidence stats from old uploads
        deleted = self.clear_orphaned_metadata()
        if deleted > 0:
            logger.info(f"Cache cleanup: Removed {deleted} orphaned metadata entries")

        return row_counts

    def _load_parquet_file(
        self,
        file_path: Path,
        table_name: str,
        replace: bool = False
    ) -> int:
        """
        Load a single Parquet file into DuckDB table.

        Note: query_logs filtering (SELECT, INSERT, UPDATE, etc.) and DISTINCT
        are done at source in PySpark extractor to minimize data transfer.

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

        # Load Parquet file with special handling for table_columns
        if table_name == 'table_columns':
            # Load table_columns and add correct_object_id column immediately
            # This handles cases where object_ids change between extractions
            self.connection.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT
                    tc.*,
                    o.object_id as correct_object_id
                FROM read_parquet('{file_path}') tc
                LEFT JOIN objects o
                    ON o.schema_name = tc.schema_name
                    AND o.object_name = tc.table_name
                    AND o.object_type = 'Table'
            """)
        else:
            # Load other tables directly (no additional filtering needed)
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

        # Build WHERE clause for batch lookup using parameterized queries
        if not lookup:
            return {}

        # Use placeholders for SQL injection protection
        placeholders = []
        params = []
        for schema, obj in lookup.values():
            placeholders.append("(schema_name = ? AND object_name = ?)")
            params.extend([schema, obj])

        where_clause = ' OR '.join(placeholders)

        query = f"""
            SELECT
                schema_name || '.' || object_name AS full_name,
                object_id
            FROM objects
            WHERE {where_clause}
        """

        results = self.connection.execute(query, params).fetchall()

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
        Update lineage_metadata for an object using UNION merge strategy.

        When lineage exists from multiple sources, inputs and outputs are merged
        (deduplicated union), and the highest confidence source is retained.

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

        import json

        # Read existing metadata if it exists
        existing = self.connection.execute("""
            SELECT inputs, outputs, primary_source, confidence
            FROM lineage_metadata
            WHERE object_id = ?
        """, [object_id]).fetchall()

        if existing and len(existing) > 0:
            # Existing record found - merge with UNION strategy
            old_inputs_json, old_outputs_json, old_source, old_confidence = existing[0]

            # Parse existing JSON arrays
            old_inputs = json.loads(old_inputs_json) if old_inputs_json else []
            old_outputs = json.loads(old_outputs_json) if old_outputs_json else []

            # v4.1.2: For Stored Procedures with 'parser' source, REPLACE instead of UNION
            # Rationale: Parser is authoritative for SPs. UNION can carry forward stale dependencies
            # from previous parses (e.g., administrative queries that are now filtered out).
            # Tables/Views still use UNION because they get complementary lineage from multiple sources.
            if primary_source == 'parser':
                # REPLACE strategy: Trust the new parser results completely
                merged_inputs = inputs
                merged_outputs = outputs
                final_source = primary_source
                final_confidence = confidence
                logger.debug(f"  REPLACE strategy for parser source (object_id={object_id})")
            else:
                # UNION strategy: Merge inputs/outputs from multiple sources
                merged_inputs = list(set(old_inputs + inputs))
                merged_outputs = list(set(old_outputs + outputs))

                # Keep highest confidence source
                if confidence > old_confidence:
                    final_source = primary_source
                    final_confidence = confidence
                else:
                    final_source = old_source
                    final_confidence = old_confidence
                logger.debug(f"  UNION strategy for non-parser source (object_id={object_id})")
        else:
            # No existing record - use new values directly
            merged_inputs = inputs
            merged_outputs = outputs
            final_source = primary_source
            final_confidence = confidence

        # Convert to JSON
        inputs_json = json.dumps(merged_inputs)
        outputs_json = json.dumps(merged_outputs)

        # Write merged result
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
            final_source,
            final_confidence,
            inputs_json,
            outputs_json
        ])

    def clear_orphaned_metadata(self):
        """
        Delete metadata for objects that no longer exist in the objects table.

        This should be called after loading new Parquet data to ensure
        lineage_metadata only contains entries for current objects.

        Critical for preventing stale cached metrics when uploading new data.

        Returns:
            Number of orphaned records deleted
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        # Check if lineage_metadata exists
        tables = [row[0] for row in self.query("SHOW TABLES")]
        if 'lineage_metadata' not in tables:
            return 0

        # Delete metadata for objects not in current objects table
        query = """
        DELETE FROM lineage_metadata
        WHERE object_id NOT IN (SELECT object_id FROM objects)
        """

        result = self.connection.execute(query)
        deleted_count = result.fetchone()[0] if result else 0

        if deleted_count > 0:
            logger.info(f"Cleared {deleted_count} orphaned metadata records")

        return deleted_count

    def create_fts_index(self):
        """
        Create full-text search index for DDL definitions.

        Called after loading definitions table on data upload.

        Features:
        - Indexes: object_name, definition_text
        - Case-insensitive search
        - Automatic stemming (e.g., "customer" matches "customers")
        - BM25 relevance ranking
        - Supports phrase search, boolean operators, wildcards

        Raises:
            RuntimeError: If not connected or definitions table doesn't exist
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        try:
            # Install and load FTS extension
            self.connection.execute("INSTALL fts;")
            self.connection.execute("LOAD fts;")

            # Create FTS index on definitions table
            # Indexes both object_name and definition_text for comprehensive search
            self.connection.execute("""
                PRAGMA create_fts_index(
                    'definitions',
                    'object_id',
                    'object_name',
                    'definition',
                    overwrite=1
                );
            """)

            print("✅ FTS index created successfully on definitions table")

        except Exception as e:
            print(f"❌ Failed to create FTS index: {e}")
            raise RuntimeError(f"FTS index creation failed: {e}")

    def create_unified_ddl_view(self):
        """
        Create unified_ddl view that combines real DDL (SPs/Views) with generated table DDL.

        This view provides a single interface to get DDL for any database object:
        - Stored Procedures and Views: Real DDL from definitions table
        - Tables: Generated CREATE TABLE DDL from table_columns
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        # Check if definitions table exists
        definitions_exists = self.connection.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'definitions'
        """).fetchone()[0] > 0

        # Check if table_columns exists
        table_columns_exists = self.connection.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'table_columns'
        """).fetchone()[0] > 0

        if not definitions_exists:
            # Can't create view without definitions table
            return

        # Build view SQL based on which tables exist
        view_parts = []

        # Part 1: Real DDL from definitions (always include if definitions exists)
        view_parts.append("""
            SELECT
                d.object_id,
                o.schema_name,
                o.object_name,
                o.object_type,
                d.definition as ddl_text
            FROM definitions d
            JOIN objects o ON d.object_id = o.object_id
            WHERE o.object_type IN ('Stored Procedure', 'View')
        """)

        # Part 2: Generated CREATE TABLE DDL (only if table_columns exists)
        if table_columns_exists:
            view_parts.append("""
                SELECT
                    tc.correct_object_id as object_id,
                    tc.schema_name,
                    tc.table_name as object_name,
                    'Table' as object_type,
                    'CREATE TABLE [' || tc.schema_name || '].[' || tc.table_name || '] (' || chr(10) ||
                    string_agg(
                        '    [' || tc.column_name || '] ' ||
                        CASE
                            WHEN tc.data_type IN ('varchar', 'nvarchar', 'char', 'nchar') THEN
                                tc.data_type ||
                                CASE
                                    WHEN tc.max_length = -1 THEN '(MAX)'
                                    WHEN tc.data_type IN ('nvarchar', 'nchar') THEN '(' || CAST(tc.max_length / 2 AS VARCHAR) || ')'
                                    ELSE '(' || CAST(tc.max_length AS VARCHAR) || ')'
                                END
                            WHEN tc.data_type IN ('decimal', 'numeric') THEN
                                tc.data_type || '(' || CAST(tc.precision AS VARCHAR) || ',' || CAST(tc.scale AS VARCHAR) || ')'
                            ELSE tc.data_type
                        END ||
                        CASE WHEN tc.is_nullable THEN ' NULL' ELSE ' NOT NULL' END,
                        ',' || chr(10)
                        ORDER BY tc.column_id
                    ) || chr(10) || ');' as ddl_text
                FROM table_columns tc
                WHERE tc.correct_object_id IS NOT NULL
                GROUP BY tc.correct_object_id, tc.schema_name, tc.table_name
            """)

        # Part 3: Fallback for tables without column metadata (ensures ALL tables are searchable)
        view_parts.append("""
            SELECT
                o.object_id,
                o.schema_name,
                o.object_name,
                o.object_type,
                'CREATE TABLE [' || o.schema_name || '].[' || o.object_name || '] (' || chr(10) ||
                '    /* Column information not available - table_columns.parquet not provided */' || chr(10) ||
                ');' as ddl_text
            FROM objects o
            WHERE o.object_type = 'Table'
            AND NOT EXISTS (
                SELECT 1 FROM table_columns tc WHERE tc.correct_object_id = o.object_id
            )
        """)

        # Create view with UNION ALL for all parts
        view_sql = "CREATE OR REPLACE VIEW unified_ddl AS " + " UNION ALL ".join(view_parts)

        self.connection.execute(view_sql)

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
                     'table_columns', 'lineage_metadata', 'lineage_results']:
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
