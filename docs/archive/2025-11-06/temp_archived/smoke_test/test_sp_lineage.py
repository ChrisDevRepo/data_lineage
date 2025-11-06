#!/usr/bin/env python3
"""
Test SP-to-SP Lineage Detection (v4.0.1)
"""
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser

print("=" * 80)
print("Testing SP-to-SP Lineage Detection (v4.0.1)")
print("=" * 80)

with DuckDBWorkspace("data/lineage_workspace.duckdb") as ws:
    parser = QualityAwareParser(ws)

    # Get a stored procedure that calls other SPs
    query = """
    SELECT o.object_id, o.object_name, d.definition
    FROM objects o
    JOIN definitions d ON o.object_id = d.object_id
    WHERE o.object_type = 'Stored Procedure'
      AND d.definition LIKE '%EXEC%'
      AND d.definition NOT LIKE '%spLastRowCount%'
      AND d.definition NOT LIKE '%LogMessage%'
    LIMIT 5
    """

    results = ws.query(query)

    for obj_id, obj_name, ddl in results:
        print(f"\n{'=' * 80}")
        print(f"Testing: {obj_name} (ID: {obj_id})")
        print(f"{'=' * 80}")

        # Extract with regex to see what SP calls are found
        regex_result = parser.extract_regex_dependencies(ddl)
        print(f"\nRegex Extraction:")
        print(f"  SP Calls Found: {len(regex_result.get('sp_calls', set()))}")
        if regex_result.get('sp_calls'):
            for sp_call in list(regex_result['sp_calls'])[:10]:
                print(f"    - {sp_call}")
        print(f"  SP Calls Validated: {len(regex_result.get('sp_calls_validated', set()))}")
        if regex_result.get('sp_calls_validated'):
            for sp_call in list(regex_result['sp_calls_validated'])[:10]:
                print(f"    - {sp_call}")

        # Parse with full parser
        parse_result = parser.parse_object(obj_id)
        print(f"\nFull Parse Result:")
        print(f"  Total Inputs: {len(parse_result['inputs'])} object IDs")
        print(f"  Total Outputs: {len(parse_result['outputs'])} object IDs")

        # Show what the inputs are
        if parse_result['inputs']:
            print(f"\n  Input Objects (first 10):")
            for input_id in parse_result['inputs'][:10]:
                # Get object info
                obj_query = "SELECT schema_name, object_name, object_type FROM objects WHERE object_id = ?"
                obj_info = ws.query(obj_query, params=[input_id])
                if obj_info:
                    schema, name, obj_type = obj_info[0]
                    print(f"    [{obj_type:20}] {schema}.{name}")

        print(f"\n  Confidence: {parse_result['confidence']:.2f}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
