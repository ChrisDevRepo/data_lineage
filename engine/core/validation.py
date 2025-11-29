"""
Simple validation for interface contracts.

Validates data against the 4-interface specification:
1. DMV - Database metadata query results
2. Parquet - File schema contracts
3. JSON - Lineage output format
4. YAML - Cleaning rule structure

Focus: Column name validation (sufficient for contract enforcement)
No overhead: Skip non-critical checks
"""

from typing import Dict, List, Set
import pandas as pd


# ============================================================================
# INTERFACE 2: PARQUET SCHEMA VALIDATION
# ============================================================================

PARQUET_SCHEMAS = {
    "objects": {"object_id", "schema_name", "object_name", "object_type"},
    "definitions": {"object_id", "definition"},
    "dependencies": {"referencing_object_id", "referenced_object_id", "referenced_schema_name", "referenced_entity_name"},
}


def validate_parquet_schema(df: pd.DataFrame, file_type: str) -> bool:
    """
    Validate Parquet DataFrame against schema contract.

    Args:
        df: Loaded Parquet DataFrame
        file_type: One of: objects, definitions, dependencies

    Returns:
        True if valid

    Raises:
        ValueError: If schema doesn't match contract
    """
    if file_type not in PARQUET_SCHEMAS:
        raise ValueError(f"Unknown file type: {file_type}")

    required_cols = PARQUET_SCHEMAS[file_type]
    actual_cols = set(df.columns)

    missing = required_cols - actual_cols
    if missing:
        raise ValueError(
            f"{file_type}.parquet missing required columns: {missing}. "
            f"Expected: {required_cols}, Got: {actual_cols}"
        )

    return True


# ============================================================================
# INTERFACE 1: DMV QUERY RESULT VALIDATION
# ============================================================================

DMV_SCHEMAS = {
    "objects_query": {"database_object_id", "schema_name", "object_name", "object_type"},
    "definitions_query": {"database_object_id", "sql_code"},
}


def validate_dmv_result(df: pd.DataFrame, query_type: str) -> bool:
    """
    Validate DMV query result against contract.

    Args:
        df: Query result as DataFrame
        query_type: One of: objects_query, definitions_query

    Returns:
        True if valid

    Raises:
        ValueError: If schema doesn't match contract
    """
    if query_type not in DMV_SCHEMAS:
        raise ValueError(f"Unknown query type: {query_type}")

    required_cols = DMV_SCHEMAS[query_type]
    actual_cols = set(df.columns)

    missing = required_cols - actual_cols
    if missing:
        raise ValueError(
            f"DMV {query_type} missing required columns: {missing}. "
            f"Expected: {required_cols}, Got: {actual_cols}"
        )

    return True


# ============================================================================
# INTERFACE 3: JSON LINEAGE VALIDATION
# ============================================================================

def validate_lineage_json(data: dict) -> bool:
    """
    Validate lineage JSON output format.

    Args:
        data: Parsed JSON data

    Returns:
        True if valid

    Raises:
        ValueError: If structure doesn't match contract
    """
    # Check top-level structure
    required_keys = {"nodes", "edges", "metadata"}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - set(data.keys())
        raise ValueError(f"Lineage JSON missing keys: {missing}")

    # Check nodes have required fields
    required_node_fields = {"id", "label", "object_type", "schema_name", "object_name", "inputs", "outputs"}
    for i, node in enumerate(data.get("nodes", [])):
        missing = required_node_fields - set(node.keys())
        if missing:
            raise ValueError(f"Node {i} missing fields: {missing}")

    # Check edges have required fields
    required_edge_fields = {"id", "source", "target", "edge_type"}
    for i, edge in enumerate(data.get("edges", [])):
        missing = required_edge_fields - set(edge.keys())
        if missing:
            raise ValueError(f"Edge {i} missing fields: {missing}")

    return True


# ============================================================================
# INTERFACE 4: YAML RULE VALIDATION
# ============================================================================

def validate_yaml_rule(rule: dict, filename: str) -> bool:
    """
    Validate YAML cleaning rule against contract.

    Args:
        rule: Parsed YAML rule dict
        filename: Rule filename (for error messages)

    Returns:
        True if valid

    Raises:
        ValueError: If rule doesn't match contract
    """
    required_fields = {"name", "description", "dialect", "enabled", "priority", "pattern", "replacement"}
    missing = required_fields - set(rule.keys())

    if missing:
        raise ValueError(
            f"{filename}: Invalid rule configuration. Missing fields: {missing}. "
            f"See engine/rules/YAML_STRUCTURE.md for required fields."
        )

    return True
