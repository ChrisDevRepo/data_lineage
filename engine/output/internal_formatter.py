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

"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

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

    def generate(
        self, output_path: str = "lineage_output/lineage.json"
    ) -> Dict[str, Any]:
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

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(lineage_nodes, f, indent=2, ensure_ascii=False)

        stats = {"total_nodes": len(lineage_nodes), "output_file": str(output_file)}

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
            objects.append(
                {
                    "object_id": row[0],
                    "schema": row[1],
                    "name": row[2],
                    "object_type": row[3],
                }
            )

        logger.info(f"Fetched {len(objects)} objects from workspace")
        return objects

    def _fetch_dependencies(self) -> Dict[int, Dict[str, Any]]:
        """
        Fetch dependencies from edge table.

        Uses lineage_edges table for inputs/outputs, lineage_metadata for provenance.
        JSON column fallback removed - edge table is required.

        Returns:
            Dict mapping object_id to dependency metadata including inputs/outputs/breakdown
        """
        # Get metadata (provenance info)
        metadata_query = """
        SELECT
            object_id,
            primary_source,
            parse_success,
            parse_failure_reason,
            expected_count,
            found_count
        FROM lineage_metadata
        ORDER BY object_id
        """

        metadata_results = self.workspace.query(metadata_query)

        deps = {}
        for row in metadata_results:
            deps[row[0]] = {
                "primary_source": row[1] or "unknown",
                "parse_success": row[2] if row[2] is not None else True,
                "inputs": [],  # Will be populated from edge table
                "outputs": [],  # Will be populated from edge table
                "parse_failure_reason": row[3],
                "expected_count": row[4],
                "found_count": row[5],
            }

        # Get inputs from edge table (source -> target, so sources are inputs)
        inputs_query = """
        SELECT target_id, LIST(source_id) as inputs
        FROM lineage_edges
        WHERE edge_type = 'dependency'
        GROUP BY target_id
        """

        inputs_results = self.workspace.query(inputs_query)
        for row in inputs_results:
            target_id, inputs_list = row
            if target_id in deps:
                deps[target_id]["inputs"] = inputs_list

        # Get outputs from edge table (source -> target, so targets are outputs)
        outputs_query = """
        SELECT source_id, LIST(target_id) as outputs
        FROM lineage_edges
        WHERE edge_type = 'dependency'
        GROUP BY source_id
        """

        outputs_results = self.workspace.query(outputs_query)
        for row in outputs_results:
            source_id, outputs_list = row
            if source_id in deps:
                deps[source_id]["outputs"] = outputs_list

        # Detect bidirectional pairs using DuckDB
        # This replaces frontend's O(n²) JavaScript detection with O(n) SQL query
        bidirectional_query = """
        SELECT DISTINCT
            LEAST(e1.source_id, e1.target_id) as node_a,
            GREATEST(e1.source_id, e1.target_id) as node_b
        FROM lineage_edges e1
        INNER JOIN lineage_edges e2
            ON e1.source_id = e2.target_id
            AND e1.target_id = e2.source_id
        WHERE e1.source_id < e1.target_id  -- Avoid duplicates
        """

        bidirectional_results = self.workspace.query(bidirectional_query)
        bidirectional_pairs = set()
        for row in bidirectional_results:
            node_a, node_b = row
            bidirectional_pairs.add((node_a, node_b))

        # Add bidirectional_with list to each node's metadata
        for node_id in deps:
            deps[node_id]["bidirectional_with"] = []

        for node_a, node_b in bidirectional_pairs:
            if node_a in deps:
                deps[node_a]["bidirectional_with"].append(node_b)
            if node_b in deps:
                deps[node_b]["bidirectional_with"].append(node_a)

        logger.info(f"Fetched dependencies for {len(deps)} objects from edge table")
        logger.info(f"Detected {len(bidirectional_pairs)} bidirectional pairs")
        return deps

    def _build_lineage_graph(
        self, objects: List[Dict[str, Any]], dependencies: Dict[int, Dict[str, Any]]
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
            object_id = obj["object_id"]
            object_type = obj["object_type"]

            # Get dependency metadata (if available, otherwise use defaults)
            if object_id in dependencies:
                dep_meta = dependencies[object_id]
            else:
                # Tables and Views exist in metadata → confidence 1.0
                # Stored Procedures not parsed → confidence 0.0
                if object_type in ["Table", "View"]:
                    dep_meta = {
                        "primary_source": "metadata",
                        "confidence": 1.0,
                        "inputs": [],
                        "outputs": [],
                        "bidirectional_with": [],
                    }
                else:  # Stored Procedure not parsed
                    dep_meta = {
                        "primary_source": "unparsed",
                        "confidence": 0.0,
                        "inputs": [],
                        "outputs": [],
                        "bidirectional_with": [],
                    }

            # Use object_type directly (already human-readable)
            object_type = obj["object_type"]

            node = {
                "id": object_id,
                "name": obj["name"],
                "schema": obj["schema"],
                "object_type": object_type,
                "inputs": dep_meta["inputs"],  # Use actual inputs from lineage_metadata
                "outputs": dep_meta[
                    "outputs"
                ],  # Use actual outputs from lineage_metadata
                "bidirectional_with": dep_meta.get(
                    "bidirectional_with", []
                ),  # Pre-computed in DuckDB
                "provenance": {
                    "primary_source": dep_meta["primary_source"],
                    "parse_success": dep_meta.get("parse_success", True),  # v4.3.6
                    "parse_failure_reason": dep_meta.get(
                        "parse_failure_reason"
                    ),  # v4.3.6
                    "expected_count": dep_meta.get("expected_count"),  # v4.3.6
                    "found_count": dep_meta.get("found_count"),  # v4.3.6
                },
            }

            nodes.append(node)
            object_map[object_id] = node

        logger.info(f"Built lineage graph with {len(nodes)} nodes")
        return nodes

    def _map_type_code_to_object_type(self, type_code: str) -> str:
        """Map sys.objects type code to object_type."""
        mapping = {
            "U": "Table",
            "V": "View",
            "P": "Stored Procedure",
            "FN": "Function",
            "IF": "Function",
            "TF": "Function",
        }
        return mapping.get(type_code, "Other")
