#!/usr/bin/env python3
"""Check SP dependencies and confidence counts."""

import sys
sys.path.insert(0, '/home/chris/sandbox')

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from pathlib import Path
import json

workspace = DuckDBWorkspace(str(Path('data/lineage_workspace.duckdb')))
workspace.connect()

print("="*80)
print("CHECKING spLoadHumanResourcesObjects")
print("="*80)

# Check the SP
result = workspace.query("""
    SELECT
        o.object_id,
        o.schema_name,
        o.object_name,
        o.object_type,
        m.confidence,
        m.inputs,
        m.outputs,
        m.primary_source
    FROM objects o
    JOIN lineage_metadata m ON o.object_id = m.object_id
    WHERE o.object_name = 'spLoadHumanResourcesObjects'
""")

if result:
    obj_id, schema, name, obj_type, conf, inputs_str, outputs_str, source = result[0]
    inputs = json.loads(inputs_str) if inputs_str else []
    outputs = json.loads(outputs_str) if outputs_str else []

    print(f"Found: {schema}.{name}")
    print(f"Object Type: {obj_type}")
    print(f"Confidence: {conf}")
    print(f"Primary Source: {source}")
    print(f"Inputs: {len(inputs)}")
    print(f"Outputs: {len(outputs)}")

    if inputs:
        print(f"\nInput Objects:")
        for inp_id in inputs[:10]:
            inp_result = workspace.query("""
                SELECT schema_name, object_name, object_type
                FROM objects
                WHERE object_id = ?
            """, params=[inp_id])
            if inp_result:
                sch, nm, typ = inp_result[0]
                print(f"  - {sch}.{nm} ({typ})")

    if outputs:
        print(f"\nOutput Objects:")
        for out_id in outputs[:10]:
            out_result = workspace.query("""
                SELECT schema_name, object_name, object_type
                FROM objects
                WHERE object_id = ?
            """, params=[out_id])
            if out_result:
                sch, nm, typ = out_result[0]
                print(f"  - {sch}.{nm} ({typ})")
else:
    print("❌ SP not found in database")

print("\n" + "="*80)
print("CONFIDENCE COUNTS ANALYSIS")
print("="*80)

# Count high confidence objects
result = workspace.query("""
    SELECT COUNT(*) as count
    FROM lineage_metadata m
    JOIN objects o ON m.object_id = o.object_id
    WHERE m.confidence >= 0.85
""")
print(f"High confidence (≥0.85) with JOIN: {result[0][0]}")

# Count without JOIN (what summary_formatter.py does)
result = workspace.query("""
    SELECT COUNT(*) as count
    FROM lineage_metadata
    WHERE confidence >= 0.85
""")
print(f"High confidence (≥0.85) WITHOUT JOIN: {result[0][0]}")

# Check for orphaned records
result = workspace.query("""
    SELECT m.object_id, m.confidence
    FROM lineage_metadata m
    LEFT JOIN objects o ON m.object_id = o.object_id
    WHERE o.object_id IS NULL
""")
if result:
    print(f"\nOrphaned metadata records: {len(result)}")
    for obj_id, conf in result:
        print(f"  - object_id: {obj_id}, confidence: {conf}")

# Check what latest_frontend_lineage.json should contain
print("\n" + "="*80)
print("CHECKING latest_frontend_lineage.json")
print("="*80)

try:
    with open('data/latest_frontend_lineage.json', 'r') as f:
        frontend_data = json.load(f)

    # Count nodes
    total_nodes = len(frontend_data)
    print(f"Total nodes in JSON: {total_nodes}")

    # Count nodes with high confidence
    high_conf = sum(1 for node in frontend_data if 'description' in node and 'Confidence: 1.' in node['description'])
    high_conf += sum(1 for node in frontend_data if 'description' in node and 'Confidence: 0.9' in node['description'])
    high_conf += sum(1 for node in frontend_data if 'description' in node and 'Confidence: 0.8' in node['description'] and 'Confidence: 0.7' not in node['description'])

    print(f"Estimated high confidence in JSON: {high_conf}")

    # Check if spLoadHumanResourcesObjects is in the JSON
    sp_found = any(node['name'] == 'spLoadHumanResourcesObjects' for node in frontend_data if 'name' in node)
    if sp_found:
        sp_node = next(node for node in frontend_data if node.get('name') == 'spLoadHumanResourcesObjects')
        print(f"\nspLoadHumanResourcesObjects in JSON:")
        print(f"  - inputs: {len(sp_node.get('inputs', []))}")
        print(f"  - outputs: {len(sp_node.get('outputs', []))}")
        print(f"  - description: {sp_node.get('description', 'N/A')}")
    else:
        print("\n❌ spLoadHumanResourcesObjects NOT in JSON")

except Exception as e:
    print(f"Error reading JSON: {e}")

workspace.disconnect()
