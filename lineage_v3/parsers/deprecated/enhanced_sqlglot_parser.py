"""
Enhanced SQLGlot Parser - Improved T-SQL handling with preprocessing
=====================================================================

This module enhances the basic SQLGlot parser with:
1. DDL preprocessing and cleanup
2. Statement splitting (GO/semicolon)
3. T-SQL-specific handling
4. Object catalog validation
5. Robust error recovery

Based on best practices from:
- https://medium.com/@anupkumarray/sql-parsing-using-sqlglot-ad8a3c7fac59
- https://github.com/tobymao/sqlglot documentation

Author: Vibecoding
Version: 3.1.0
Date: 2025-10-26
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import sqlglot
from sqlglot import exp, parse_one, parse
import logging
import re

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from lineage_v3.utils.validators import validate_object_id, sanitize_identifier


# Configure logging
logger = logging.getLogger(__name__)


class EnhancedSQLGlotParser:
    """
    Enhanced T-SQL parser with preprocessing and robust error handling.

    Key improvements:
    1. DDL preprocessing (remove control flow, clean syntax)
    2. Statement-by-statement parsing (split on GO/semicolon)
    3. Object catalog validation
    4. Fallback strategies for complex patterns
    """

    # Confidence score for static AST analysis
    CONFIDENCE = 0.85

    # System schemas to exclude
    EXCLUDED_SCHEMAS = {'sys', 'INFORMATION_SCHEMA'}

    # T-SQL control flow keywords to remove/simplify
    CONTROL_FLOW_PATTERNS = [
        # IF statements
        (r'\bIF\s+OBJECT_ID\s*\([^)]+\)\s+IS\s+NOT\s+NULL\s+BEGIN\s+DROP\s+TABLE\s+[^;]+;\s*END',
         '-- IF removed'),
        (r'\bIF\s+OBJECT_ID\s*\([^)]+\)\s+IS\s+NOT\s+NULL\s+DROP\s+TABLE\s+[^;]+;?',
         '-- IF removed'),

        # BEGIN/END blocks (but keep transaction blocks)
        (r'\bBEGIN\s+TRY\b', 'BEGIN /* TRY */'),
        (r'\bEND\s+TRY\b', 'END /* TRY */'),
        (r'\bBEGIN\s+CATCH\b', 'BEGIN /* CATCH */'),
        (r'\bEND\s+CATCH\b', 'END /* CATCH */'),

        # RAISERROR statements
        (r'\bRAISERROR\s*\([^)]+\)', '-- RAISERROR removed'),

        # PRINT statements
        (r'\bPRINT\s+[^\n;]+', '-- PRINT removed'),

        # DECLARE statements (keep variables for context)
        # Don't remove - they might be table variables
    ]

    def __init__(self, workspace: DuckDBWorkspace):
        """
        Initialize enhanced parser with DuckDB workspace.

        Args:
            workspace: DuckDBWorkspace instance with initialized database
        """
        self.workspace = workspace
        self._object_catalog = None  # Lazy-loaded object catalog

    def parse_object(self, object_id: int) -> Dict[str, Any]:
        """
        Parse DDL for a single object with enhanced preprocessing.

        Args:
            object_id: Object to parse

        Returns:
            {
                'object_id': int,
                'inputs': List[int],   # source tables (FROM/JOIN)
                'outputs': List[int],  # target tables (INSERT/UPDATE/MERGE)
                'confidence': 0.85,
                'source': 'parser',
                'parse_error': Optional[str],
                'debug_info': Dict  # For troubleshooting
            }
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

        # Preprocess DDL
        try:
            cleaned_ddl = self._preprocess_ddl(ddl)

            # Extract table references using multiple strategies
            references = self._extract_table_references_multi_strategy(cleaned_ddl, ddl)

            # Validate against object catalog
            validated_sources = self._validate_against_catalog(references['sources'])
            validated_targets = self._validate_against_catalog(references['targets'])

            # Resolve table names to object_ids
            input_ids = self._resolve_table_names(validated_sources)
            output_ids = self._resolve_table_names(validated_targets)

            return {
                'object_id': object_id,
                'inputs': input_ids,
                'outputs': output_ids,
                'confidence': self.CONFIDENCE,
                'source': 'parser',
                'parse_error': None,
                'debug_info': {
                    'sources_found': len(validated_sources),
                    'targets_found': len(validated_targets),
                    'sources': list(validated_sources),
                    'targets': list(validated_targets)
                }
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

    def _preprocess_ddl(self, ddl: str) -> str:
        """
        Preprocess DDL to make it more parseable.

        Steps:
        1. Remove CREATE PROC wrapper
        2. Remove control flow statements (IF, BEGIN TRY, RAISERROR, etc.)
        3. Split on GO statements
        4. Clean up ANSI escape codes
        5. Normalize whitespace

        Args:
            ddl: Raw DDL text

        Returns:
            Cleaned DDL text
        """
        cleaned = ddl

        # Remove ANSI escape codes (e.g., [4m, [0m)
        cleaned = re.sub(r'\x1b\[[0-9;]+m', '', cleaned)
        cleaned = re.sub(r'\[4m', '', cleaned)
        cleaned = re.sub(r'\[0m', '', cleaned)

        # Remove CREATE PROC header (keep only body)
        # Pattern: CREATE PROC [schema].[name] AS BEGIN ... END
        match = re.search(r'CREATE\s+PROC(?:EDURE)?\s+\[[^\]]+\]\.\[[^\]]+\]\s+AS\s+BEGIN',
                         cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            # Remove up to AS BEGIN
            cleaned = cleaned[match.end():]

            # Remove trailing END
            cleaned = re.sub(r'\s*END\s*$', '', cleaned, flags=re.IGNORECASE)

        # Apply control flow removal patterns
        for pattern, replacement in self.CONTROL_FLOW_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.DOTALL)

        # Normalize whitespace
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # Remove blank lines
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces

        return cleaned.strip()

    def _split_statements(self, sql: str) -> List[str]:
        """
        Split SQL into individual statements.

        Splits on:
        1. GO statements (T-SQL batch separator)
        2. Semicolons (standard SQL separator)

        Args:
            sql: SQL text

        Returns:
            List of individual statements
        """
        statements = []

        # First split on GO (case-insensitive, whole word)
        batches = re.split(r'\bGO\b', sql, flags=re.IGNORECASE)

        for batch in batches:
            batch = batch.strip()
            if not batch:
                continue

            # Split batch on semicolons (but not inside strings)
            # Simple heuristic: split on ; followed by whitespace or newline
            parts = re.split(r';\s*(?=\S)', batch)

            for part in parts:
                part = part.strip()
                if part and not part.startswith('--'):
                    statements.append(part)

        return statements

    def _extract_table_references_multi_strategy(
        self,
        cleaned_ddl: str,
        original_ddl: str
    ) -> Dict[str, Set[str]]:
        """
        Extract table references using multiple strategies.

        Strategy 1: Parse cleaned DDL statement-by-statement
        Strategy 2: Regex extraction from original DDL (fallback)
        Strategy 3: Merge results with validation

        Args:
            cleaned_ddl: Preprocessed DDL
            original_ddl: Original DDL text

        Returns:
            {
                'sources': Set[str],  # Tables read from
                'targets': Set[str]   # Tables written to
            }
        """
        sources = set()
        targets = set()

        # Strategy 1: Parse cleaned DDL statement-by-statement
        statements = self._split_statements(cleaned_ddl)

        for stmt in statements:
            try:
                # Try to parse with SQLGlot
                parsed = parse_one(stmt, dialect='tsql', error_level=None)

                if parsed:
                    # Extract from AST
                    stmt_sources, stmt_targets = self._extract_from_ast(parsed)
                    sources.update(stmt_sources)
                    targets.update(stmt_targets)
            except Exception as e:
                logger.debug(f"Failed to parse statement with SQLGlot: {e}")
                # Try regex fallback for this statement
                regex_sources, regex_targets = self._extract_with_regex(stmt)
                sources.update(regex_sources)
                targets.update(regex_targets)

        # Strategy 2: Regex extraction from original DDL (fallback)
        if not sources and not targets:
            logger.debug("SQLGlot parsing failed, using regex fallback")
            sources, targets = self._extract_with_regex(original_ddl)

        return {
            'sources': sources,
            'targets': targets
        }

    def _extract_from_ast(self, parsed: exp.Expression) -> Tuple[Set[str], Set[str]]:
        """
        Extract table references from SQLGlot AST.

        Args:
            parsed: Parsed SQLGlot expression

        Returns:
            (sources, targets) tuple of sets
        """
        sources = set()
        targets = set()

        # Extract source tables (FROM, JOIN)
        for table in parsed.find_all(exp.Table):
            table_name = self._get_table_name(table)
            if table_name:
                sources.add(table_name)

        # Extract target tables (INSERT, UPDATE, MERGE, DELETE)
        for insert in parsed.find_all(exp.Insert):
            if insert.this:
                table_name = self._get_table_name(insert.this)
                if table_name:
                    targets.add(table_name)

        for update in parsed.find_all(exp.Update):
            if update.this:
                table_name = self._get_table_name(update.this)
                if table_name:
                    targets.add(table_name)

        for merge in parsed.find_all(exp.Merge):
            if merge.this:
                table_name = self._get_table_name(merge.this)
                if table_name:
                    targets.add(table_name)

        for delete in parsed.find_all(exp.Delete):
            if delete.this:
                table_name = self._get_table_name(delete.this)
                if table_name:
                    targets.add(table_name)

        # TRUNCATE is not always supported, but check for it
        # Look for TRUNCATE keyword manually in original statement

        return sources, targets

    def _extract_with_regex(self, sql: str) -> Tuple[Set[str], Set[str]]:
        """
        Extract table references using regex patterns (fallback).

        Patterns:
        - FROM [schema].[table]
        - JOIN [schema].[table]
        - INSERT INTO [schema].[table]
        - UPDATE [schema].[table]
        - MERGE INTO [schema].[table]
        - TRUNCATE TABLE [schema].[table]

        Args:
            sql: SQL text

        Returns:
            (sources, targets) tuple of sets
        """
        sources = set()
        targets = set()

        # Source patterns (FROM, JOIN)
        source_patterns = [
            r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bJOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bINNER\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bLEFT\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bRIGHT\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bFULL\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?',
        ]

        for pattern in source_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for schema, table in matches:
                sources.add(f"{schema}.{table}")

        # Target patterns (INSERT, UPDATE, MERGE, TRUNCATE)
        target_patterns = [
            r'\bINSERT\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bUPDATE\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bMERGE\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?',
            r'\bTRUNCATE\s+TABLE\s+\[?(\w+)\]?\.\[?(\w+)\]?',
        ]

        for pattern in target_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for schema, table in matches:
                targets.add(f"{schema}.{table}")

        return sources, targets

    def _get_object_catalog(self) -> Set[str]:
        """
        Get set of all valid table names from workspace.

        Returns:
            Set of 'schema.table' strings
        """
        if self._object_catalog is None:
            query = """
                SELECT schema_name || '.' || object_name as full_name
                FROM objects
                WHERE object_type IN ('Table', 'View')
            """
            results = self.workspace.query(query)
            self._object_catalog = {row[0] for row in results}
            logger.debug(f"Loaded object catalog: {len(self._object_catalog)} objects")

        return self._object_catalog

    def _validate_against_catalog(self, table_names: Set[str]) -> Set[str]:
        """
        Validate table names against object catalog.

        Only return tables that actually exist in the database.
        This filters out temp tables, variables, and typos.

        Args:
            table_names: Set of table names to validate

        Returns:
            Filtered set of valid table names
        """
        catalog = self._get_object_catalog()
        validated = set()

        for name in table_names:
            # Check exact match
            if name in catalog:
                validated.add(name)
            else:
                # Try case-insensitive match
                name_lower = name.lower()
                for catalog_name in catalog:
                    if catalog_name.lower() == name_lower:
                        validated.add(catalog_name)
                        break

        if len(validated) < len(table_names):
            invalid = table_names - validated
            logger.debug(f"Filtered out invalid table names: {invalid}")

        return validated

    def _get_table_name(self, table: exp.Table) -> Optional[str]:
        """
        Extract schema.object_name from Table node.

        Args:
            table: SQLGlot Table expression

        Returns:
            'schema.object_name' or None if invalid
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

    def _fetch_ddl(self, object_id: int) -> Optional[str]:
        """
        Fetch DDL definition from workspace.

        Args:
            object_id: Object to fetch

        Returns:
            DDL text or None if not found
        """
        # Validate object_id (defense in depth)
        validated_id = validate_object_id(object_id)

        query = f"""
        SELECT definition
        FROM definitions
        WHERE object_id = {validated_id}
        """

        results = self.workspace.query(query)

        if not results:
            return None

        # Results are tuples: (definition,)
        return results[0][0]

    def _resolve_table_names(self, table_names: Set[str]) -> List[int]:
        """
        Resolve table names to object_ids.

        Args:
            table_names: Set of table names (schema.table format)

        Returns:
            List of object_ids (excludes unresolved names)
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

            # Sanitize identifiers (defense in depth)
            try:
                schema = sanitize_identifier(schema)
                obj_name = sanitize_identifier(obj_name)
            except ValueError as e:
                logger.warning(f"Invalid identifier: {e}")
                continue

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
