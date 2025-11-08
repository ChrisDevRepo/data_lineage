#!/usr/bin/env python3
"""
Internal Lineage Formatter
===========================

Generates lineage.json in internal format with integer object_ids.

Format:
{
  "id": 1001,
  "name": "object_name",
  "schema": "schema",
  "object_type": "Table|View|Stored Procedure",
  "inputs": [2002, 2003],
  "outputs": [3004],
  "provenance": {
    "primary_source": "dmv|query_log|parser|ai",
    "confidence": 0.0-1.0
  }
}

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-26
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class InternalFormatter:
    """
    Formatter for internal lineage.json with integer object_ids.
    
    Uses confidence score in the description field as requested.
    """
    
    def __init__(self, workspace):
        """
        Initialize internal formatter.
        
        Args:
            workspace: DuckDB workspace instance
        """
        self.workspace = workspace
    
    def generate(self, output_path: str = "lineage_output/lineage.json") -> Dict[str, Any]:
        """
        Generate internal lineage.json file.
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            Statistics about generation (node count, etc.)
        """
        logger.info("Generating internal lineage.json...")
        
        # Step 1: Get all objects from workspace
        objects = self._fetch_objects()
        
        # Step 2: Get all dependencies (from parser comparison log or lineage_metadata)
        dependencies = self._fetch_dependencies()
        
        # Step 3: Build bidirectional graph
        lineage_nodes = self._build_lineage_graph(objects, dependencies)
        
        # Step 4: Write to JSON file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(lineage_nodes, f, indent=2, ensure_ascii=False)
        
        stats = {
            'total_nodes': len(lineage_nodes),
            'output_file': str(output_file)
        }
        
        logger.info(f"✓ Generated lineage.json with {stats['total_nodes']} nodes")
        return stats
    
    def _fetch_objects(self) -> List[Dict[str, Any]]:
        """
        Fetch ALL objects from workspace.

        Returns all objects regardless of whether they have been parsed or not.
        Objects without dependencies will have empty inputs/outputs and confidence 0.
        """
        query = """
        SELECT
            object_id,
            schema_name,
            object_name,
            object_type
        FROM objects
        WHERE object_type IN ('Table', 'View', 'Stored Procedure')
        ORDER BY object_id
        """

        results = self.workspace.query(query)

        objects = []
        for row in results:
            objects.append({
                'object_id': row[0],
                'schema': row[1],
                'name': row[2],
                'object_type': row[3]  # Already human-readable
            })

        logger.info(f"Fetched {len(objects)} objects from workspace")
        return objects
    
    def _fetch_dependencies(self) -> Dict[int, Dict[str, Any]]:
        """
        Fetch dependencies from lineage_metadata.

        Returns:
            Dict mapping object_id to dependency metadata including inputs/outputs/breakdown
        """
        # Check if lineage_metadata table exists
        tables = [row[0] for row in self.workspace.query("SHOW TABLES")]

        if 'lineage_metadata' in tables:
            query = """
            SELECT
                object_id,
                primary_source,
                confidence,
                inputs,
                outputs,
                confidence_breakdown,
                parse_failure_reason,
                expected_count,
                found_count
            FROM lineage_metadata
            ORDER BY object_id
            """

            results = self.workspace.query(query)

            import json
            deps = {}
            for row in results:
                # Parse JSON arrays for inputs/outputs
                inputs = json.loads(row[3]) if row[3] else []
                outputs = json.loads(row[4]) if row[4] else []
                breakdown = json.loads(row[5]) if row[5] else None
                parse_failure_reason = row[6]  # v2.1.0 / BUG-002
                expected_count = row[7]  # v2.1.0 / BUG-002
                found_count = row[8]  # v2.1.0 / BUG-002

                deps[row[0]] = {
                    'primary_source': row[1] or 'unknown',
                    'confidence': row[2] or 0.0,
                    'inputs': inputs,
                    'outputs': outputs,
                    'confidence_breakdown': breakdown,  # v2.0.0
                    'parse_failure_reason': parse_failure_reason,  # v2.1.0 / BUG-002
                    'expected_count': expected_count,  # v2.1.0 / BUG-002
                    'found_count': found_count  # v2.1.0 / BUG-002
                }

            logger.info(f"Fetched dependencies for {len(deps)} objects from lineage_metadata")
            return deps
        else:
            logger.warning("lineage_metadata table not found - using empty dependencies")
            return {}
    
    def _build_lineage_graph(
        self,
        objects: List[Dict[str, Any]],
        dependencies: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build bidirectional lineage graph.
        
        Args:
            objects: List of object metadata
            dependencies: Dict of dependency metadata by object_id
            
        Returns:
            List of lineage nodes in internal format
        """
        nodes = []
        
        # First pass: Create all nodes with direct dependencies
        object_map = {}
        for obj in objects:
            object_id = obj['object_id']
            object_type = obj['object_type']

            # Get dependency metadata (if available, otherwise use defaults)
            if object_id in dependencies:
                dep_meta = dependencies[object_id]
            else:
                # Tables and Views exist in metadata → confidence 1.0
                # Stored Procedures not parsed → confidence 0.0
                if object_type in ['Table', 'View']:
                    dep_meta = {
                        'primary_source': 'metadata',
                        'confidence': 1.0,
                        'inputs': [],
                        'outputs': []
                    }
                else:  # Stored Procedure not parsed
                    dep_meta = {
                        'primary_source': 'unparsed',
                        'confidence': 0.0,
                        'inputs': [],
                        'outputs': []
                    }

            # Use object_type directly (already human-readable)
            object_type = obj['object_type']

            node = {
                'id': object_id,
                'name': obj['name'],
                'schema': obj['schema'],
                'object_type': object_type,
                'inputs': dep_meta['inputs'],  # Use actual inputs from lineage_metadata
                'outputs': dep_meta['outputs'],  # Use actual outputs from lineage_metadata
                'provenance': {
                    'primary_source': dep_meta['primary_source'],
                    'confidence': float(dep_meta['confidence']),
                    'confidence_breakdown': dep_meta.get('confidence_breakdown'),  # v2.0.0
                    'parse_failure_reason': dep_meta.get('parse_failure_reason'),  # v2.1.0 / BUG-002
                    'expected_count': dep_meta.get('expected_count'),  # v2.1.0 / BUG-002
                    'found_count': dep_meta.get('found_count')  # v2.1.0 / BUG-002
                }
            }

            nodes.append(node)
            object_map[object_id] = node
        
        logger.info(f"Built lineage graph with {len(nodes)} nodes")
        return nodes
    
    def _map_type_code_to_object_type(self, type_code: str) -> str:
        """Map sys.objects type code to object_type."""
        mapping = {
            'U': 'Table',
            'V': 'View',
            'P': 'Stored Procedure',
            'FN': 'Function',
            'IF': 'Function',
            'TF': 'Function'
        }
        return mapping.get(type_code, 'Other')
