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
        
        # Step 5: Build summary
        summary = self._build_summary(
            total_counts,
            parsed_counts,
            source_distribution,
            confidence_stats
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
        """Get confidence statistics."""
        # Check if lineage_metadata exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'lineage_metadata' not in tables:
            logger.warning("lineage_metadata not found - returning empty confidence stats")
            return {}

        query = """
        SELECT
            AVG(confidence) as avg_confidence,
            MIN(confidence) as min_confidence,
            MAX(confidence) as max_confidence,
            COUNT(CASE WHEN confidence >= 0.85 THEN 1 END) as high_confidence_count,
            COUNT(CASE WHEN confidence >= 0.75 AND confidence < 0.85 THEN 1 END) as medium_confidence_count,
            COUNT(CASE WHEN confidence < 0.75 THEN 1 END) as low_confidence_count
        FROM lineage_metadata
        """

        result = self.workspace.query(query)

        if result:
            row = result[0]
            return {
                'average': float(row[0] or 0.0),
                'min': float(row[1] or 0.0),
                'max': float(row[2] or 0.0),
                'high_confidence_count': row[3] or 0,
                'medium_confidence_count': row[4] or 0,
                'low_confidence_count': row[5] or 0
            }

        return {}
    
    def _build_summary(
        self,
        total_counts: Dict[str, int],
        parsed_counts: Dict[str, int],
        source_distribution: Dict[str, int],
        confidence_stats: Dict[str, Any]
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
            'confidence_statistics': confidence_stats
        }
        
        return summary
