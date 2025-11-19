#!/usr/bin/env python3
"""
Check specific SP parsing results with actual table names.
"""
import duckdb
import json

conn = duckdb.connect('data/lineage_workspace.duckdb')

sp_name = 'spLoadFactLaborCostForEarnedValue_Post'

print("="*80)
print(f"DETAILED RESULTS FOR: {sp_name}")
print("="*80)
print()

# Get SP details with actual table names
result = conn.execute("""
    SELECT
        o.object_name,
        o.schema_name,
        lm.inputs,
        lm.outputs,
        lm.confidence
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    WHERE o.object_name = ?
""", [sp_name]).fetchone()

if result:
    name, schema, inputs_json, outputs_json, confidence = result
    input_ids = json.loads(inputs_json) if inputs_json else []
    output_ids = json.loads(outputs_json) if outputs_json else []

    print(f"📋 SP: {schema}.{name}")
    print(f"🎯 Confidence: {confidence}")
    print()

    # Get actual table names for inputs
    print(f"📥 INPUTS ({len(input_ids)} tables):")
    print("-"*80)
    for obj_id in input_ids:
        obj = conn.execute("""
            SELECT schema_name, object_name, object_type
            FROM objects
            WHERE object_id = ?
        """, [obj_id]).fetchone()

        if obj:
            obj_schema, obj_name, obj_type = obj
            print(f"  [{obj_schema}].[{obj_name}]")
            print(f"    Type: {obj_type}, ID: {obj_id}")
        else:
            print(f"  ❌ Object ID {obj_id} not found in catalog")

    print()

    # Get actual table names for outputs
    print(f"📤 OUTPUTS ({len(output_ids)} tables):")
    print("-"*80)
    for obj_id in output_ids:
        obj = conn.execute("""
            SELECT schema_name, object_name, object_type
            FROM objects
            WHERE object_id = ?
        """, [obj_id]).fetchone()

        if obj:
            obj_schema, obj_name, obj_type = obj
            print(f"  [{obj_schema}].[{obj_name}]")
            print(f"    Type: {obj_type}, ID: {obj_id}")
        else:
            print(f"  ❌ Object ID {obj_id} not found in catalog")

    print()
    print("="*80)
    print("VERIFICATION:")
    print("-"*80)

    # Check for expected tables
    expected_sources = [
        "CONSUMPTION_POWERBI.FactLaborCostForEarnedValue",
        "CONSUMPTION_ClinOpsFinance.CadenceBudget_LaborCost_PrimaContractUtilization_Junc"
    ]

    expected_target = "CONSUMPTION_ClinOpsFinance.FactLaborCostForEarnedValue_Post"

    # Get actual names
    actual_inputs = []
    for obj_id in input_ids:
        obj = conn.execute("SELECT schema_name, object_name FROM objects WHERE object_id = ?", [obj_id]).fetchone()
        if obj:
            actual_inputs.append(f"{obj[0]}.{obj[1]}")

    actual_outputs = []
    for obj_id in output_ids:
        obj = conn.execute("SELECT schema_name, object_name FROM objects WHERE object_id = ?", [obj_id]).fetchone()
        if obj:
            actual_outputs.append(f"{obj[0]}.{obj[1]}")

    print(f"Expected sources: {len(expected_sources)}")
    for src in expected_sources:
        if src in actual_inputs:
            print(f"  ✅ {src} - FOUND")
        else:
            print(f"  ❌ {src} - MISSING")

    print()
    print(f"Expected target: {expected_target}")
    if expected_target in actual_outputs:
        print(f"  ✅ {expected_target} - FOUND")
    else:
        print(f"  ❌ {expected_target} - MISSING")

    print()

    # Show any additional found tables
    extra_inputs = [t for t in actual_inputs if t not in expected_sources]
    if extra_inputs:
        print(f"Additional inputs found ({len(extra_inputs)}):")
        for inp in extra_inputs:
            print(f"  ℹ️  {inp}")

else:
    print(f"❌ SP '{sp_name}' not found in database")

print()
print("="*80)

conn.close()
