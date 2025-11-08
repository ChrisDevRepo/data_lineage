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
  "outputs": ["node_3"],
  "ddl_text": "CREATE PROCEDURE..."  # Optional: DDL for SPs/Views (v3.0 SQL Viewer)
}

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-27 (SQL Viewer feature added)
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
        output_path: str = "lineage_output/frontend_lineage.json",
        include_ddl: bool = False
    ) -> Dict[str, Any]:
        """
        Generate frontend_lineage.json from internal lineage.

        Args:
            internal_lineage: List of nodes in internal format
            output_path: Path to output JSON file
            include_ddl: If True, include DDL text for SPs and Views (default: False for performance)

        Returns:
            Statistics about generation
        """
        logger.info("Generating frontend_lineage.json...")
        
        # Step 1: Assign node IDs to all objects
        self._assign_node_ids(internal_lineage)
        
        # Step 2: Transform to frontend format
        frontend_nodes = self._transform_to_frontend(internal_lineage, include_ddl)
        
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
        internal_lineage: List[Dict[str, Any]],
        include_ddl: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Transform internal format to frontend format.

        Args:
            internal_lineage: List of nodes in internal format
            include_ddl: If True, include DDL text for SPs and Views

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
            
            # Get confidence and enhanced metadata for description (v4.2.0)
            confidence = node['provenance']['confidence']
            confidence_breakdown = node['provenance'].get('confidence_breakdown')  # v2.0.0
            parse_failure_reason = node['provenance'].get('parse_failure_reason')  # v4.2.0
            expected_count = node['provenance'].get('expected_count', 0)  # v4.2.0
            found_count = node['provenance'].get('found_count', 0)  # v4.2.0
            source = node['provenance'].get('primary_source', 'unknown')

            if node['object_type'] == 'Stored Procedure':
                # Enhanced description with actionable guidance (v4.2.0)
                description = self._format_sp_description(
                    confidence=confidence,
                    parse_failure_reason=parse_failure_reason,
                    expected_count=expected_count,
                    found_count=found_count,
                    source=source,
                    confidence_breakdown=confidence_breakdown
                )
            else:
                # Tables and Views always show 1.00 (they exist in metadata)
                description = "Confidence: 1.00"

            # Classify data model type
            data_model_type = self._classify_data_model_type(
                node['name'],
                node['object_type']
            )

            # Create frontend node (base properties)
            frontend_node = {
                'id': node_id,
                'name': node['name'],
                'schema': node['schema'],
                'object_type': node['object_type'],
                'description': description,
                'data_model_type': data_model_type,
                'inputs': sorted(input_node_ids, key=lambda x: int(x)),
                'outputs': sorted(output_node_ids, key=lambda x: int(x)),
                'confidence': confidence,  # v2.0.0 - explicit confidence field
                'confidence_breakdown': confidence_breakdown  # v2.0.0 - multi-factor breakdown
            }

            # Conditionally add DDL text if requested (for JSON mode with embedded DDL)
            # In Parquet mode (include_ddl=False), property is omitted entirely
            if include_ddl:
                if node['object_type'] in ['Stored Procedure', 'View']:
                    # Query definitions table for DDL
                    ddl_text = self._get_ddl_for_object(object_id)
                elif node['object_type'] == 'Table':
                    # Generate DDL from table_columns if available
                    ddl_text = self._generate_table_ddl(object_id, node['schema'], node['name'])
                else:
                    ddl_text = None

                frontend_node['ddl_text'] = ddl_text  # Add property only in JSON mode

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

        # Normalize name for matching (check patterns)
        name_lower = object_name.lower()

        # Check for dimension patterns:
        # - Tables: Dim*, DIM*
        # - Views: vw_Dim*, v_Dim*, vwDim*, vDim*
        if (object_name.startswith("Dim") or
            name_lower.startswith("vw_dim") or
            name_lower.startswith("v_dim") or
            name_lower.startswith("vwdim") or
            name_lower.startswith("vdim")):
            return "Dimension"

        # Check for fact patterns:
        # - Tables: Fact*, FACT*
        # - Views: vw_Fact*, v_Fact*, vwFact*, vFact*
        if (object_name.startswith("Fact") or
            name_lower.startswith("vw_fact") or
            name_lower.startswith("v_fact") or
            name_lower.startswith("vwfact") or
            name_lower.startswith("vfact")):
            return "Fact"

        # Default to Other for staging tables, junction tables, etc.
        return "Other"

    def _format_sp_description(
        self,
        confidence: float,
        parse_failure_reason: str | None,
        expected_count: int,
        found_count: int,
        source: str,
        confidence_breakdown: Dict[str, Any] | None
    ) -> str:
        """
        Generate enhanced description for stored procedure nodes.

        Provides user-friendly description with actionable guidance for low confidence SPs.

        Args:
            confidence: Confidence score (0.0 - 1.0)
            parse_failure_reason: Detailed reason why parsing failed (v4.2.0)
            expected_count: Expected number of tables from smoke test
            found_count: Actual number of tables extracted
            source: Primary source (parser, parser_with_hints, etc.)
            confidence_breakdown: Multi-factor confidence breakdown

        Returns:
            Human-readable description string

        Examples:
            "✅ High Confidence: 0.85"
            "⚠️ Low Confidence: 0.50 | Dynamic SQL detected → Add @LINEAGE hints"
            "❌ Parse Failed: 0.00 | WHILE loop - Expected 8 tables, found 0 → Add @LINEAGE hints"

        Version: 4.2.0 (2025-11-07)
        """
        parts = []

        # Start with actionable message (warnings/failures first)

        # Parse failure reason (most critical - show first)
        if confidence == 0 and parse_failure_reason:
            # Truncate very long reasons for readability
            if len(parse_failure_reason) > 80:
                reason_short = parse_failure_reason[:77] + "..."
            else:
                reason_short = parse_failure_reason
            parts.append(f"❌ {reason_short}")

        # Missing dependencies warning
        elif expected_count is not None and found_count is not None and expected_count > 0 and found_count >= 0:
            missing = expected_count - found_count
            if missing > 2 and confidence < 0.85:
                parts.append(f"⚠️ {missing} tables may be missing - add @LINEAGE hints")

        # Low confidence warning (no specific reason)
        elif confidence < 0.75:
            parts.append(f"⚠️ Low confidence - review parsing")

        # Good confidence (no action needed)
        else:
            parts.append(f"✅ Good quality")

        # Hint usage indicator (if applicable)
        if source == 'parser_with_hints' and confidence_breakdown:
            hint_factor = confidence_breakdown.get('comment_hints', {})
            if hint_factor.get('score', 0) > 0:
                parts.append("with hints")

        # End with confidence score in brackets
        parts.append(f"(score {confidence:.2f})")

        return " ".join(parts)

    def _get_ddl_for_object(self, object_id: int) -> str | None:
        """
        Retrieve DDL definition from definitions table.

        Args:
            object_id: Integer object_id from sys.objects

        Returns:
            DDL text as string, or None if not found
        """
        try:
            result = self.workspace.query("""
                SELECT definition
                FROM definitions
                WHERE object_id = ?
            """, [object_id])

            if result and len(result) > 0:
                ddl_text = result[0][0]
                # Return DDL if it's not empty
                if ddl_text and ddl_text.strip():
                    return ddl_text

            return None

        except Exception as e:
            logger.warning(f"Failed to retrieve DDL for object_id {object_id}: {e}")
            return None

    def _generate_table_ddl(self, object_id: int, schema_name: str, table_name: str) -> str | None:
        """
        Generate CREATE TABLE DDL from table_columns data.

        Args:
            object_id: Integer object_id from sys.objects
            schema_name: Schema name for the table
            table_name: Table name

        Returns:
            Generated DDL text as string, or None if table_columns not available
        """
        try:
            # Query table_columns using correct_object_id (mapped from objects table)
            # Note: correct_object_id is populated by joining on schema_name + table_name
            # to handle cases where object_ids change between extractions
            columns = self.workspace.query("""
                SELECT
                    column_name,
                    data_type,
                    max_length,
                    precision,
                    scale,
                    is_nullable,
                    column_id
                FROM table_columns
                WHERE correct_object_id = ?
                ORDER BY column_id
            """, [object_id])

            if not columns or len(columns) == 0:
                return None

            # Build CREATE TABLE statement
            ddl_lines = [f"CREATE TABLE [{schema_name}].[{table_name}] ("]
            column_definitions = []

            for col in columns:
                col_name, data_type, max_length, precision, scale, is_nullable, _ = col

                # Format data type with size/precision
                if data_type in ['varchar', 'nvarchar', 'char', 'nchar']:
                    if max_length == -1:
                        type_spec = f"{data_type}(MAX)"
                    elif data_type.startswith('n'):
                        # nvarchar and nchar use half the byte length
                        type_spec = f"{data_type}({max_length // 2})"
                    else:
                        type_spec = f"{data_type}({max_length})"
                elif data_type in ['decimal', 'numeric']:
                    type_spec = f"{data_type}({precision},{scale})"
                else:
                    type_spec = data_type

                # Add nullable constraint
                nullable_spec = "NULL" if is_nullable else "NOT NULL"

                column_definitions.append(f"    [{col_name}] {type_spec} {nullable_spec}")

            ddl_lines.append(",\n".join(column_definitions))
            ddl_lines.append(");")

            return "\n".join(ddl_lines)

        except Exception as e:
            # If table_columns doesn't exist or query fails, return None
            logger.debug(f"Could not generate DDL for table {schema_name}.{table_name}: {e}")
            return None
