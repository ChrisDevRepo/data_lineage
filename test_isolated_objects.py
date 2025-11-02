#!/usr/bin/env python3
"""
Smoke Test: Validate Parse Results
===================================

Validates parser output by checking JSON files and database.
Run this after every full parse to ensure dependencies are captured correctly.

Usage:
    python test_isolated_objects.py [--db lineage_workspace.duckdb] [--json lineage_output/lineage.json]

Expected Results:
    - SP-to-SP dependencies: >0 (target: 50-100)
    - SP parse success rate: >95%
    - Isolated tables: Only in failed/low-confidence SPs

Author: Vibecoding Data Lineage Team
Date: 2025-11-02 (Updated to check JSON output)
"""

import duckdb
import json
import re
import argparse
import os
from typing import List, Tuple, Dict, Set


def test_sp_to_sp_dependencies(json_data: List[Dict], conn: duckdb.DuckDBPyConnection) -> Tuple[int, bool]:
    """
    Test 1: SP-to-SP Dependencies Count (from JSON)

    Returns: (count, pass/fail)
    """
    print("=" * 80)
    print("TEST 1: SP-to-SP Dependencies (JSON)")
    print("=" * 80)

    # Get all SP IDs from DB
    sp_ids = {row[0] for row in conn.execute("SELECT object_id FROM objects WHERE object_type = 'Stored Procedure'").fetchall()}

    # Find SP-to-SP dependencies in JSON
    sp_to_sp_deps = []

    for item in json_data:
        if item.get('object_type') == 'Stored Procedure':
            inputs = item.get('inputs', [])
            # Find inputs that are also SPs (excluding self-references)
            sp_inputs = [inp for inp in inputs if inp in sp_ids and inp != item.get('id')]

            if sp_inputs:
                sp_name = item['name']
                for sp_id in sp_inputs:
                    dep_name = conn.execute(f"SELECT object_name FROM objects WHERE object_id = {sp_id}").fetchone()[0]
                    sp_to_sp_deps.append((sp_name, dep_name))

    count = len(sp_to_sp_deps)
    passed = count > 0

    print(f"\nSP-to-SP dependencies in JSON: {count}")
    print(f"Expected: >0 (target: 50-100)")
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")

    if count > 0:
        print(f"\nExamples (first 10):")
        for i, (calling, called) in enumerate(sp_to_sp_deps[:10], 1):
            print(f"  {i}. {calling} → {called}")

    return count, passed


def test_sp_parse_success_rate(json_data: List[Dict]) -> Tuple[int, int, bool]:
    """
    Test 2: SP Parse Success Rate (from JSON)

    Returns: (total_sps, sps_with_deps, pass/fail)
    """
    print("\n" + "=" * 80)
    print("TEST 2: SP Parse Success Rate (JSON)")
    print("=" * 80)

    sp_items = [item for item in json_data if item.get('object_type') == 'Stored Procedure']
    total_sps = len(sp_items)

    # Count SPs with at least one input or output
    sps_with_deps = sum(1 for item in sp_items if item.get('inputs') or item.get('outputs'))

    success_rate = (sps_with_deps / total_sps * 100) if total_sps > 0 else 0
    passed = success_rate >= 95.0  # Target: 95%+

    print(f"\nTotal SPs in JSON: {total_sps}")
    print(f"SPs with dependencies: {sps_with_deps} ({success_rate:.1f}%)")
    print(f"SPs with NO dependencies: {total_sps - sps_with_deps}")
    print(f"Expected: >95% parse success")
    print(f"Status: {'✅ PASS' if passed else '⚠️  WARNING' if success_rate > 90 else '❌ FAIL'}")

    # Show failed SPs
    failed_sps = [item['name'] for item in sp_items if not (item.get('inputs') or item.get('outputs'))]
    if failed_sps:
        print(f"\nFailed SPs (no dependencies captured):")
        for sp in failed_sps[:10]:
            print(f"  - {sp}")
        if len(failed_sps) > 10:
            print(f"  ... and {len(failed_sps) - 10} more")

    return total_sps, sps_with_deps, passed


def test_isolated_tables(json_data: List[Dict], conn: duckdb.DuckDBPyConnection) -> Tuple[int, int, bool]:
    """
    Test 3: Isolated Tables Validation

    Checks if isolated tables only appear in failed/low-confidence SPs.

    FIXED: Now checks both dependencies table AND lineage_metadata since:
    - DMV dependencies (Views) → dependencies table
    - Parser dependencies (SPs) → lineage_metadata → JSON

    Returns: (total_isolated, false_positives, pass/fail)
    """
    print("\n" + "=" * 80)
    print("TEST 3: Isolated Tables Validation (FIXED)")
    print("=" * 80)

    # Get isolated tables from DB - check BOTH dependencies and lineage_metadata
    isolated_tables = conn.execute('''
        SELECT object_id, schema_name, object_name
        FROM objects
        WHERE object_type = 'Table'
        AND object_id NOT IN (
            -- From DMV dependencies (Views, Functions)
            SELECT DISTINCT referencing_object_id FROM dependencies
            UNION
            SELECT DISTINCT referenced_object_id FROM dependencies
            UNION
            -- From parser dependencies (Stored Procedures) - check lineage_metadata
            SELECT DISTINCT CAST(json_extract(inputs_item.value, '$') AS INTEGER)
            FROM lineage_metadata,
            json_each(CAST(inputs AS VARCHAR)) AS inputs_item
            WHERE inputs IS NOT NULL AND inputs != '[]'
            UNION
            SELECT DISTINCT CAST(json_extract(outputs_item.value, '$') AS INTEGER)
            FROM lineage_metadata,
            json_each(CAST(outputs AS VARCHAR)) AS outputs_item
            WHERE outputs IS NOT NULL AND outputs != '[]'
        )
    ''').fetchall()

    isolated_table_ids = {row[0] for row in isolated_tables}
    isolated_table_names = {f"{row[1]}.{row[2]}" for row in isolated_tables}

    print(f"\nTotal isolated tables in DB: {len(isolated_tables)}")
    print(f"  (Checked both dependencies table AND lineage_metadata)")

    # Check JSON: Are any isolated tables referenced by SUCCESSFUL SPs?
    # Successful SP = has inputs/outputs in JSON
    false_positives = []

    for item in json_data:
        if item.get('object_type') == 'Stored Procedure':
            # Check if this SP is "successful" (has any dependencies)
            has_deps = bool(item.get('inputs') or item.get('outputs'))

            if has_deps:
                # Check if it references any isolated tables
                all_refs = (item.get('inputs', []) + item.get('outputs', []))
                isolated_refs = [ref for ref in all_refs if ref in isolated_table_ids]

                if isolated_refs:
                    sp_name = item['name']
                    for table_id in isolated_refs:
                        # Get table name
                        table_info = conn.execute(f"SELECT schema_name, object_name FROM objects WHERE object_id = {table_id}").fetchone()
                        if table_info:
                            false_positives.append((f"{table_info[0]}.{table_info[1]}", sp_name))

    fp_count = len(false_positives)
    fp_rate = (fp_count / len(isolated_tables) * 100) if len(isolated_tables) > 0 else 0
    passed = fp_count == 0  # Target: 0 false positives

    print(f"\nResults:")
    print(f"  Isolated tables in successful SPs: {fp_count} ({fp_rate:.1f}%)")
    print(f"  Expected: 0 (all isolated tables should be in failed SPs only)")
    print(f"  Status: {'✅ PASS' if passed else '❌ FAIL'}")

    if fp_count > 0:
        print(f"\n❌ CRITICAL: Isolated tables found in SUCCESSFUL SPs!")
        print(f"   This means successful SPs have incomplete dependencies")
        print(f"\nExamples:")
        for table, sp in false_positives[:10]:
            print(f"  - {table} referenced by: {sp}")
        if fp_count > 10:
            print(f"  ... and {fp_count - 10} more")
    else:
        print(f"\n✅ All isolated tables are ONLY in failed SPs (expected)")

    return len(isolated_tables), fp_count, passed


def test_confidence_distribution(db_path: str) -> Tuple[int, int, int]:
    """
    Test 4: Confidence Score Distribution (using MetricsService)

    IMPORTANT: Now uses MetricsService for consistency with CLI and JSON output.

    Returns: (high_count, medium_count, low_count)
    """
    print("\n" + "=" * 80)
    print("TEST 4: Confidence Distribution (MetricsService)")
    print("=" * 80)

    from lineage_v3.metrics import MetricsService
    from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

    # Create workspace and connect
    db = DuckDBWorkspace(db_path)
    db.connect()

    metrics_service = MetricsService(db)
    sp_metrics = metrics_service.get_parse_metrics(object_type='Stored Procedure')

    total = sp_metrics['total']
    high_conf = sp_metrics['confidence']['high']['count']
    medium_conf = sp_metrics['confidence']['medium']['count']
    low_conf = sp_metrics['confidence']['low']['count']

    print(f"\nScope: {sp_metrics['scope']}")
    print(f"Total: {total}")
    print(f"  High confidence (≥0.85): {high_conf} ({sp_metrics['confidence']['high']['pct']:.1f}%)")
    print(f"  Medium confidence (0.75-0.84): {medium_conf} ({sp_metrics['confidence']['medium']['pct']:.1f}%)")
    print(f"  Low confidence (<0.75): {low_conf} ({sp_metrics['confidence']['low']['pct']:.1f}%)")

    # Check if distribution makes sense
    if sp_metrics['confidence']['high']['pct'] >= 70.0:
        print(f"\n✅ Good distribution - {sp_metrics['confidence']['high']['pct']:.1f}% high confidence")
    elif sp_metrics['confidence']['high']['pct'] >= 50.0:
        print(f"\n⚠️  Acceptable - {sp_metrics['confidence']['high']['pct']:.1f}% high confidence")
    else:
        print(f"\n❌ Low confidence rate - only {sp_metrics['confidence']['high']['pct']:.1f}% high confidence")

    return high_conf, medium_conf, low_conf


def main():
    parser = argparse.ArgumentParser(description='Smoke test for parse results')
    parser.add_argument('--db', default='lineage_workspace.duckdb',
                       help='Path to DuckDB database')
    parser.add_argument('--json', default='lineage_output/lineage.json',
                       help='Path to lineage JSON output')
    args = parser.parse_args()

    print("=" * 80)
    print("PARSE RESULTS VALIDATION")
    print("=" * 80)
    print(f"Database: {args.db}")
    print(f"JSON Output: {args.json}\n")

    # Check files exist
    if not os.path.exists(args.db):
        print(f"❌ ERROR: Database not found: {args.db}")
        return 1

    if not os.path.exists(args.json):
        print(f"❌ ERROR: JSON output not found: {args.json}")
        return 1

    # Load JSON
    with open(args.json, 'r') as f:
        json_data = json.load(f)

    print(f"✅ Loaded JSON: {len(json_data)} objects")

    # Connect to DB
    conn = duckdb.connect(args.db)

    # Run tests
    sp_to_sp_count, test1_pass = test_sp_to_sp_dependencies(json_data, conn)
    total_sps, sps_with_deps, test2_pass = test_sp_parse_success_rate(json_data)
    isolated_total, isolated_fp, test3_pass = test_isolated_tables(json_data, conn)
    high_conf, med_conf, low_conf = test_confidence_distribution(args.db)  # Now uses MetricsService

    conn.close()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    all_passed = test1_pass and test2_pass and test3_pass

    print(f"\nTest Results:")
    print(f"  Test 1 (SP-to-SP deps): {'✅ PASS' if test1_pass else '❌ FAIL'} ({sp_to_sp_count} deps)")
    print(f"  Test 2 (Parse success): {'✅ PASS' if test2_pass else '❌ FAIL'} ({sps_with_deps}/{total_sps} = {sps_with_deps/total_sps*100:.1f}%)")
    print(f"  Test 3 (Isolated tables): {'✅ PASS' if test3_pass else '❌ FAIL'} ({isolated_fp} false positives)")
    print(f"  Test 4 (Confidence dist): INFO ({high_conf} high, {med_conf} med, {low_conf} low)")

    print(f"\n{'✅ ALL CRITICAL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    if not all_passed:
        print("\nRecommended Actions:")
        if not test1_pass:
            print("  - Check SP-to-SP regex pattern in quality_aware_parser.py")
            print("  - Verify preprocessing doesn't remove EXEC statements")
        if not test2_pass:
            print("  - Review failed SPs - may need AI fallback")
            print("  - Check if preprocessing is too aggressive")
        if not test3_pass:
            print("  - CRITICAL: Successful SPs have missing dependencies")
            print("  - Review parser logic - silent failures detected")

    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
