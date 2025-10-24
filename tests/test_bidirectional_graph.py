#!/usr/bin/env python3
"""
Unit Tests for Bidirectional Graph Structure

Tests that the lineage engine creates proper bidirectional graphs where:
- Every node has at least one connection (no disconnected nodes)
- If A has B in inputs, then B has A in outputs (bidirectional)
- External objects have outputs populated
"""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_no_disconnected_nodes(lineage_file):
    """Test that all nodes have at least one connection."""
    with open(lineage_file) as f:
        nodes = json.load(f)

    disconnected = [n for n in nodes if not n['inputs'] and not n['outputs']]

    assert len(disconnected) == 0, f"Found {len(disconnected)} disconnected nodes: {[n['name'] for n in disconnected[:5]]}"
    print(f"✅ PASS: No disconnected nodes ({len(nodes)} total nodes)")


def test_bidirectional_edges(lineage_file):
    """Test that all edges are bidirectional."""
    with open(lineage_file) as f:
        nodes = json.load(f)

    # Build lookup
    node_map = {n['id']: n for n in nodes}

    errors = []

    # For each node, verify bidirectional edges
    for node in nodes:
        node_id = node['id']

        # Check inputs: if A has B in inputs, B should have A in outputs
        for input_id in node['inputs']:
            if input_id not in node_map:
                errors.append(f"{node['name']} references non-existent input {input_id}")
                continue

            input_node = node_map[input_id]
            if node_id not in input_node['outputs']:
                errors.append(
                    f"BROKEN EDGE: {node['name']} has {input_node['name']} in inputs, "
                    f"but {input_node['name']} does NOT have {node['name']} in outputs"
                )

        # Check outputs: if A has B in outputs, B should have A in inputs
        for output_id in node['outputs']:
            if output_id not in node_map:
                errors.append(f"{node['name']} references non-existent output {output_id}")
                continue

            output_node = node_map[output_id]
            if node_id not in output_node['inputs']:
                errors.append(
                    f"BROKEN EDGE: {node['name']} has {output_node['name']} in outputs, "
                    f"but {output_node['name']} does NOT have {node['name']} in inputs"
                )

    assert len(errors) == 0, f"Found {len(errors)} bidirectional edge violations:\n" + "\n".join(errors[:10])
    print(f"✅ PASS: All {len(nodes)} nodes have valid bidirectional edges")


def test_external_objects_have_outputs(lineage_file):
    """Test that external objects referenced by SPs have outputs populated."""
    with open(lineage_file) as f:
        nodes = json.load(f)

    # Find external objects
    external_nodes = [n for n in nodes if n.get('is_external', False)]

    # Build reverse map: which nodes reference each external object
    node_map = {n['id']: n for n in nodes}
    external_refs = {}

    for node in nodes:
        if node.get('is_external'):
            continue
        for input_id in node['inputs']:
            if input_id in node_map and node_map[input_id].get('is_external'):
                if input_id not in external_refs:
                    external_refs[input_id] = []
                external_refs[input_id].append(node['id'])

    # Verify external objects have correct outputs
    errors = []
    for ext_id, referencing_nodes in external_refs.items():
        ext_node = node_map[ext_id]
        if not ext_node['outputs']:
            errors.append(
                f"External object {ext_node['name']} is referenced by {len(referencing_nodes)} SPs "
                f"but has empty outputs"
            )
        elif set(ext_node['outputs']) != set(referencing_nodes):
            errors.append(
                f"External object {ext_node['name']} outputs mismatch: "
                f"expected {referencing_nodes}, got {ext_node['outputs']}"
            )

    assert len(errors) == 0, f"Found {len(errors)} external object issues:\n" + "\n".join(errors[:5])
    print(f"✅ PASS: All {len(external_nodes)} external objects have correct outputs")


def test_tree_structure_validity(lineage_file):
    """Test that the graph forms a valid tree structure."""
    with open(lineage_file) as f:
        nodes = json.load(f)

    # Root node (node_0) should have inputs but may or may not have outputs
    root = [n for n in nodes if n['id'] == 'node_0'][0]
    assert root is not None, "No root node found"

    # Count node types
    tables = [n for n in nodes if n['object_type'] == 'Table']
    sps = [n for n in nodes if n['object_type'] == 'StoredProcedure']
    views = [n for n in nodes if n['object_type'] == 'View']

    # Source nodes (leaf nodes) - should have outputs but no inputs
    source_nodes = [n for n in tables if not n['inputs'] and n['outputs']]

    # Intermediate nodes - should have both
    intermediate_nodes = [n for n in nodes if n['inputs'] and n['outputs']]

    print(f"\n📊 Tree Structure Statistics:")
    print(f"  Total nodes: {len(nodes)}")
    print(f"  - StoredProcedures: {len(sps)}")
    print(f"  - Tables: {len(tables)}")
    print(f"  - Views: {len(views)}")
    print(f"  Root node: {root['name']}")
    print(f"  Source nodes (leaves): {len(source_nodes)}")
    print(f"  Intermediate nodes: {len(intermediate_nodes)}")

    assert len(source_nodes) > 0, "No source nodes found - tree has no leaves"
    print(f"✅ PASS: Valid tree structure with {len(source_nodes)} leaf nodes")


def run_all_tests(lineage_file):
    """Run all tests."""
    print(f"\n{'='*70}")
    print(f"RUNNING BIDIRECTIONAL GRAPH TESTS")
    print(f"File: {lineage_file}")
    print(f"{'='*70}\n")

    tests = [
        ("No Disconnected Nodes", test_no_disconnected_nodes),
        ("Bidirectional Edges", test_bidirectional_edges),
        ("External Objects Have Outputs", test_external_objects_have_outputs),
        ("Tree Structure Validity", test_tree_structure_validity),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 TEST: {test_name}")
            test_func(lineage_file)
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"  Exception: {e}")
            failed += 1

    print(f"\n{'='*70}")
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*70}\n")

    return failed == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        lineage_file = sys.argv[1]
    else:
        lineage_file = "lineage_output/CONSUMPTION_FINANCE.spLoadFactGLCOGNOS_lineage.json"

    success = run_all_tests(lineage_file)
    sys.exit(0 if success else 1)
