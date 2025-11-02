#!/usr/bin/env python3
"""Extract DDL for spLoadHumanResourcesObjects to analyze parsing failure."""

import sys
sys.path.insert(0, '/home/chris/sandbox')

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from pathlib import Path

workspace = DuckDBWorkspace(str(Path('data/lineage_workspace.duckdb')))
workspace.connect()

print("="*80)
print("EXTRACTING DDL FOR spLoadHumanResourcesObjects")
print("="*80)

# Get the SP details
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
    WHERE o.object_name = 'spLoadHumanResourcesObjects'
""")

if not result:
    print("❌ SP not found in database")
    workspace.disconnect()
    sys.exit(1)

obj_id, schema, name, conf, inputs_str, outputs_str, source = result[0]

print(f"\nSP Info:")
print(f"  Object ID: {obj_id}")
print(f"  Schema: {schema}")
print(f"  Name: {name}")
print(f"  Confidence: {conf}")
print(f"  Primary Source: {source}")
print(f"  Inputs: {inputs_str}")
print(f"  Outputs: {outputs_str}")

# Get the DDL
ddl_result = workspace.query("""
    SELECT definition
    FROM definitions
    WHERE object_id = ?
""", params=[obj_id])

if not ddl_result:
    print("\n❌ DDL not found in definitions table")
    workspace.disconnect()
    sys.exit(1)

ddl = ddl_result[0][0]

print("\n" + "="*80)
print("DDL:")
print("="*80)
print(ddl)

print("\n" + "="*80)
print("DDL LENGTH:")
print("="*80)
print(f"Characters: {len(ddl)}")
print(f"Lines: {len(ddl.split(chr(10)))}")

# Save to file for detailed analysis
output_file = Path('spLoadHumanResourcesObjects_DDL.sql')
with open(output_file, 'w') as f:
    f.write(ddl)

print(f"\n✅ DDL saved to: {output_file}")

workspace.disconnect()
