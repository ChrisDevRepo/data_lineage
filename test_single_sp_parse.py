#!/usr/bin/env python3
"""Test full parsing pipeline on spLoadHumanResourcesObjects."""

import sys
sys.path.insert(0, '/home/chris/sandbox')

from lineage_v3.parsers.quality_aware_parser import QualityAwareParser
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from pathlib import Path
import json

# Initialize workspace
workspace = DuckDBWorkspace(str(Path('data/lineage_workspace.duckdb')))
workspace.connect()

# Initialize parser
parser = QualityAwareParser(workspace)

# Get spLoadHumanResourcesObjects object_id
result = workspace.query("""
    SELECT object_id, schema_name, object_name
    FROM objects
    WHERE object_name = 'spLoadHumanResourcesObjects'
""")

if not result:
    print("❌ SP not found in database")
    workspace.disconnect()
    sys.exit(1)

object_id, schema, name = result[0]
sp_name = f"{schema}.{name}"

print("="*80)
print(f"TESTING: {sp_name}")
print(f"Object ID: {object_id}")
print("="*80)

# Get current result from database (BEFORE)
before_result = workspace.query("""
    SELECT confidence, inputs, outputs
    FROM lineage_metadata
    WHERE object_id = ?
""", params=[object_id])

if before_result:
    conf_before, inputs_before, outputs_before = before_result[0]
    inputs_before = json.loads(inputs_before) if inputs_before else []
    outputs_before = json.loads(outputs_before) if outputs_before else []
    print(f"\nBEFORE (current in database):")
    print(f"  Confidence: {conf_before}")
    print(f"  Inputs: {len(inputs_before)}")
    print(f"  Outputs: {len(outputs_before)}")

# Parse with UPDATED preprocessing
print(f"\nParsing with updated preprocessing...")
result = parser.parse_object(object_id)

print(f"\nAFTER (with updated preprocessing):")
print(f"  Confidence: {result['confidence']}")
print(f"  Inputs: {len(result['inputs'])}")
print(f"  Outputs: {len(result['outputs'])}")
print(f"  Primary Source: {result['source']}")

# Show improvement
if before_result:
    conf_diff = result['confidence'] - conf_before
    input_diff = len(result['inputs']) - len(inputs_before)
    output_diff = len(result['outputs']) - len(outputs_before)

    print(f"\nIMPROVEMENT:")
    print(f"  Confidence: {conf_before:.2f} → {result['confidence']:.2f} ({conf_diff:+.2f})")
    print(f"  Inputs: {len(inputs_before)} → {len(result['inputs'])} ({input_diff:+d})")
    print(f"  Outputs: {len(outputs_before)} → {len(result['outputs'])} ({output_diff:+d})")

    if result['confidence'] >= 0.85:
        print(f"\n✅ SUCCESS! Moved to high confidence (≥0.85)")
    else:
        print(f"\n⚠️  Still low confidence (<0.85) - needs AI")

# Show first few dependencies
if result['inputs']:
    print(f"\nInput Dependencies (first 5):")
    for i, inp_id in enumerate(result['inputs'][:5], 1):
        inp = workspace.query("SELECT schema_name, object_name FROM objects WHERE object_id = ?", [inp_id])
        if inp:
            print(f"  {i}. {inp[0][0]}.{inp[0][1]}")

if result['outputs']:
    print(f"\nOutput Dependencies (first 5):")
    for i, out_id in enumerate(result['outputs'][:5], 1):
        out = workspace.query("SELECT schema_name, object_name FROM objects WHERE object_id = ?", [out_id])
        if out:
            print(f"  {i}. {out[0][0]}.{out[0][1]}")

workspace.disconnect()
print("\n" + "="*80)
