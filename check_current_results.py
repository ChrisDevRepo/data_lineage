#!/usr/bin/env python3
"""Check current parse results directly from database."""

import sys
sys.path.insert(0, '/home/chris/sandbox')

import duckdb

# Connect to workspace
conn = duckdb.connect('data/lineage_workspace.duckdb', read_only=True)

# Count SPs by confidence
result = conn.execute("""
    SELECT
        COUNT(*) as total_sps,
        SUM(CASE WHEN confidence >= 0.85 THEN 1 ELSE 0 END) as high_conf,
        SUM(CASE WHEN confidence >= 0.75 AND confidence < 0.85 THEN 1 ELSE 0 END) as medium_conf,
        SUM(CASE WHEN confidence < 0.75 THEN 1 ELSE 0 END) as low_conf
    FROM lineage_metadata lm
    JOIN objects o ON lm.object_id = o.object_id
    WHERE o.object_type = 'Stored Procedure'
""").fetchone()

total, high, medium, low = result

print("="*80)
print("CURRENT DATABASE STATE")
print("="*80)
print(f"Total SPs: {total}")
print(f"High confidence (≥0.85): {high} ({high/total*100:.1f}%)")
print(f"Medium confidence (0.75-0.84): {medium}")
print(f"Low confidence (<0.75): {low}")
print()

# Check spLoadHumanResourcesObjects
sp_result = conn.execute("""
    SELECT
        lm.confidence,
        lm.primary_source,
        lm.inputs,
        lm.outputs,
        o.object_name
    FROM lineage_metadata lm
    JOIN objects o ON lm.object_id = o.object_id
    WHERE o.object_name = 'spLoadHumanResourcesObjects'
""").fetchone()

if sp_result:
    conf, source, inputs, outputs, name = sp_result
    import json
    inputs_list = json.loads(inputs) if inputs else []
    outputs_list = json.loads(outputs) if outputs else []

    print(f"spLoadHumanResourcesObjects:")
    print(f"  Confidence: {conf}")
    print(f"  Source: {source}")
    print(f"  Inputs: {len(inputs_list)}")
    print(f"  Outputs: {len(outputs_list)}")
else:
    print("spLoadHumanResourcesObjects: NOT FOUND")

conn.close()
