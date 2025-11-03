#!/usr/bin/env python3
"""
Focused test for FactAgingSAP AI inference - rapid iteration without full parser run
"""
import sys
sys.path.insert(0, '/home/chris/sandbox/lineage_v3')

import duckdb
from lineage_v3.parsers.ai_disambiguator import AIDisambiguator

def main():
    # Connect to database
    conn = duckdb.connect('/home/chris/sandbox/lineage_v3/lineage_workspace.duckdb', read_only=True)

    # Test case
    table_schema = "CONSUMPTION_FINANCE"
    table_name = "FactAgingSAP"
    expected_sp = "spLoadFactAgingSAP"

    print("=" * 80)
    print(f"FOCUSED TEST: {table_schema}.{table_name}")
    print("=" * 80)
    print(f"Expected match: {table_schema}.{expected_sp}")
    print()

    # Get all SP data
    all_sps = conn.execute("""
        SELECT
            o.object_id,
            o.schema_name as schema,
            o.object_name as name,
            d.definition
        FROM objects o
        LEFT JOIN definitions d ON o.object_id = d.object_id
        WHERE o.object_type = 'Stored Procedure'
    """).fetchall()

    all_sp_data = [
        {
            'object_id': row[0],
            'schema': row[1],
            'name': row[2],
            'definition': row[3] or ''
        }
        for row in all_sps
    ]

    print(f"Total SPs in database: {len(all_sp_data)}")
    print()

    # Initialize AI disambiguator
    disambiguator = AIDisambiguator(conn)

    # Test the inference
    print("Running AI inference...")
    print("-" * 80)

    result = disambiguator.infer_dependencies_for_unreferenced_table(
        table_schema=table_schema,
        table_name=table_name,
        all_sp_data=all_sp_data
    )

    print()
    print("=" * 80)
    print("RESULT:")
    print("=" * 80)

    if result:
        print(f"Confidence: {result.confidence}")
        print(f"Source object_ids: {result.sources}")
        print(f"Target object_ids: {result.targets}")
        print(f"Reasoning: {result.reasoning}")
        print()

        # Resolve object IDs to SP names
        all_matched_ids = result.sources + result.targets
        matched_sp_names = []
        for obj_id in all_matched_ids:
            sp_info = conn.execute(f"SELECT schema_name, object_name FROM objects WHERE object_id = {obj_id}").fetchone()
            if sp_info:
                matched_sp_names.append(f"{sp_info[0]}.{sp_info[1]}")

        print(f"Matched SPs: {matched_sp_names}")
        print()

        # Check if expected SP is in the results
        if expected_sp in [sp.split('.')[-1] for sp in matched_sp_names]:
            print(f"✅ SUCCESS: Found expected SP '{expected_sp}'")
        else:
            print(f"❌ FAILED: Expected SP '{expected_sp}' not found")
    else:
        print("❌ FAILED: No result returned (empty)")

    conn.close()

if __name__ == "__main__":
    main()
