#!/usr/bin/env python3
"""
JSON Formatter

Formats lineage data into the strict JSON format required by the specification.

Format:
[
  {
    "id": "node_0",
    "name": "ObjectName",
    "schema": "SchemaName",
    "object_type": "Table|View|StoredProcedure",
    "inputs": ["node_1", "node_2"]
  }
]
"""

import json
from typing import List, Dict, Set
from pathlib import Path


class JSONFormatter:
    """Formats lineage data into strict JSON format."""

    def __init__(self):
        self.node_id_counter = 0
        self.object_to_node_id: Dict[str, str] = {}

    def generate_node_id(self) -> str:
        """Generate a unique node ID."""
        node_id = f"node_{self.node_id_counter}"
        self.node_id_counter += 1
        return node_id

    def get_or_create_node_id(self, schema: str, object_name: str) -> str:
        """Get existing node ID or create a new one."""
        key = f"{schema}.{object_name}"

        if key not in self.object_to_node_id:
            self.object_to_node_id[key] = self.generate_node_id()

        return self.object_to_node_id[key]

    def format_lineage(
        self,
        lineage_graph: Dict[str, Dict],
        target_object: str
    ) -> List[Dict]:
        """
        Format lineage graph into strict JSON format.

        Args:
            lineage_graph: Dict mapping "schema.object_name" to object metadata
                          including dependencies
            target_object: The target object name

        Returns:
            List of node dictionaries in the required format
        """
        nodes = []

        # Assign node IDs to all objects
        for obj_key in lineage_graph.keys():
            parts = obj_key.split('.', 1)
            if len(parts) == 2:
                schema, obj_name = parts
            else:
                schema = "dbo"
                obj_name = obj_key

            self.get_or_create_node_id(schema, obj_name)

        # Build nodes
        for obj_key, obj_info in lineage_graph.items():
            parts = obj_key.split('.', 1)
            if len(parts) == 2:
                schema, obj_name = parts
            else:
                schema = "dbo"
                obj_name = obj_key

            node_id = self.get_or_create_node_id(schema, obj_name)

            # Get input node IDs
            input_ids = []
            for dep_key in obj_info.get('dependencies', []):
                dep_parts = dep_key.split('.', 1)
                if len(dep_parts) == 2:
                    dep_schema, dep_name = dep_parts
                else:
                    dep_schema = "dbo"
                    dep_name = dep_key

                dep_node_id = self.get_or_create_node_id(dep_schema, dep_name)
                input_ids.append(dep_node_id)

            # Remove duplicates and sort
            input_ids = sorted(list(set(input_ids)))

            # Get output node IDs (for stored procedures)
            output_ids = []
            for out_key in obj_info.get('outputs', []):
                out_parts = out_key.split('.', 1)
                if len(out_parts) == 2:
                    out_schema, out_name = out_parts
                else:
                    out_schema = "dbo"
                    out_name = out_key

                out_node_id = self.get_or_create_node_id(out_schema, out_name)
                output_ids.append(out_node_id)

            # Remove duplicates and sort
            output_ids = sorted(list(set(output_ids)))

            # Create node
            node = {
                "id": node_id,
                "name": obj_name,
                "schema": schema,
                "object_type": obj_info.get('object_type', 'Table'),
                "inputs": input_ids,
                "outputs": output_ids
            }

            # Add metadata for external/missing objects
            if 'exists_in_repo' in obj_info:
                node['exists_in_repo'] = obj_info['exists_in_repo']
            if 'is_external' in obj_info:
                node['is_external'] = obj_info['is_external']

            nodes.append(node)

        # Sort nodes by ID
        nodes.sort(key=lambda n: int(n['id'].replace('node_', '')))

        return nodes

    def write_json(self, nodes: List[Dict], output_file: str):
        """
        Write nodes to JSON file.

        Args:
            nodes: List of node dictionaries
            output_file: Path to output JSON file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)

    def validate_json_format(self, nodes: List[Dict]) -> bool:
        """
        Validate that nodes conform to the required format.

        Returns:
            True if valid, False otherwise
        """
        required_fields = {'id', 'name', 'schema', 'object_type', 'inputs', 'outputs'}

        for node in nodes:
            # Check required fields
            if not all(field in node for field in required_fields):
                return False

            # Check types
            if not isinstance(node['id'], str):
                return False
            if not isinstance(node['name'], str):
                return False
            if not isinstance(node['schema'], str):
                return False
            if not isinstance(node['object_type'], str):
                return False
            if not isinstance(node['inputs'], list):
                return False
            if not isinstance(node['outputs'], list):
                return False

            # Check object_type values
            if node['object_type'] not in ['Table', 'View', 'StoredProcedure']:
                return False

            # Check inputs are strings
            if not all(isinstance(inp, str) for inp in node['inputs']):
                return False

            # Check outputs are strings
            if not all(isinstance(out, str) for out in node['outputs']):
                return False

        return True
