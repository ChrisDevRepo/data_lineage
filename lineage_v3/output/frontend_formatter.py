#!/usr/bin/env python3
"""
Frontend Lineage Formatter
===========================

Generates frontend_lineage.json with string node_ids for React Flow.

Format:
{
  "id": "node_0",
  "name": "object_name",
  "schema": "schema",
  "object_type": "Table|View|Stored Procedure",
  "description": "Confidence: 0.85",  # Shows confidence score
  "data_model_type": "Dimension|Fact|Other",
  "inputs": ["node_1", "node_2"],
  "outputs": ["node_3"]
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


class FrontendFormatter:
    """
    Formatter for frontend_lineage.json with string node_ids.
    
    Transforms internal format (integer object_ids) to frontend format (string node_ids).
    Uses confidence score in the description field.
    """
    
    def __init__(self, workspace):
        """
        Initialize frontend formatter.

        Args:
            workspace: DuckDB workspace instance
        """
        self.workspace = workspace
        self.object_id_to_node_id: Dict[int, str] = {}
    
    def generate(
        self,
        internal_lineage: List[Dict[str, Any]],
        output_path: str = "lineage_output/frontend_lineage.json"
    ) -> Dict[str, Any]:
        """
        Generate frontend_lineage.json from internal lineage.
        
        Args:
            internal_lineage: List of nodes in internal format
            output_path: Path to output JSON file
            
        Returns:
            Statistics about generation
        """
        logger.info("Generating frontend_lineage.json...")
        
        # Step 1: Assign node IDs to all objects
        self._assign_node_ids(internal_lineage)
        
        # Step 2: Transform to frontend format
        frontend_nodes = self._transform_to_frontend(internal_lineage)
        
        # Step 3: Write to JSON file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(frontend_nodes, f, indent=2, ensure_ascii=False)
        
        stats = {
            'total_nodes': len(frontend_nodes),
            'output_file': str(output_file)
        }
        
        logger.info(f"✓ Generated frontend_lineage.json with {stats['total_nodes']} nodes")
        return stats
    
    def _assign_node_ids(self, internal_lineage: List[Dict[str, Any]]):
        """Map object_ids to string IDs (string cast of object_id)."""
        for node in internal_lineage:
            object_id = node['id']
            if object_id not in self.object_id_to_node_id:
                # Use string representation of actual object_id from database
                node_id = str(object_id)
                self.object_id_to_node_id[object_id] = node_id
    
    def _transform_to_frontend(
        self,
        internal_lineage: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform internal format to frontend format.
        
        Args:
            internal_lineage: List of nodes in internal format
            
        Returns:
            List of nodes in frontend format
        """
        frontend_nodes = []
        
        for node in internal_lineage:
            object_id = node['id']
            node_id = self.object_id_to_node_id[object_id]
            
            # Transform inputs (int[] -> string[])
            input_node_ids = [
                self.object_id_to_node_id[inp_id]
                for inp_id in node['inputs']
                if inp_id in self.object_id_to_node_id
            ]
            
            # Transform outputs (int[] -> string[])
            output_node_ids = [
                self.object_id_to_node_id[out_id]
                for out_id in node['outputs']
                if out_id in self.object_id_to_node_id
            ]
            
            # Get confidence for description
            confidence = node['provenance']['confidence']
            description = f"Confidence: {confidence:.2f}"
            
            # Classify data model type
            data_model_type = self._classify_data_model_type(
                node['name'],
                node['object_type']
            )
            
            # Create frontend node
            frontend_node = {
                'id': node_id,
                'name': node['name'],
                'schema': node['schema'],
                'object_type': node['object_type'],
                'description': description,
                'data_model_type': data_model_type,
                'inputs': sorted(input_node_ids, key=lambda x: int(x)),
                'outputs': sorted(output_node_ids, key=lambda x: int(x))
            }

            frontend_nodes.append(frontend_node)

        # Sort by object_id (now string representation of integer)
        frontend_nodes.sort(key=lambda n: int(n['id']))
        
        return frontend_nodes
    
    def _classify_data_model_type(self, object_name: str, object_type: str) -> str:
        """
        Classify data model type based on naming conventions.
        
        Args:
            object_name: Object name (e.g., "DimCustomers", "FactOrders")
            object_type: Object type ("Table", "View", "Stored Procedure")
            
        Returns:
            One of: "Dimension", "Fact", "Other"
        """
        # Only classify tables and views
        if object_type not in ["Table", "View"]:
            return "Other"
        
        # Check for dimension tables (starts with "Dim")
        if object_name.startswith("Dim"):
            return "Dimension"
        
        # Check for fact tables (starts with "Fact")
        if object_name.startswith("Fact"):
            return "Fact"
        
        # Default to Other for staging tables, junction tables, etc.
        return "Other"
