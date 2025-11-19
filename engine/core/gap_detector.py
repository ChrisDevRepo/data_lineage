"""
Gap Detector - Identifies objects with missing dependencies

This module identifies stored procedures, tables, and views that have no
resolved dependencies in the lineage_metadata table. These "gaps" need to
be filled by the SQLGlot parser or AI fallback.

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-26
"""

from typing import List, Dict, Any, Optional
from .duckdb_workspace import DuckDBWorkspace
from ..utils.validators import validate_object_type


class GapDetector:
    """
    Detects objects with missing or incomplete lineage dependencies.

    A "gap" is defined as:
    1. Object exists in objects table
    2. Object has no entry in lineage_metadata (never parsed)
    3. OR object has entry but inputs=[] AND outputs=[] (no dependencies found)

    Primary use case: Identify stored procedures that need SQLGlot parsing
    after DMV extraction fails to find dependencies.
    """

    def __init__(self, workspace: DuckDBWorkspace):
        """
        Initialize gap detector with DuckDB workspace.

        Args:
            workspace: DuckDBWorkspace instance with initialized database
        """
        self.workspace = workspace

    def detect_gaps(
        self,
        object_type: Optional[str] = "Stored Procedure"
    ) -> List[Dict[str, Any]]:
        """
        Find objects with no resolved dependencies.

        Args:
            object_type: Filter by object type (default: "Stored Procedure")
                        Set to None to include all object types

        Returns:
            List of dicts with:
            - object_id: int
            - schema_name: str
            - object_name: str
            - object_type: str
            - modify_date: str (ISO format)

        Example:
            >>> detector = GapDetector(workspace)
            >>> gaps = detector.detect_gaps()
            >>> print(f"Found {len(gaps)} gaps")
            Found 42 gaps
        """
        query = """
        SELECT
            o.object_id,
            o.schema_name,
            o.object_name,
            o.object_type,
            o.modify_date
        FROM objects o
        LEFT JOIN lineage_metadata m ON o.object_id = m.object_id
        WHERE
            (
                m.object_id IS NULL  -- Never parsed
                OR (m.inputs = '[]' AND m.outputs = '[]')  -- No dependencies found
            )
        """

        # Add object_type filter if specified
        if object_type is not None:
            # Validate to prevent SQL injection (defense in depth)
            validated_type = validate_object_type(object_type)
            query += f"\n    AND o.object_type = '{validated_type}'"

        query += "\nORDER BY o.schema_name, o.object_name"

        results = self.workspace.query(query)

        # Convert tuples to dictionaries
        return [
            {
                'object_id': row[0],
                'schema_name': row[1],
                'object_name': row[2],
                'object_type': row[3],
                'modify_date': row[4]
            }
            for row in results
        ]

    def detect_low_confidence_gaps(
        self,
        confidence_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Find objects with low-confidence lineage that need re-parsing.

        Args:
            confidence_threshold: Minimum acceptable confidence (default: 0.85)

        Returns:
            List of dicts with same format as detect_gaps()

        Use case: Find objects that need AI fallback after SQLGlot parsing
        """
        query = f"""
        SELECT
            o.object_id,
            o.schema_name,
            o.object_name,
            o.object_type,
            o.modify_date,
            m.parse_success,
            m.primary_source
        FROM objects o
        INNER JOIN lineage_metadata m ON o.object_id = m.object_id
        WHERE
            m.parse_success = false
        ORDER BY o.schema_name, o.object_name
        """

        results = self.workspace.query(query)

        # Convert tuples to dictionaries
        return [
            {
                'object_id': row[0],
                'schema_name': row[1],
                'object_name': row[2],
                'object_type': row[3],
                'modify_date': row[4],
                'parse_success': row[5],
                'primary_source': row[6]
            }
            for row in results
        ]

    def get_gap_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about gaps in the lineage.

        Returns:
            Dict with:
            - total_objects: Total count in objects table
            - parsed_objects: Count with metadata entries
            - unparsed_objects: Count with no metadata
            - empty_dependencies: Count with metadata but no deps
            - total_gaps: unparsed + empty_dependencies
            - gap_percentage: (total_gaps / total_objects) * 100
            - by_object_type: Breakdown by object type

        Example:
            >>> stats = detector.get_gap_statistics()
            >>> print(f"Gap coverage: {stats['gap_percentage']:.1f}%")
            Gap coverage: 12.5%
        """
        # Overall statistics
        overall_query = """
        SELECT
            COUNT(*) as total_objects,
            COUNT(m.object_id) as parsed_objects,
            COUNT(*) - COUNT(m.object_id) as unparsed_objects,
            SUM(CASE WHEN m.inputs = '[]' AND m.outputs = '[]' THEN 1 ELSE 0 END) as empty_dependencies
        FROM objects o
        LEFT JOIN lineage_metadata m ON o.object_id = m.object_id
        """

        overall_stats_tuple = self.workspace.query(overall_query)[0]

        # Convert tuple to dict
        overall_stats = {
            'total_objects': overall_stats_tuple[0],
            'parsed_objects': overall_stats_tuple[1],
            'unparsed_objects': overall_stats_tuple[2],
            'empty_dependencies': overall_stats_tuple[3]
        }

        total_gaps = (
            overall_stats['unparsed_objects'] +
            overall_stats['empty_dependencies']
        )

        gap_percentage = (
            (total_gaps / overall_stats['total_objects'] * 100)
            if overall_stats['total_objects'] > 0
            else 0.0
        )

        # By object type
        by_type_query = """
        SELECT
            o.object_type,
            COUNT(*) as total,
            COUNT(m.object_id) as parsed,
            COUNT(*) - COUNT(m.object_id) as unparsed,
            SUM(CASE WHEN m.inputs = '[]' AND m.outputs = '[]' THEN 1 ELSE 0 END) as empty
        FROM objects o
        LEFT JOIN lineage_metadata m ON o.object_id = m.object_id
        GROUP BY o.object_type
        ORDER BY total DESC
        """

        by_type_tuples = self.workspace.query(by_type_query)

        # Convert tuples to dicts
        by_type = [
            {
                'object_type': row[0],
                'total': row[1],
                'parsed': row[2],
                'unparsed': row[3],
                'empty': row[4]
            }
            for row in by_type_tuples
        ]

        return {
            'total_objects': overall_stats['total_objects'],
            'parsed_objects': overall_stats['parsed_objects'],
            'unparsed_objects': overall_stats['unparsed_objects'],
            'empty_dependencies': overall_stats['empty_dependencies'],
            'total_gaps': total_gaps,
            'gap_percentage': round(gap_percentage, 2),
            'by_object_type': by_type
        }

    def should_parse(
        self,
        object_id: int,
        force_reparse: bool = False
    ) -> bool:
        """
        Determine if an object should be parsed.

        Args:
            object_id: Object to check
            force_reparse: Ignore modify_date check (default: False)

        Returns:
            True if object should be parsed, False otherwise

        Logic:
        - If no metadata: True (never parsed)
        - If force_reparse: True
        - If modify_date > last_parsed_modify_date: True (object changed)
        - Otherwise: False (already parsed and up-to-date)
        """
        query = f"""
        SELECT
            o.modify_date as current_modify_date,
            m.last_parsed_modify_date,
            m.confidence
        FROM objects o
        LEFT JOIN lineage_metadata m ON o.object_id = m.object_id
        WHERE o.object_id = {object_id}
        """

        results = self.workspace.query(query)

        if not results:
            return False  # Object doesn't exist

        obj = results[0]

        # Never parsed
        if obj['last_parsed_modify_date'] is None:
            return True

        # Force reparse
        if force_reparse:
            return True

        # Object modified since last parse
        if obj['current_modify_date'] > obj['last_parsed_modify_date']:
            return True

        return False
