"""
MetricsService - Single Source of Truth for All Lineage Metrics
================================================================

This is the ONLY place where lineage metrics should be calculated.
All consumers MUST use this service to ensure consistency.

Author: Vibecoding Data Lineage Team
Date: 2025-11-02
"""

from typing import Dict, Any, Optional, List
import logging
from engine.core.duckdb_workspace import DuckDBWorkspace

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Single source of truth for all lineage metrics.

    All CLI, JSON, tests, and subagents MUST use this service.
    This ensures consistency and avoids confusion.
    """

    def __init__(self, workspace: DuckDBWorkspace):
        """
        Initialize metrics service.

        Args:
            workspace: DuckDB workspace instance
        """
        self.workspace = workspace

    def get_parse_metrics(self, object_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get parse metrics with clear scope.

        This is the primary method for getting lineage metrics.
        All consumers should use this method.

        Args:
            object_type: Filter by type ('Stored Procedure', 'View', 'Table')
                        None = ALL objects

        Returns:
            {
                'scope': 'Stored Procedure' | 'View' | 'Table' | 'ALL',
                'total': 202,
                'parsed': 201,
                'parse_rate': 99.5,
                'confidence': {
                    'high': {'count': 170, 'pct': 84.2, 'threshold': '≥0.75'},
                    'medium': {'count': 0, 'pct': 0.0, 'threshold': '0.65-0.74'},
                    'low': {'count': 32, 'pct': 15.8, 'threshold': '<0.65'}
                },
                'by_source': {
                    'parser': 160,
                    'dmv': 41,
                    'metadata': 0
                }
            }
        """
        # Check if lineage_metadata exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'lineage_metadata' not in tables:
            logger.warning("lineage_metadata not found - returning empty metrics")
            return self._empty_metrics(object_type)

        # Build query with optional object_type filter
        where_clause = ""
        if object_type:
            where_clause = f"WHERE o.object_type = '{object_type}'"

        query = f"""
        SELECT
            -- Counts
            COUNT(*) as total,
            COUNT(CASE WHEN lm.confidence IS NOT NULL THEN 1 END) as parsed,

            -- Confidence distribution
            COUNT(CASE WHEN lm.confidence >= 0.75 THEN 1 END) as high_confidence,
            COUNT(CASE WHEN lm.confidence >= 0.65 AND lm.confidence < 0.75 THEN 1 END) as medium_confidence,
            COUNT(CASE WHEN lm.confidence < 0.65 THEN 1 END) as low_confidence,

            -- Source distribution
            COUNT(CASE WHEN lm.primary_source = 'parser' THEN 1 END) as source_parser,
            COUNT(CASE WHEN lm.primary_source = 'dmv' THEN 1 END) as source_dmv,
            COUNT(CASE WHEN lm.primary_source = 'metadata' THEN 1 END) as source_metadata

        FROM objects o
        LEFT JOIN lineage_metadata lm ON o.object_id = lm.object_id
        {where_clause}
        """

        result = self.workspace.query(query)

        if not result or not result[0]:
            return self._empty_metrics(object_type)

        row = result[0]

        total = row[0] or 0
        parsed = row[1] or 0
        high_conf = row[2] or 0
        medium_conf = row[3] or 0
        low_conf = row[4] or 0
        source_parser = row[5] or 0
        source_dmv = row[6] or 0
        source_metadata = row[7] or 0

        # Calculate percentages
        parse_rate = (parsed / total * 100) if total > 0 else 0.0
        high_pct = (high_conf / total * 100) if total > 0 else 0.0
        medium_pct = (medium_conf / total * 100) if total > 0 else 0.0
        low_pct = (low_conf / total * 100) if total > 0 else 0.0

        return {
            'scope': object_type or 'ALL',
            'total': total,
            'parsed': parsed,
            'parse_rate': round(parse_rate, 1),
            'confidence': {
                'high': {
                    'count': high_conf,
                    'pct': round(high_pct, 1),
                    'threshold': '≥0.75'
                },
                'medium': {
                    'count': medium_conf,
                    'pct': round(medium_pct, 1),
                    'threshold': '0.65-0.74'
                },
                'low': {
                    'count': low_conf,
                    'pct': round(low_pct, 1),
                    'threshold': '<0.65'
                }
            },
            'by_source': {
                'parser': source_parser,
                'dmv': source_dmv,
                'metadata': source_metadata
            }
        }

    def get_dependency_metrics(self) -> Dict[str, Any]:
        """
        Get dependency relationship metrics.

        Returns:
            {
                'sp_to_sp': 62,
                'sp_to_table': 584,
                'sp_to_view': 23,
                'view_to_table': 259,
                'view_to_view': 5,
                'total': 933
            }
        """
        # Check if dependencies table exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'dependencies' not in tables:
            logger.warning("dependencies table not found - returning empty metrics")
            return {
                'sp_to_sp': 0,
                'sp_to_table': 0,
                'sp_to_view': 0,
                'view_to_table': 0,
                'view_to_view': 0,
                'total': 0
            }

        query = """
        SELECT
            COUNT(CASE
                WHEN o1.object_type = 'Stored Procedure'
                AND o2.object_type = 'Stored Procedure' THEN 1
            END) as sp_to_sp,

            COUNT(CASE
                WHEN o1.object_type = 'Stored Procedure'
                AND o2.object_type = 'Table' THEN 1
            END) as sp_to_table,

            COUNT(CASE
                WHEN o1.object_type = 'Stored Procedure'
                AND o2.object_type = 'View' THEN 1
            END) as sp_to_view,

            COUNT(CASE
                WHEN o1.object_type = 'View'
                AND o2.object_type = 'Table' THEN 1
            END) as view_to_table,

            COUNT(CASE
                WHEN o1.object_type = 'View'
                AND o2.object_type = 'View' THEN 1
            END) as view_to_view,

            COUNT(*) as total

        FROM dependencies d
        JOIN objects o1 ON d.referencing_object_id = o1.object_id
        JOIN objects o2 ON d.referenced_object_id = o2.object_id
        """

        result = self.workspace.query(query)

        if not result or not result[0]:
            return {
                'sp_to_sp': 0,
                'sp_to_table': 0,
                'sp_to_view': 0,
                'view_to_table': 0,
                'view_to_view': 0,
                'total': 0
            }

        row = result[0]

        return {
            'sp_to_sp': row[0] or 0,
            'sp_to_table': row[1] or 0,
            'sp_to_view': row[2] or 0,
            'view_to_table': row[3] or 0,
            'view_to_view': row[4] or 0,
            'total': row[5] or 0
        }

    def get_isolation_metrics(self) -> Dict[str, Any]:
        """
        Get isolated objects metrics.

        Returns:
            {
                'total_isolated': 411,
                'by_type': {
                    'Stored Procedure': 5,
                    'Table': 400,
                    'View': 6
                },
                'isolation_rate': 53.8  # % of all objects
            }
        """
        # Check if required tables exist
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'objects' not in tables or 'dependencies' not in tables:
            logger.warning("Required tables not found - returning empty metrics")
            return {
                'total_isolated': 0,
                'by_type': {},
                'isolation_rate': 0.0
            }

        # Get isolated objects by type
        query = """
        SELECT
            object_type,
            COUNT(*) as count
        FROM objects
        WHERE object_id NOT IN (
            SELECT DISTINCT referencing_object_id FROM dependencies
            UNION
            SELECT DISTINCT referenced_object_id FROM dependencies
        )
        GROUP BY object_type
        """

        result = self.workspace.query(query)

        by_type = {}
        total_isolated = 0

        for row in result:
            obj_type = row[0]
            count = row[1] or 0
            by_type[obj_type] = count
            total_isolated += count

        # Get total objects for isolation rate
        total_objects_result = self.workspace.query("SELECT COUNT(*) FROM objects")
        total_objects = total_objects_result[0][0] if total_objects_result else 0

        isolation_rate = (total_isolated / total_objects * 100) if total_objects > 0 else 0.0

        return {
            'total_isolated': total_isolated,
            'by_type': by_type,
            'isolation_rate': round(isolation_rate, 1)
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in one call.

        This is useful for generating comprehensive reports.

        Returns:
            {
                'overall': {...},  # All objects
                'by_object_type': {
                    'stored_procedures': {...},
                    'views': {...},
                    'tables': {...}
                },
                'dependencies': {...},
                'isolation': {...}
            }
        """
        return {
            'overall': self.get_parse_metrics(object_type=None),
            'by_object_type': {
                'stored_procedures': self.get_parse_metrics(object_type='Stored Procedure'),
                'views': self.get_parse_metrics(object_type='View'),
                'tables': self.get_parse_metrics(object_type='Table')
            },
            'dependencies': self.get_dependency_metrics(),
            'isolation': self.get_isolation_metrics()
        }

    def _empty_metrics(self, object_type: Optional[str] = None) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            'scope': object_type or 'ALL',
            'total': 0,
            'parsed': 0,
            'parse_rate': 0.0,
            'confidence': {
                'high': {'count': 0, 'pct': 0.0, 'threshold': '≥0.75'},
                'medium': {'count': 0, 'pct': 0.0, 'threshold': '0.65-0.74'},
                'low': {'count': 0, 'pct': 0.0, 'threshold': '<0.65'}
            },
            'by_source': {
                'parser': 0,
                'dmv': 0,
                'metadata': 0
            }
        }
