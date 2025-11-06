#!/usr/bin/env python3
"""
Smoke Test: Dataflow Mode v4.1.2 - Administrative Query Filtering

Tests that SELECT COUNT and other administrative queries are correctly filtered
from stored procedure lineage, leaving only data transformation operations.

Target SP: CONSUMPTION_FINANCE.spLoadGLCognosData
Expected: GLCognosData should ONLY appear in outputs, NOT inputs
"""

import sys
import json
from pathlib import Path

# Test configuration
TEST_SP = "spLoadGLCognosData"
TEST_SCHEMA = "CONSUMPTION_FINANCE"
TEST_TABLE = "GLCognosData"

def load_lineage_data(lineage_file):
    """Load frontend lineage JSON."""
    with open(lineage_file, 'r') as f:
        return json.load(f)

def find_object_by_name(data, schema, name):
    """Find object by schema and name."""
    for obj in data:
        if obj.get('schema') == schema and obj.get('name') == name:
            return obj
    return None

def get_object_name(data, obj_id):
    """Get object name from ID."""
    for obj in data:
        if obj['id'] == obj_id:
            return f"{obj.get('schema', 'unknown')}.{obj.get('name', 'unknown')}"
    return f"Unknown({obj_id})"

def test_sp_lineage(sp_obj, data):
    """
    Test that spLoadGLCognosData has correct lineage.

    Expected inputs:
      - STAGING_FINANCE_COGNOS.GLCognosData_HC100500 (legitimate - used in INSERT)
      - STAGING_FINANCE_COGNOS.v_CCR2PowerBI_facts (legitimate - source data)

    Expected outputs:
      - CONSUMPTION_FINANCE.GLCognosData (target table)
      - STAGING_FINANCE_COGNOS.GLCognosData_HC100500 (staging table)

    NOT expected:
      - CONSUMPTION_FINANCE.GLCognosData in inputs (from SELECT COUNT - should be filtered)
    """
    results = {
        'test_name': 'Dataflow Mode - Administrative Query Filtering',
        'sp_name': f"{TEST_SCHEMA}.{TEST_SP}",
        'passed': False,
        'details': {}
    }

    # Get input/output lists
    inputs = sp_obj.get('inputs', [])
    outputs = sp_obj.get('outputs', [])

    results['details']['input_count'] = len(inputs)
    results['details']['output_count'] = len(outputs)
    results['details']['inputs'] = [get_object_name(data, inp) for inp in inputs]
    results['details']['outputs'] = [get_object_name(data, out) for out in outputs]

    # Check if GLCognosData is in inputs (should NOT be)
    target_table_id = None
    for obj in data:
        if obj.get('schema') == TEST_SCHEMA and obj.get('name') == TEST_TABLE and obj.get('object_type') == 'Table':
            target_table_id = obj['id']
            break

    if target_table_id:
        glc_in_inputs = target_table_id in inputs
        glc_in_outputs = target_table_id in outputs

        results['details']['glc_in_inputs'] = glc_in_inputs
        results['details']['glc_in_outputs'] = glc_in_outputs

        # PASS criteria:
        # 1. GLCognosData should NOT be in inputs
        # 2. GLCognosData SHOULD be in outputs
        if not glc_in_inputs and glc_in_outputs:
            results['passed'] = True
            results['message'] = "✅ SUCCESS: Dataflow mode working correctly"
            results['details']['validation'] = [
                "✅ GLCognosData NOT in inputs (SELECT COUNT filtered)",
                "✅ GLCognosData in outputs (INSERT captured)",
                "✅ Clean dataflow lineage"
            ]
        else:
            results['passed'] = False
            if glc_in_inputs:
                results['message'] = "❌ FAILED: GLCognosData appears in inputs (SELECT COUNT not filtered)"
                results['details']['validation'] = [
                    "❌ GLCognosData in inputs (administrative query leaked through)",
                    "✅ GLCognosData in outputs" if glc_in_outputs else "❌ GLCognosData NOT in outputs",
                    "⚠️  Noise in lineage graph"
                ]
            else:
                results['message'] = "⚠️  UNEXPECTED: GLCognosData not in outputs"
                results['details']['validation'] = [
                    "✅ GLCognosData NOT in inputs",
                    "❌ GLCognosData NOT in outputs (INSERT not captured)",
                    "⚠️  Missing data transformation"
                ]
    else:
        results['passed'] = False
        results['message'] = f"❌ ERROR: Could not find {TEST_SCHEMA}.{TEST_TABLE} in data"

    return results

def print_results(results):
    """Print test results in readable format."""
    print("\n" + "="*70)
    print(f"  {results['test_name']}")
    print("="*70)
    print(f"\nTesting: {results['sp_name']}")
    print(f"Status: {results['message']}\n")

    details = results['details']

    print(f"📥 Inputs ({details['input_count']}):")
    for inp in details['inputs']:
        print(f"  - {inp}")

    print(f"\n📤 Outputs ({details['output_count']}):")
    for out in details['outputs']:
        print(f"  - {out}")

    if 'validation' in details:
        print("\n🔍 Validation:")
        for item in details['validation']:
            print(f"  {item}")

    print("\n" + "="*70)
    if results['passed']:
        print("  ✅ TEST PASSED")
    else:
        print("  ❌ TEST FAILED")
    print("="*70 + "\n")

    return results['passed']

def main():
    """Run smoke test."""
    # Check if lineage file exists
    lineage_file = Path(__file__).parent.parent.parent / "lineage_output" / "frontend_lineage.json"

    if not lineage_file.exists():
        print(f"❌ ERROR: Lineage file not found: {lineage_file}")
        print("   Run the parser first: python lineage_v3/main.py run --parquet parquet_snapshots/")
        return 1

    print(f"📂 Loading lineage data from: {lineage_file}")
    data = load_lineage_data(lineage_file)
    print(f"✅ Loaded {len(data)} objects\n")

    # Find test SP
    sp_obj = find_object_by_name(data, TEST_SCHEMA, TEST_SP)

    if not sp_obj:
        print(f"❌ ERROR: Could not find {TEST_SCHEMA}.{TEST_SP} in lineage data")
        return 1

    # Run test
    results = test_sp_lineage(sp_obj, data)

    # Print results
    passed = print_results(results)

    # Save results to JSON
    output_file = Path(__file__).parent / "dataflow_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📊 Results saved to: {output_file}\n")

    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())
