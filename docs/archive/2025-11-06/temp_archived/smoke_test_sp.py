#!/usr/bin/env python3
"""Smoke test for SP dependencies - verify parser results against DDL."""

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from pathlib import Path
import json

workspace = DuckDBWorkspace(str(Path('lineage_workspace.duckdb')))
workspace.connect()

def test_sp(sp_name, description):
    """Test a single SP and show its dependencies."""
    print(f"\n{'='*80}")
    print(f"TEST CASE: {sp_name}")
    print(f"Description: {description}")
    print(f"{'='*80}")

    # Get object details
    result = workspace.query("""
        SELECT
            o.object_id,
            o.schema_name,
            o.object_name,
            m.confidence,
            m.inputs,
            m.outputs,
            m.primary_source
        FROM objects o
        JOIN lineage_metadata m ON o.object_id = m.object_id
        WHERE o.object_name = ?
    """, params=[sp_name])

    if not result:
        print(f"❌ SP not found: {sp_name}")
        return None

    obj_id, schema, name, conf, inputs_str, outputs_str, source = result[0]

    # Parse JSON strings
    inputs = json.loads(inputs_str) if inputs_str else []
    outputs = json.loads(outputs_str) if outputs_str else []

    print(f"Schema: {schema}.{name}")
    print(f"Confidence: {conf}")
    print(f"Primary Source: {source}")
    print(f"Inputs: {len(inputs)} objects")
    print(f"Outputs: {len(outputs)} objects")
    print()

    # Resolve input names
    if inputs:
        print(f"Inputs ({len(inputs)} total, showing first 10):")
        for i, inp_id in enumerate(inputs[:10], 1):
            inp_result = workspace.query("""
                SELECT schema_name, object_name, object_type
                FROM objects
                WHERE object_id = ?
            """, params=[inp_id])
            if inp_result:
                sch, nm, typ = inp_result[0]
                icon = '⚙️' if typ == 'Stored Procedure' else '🗃️'
                print(f"  {i:2d}. {icon} {sch}.{nm} ({typ})")

    # Resolve output names
    if outputs:
        print(f"\nOutputs ({len(outputs)} total):")
        for i, out_id in enumerate(outputs, 1):
            out_result = workspace.query("""
                SELECT schema_name, object_name, object_type
                FROM objects
                WHERE object_id = ?
            """, params=[out_id])
            if out_result:
                sch, nm, typ = out_result[0]
                icon = '⚙️' if typ == 'Stored Procedure' else '🗃️'
                print(f"  {i:2d}. {icon} {sch}.{nm} ({typ})")

    return obj_id

# Test Cases
test_cases = [
    ('spLoadDimCustomers', 'Pattern: 12 inputs, 2 outputs (most common, 85 SPs) - Low confidence 0.52'),
    ('spLoadDateRangeMonthClose_Config', 'Pattern: 23 inputs, 2 outputs - Medium confidence 0.68'),
    ('spLoadDimAccount', 'Pattern: 11 inputs, 12 outputs - Medium confidence 0.75'),
    ('spLoadDateRange', 'SP-to-SP dependencies - After v3.8.0 fix (0.85 confidence)'),
]

sp_ids_for_ddl = []
for sp_name, description in test_cases:
    sp_id = test_sp(sp_name, description)
    if sp_id:
        sp_ids_for_ddl.append((sp_id, sp_name))

# Print DDL retrieval info
print(f"\n{'='*80}")
print("DDL RETRIEVAL")
print(f"{'='*80}")
print("\nTo view DDL for these SPs, use:")
for sp_id, sp_name in sp_ids_for_ddl:
    print(f"  SELECT definition FROM definitions WHERE object_id = {sp_id}; -- {sp_name}")

workspace.disconnect()
