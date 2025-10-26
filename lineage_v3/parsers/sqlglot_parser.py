"""
SQLGlot Parser - Extract lineage from DDL using AST traversal

This module uses SQLGlot to parse T-SQL DDL definitions and extract
table-level lineage (source and target table references).

Confidence: 0.85 (static AST analysis)

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-26
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import sqlglot
from sqlglot import exp
import logging

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace


# Configure logging
logger = logging.getLogger(__name__)


class SQLGlotParser:
    """
    Parse T-SQL DDL to extract table lineage using SQLGlot AST.

    Extracts:
    - Source tables (inputs): FROM, JOIN clauses
    - Target tables (outputs): INSERT INTO, UPDATE, MERGE

    Resolves table names to object_ids via DuckDB workspace.
    """

    # Confidence score for static AST analysis
    CONFIDENCE = 0.85

    # System schemas to exclude
    EXCLUDED_SCHEMAS = {'sys', 'INFORMATION_SCHEMA'}

    def __init__(self, workspace: DuckDBWorkspace):
        """
        Initialize parser with DuckDB workspace.

        Args:
            workspace: DuckDBWorkspace instance with initialized database
        """
        self.workspace = workspace

    def parse_object(self, object_id: int) -> Dict[str, Any]:
        """
        Parse DDL for a single object.

        Args:
            object_id: Object to parse

        Returns:
            {
                'object_id': int,
                'inputs': List[int],   # source tables (FROM/JOIN)
                'outputs': List[int],  # target tables (INSERT/UPDATE/MERGE)
                'confidence': 0.85,
                'source': 'parser',
                'parse_error': Optional[str]  # If parsing failed
            }

        Raises:
            ValueError: If object_id not found
        """
        # Fetch DDL from definitions table
        ddl = self._fetch_ddl(object_id)

        if not ddl:
            logger.warning(f"No DDL found for object_id {object_id}")
            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'confidence': 0.0,
                'source': 'parser',
                'parse_error': 'No DDL definition found'
            }

        # Extract table references
        try:
            references = self._extract_table_references(ddl)

            # Resolve table names to object_ids
            input_ids = self._resolve_table_names(references['sources'])
            output_ids = self._resolve_table_names(references['targets'])

            return {
                'object_id': object_id,
                'inputs': input_ids,
                'outputs': output_ids,
                'confidence': self.CONFIDENCE,
                'source': 'parser',
                'parse_error': None
            }

        except Exception as e:
            logger.error(f"Failed to parse object_id {object_id}: {e}")
            return {
                'object_id': object_id,
                'inputs': [],
                'outputs': [],
                'confidence': 0.0,
                'source': 'parser',
                'parse_error': str(e)
            }

    def parse_batch(self, object_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Parse multiple objects in batch.

        Args:
            object_ids: List of object_ids to parse

        Returns:
            List of parse results (same format as parse_object)
        """
        results = []

        for obj_id in object_ids:
            result = self.parse_object(obj_id)
            results.append(result)

        return results

    def _fetch_ddl(self, object_id: int) -> Optional[str]:
        """
        Fetch DDL definition from workspace.

        Args:
            object_id: Object to fetch

        Returns:
            DDL text or None if not found
        """
        query = f"""
        SELECT definition
        FROM definitions
        WHERE object_id = {object_id}
        """

        results = self.workspace.query(query)

        if not results:
            return None

        # Results are tuples: (definition,)
        return results[0][0]

    def _extract_table_references(self, ddl: str) -> Dict[str, List[str]]:
        """
        Extract table names from DDL using SQLGlot AST.

        Args:
            ddl: DDL text (T-SQL)

        Returns:
            {
                'sources': ['schema.table1', 'schema.table2'],
                'targets': ['schema.table3']
            }

        Note: Table names are normalized to schema.object_name format
        """
        sources = set()
        targets = set()

        try:
            # Parse T-SQL (handle multiple statements)
            statements = sqlglot.parse(ddl, dialect='tsql')

            # Track procedure/view names to exclude from table lists
            excluded_names = set()

            for statement in statements:
                if statement is None:
                    continue

                # If this is a CREATE PROCEDURE/VIEW, track its name
                if isinstance(statement, exp.Create) and statement.this:
                    proc_name = self._get_table_name(statement.this)
                    if proc_name:
                        excluded_names.add(proc_name)

                # Extract source tables (FROM, JOIN)
                sources.update(self._extract_source_tables(statement))

                # Extract target tables (INSERT, UPDATE, MERGE)
                targets.update(self._extract_target_tables(statement))

            # Remove procedure/view names from both sources and targets
            sources = sources - excluded_names
            targets = targets - excluded_names

            # Remove target tables from sources (INSERT target shouldn't be in inputs)
            sources = sources - targets

        except Exception as e:
            logger.warning(f"SQLGlot parse error: {e}")
            # Re-raise so parse_object can catch and return confidence 0.0
            raise

        # Filter out system tables and temp tables
        sources = self._filter_table_names(sources)
        targets = self._filter_table_names(targets)

        return {
            'sources': list(sources),
            'targets': list(targets)
        }

    def _extract_source_tables(self, statement: exp.Expression) -> Set[str]:
        """
        Extract source tables (FROM, JOIN) from AST.

        Args:
            statement: Parsed SQLGlot expression

        Returns:
            Set of table names in schema.object_name format
        """
        tables = set()

        # Find all Table nodes
        for table in statement.find_all(exp.Table):
            table_name = self._get_table_name(table)
            if table_name:
                tables.add(table_name)

        return tables

    def _extract_target_tables(self, statement: exp.Expression) -> Set[str]:
        """
        Extract target tables (INSERT, UPDATE, MERGE) from AST.

        Args:
            statement: Parsed SQLGlot expression

        Returns:
            Set of table names in schema.object_name format
        """
        tables = set()

        # Find INSERT statements
        for insert in statement.find_all(exp.Insert):
            if insert.this:
                table_name = self._get_table_name(insert.this)
                if table_name:
                    tables.add(table_name)

        # Find UPDATE statements
        for update in statement.find_all(exp.Update):
            if update.this:
                table_name = self._get_table_name(update.this)
                if table_name:
                    tables.add(table_name)

        # Find MERGE statements
        for merge in statement.find_all(exp.Merge):
            if merge.this:
                table_name = self._get_table_name(merge.this)
                if table_name:
                    tables.add(table_name)

        # Find DELETE statements (also modifies tables)
        for delete in statement.find_all(exp.Delete):
            if delete.this:
                table_name = self._get_table_name(delete.this)
                if table_name:
                    tables.add(table_name)

        # Note: TRUNCATE is not a supported expression type in SQLGlot
        # TRUNCATE statements will not be detected automatically
        # This is a known limitation and will be handled by AI fallback if needed

        return tables

    def _get_table_name(self, table: exp.Table) -> Optional[str]:
        """
        Extract schema.object_name from Table node.

        Args:
            table: SQLGlot Table expression

        Returns:
            'schema.object_name' or None if invalid

        Handles:
        - dbo.Table1 → 'dbo.Table1'
        - Table1 → 'dbo.Table1' (assumes dbo schema)
        - [schema].[table] → 'schema.table' (strips brackets)
        """
        try:
            # Get table name (required)
            name = table.name
            if not name:
                return None

            # Strip brackets if present
            name = name.strip('[]')

            # Get schema (optional, defaults to dbo)
            schema = table.db if table.db else 'dbo'
            schema = schema.strip('[]')

            # Format as schema.object_name
            return f"{schema}.{name}"

        except Exception as e:
            logger.debug(f"Failed to extract table name: {e}")
            return None

    def _filter_table_names(self, table_names: Set[str]) -> Set[str]:
        """
        Filter out system tables, temp tables, and invalid names.

        Args:
            table_names: Set of table names

        Returns:
            Filtered set

        Excludes:
        - System schemas (sys, INFORMATION_SCHEMA)
        - Temp tables (#temp, ##global)
        - Table variables (@table)
        """
        filtered = set()

        for name in table_names:
            # Skip empty names
            if not name:
                continue

            # Parse schema.object_name
            parts = name.split('.')
            if len(parts) != 2:
                continue

            schema, obj_name = parts

            # Skip system schemas
            if schema in self.EXCLUDED_SCHEMAS:
                continue

            # Skip temp tables
            if obj_name.startswith('#') or obj_name.startswith('@'):
                continue

            filtered.add(name)

        return filtered

    def _resolve_table_names(self, table_names: List[str]) -> List[int]:
        """
        Resolve table names to object_ids.

        Args:
            table_names: List of table names (schema.table format)

        Returns:
            List of object_ids (excludes unresolved names)

        Uses case-insensitive matching for schema and object_name.
        """
        if not table_names:
            return []

        object_ids = []

        for name in table_names:
            # Parse schema.object_name
            parts = name.split('.')
            if len(parts) != 2:
                logger.debug(f"Invalid table name format: {name}")
                continue

            schema, obj_name = parts

            # Query workspace for object_id
            query = f"""
            SELECT object_id
            FROM objects
            WHERE LOWER(schema_name) = LOWER('{schema}')
              AND LOWER(object_name) = LOWER('{obj_name}')
            """

            results = self.workspace.query(query)

            if results:
                # Results are tuples: (object_id,)
                object_ids.append(results[0][0])
            else:
                logger.debug(f"Table not found: {name}")

        return object_ids

    def get_parse_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about parser coverage.

        Returns:
            {
                'total_parsed': int,
                'successful_parses': int,
                'failed_parses': int,
                'success_rate': float
            }
        """
        query = """
        SELECT
            COUNT(*) as total_parsed,
            SUM(CASE WHEN primary_source = 'parser' AND confidence > 0 THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN primary_source = 'parser' AND confidence = 0 THEN 1 ELSE 0 END) as failed
        FROM lineage_metadata
        WHERE primary_source = 'parser'
        """

        results = self.workspace.query(query)

        if not results:
            return {
                'total_parsed': 0,
                'successful_parses': 0,
                'failed_parses': 0,
                'success_rate': 0.0
            }

        # Results are tuples: (total_parsed, successful, failed)
        stats_tuple = results[0]
        total = stats_tuple[0]
        successful = stats_tuple[1]
        failed = stats_tuple[2]

        success_rate = (successful / total * 100) if total > 0 else 0.0

        return {
            'total_parsed': total,
            'successful_parses': successful,
            'failed_parses': failed,
            'success_rate': round(success_rate, 2)
        }
