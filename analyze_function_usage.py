#!/usr/bin/env python3
"""
Function Usage Analyzer
=======================

Pre-flight check: Scans your stored procedures for function calls
BEFORE running full reload, so you know what to expect.

Usage:
    python analyze_function_usage.py

Author: Claude Code Agent
Date: 2025-11-11
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from lineage_v3.core import DuckDBWorkspace
except ImportError:
    print("❌ Cannot import lineage modules. Run from project root.")
    sys.exit(1)


def analyze_functions(workspace_path="parquet_snapshots/lineage_workspace.duckdb"):
    """
    Analyze stored procedures for function usage.

    Reports:
    - How many SPs use functions
    - Which functions are called
    - Which would be phantom (not in catalog)
    """
    print("=" * 70)
    print("Function Usage Analysis")
    print("=" * 70)
    print("\nConnecting to workspace...")

    workspace = DuckDBWorkspace(workspace_path)
    workspace.connect()

    # Get all stored procedures with DDL
    print("\n1. Fetching stored procedures...")
    sp_query = """
        SELECT
            o.object_id,
            o.schema_name,
            o.object_name,
            d.definition
        FROM objects o
        JOIN definitions d ON o.object_id = d.object_id
        WHERE o.object_type = 'Stored Procedure'
        ORDER BY o.schema_name, o.object_name
    """

    sps = workspace.query(sp_query)
    print(f"   Found {len(sps)} stored procedures")

    # Get function catalog (if any)
    print("\n2. Checking function catalog...")
    func_query = """
        SELECT LOWER(schema_name || '.' || object_name)
        FROM objects
        WHERE object_type IN ('Function', 'Scalar Function', 'Table-valued Function')
    """

    results = workspace.query(func_query)
    function_catalog = {row[0] for row in results}
    print(f"   Functions in catalog: {len(function_catalog)}")
    if function_catalog:
        for func in sorted(function_catalog)[:5]:
            print(f"     - {func}")
        if len(function_catalog) > 5:
            print(f"     ... and {len(function_catalog) - 5} more")
    else:
        print("     ⚠️  No functions in catalog (all detected will be phantoms)")

    # Scan SPs for function calls
    print("\n3. Scanning stored procedures for function calls...")

    function_patterns = [
        r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',
        r'\bJOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',
        r'\bINNER\s+JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',
        r'\bLEFT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',
        r'\bRIGHT\s+(?:OUTER\s+)?JOIN\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',
        r'\bCROSS\s+APPLY\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',
        r'\bOUTER\s+APPLY\s+\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',
        r'\b\[?(\w+)\]?\.\[?(\w+)\]?\s*\(',  # General pattern
    ]

    builtin_functions = {
        'CAST', 'CONVERT', 'COALESCE', 'ISNULL', 'CASE', 'NULLIF',
        'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'STDEV', 'VAR',
        'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE',
        'GETDATE', 'DATEADD', 'DATEDIFF', 'YEAR', 'MONTH', 'DAY',
        'LEN', 'SUBSTRING', 'REPLACE', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM',
        'ROUND', 'CEILING', 'FLOOR', 'ABS', 'POWER', 'SQRT',
        'STRING_AGG', 'JSON_VALUE', 'JSON_QUERY',
        'TRY_CAST', 'TRY_CONVERT', 'IIF', 'CHOOSE'
    }

    all_functions_found = {}  # func_name -> [list of SPs using it]
    sps_with_functions = set()

    for sp_id, sp_schema, sp_name, ddl in sps:
        if not ddl:
            continue

        functions_in_sp = set()

        for pattern in function_patterns:
            matches = re.findall(pattern, ddl, re.IGNORECASE)
            for schema, func_name in matches:
                # Skip built-in functions
                if func_name.upper() in builtin_functions:
                    continue

                # Skip system schemas
                if schema.lower() in ['sys', 'information_schema']:
                    continue

                func_full = f"{schema}.{func_name}"
                functions_in_sp.add(func_full)

        if functions_in_sp:
            sps_with_functions.add(f"{sp_schema}.{sp_name}")
            for func in functions_in_sp:
                if func not in all_functions_found:
                    all_functions_found[func] = []
                all_functions_found[func].append(f"{sp_schema}.{sp_name}")

    # Classify functions
    real_functions = {f for f in all_functions_found if f.lower() in function_catalog}
    phantom_functions = {f for f in all_functions_found if f.lower() not in function_catalog}

    # Report results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n📊 Summary:")
    print(f"   - Total SPs analyzed: {len(sps)}")
    print(f"   - SPs using functions: {len(sps_with_functions)} ({len(sps_with_functions)/len(sps)*100:.1f}%)")
    print(f"   - Unique functions called: {len(all_functions_found)}")
    print(f"     • Real (in catalog): {len(real_functions)}")
    print(f"     • Phantom (not in catalog): {len(phantom_functions)}")

    if phantom_functions:
        print(f"\n⚠️  Phantom Functions (will get negative IDs + ❓ symbol):")
        for func in sorted(phantom_functions)[:10]:
            used_by_count = len(all_functions_found[func])
            print(f"   - {func} (used by {used_by_count} SP{'s' if used_by_count > 1 else ''})")

        if len(phantom_functions) > 10:
            print(f"   ... and {len(phantom_functions) - 10} more")

        print(f"\n   Top 5 SPs using phantom functions:")
        sp_func_counts = {}
        for func in phantom_functions:
            for sp in all_functions_found[func]:
                sp_func_counts[sp] = sp_func_counts.get(sp, 0) + 1

        for sp, count in sorted(sp_func_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {sp}: {count} function{'s' if count > 1 else ''}")

    if real_functions:
        print(f"\n✅ Real Functions (will get ◆ diamond symbol):")
        for func in sorted(real_functions)[:10]:
            used_by_count = len(all_functions_found[func])
            print(f"   - {func} (used by {used_by_count} SP{'s' if used_by_count > 1 else ''})")

        if len(real_functions) > 10:
            print(f"   ... and {len(real_functions) - 10} more")

    if not all_functions_found:
        print("\n✅ No user-defined functions detected in your stored procedures.")
        print("   Your SPs only use built-in functions (CAST, CONVERT, etc.)")

    workspace.disconnect()

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    if phantom_functions:
        print(f"\n1. Run full reload: ./start-app.sh")
        print(f"2. Expect {len(phantom_functions)} phantom functions with negative IDs")
        print(f"3. Frontend will show them with ❓ question mark symbol")
        print(f"4. When you extract function metadata, they'll be promoted to ◆ diamond")
    elif real_functions:
        print(f"\n1. Run full reload: ./start-app.sh")
        print(f"2. All {len(real_functions)} functions will show with ◆ diamond symbol")
    else:
        print(f"\n1. Run full reload: ./start-app.sh")
        print(f"2. No function nodes will appear in lineage graph")
        print(f"3. Focus will be on phantom tables instead")


if __name__ == "__main__":
    try:
        analyze_functions()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
