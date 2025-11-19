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
            inputs TEXT,  -- JSON array of integer object_ids
            outputs TEXT,  -- JSON array of integer object_ids
            parse_success BOOLEAN,  -- v4.3.6: Replaced confidence with simple boolean
            expected_tables INTEGER,  -- v4.3.6: Diagnostic count
            found_tables INTEGER  -- v4.3.6: Diagnostic count
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    # Schema for parser comparison logs (deprecated in v4.3.6)
    # This table is no longer used since SQLGlot was removed
    SCHEMA_PARSER_COMPARISON = """
        CREATE TABLE IF NOT EXISTS parser_comparison_log (
            object_id INTEGER,
            object_name TEXT,
            schema_name TEXT,
            object_type TEXT,
            parse_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Regex extraction (only method as of v4.3.6)
            regex_sources_expected INTEGER,
            regex_targets_expected INTEGER,
            found_sources_count INTEGER,
            found_targets_count INTEGER,
            final_source TEXT,  -- 'regex', 'query_log'

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

                # Migration v4.3.6: Drop confidence columns (replaced with parse_success boolean)
        try:
            # Check if lineage_metadata exists first
            tables = [row[0] for row in self.query("SHOW TABLES")]
            if 'lineage_metadata' not in tables:
                return

            # Check which columns exist
            columns = self.connection.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'lineage_metadata'
            """).fetchall()

            column_names = [col[0] for col in columns]

            # Drop confidence columns if they exist (v4.3.6)
            if 'confidence' in column_names:
                logger.info("Migrating lineage_metadata: dropping confidence column (v4.3.6)...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata DROP COLUMN confidence
                """)
                logger.info("✓ Migration complete: confidence column dropped")

            if 'confidence_breakdown' in column_names:
                logger.info("Migrating lineage_metadata: dropping confidence_breakdown column (v4.3.6)...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata DROP COLUMN confidence_breakdown
                """)
                logger.info("✓ Migration complete: confidence_breakdown column dropped")

            # Add new columns for v4.3.6
            if 'parse_success' not in column_names:
                logger.info("Migrating lineage_metadata: adding parse_success column (v4.3.6)...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata ADD COLUMN parse_success BOOLEAN DEFAULT TRUE
                """)
                logger.info("✓ Migration complete: parse_success column added")

            if 'expected_tables' not in column_names:
                logger.info("Migrating lineage_metadata: adding expected_tables column (v4.3.6)...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata ADD COLUMN expected_tables INTEGER DEFAULT 0
                """)
                logger.info("✓ Migration complete: expected_tables column added")

            if 'found_tables' not in column_names:
                logger.info("Migrating lineage_metadata: adding found_tables column (v4.3.6)...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata ADD COLUMN found_tables INTEGER DEFAULT 0
                """)
                logger.info("✓ Migration complete: found_tables column added")

        except Exception as e:
            logger.warning(f"Could not migrate lineage_metadata columns: {e}")

        # Migration: Add parse failure fields if they don't exist (v2.1.0 / BUG-002)
        try:
            # Re-fetch columns to check for new fields
            columns = self.connection.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'lineage_metadata'
            """).fetchall()

            column_names = [col[0] for col in columns]

            # Add parse_failure_reason column
            if 'parse_failure_reason' not in column_names:
                logger.info("Migrating lineage_metadata: adding parse_failure_reason column...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata
                    ADD COLUMN parse_failure_reason VARCHAR
                """)
                logger.info("✓ Migration complete: parse_failure_reason column added")

            # Add expected_count column
            if 'expected_count' not in column_names:
                logger.info("Migrating lineage_metadata: adding expected_count column...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata
                    ADD COLUMN expected_count INTEGER
                """)
                logger.info("✓ Migration complete: expected_count column added")

            # Add found_count column
            if 'found_count' not in column_names:
                logger.info("Migrating lineage_metadata: adding found_count column...")
                self.connection.execute("""
                    ALTER TABLE lineage_metadata
                    ADD COLUMN found_count INTEGER
                """)
                logger.info("✓ Migration complete: found_count column added")
        except Exception as e:
            logger.warning(f"Could not check/add parse failure fields: {e}")

        # Create lineage_results table
        self.connection.execute(self.SCHEMA_LINEAGE_RESULTS)

        # Create parser_comparison_log table
        self.connection.execute(self.SCHEMA_PARSER_COMPARISON)

        # Migration: Add referenced_id column to dependencies table (v4.3.0)
        try:
            # Check if dependencies table exists
            tables = self.connection.execute("SHOW TABLES").fetchall()
            table_names = [t[0] for t in tables]

            if 'dependencies' in table_names:
                # Check if referenced_id column exists
                columns = self.connection.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'dependencies'
                """).fetchall()

                column_names = [col[0] for col in columns]

                if 'referenced_id' not in column_names:
                    logger.info("Migrating dependencies: adding referenced_id column...")
                    self.connection.execute("""
                        ALTER TABLE dependencies
                        ADD COLUMN referenced_id BIGINT
                    """)
                    logger.info("✓ Migration complete: referenced_id column added")
        except Exception as e:
            logger.warning(f"Could not check/add referenced_id column to dependencies: {e}")

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

    def load_parquet_files(
        self,
        parquet_dir: Path | str,
        full_refresh: bool = False
    ) -> Dict[str, int]:
        """
        Load Parquet files into DuckDB tables by auto-detecting schemas.

        Automatically detects table type by inspecting column names (no fixed filenames required):
        - objects: object_id, schema_name, object_name, object_type, create_date
        - dependencies: referencing_object_id, referenced_object_id, referenced_schema_name
        - definitions: object_id, object_name, schema_name, definition
        - query_logs: command_text (optional)
        - table_columns: object_id, schema_name, table_name, column_name (optional)

        Args:
            parquet_dir: Directory containing Parquet files (any filenames accepted)
            full_refresh: If True, drop existing tables before loading

        Returns:
            Dictionary mapping table name to row count

        Raises:
            FileNotFoundError: If required tables (objects, dependencies, definitions) not found
            RuntimeError: If loading fails
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        parquet_dir = Path(parquet_dir)
        if not parquet_dir.exists():
            raise FileNotFoundError(f"Parquet directory not found: {parquet_dir}")

        # Find all Parquet files and detect their table types
        parquet_files = list(parquet_dir.glob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(f"No Parquet files found in {parquet_dir}")

        logger.info(f"Found {len(parquet_files)} Parquet files, detecting schemas...")

        # Map files to table types by schema detection
        file_mapping = {}
        for file_path in parquet_files:
            table_name = self._detect_table_type(file_path)
            if table_name:
                file_mapping[table_name] = file_path
                logger.info(f"✓ {file_path.name} → {table_name} table")
            else:
                logger.warning(f"✗ {file_path.name} → unknown schema (skipped)")

        # Verify required tables are present
        required_tables = ['objects', 'dependencies', 'definitions']
        missing = [t for t in required_tables if t not in file_mapping]
        if missing:
            raise FileNotFoundError(
                f"Required tables missing: {missing}. "
                f"Found: {list(file_mapping.keys())}"
            )

        row_counts = {}

        # Load required files first (order matters for table_columns FK)
        for table_name in required_tables:
            file_path = file_mapping[table_name]
            row_count = self._load_parquet_file(
                file_path,
                table_name,
                full_refresh
            )
            row_counts[table_name] = row_count

        # Load optional files
        optional_tables = ['query_logs', 'table_columns']
        for table_name in optional_tables:
            if table_name in file_mapping:
                file_path = file_mapping[table_name]
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

    def _detect_table_type(self, file_path: Path) -> str | None:
        """
        Detect table type by inspecting Parquet file schema.

        Args:
            file_path: Path to Parquet file

        Returns:
            Table name ('objects', 'dependencies', 'definitions', 'query_logs', 'table_columns')
            or None if schema doesn't match any known table
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        try:
            # Get column names from Parquet file
            result = self.connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{file_path}')"
            ).fetchall()
            columns = {row[0].lower() for row in result}

            # Match against known table schemas
            if {'object_id', 'schema_name', 'object_name', 'object_type', 'create_date'}.issubset(columns):
                return 'objects'
            elif {'referencing_object_id', 'referenced_object_id', 'referenced_schema_name', 'referenced_entity_name'}.issubset(columns):
                return 'dependencies'
            elif {'object_id', 'object_name', 'schema_name', 'definition'}.issubset(columns):
                return 'definitions'
            elif 'command_text' in columns and len(columns) == 1:
                return 'query_logs'
            elif {'object_id', 'schema_name', 'table_name', 'column_name', 'data_type'}.issubset(columns):
                return 'table_columns'
            else:
                logger.warning(f"Unknown Parquet schema in {file_path.name}: {columns}")
                return None

        except Exception as e:
            logger.error(f"Failed to detect table type for {file_path.name}: {e}")
            return None

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
          3. Have parse_success = False (failed parsing)

        Args:
            full_refresh: If True, ignore metadata and return all objects
            confidence_threshold: Legacy parameter (ignored in v4.3.6+)

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
            # Check if lineage_metadata table exists
            tables = [row[0] for row in self.connection.execute("SHOW TABLES").fetchall()]

            if 'lineage_metadata' not in tables:
                # No metadata table means nothing has been parsed yet
                # Treat as full refresh
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
                query = """
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
                        -- OR parsing failed (parse_success = False)
                        OR m.parse_success = FALSE
                    ORDER BY o.schema_name, o.object_name
                """

        results = self.connection.execute(query).fetchall()

        # Convert to list of dicts
        columns = ['object_id', 'schema_name', 'object_name', 'object_type', 'modify_date']
        return [dict(zip(columns, row)) for row in results]

    def get_dmv_dependencies(self) -> List[Dict[str, Any]]:
        """
        Get all DMV dependencies (baseline - parse_success true).

        Returns:
            List of dependency dictionaries with fields:
            - referencing_object_id
            - referenced_object_id
            - source: 'dmv'
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        query = """
            SELECT
                referencing_object_id,
                referenced_object_id,
                'dmv' AS source
            FROM dependencies
            WHERE referencing_object_id IS NOT NULL
                AND referenced_object_id IS NOT NULL
        """

        results = self.connection.execute(query).fetchall()

        columns = ['referencing_object_id', 'referenced_object_id', 'source']
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
        inputs: List[int],
        outputs: List[int],
        parse_failure_reason: str = None,
        expected_count: int = None,
        found_count: int = None,
        parse_success: bool = True
    ):
        """
        Update lineage_metadata for an object using UNION merge strategy.

        When lineage exists from multiple sources, inputs and outputs are merged
        (deduplicated union), and the highest confidence source is retained.

        Args:
            object_id: Object ID
            modify_date: Modification date from objects.parquet
            primary_source: Source with highest confidence (dmv, query_log, parser, ai)
            inputs: List of input object_ids
            outputs: List of output object_ids
            parse_failure_reason: Reason for parse failure (v4.3.6)
            expected_count: Expected number of tables (v4.3.6)
            found_count: Number of tables actually found (v4.3.6)
            parse_success: Whether parsing succeeded (v4.3.6)
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        import json

        # Read existing metadata if it exists
        existing = self.connection.execute("""
            SELECT inputs, outputs, primary_source, parse_success
            FROM lineage_metadata
            WHERE object_id = ?
        """, [object_id]).fetchall()

        if existing and len(existing) > 0:
            # Existing record found - merge with UNION strategy
            old_inputs_json, old_outputs_json, old_source, old_parse_success = existing[0]

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
                final_parse_success = parse_success
                logger.debug(f"  REPLACE strategy for parser source (object_id={object_id})")
            else:
                # UNION strategy: Merge inputs/outputs from multiple sources
                merged_inputs = list(set(old_inputs + inputs))
                merged_outputs = list(set(old_outputs + outputs))

                # Keep source with successful parsing, prefer new if both successful
                if parse_success and not old_parse_success:
                    final_source = primary_source
                    final_parse_success = parse_success
                elif old_parse_success and not parse_success:
                    final_source = old_source
                    final_parse_success = old_parse_success
                else:
                    # Both same success status, keep existing
                    final_source = old_source
                    final_parse_success = old_parse_success
                logger.debug(f"  UNION strategy for non-parser source (object_id={object_id})")
        else:
            # No existing record - use new values directly
            merged_inputs = inputs
            merged_outputs = outputs
            final_source = primary_source
            final_parse_success = parse_success

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
                parse_success,
                inputs,
                outputs,
                parse_failure_reason,
                expected_count,
                found_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.connection.execute(query, [
            object_id,
            modify_date,
            datetime.now(),
            final_source,
            final_parse_success,
            inputs_json,
            outputs_json,
            parse_failure_reason,
            expected_count,
            found_count
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

        Called after loading definitions table and creating unified_ddl view on data upload.

        Features:
        - Indexes: object_name, ddl_text (includes generated CREATE TABLE statements)
        - Case-insensitive search
        - Automatic stemming (e.g., "customer" matches "customers")
        - BM25 relevance ranking
        - Supports phrase search, boolean operators, wildcards

        Raises:
            RuntimeError: If not connected or unified_ddl view doesn't exist
        """
        if not self.connection:
            raise RuntimeError("Not connected to DuckDB workspace")

        try:
            # Install and load FTS extension
            self.connection.execute("INSTALL fts;")
            self.connection.execute("LOAD fts;")

            # Materialize unified_ddl view as a table (FTS can't index views)
            # This creates a searchable table with all DDL (real + generated)
            self.connection.execute("""
                CREATE OR REPLACE TABLE unified_ddl_materialized AS
                SELECT * FROM unified_ddl
            """)

            # Create FTS index on materialized table
            # Indexes both object_name and ddl_text for comprehensive search
            self.connection.execute("""
                PRAGMA create_fts_index(
                    'unified_ddl_materialized',
                    'object_id',
                    'object_name',
                    'ddl_text',
                    overwrite=1
                );
            """)

            logger.info("FTS index created successfully on unified_ddl_materialized table")

        except Exception as e:
            logger.warning(f"Failed to create FTS index (optional feature): {e}")
            logger.info("Continuing without FTS index - search functionality will be limited")

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
        if table_columns_exists:
            # Only show tables NOT in table_columns
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
        else:
            # Show ALL tables with fallback DDL (table_columns.parquet not provided)
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
            except (duckdb.CatalogException, RuntimeError) as e:
                logger.debug(f"Table {table} not found: {e}")
                stats[f"{table}_count"] = 0

        # Metadata stats
        try:
            result = self.connection.execute("""
                SELECT
                    primary_source,
                    COUNT(*) as count,
                    AVG(CASE WHEN parse_success THEN 1.0 ELSE 0.0 END) as avg_success_rate
                FROM lineage_metadata
                GROUP BY primary_source
            """).fetchall()

            stats['source_breakdown'] = {
                row[0]: {'count': row[1], 'avg_success_rate': row[2]}
                for row in result
            }
        except Exception as e:
            logger.warning(f"Failed to calculate source breakdown: {e}")
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
