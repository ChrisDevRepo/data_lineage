"""
Query Log Validator - Cross-validates parsed stored procedures with query log evidence.

This module provides runtime confirmation for static parsing results by checking
if parsed table dependencies appear in actual query execution logs.

Purpose:
    - Boost confidence for validated stored procedures (0.85 → 0.95)
    - Provide runtime confirmation of static parsing accuracy
    - No new lineage objects created (validation only)

Author: Claude Code
Date: 2025-10-27
Version: 1.0.0
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class QueryLogValidator:
    """
    Cross-validates parsed stored procedures with query log evidence.

    Only boosts confidence for existing lineage (no new objects created).
    Focus: Runtime confirmation of static parsing results.
    """

    def __init__(self, workspace):
        """
        Initialize validator with DuckDB workspace.

        Args:
            workspace: DuckDBWorkspace instance
        """
        self.workspace = workspace
        self._query_logs_available = None
        self._dml_queries = None

    def validate_parsed_objects(self) -> Dict[str, Any]:
        """
        Cross-validate parsed SPs with query log evidence.

        Returns:
            {
                'validated_objects': 6,
                'confidence_boosted': [(object_id, old_conf, new_conf), ...],
                'unvalidated_objects': 2,
                'total_matching_queries': 18,
                'skipped': False
            }
        """
        # Check if query logs are available
        if not self._check_query_logs_available():
            logger.info("Query logs not available - skipping validation")
            return {
                'validated_objects': 0,
                'confidence_boosted': [],
                'unvalidated_objects': 0,
                'total_matching_queries': 0,
                'skipped': True
            }

        # Get all high-confidence parsed SPs (≥0.85)
        parsed_sps = self._get_high_confidence_sps()

        if not parsed_sps:
            logger.info("No high-confidence SPs to validate")
            return {
                'validated_objects': 0,
                'confidence_boosted': [],
                'unvalidated_objects': 0,
                'total_matching_queries': 0,
                'skipped': False
            }

        logger.info(f"Validating {len(parsed_sps)} high-confidence stored procedures...")

        # Load all DML queries from query logs
        dml_queries = self._load_dml_queries()
        logger.info(f"Loaded {len(dml_queries)} DML queries from logs")

        validated_objects = []
        confidence_boosted = []
        total_matching_queries = 0

        for sp in parsed_sps:
            object_id = sp['object_id']
            old_confidence = sp['confidence']
            inputs = sp['inputs']
            outputs = sp['outputs']

            # Find matching queries
            matching_queries = self._find_matching_queries(
                object_id=object_id,
                inputs=inputs,
                outputs=outputs,
                dml_queries=dml_queries
            )

            if matching_queries:
                # Boost confidence: 0.85 → 0.95
                new_confidence = 0.95

                # Update lineage_metadata
                self._update_confidence(
                    object_id=object_id,
                    confidence=new_confidence,
                    validated_queries=len(matching_queries)
                )

                validated_objects.append(object_id)
                confidence_boosted.append((object_id, old_confidence, new_confidence))
                total_matching_queries += len(matching_queries)

                logger.debug(f"Validated object {object_id}: {old_confidence:.2f} → {new_confidence:.2f} "
                           f"({len(matching_queries)} matching queries)")

        unvalidated_count = len(parsed_sps) - len(validated_objects)

        logger.info(f"Validation complete: {len(validated_objects)} validated, {unvalidated_count} unvalidated")

        return {
            'validated_objects': len(validated_objects),
            'confidence_boosted': confidence_boosted,
            'unvalidated_objects': unvalidated_count,
            'total_matching_queries': total_matching_queries,
            'skipped': False
        }

    def _check_query_logs_available(self) -> bool:
        """Check if query_logs table exists and has data."""
        if self._query_logs_available is not None:
            return self._query_logs_available

        try:
            result = self.workspace.query("SELECT COUNT(*) FROM query_logs")
            count = result[0][0] if result else 0
            self._query_logs_available = count > 0
            logger.info(f"Query logs available: {count} entries")
        except Exception as e:
            logger.warning(f"Query logs table not available: {e}")
            self._query_logs_available = False

        return self._query_logs_available

    def _get_high_confidence_sps(self) -> List[Dict]:
        """Get all high-confidence parsed stored procedures (≥0.85)."""
        query = """
            SELECT
                lm.object_id,
                lm.confidence,
                lm.inputs,
                lm.outputs
            FROM lineage_metadata lm
            JOIN objects o ON lm.object_id = o.object_id
            WHERE o.object_type = 'Stored Procedure'
              AND lm.confidence >= 0.85
              AND lm.primary_source IN ('parser', 'dual_parser')
            ORDER BY lm.confidence DESC
        """

        results = self.workspace.query(query)

        sps = []
        for row in results:
            # Parse inputs/outputs (stored as string representation of list)
            inputs = eval(row[2]) if row[2] else []
            outputs = eval(row[3]) if row[3] else []

            sps.append({
                'object_id': row[0],
                'confidence': row[1],
                'inputs': inputs,
                'outputs': outputs
            })

        return sps

    def _load_dml_queries(self) -> List[str]:
        """Load DML statements from query logs (INSERT/UPDATE/MERGE)."""
        if self._dml_queries is not None:
            return self._dml_queries

        query = """
            SELECT DISTINCT command_text
            FROM query_logs
            WHERE command_text LIKE 'INSERT%'
               OR command_text LIKE 'UPDATE%'
               OR command_text LIKE 'MERGE%'
        """

        results = self.workspace.query(query)
        self._dml_queries = [row[0] for row in results if row[0]]

        return self._dml_queries

    def _find_matching_queries(
        self,
        object_id: int,
        inputs: List[int],
        outputs: List[int],
        dml_queries: List[str]
    ) -> List[str]:
        """
        Find query log entries that reference SP's tables.

        Args:
            object_id: Stored procedure object_id
            inputs: List of input table object_ids
            outputs: List of output table object_ids
            dml_queries: List of DML query texts

        Returns:
            List of matching query texts
        """
        # Get table names for SP's dependencies
        sp_tables = self._get_table_names(inputs + outputs)

        if not sp_tables:
            return []

        matching = []

        for query in dml_queries:
            # Extract tables from query text
            query_tables = self._extract_tables_from_query(query)

            # Filter out temp tables
            query_tables = self._filter_temp_tables(query_tables)

            # Check for overlap
            if sp_tables.intersection(query_tables):
                matching.append(query)

        return matching

    def _get_table_names(self, object_ids: List[int]) -> Set[str]:
        """
        Get schema.table names for given object_ids.

        Args:
            object_ids: List of object IDs

        Returns:
            Set of 'schema.table' strings
        """
        if not object_ids:
            return set()

        # Build query with placeholders
        placeholders = ','.join('?' * len(object_ids))
        query = f"""
            SELECT schema_name || '.' || object_name
            FROM objects
            WHERE object_id IN ({placeholders})
        """

        results = self.workspace.query(query, object_ids)
        return {row[0] for row in results if row[0]}

    def _extract_tables_from_query(self, query_text: str) -> Set[str]:
        """
        Extract table references from DML query using regex.

        Matches patterns like:
        - [SCHEMA].[TABLE]
        - SCHEMA.TABLE
        - [SCHEMA].TABLE
        - SCHEMA.[TABLE]

        Args:
            query_text: SQL query text

        Returns:
            Set of 'schema.table' strings (normalized, no brackets)
        """
        tables = set()

        # Pattern 1: [schema].[table] or schema.table (with optional brackets)
        pattern = r'\[?([A-Z_a-z][A-Z_a-z0-9]*)\]?\.\[?([A-Z_a-z][A-Z_a-z0-9]*)\]?'
        matches = re.findall(pattern, query_text)

        for schema, table in matches:
            # Normalize: remove brackets, standardize case
            schema = schema.strip('[]')
            table = table.strip('[]')

            # Skip system schemas and obvious non-tables
            if schema.lower() in ('sys', 'tempdb', 'master', 'model', 'msdb'):
                continue

            # Skip if looks like a function call (has parentheses nearby)
            # Simple heuristic: check if pattern is followed by '('
            full_pattern = f"{schema}.{table}"
            if re.search(rf'\b{re.escape(full_pattern)}\s*\(', query_text):
                continue

            tables.add(f"{schema}.{table}")

        return tables

    def _filter_temp_tables(self, tables: Set[str]) -> Set[str]:
        """
        Remove temp tables (contain #) from set.

        Args:
            tables: Set of table names

        Returns:
            Filtered set without temp tables
        """
        return {t for t in tables if '#' not in t and '@' not in t}

    def _update_confidence(
        self,
        object_id: int,
        confidence: float,
        validated_queries: int
    ) -> None:
        """
        Update lineage_metadata with boosted confidence.

        Args:
            object_id: Object to update
            confidence: New confidence value (0.95)
            validated_queries: Number of matching queries found
        """
        # Note: We don't have a validation_source or validated_queries column yet
        # For now, just update the confidence
        # TODO: Add these columns in future schema enhancement

        update_query = """
            UPDATE lineage_metadata
            SET confidence = ?
            WHERE object_id = ?
        """

        self.workspace.query(update_query, [confidence, object_id])
        logger.debug(f"Updated object {object_id} confidence to {confidence:.2f}")


# Module-level convenience function
def validate_with_query_logs(workspace) -> Dict[str, Any]:
    """
    Convenience function to validate parsed objects with query logs.

    Args:
        workspace: DuckDBWorkspace instance

    Returns:
        Validation results dictionary
    """
    validator = QueryLogValidator(workspace)
    return validator.validate_parsed_objects()
