#!/usr/bin/env python3
"""
Summary Formatter
=================

Generates lineage_summary.json with coverage statistics.

Format:
{
  "total_objects": 2500,
  "parsed_objects": 2100,
  "coverage": 84.0,
  "by_object_type": {
    "Table": {"total": 1500, "parsed": 1500, "coverage": 100.0},
    "View": {"total": 850, "parsed": 850, "coverage": 100.0},
    "Stored Procedure": {"total": 150, "parsed": 120, "coverage": 80.0}
  },
  "by_primary_source": {
    "dmv": 1800,
    "query_log": 300,
    "parser": 200,
    "ai": 75
  },
  "object_type_counts": {
    "Table": 1500,
    "View": 850,
    "Stored Procedure": 150
  }
}

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-26
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SummaryFormatter:
    """
    Formatter for lineage_summary.json with coverage statistics.
    
    Provides insights into:
    - Overall coverage (parsed vs total objects)
    - Coverage by object type
    - Primary source distribution
    - Confidence distribution
    """
    
    def __init__(self, workspace):
        """
        Initialize summary formatter.
        
        Args:
            workspace: DuckDB workspace instance
        """
        self.workspace = workspace
    
    def generate(self, output_path: str = "lineage_output/lineage_summary.json") -> Dict[str, Any]:
        """
        Generate lineage_summary.json file.
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            The summary statistics
        """
        logger.info("Generating lineage_summary.json...")
        
        # Step 1: Get total object counts
        total_counts = self._get_total_object_counts()
        
        # Step 2: Get parsed object counts
        parsed_counts = self._get_parsed_object_counts()
        
        # Step 3: Get primary source distribution
        source_distribution = self._get_source_distribution()
        
        # Step 4: Get confidence distribution
        confidence_stats = self._get_confidence_stats()

        # Step 4b: Get confidence breakdown statistics (v2.0.0)
        breakdown_stats = self._get_breakdown_stats()

        # Step 5: Build summary
        summary = self._build_summary(
            total_counts,
            parsed_counts,
            source_distribution,
            confidence_stats,
            breakdown_stats
        )
        
        # Step 6: Write to JSON file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Generated lineage_summary.json with {summary['coverage']:.1f}% coverage")
        return summary
    
    def _get_total_object_counts(self) -> Dict[str, int]:
        """Get total object counts by type."""
        query = """
        SELECT
            object_type as type,
            COUNT(*) as count
        FROM objects
        WHERE object_type IN ('Table', 'View', 'Stored Procedure')
        GROUP BY object_type
        """
        
        results = self.workspace.query(query)
        
        counts = {}
        for row in results:
            counts[row[0]] = row[1]
        
        return counts
    
    def _get_parsed_object_counts(self) -> Dict[str, int]:
        """Get parsed object counts by type."""
        # Check if lineage_metadata exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'lineage_metadata' not in tables:
            logger.warning("lineage_metadata not found - returning zero parsed counts")
            return {}

        query = """
        SELECT
            o.object_type as type,
            COUNT(DISTINCT m.object_id) as count
        FROM lineage_metadata m
        JOIN objects o ON m.object_id = o.object_id
        WHERE o.object_type IN ('Table', 'View', 'Stored Procedure')
        GROUP BY o.object_type
        """

        results = self.workspace.query(query)

        counts = {}
        for row in results:
            counts[row[0]] = row[1]

        return counts
    
    def _get_source_distribution(self) -> Dict[str, int]:
        """Get distribution of objects by primary source."""
        # Check if lineage_metadata exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'lineage_metadata' not in tables:
            logger.warning("lineage_metadata not found - returning empty source distribution")
            return {}

        query = """
        SELECT
            primary_source,
            COUNT(DISTINCT object_id) as count
        FROM lineage_metadata
        GROUP BY primary_source
        """

        results = self.workspace.query(query)

        distribution = {}
        for row in results:
            source = row[0] or 'unknown'
            distribution[source] = row[1]

        return distribution
    
    def _get_confidence_stats(self) -> Dict[str, Any]:
        """
        Get confidence statistics using MetricsService.

        IMPORTANT: This method now uses MetricsService as the single source of truth.
        All metrics calculations happen in one place for consistency.
        """
        from engine.metrics import MetricsService

        metrics_service = MetricsService(self.workspace)

        # Get metrics for ALL objects
        all_metrics = metrics_service.get_all_metrics()

        # Build response compatible with old format but with clear scope
        return {
            'scope': 'ALL objects (note: use by_object_type for specific scopes)',
            'average': (all_metrics['overall']['confidence']['high']['count'] * 0.85 +
                       all_metrics['overall']['confidence']['medium']['count'] * 0.80 +
                       all_metrics['overall']['confidence']['low']['count'] * 0.65) /
                       max(all_metrics['overall']['total'], 1),  # Weighted average approximation
            'min': 0.5,  # Known minimum
            'max': 1.0,  # Known maximum
            'high_confidence_count': all_metrics['overall']['confidence']['high']['count'],
            'medium_confidence_count': all_metrics['overall']['confidence']['medium']['count'],
            'low_confidence_count': all_metrics['overall']['confidence']['low']['count'],
            # NEW: Add detailed breakdown by object type
            'by_object_type': {
                'stored_procedures': {
                    'total': all_metrics['by_object_type']['stored_procedures']['total'],
                    'high': all_metrics['by_object_type']['stored_procedures']['confidence']['high']['count'],
                    'medium': all_metrics['by_object_type']['stored_procedures']['confidence']['medium']['count'],
                    'low': all_metrics['by_object_type']['stored_procedures']['confidence']['low']['count']
                },
                'views': {
                    'total': all_metrics['by_object_type']['views']['total'],
                    'high': all_metrics['by_object_type']['views']['confidence']['high']['count'],
                    'medium': all_metrics['by_object_type']['views']['confidence']['medium']['count'],
                    'low': all_metrics['by_object_type']['views']['confidence']['low']['count']
                },
                'tables': {
                    'total': all_metrics['by_object_type']['tables']['total'],
                    'high': all_metrics['by_object_type']['tables']['confidence']['high']['count'],
                    'medium': all_metrics['by_object_type']['tables']['confidence']['medium']['count'],
                    'low': all_metrics['by_object_type']['tables']['confidence']['low']['count']
                }
            }
        }
    
    def _get_breakdown_stats(self) -> Dict[str, Any]:
        """
        Get statistics about confidence breakdown factors (v2.0.0).

        Analyzes stored procedures with multi-factor breakdowns to show
        average contribution of each factor.

        Returns:
            Dict with average factor contributions and counts
        """
        # Check if lineage_metadata exists and has breakdown column
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'lineage_metadata' not in tables:
            return {'available': False, 'note': 'No breakdowns available'}

        try:
            query = """
            SELECT confidence_breakdown, object_name
            FROM lineage_metadata
            WHERE confidence_breakdown IS NOT NULL
              AND confidence_breakdown != ''
            """

            results = self.workspace.query(query)

            if not results or len(results) == 0:
                return {'available': False, 'note': 'No breakdowns stored yet'}

            import json

            # Aggregate breakdown statistics
            total_count = 0
            sum_parse_success = 0.0
            sum_method_agreement = 0.0
            sum_catalog_validation = 0.0
            sum_comment_hints = 0.0
            sum_uat_validation = 0.0

            for row in results:
                breakdown_json = row[0]
                object_name = row[1] if len(row) > 1 else 'unknown'

                if not breakdown_json:
                    continue

                try:
                    breakdown = json.loads(breakdown_json)
                    total_count += 1

                    sum_parse_success += breakdown['parse_success']['contribution']
                    sum_method_agreement += breakdown['method_agreement']['contribution']
                    sum_catalog_validation += breakdown['catalog_validation']['contribution']
                    sum_comment_hints += breakdown['comment_hints']['contribution']
                    sum_uat_validation += breakdown['uat_validation']['contribution']

                except json.JSONDecodeError as e:
                    logger.debug(f"{object_name}: Invalid JSON in confidence_breakdown - {e}")
                    continue
                except KeyError as e:
                    logger.debug(f"{object_name}: Missing required field in confidence_breakdown - {e}")
                    continue

            if total_count == 0:
                return {'available': False, 'note': 'No valid breakdowns found'}

            # Calculate averages
            return {
                'available': True,
                'total_objects_with_breakdown': total_count,
                'average_contributions': {
                    'parse_success': round(sum_parse_success / total_count, 4),
                    'method_agreement': round(sum_method_agreement / total_count, 4),
                    'catalog_validation': round(sum_catalog_validation / total_count, 4),
                    'comment_hints': round(sum_comment_hints / total_count, 4),
                    'uat_validation': round(sum_uat_validation / total_count, 4)
                },
                'factor_weights': {
                    'parse_success': 0.30,
                    'method_agreement': 0.25,
                    'catalog_validation': 0.20,
                    'comment_hints': 0.10,
                    'uat_validation': 0.15
                },
                'note': 'Multi-factor confidence model (v2.0.0)'
            }

        except Exception as e:
            logger.error(f"Failed to calculate breakdown stats: {e}")
            return {'available': False, 'error': str(e)}

    def _build_summary(
        self,
        total_counts: Dict[str, int],
        parsed_counts: Dict[str, int],
        source_distribution: Dict[str, int],
        confidence_stats: Dict[str, Any],
        breakdown_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build complete summary statistics."""
        # Calculate totals
        total_objects = sum(total_counts.values())
        parsed_objects = sum(parsed_counts.values())
        coverage = (parsed_objects / total_objects * 100) if total_objects > 0 else 0.0
        
        # Build by_object_type breakdown
        by_object_type = {}
        for obj_type in total_counts.keys():
            total = total_counts[obj_type]
            parsed = parsed_counts.get(obj_type, 0)
            type_coverage = (parsed / total * 100) if total > 0 else 0.0
            
            by_object_type[obj_type] = {
                'total': total,
                'parsed': parsed,
                'coverage': round(type_coverage, 1)
            }
        
        summary = {
            'total_objects': total_objects,
            'parsed_objects': parsed_objects,
            'coverage': round(coverage, 1),
            'by_object_type': by_object_type,
            'by_primary_source': source_distribution,
            'object_type_counts': total_counts,
            'confidence_statistics': confidence_stats,
            'confidence_breakdown_statistics': breakdown_stats  # v2.0.0
        }

        return summary
