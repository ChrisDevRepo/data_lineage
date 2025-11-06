#!/usr/bin/env python3
"""
Check for Unrelated Objects - Objects with No Inputs AND No Outputs

This script identifies objects that were successfully parsed but have neither
inputs nor outputs, indicating potential parsing issues.

Author: Claude Code
Date: 2025-11-03
"""
import json
from pathlib import Path
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

print("=" * 80)
print("UNRELATED OBJECTS CHECK - v4.0.1")
print("Finding objects with NO inputs AND NO outputs")
print("=" * 80)

with DuckDBWorkspace("data/lineage_workspace.duckdb") as ws:
    # Query for objects with empty inputs AND outputs
    # High confidence (≥0.85) but no connections = suspicious
    query = """
    SELECT
        o.object_id,
        o.schema_name,
        o.object_name,
        o.object_type,
        lm.confidence,
        lm.inputs,
        lm.outputs,
        d.definition
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    JOIN definitions d ON o.object_id = d.object_id
    WHERE lm.confidence >= 0.50  -- Successfully parsed (not failed)
      AND (lm.inputs = '[]' OR lm.inputs IS NULL)
      AND (lm.outputs = '[]' OR lm.outputs IS NULL)
    ORDER BY lm.confidence DESC, o.object_type, o.object_name
    """

    results = ws.query(query)

    print(f"\n📊 SUMMARY")
    print(f"   Found: {len(results)} unrelated objects")
    print(f"   Criteria: confidence ≥0.50, inputs = [], outputs = []")

    if not results:
        print("\n✅ No unrelated objects found - all objects have connections!")
        exit(0)

    # Categorize by confidence
    high_conf = [r for r in results if r[4] >= 0.85]
    med_conf = [r for r in results if 0.75 <= r[4] < 0.85]
    low_conf = [r for r in results if r[4] < 0.75]

    print(f"\n   Breakdown by confidence:")
    print(f"   - High (≥0.85): {len(high_conf)} objects")
    print(f"   - Medium (0.75-0.84): {len(med_conf)} objects")
    print(f"   - Low (0.50-0.74): {len(low_conf)} objects")

    # Categorize by object type
    by_type = {}
    for r in results:
        obj_type = r[3]
        if obj_type not in by_type:
            by_type[obj_type] = []
        by_type[obj_type].append(r)

    print(f"\n   Breakdown by type:")
    for obj_type, objs in sorted(by_type.items()):
        print(f"   - {obj_type}: {len(objs)} objects")

    # Search patterns to look for in DDL
    suspicious_patterns = [
        # DML operations that should have targets
        (r'\bINSERT\s+INTO\s+', 'INSERT INTO'),
        (r'\bUPDATE\s+', 'UPDATE'),
        (r'\bDELETE\s+FROM\s+', 'DELETE FROM'),
        (r'\bMERGE\s+INTO\s+', 'MERGE INTO'),
        (r'\bTRUNCATE\s+TABLE\s+', 'TRUNCATE TABLE'),

        # DML operations that should have sources
        (r'\bFROM\s+\[?[a-zA-Z]', 'FROM clause'),
        (r'\bJOIN\s+\[?[a-zA-Z]', 'JOIN clause'),

        # Other indicators
        (r'\bSELECT\s+', 'SELECT statement'),
        (r'\bEXEC(?:UTE)?\s+\[?[a-zA-Z]', 'EXEC statement'),
        (r'\bCREATE\s+TABLE\s+', 'CREATE TABLE'),
        (r'\bDROP\s+TABLE\s+', 'DROP TABLE'),
    ]

    # Detailed analysis
    print(f"\n" + "=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80)

    issues_found = []

    for obj_id, schema, name, obj_type, conf, inputs, outputs, ddl in results:
        full_name = f"{schema}.{name}"

        print(f"\n{'─' * 80}")
        print(f"🔍 {full_name} [{obj_type}]")
        print(f"   Confidence: {conf:.2f}")
        print(f"   Object ID: {obj_id}")

        # Search for suspicious patterns
        import re
        patterns_found = []

        for pattern, description in suspicious_patterns:
            matches = re.findall(pattern, ddl, re.IGNORECASE)
            if matches:
                patterns_found.append((description, len(matches)))

        if patterns_found:
            print(f"\n   ⚠️  SUSPICIOUS PATTERNS FOUND:")
            for desc, count in patterns_found:
                print(f"      - {desc}: {count} occurrence(s)")

            # Show DDL snippet (first 500 chars)
            print(f"\n   📄 DDL SNIPPET (first 500 chars):")
            ddl_clean = re.sub(r'\s+', ' ', ddl[:500]).strip()
            print(f"      {ddl_clean}...")

            issues_found.append({
                'name': full_name,
                'type': obj_type,
                'confidence': conf,
                'patterns': patterns_found,
                'ddl_length': len(ddl)
            })
        else:
            print(f"   ✅ No suspicious patterns (might be utility SP or empty definition)")

    # Summary report
    print(f"\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)

    if issues_found:
        print(f"\n🔴 POTENTIAL ISSUES FOUND: {len(issues_found)} objects")
        print(f"\nThese objects have DML/DQL statements but no parsed connections.")
        print(f"This suggests potential parser bugs or edge cases.\n")

        # Sort by confidence (highest first)
        issues_found.sort(key=lambda x: x['confidence'], reverse=True)

        print(f"Top 10 High-Priority Objects (by confidence):")
        for i, issue in enumerate(issues_found[:10], 1):
            print(f"\n{i}. {issue['name']} [{issue['type']}]")
            print(f"   Confidence: {issue['confidence']:.2f}")
            print(f"   DDL Length: {issue['ddl_length']:,} chars")
            print(f"   Patterns found:")
            for desc, count in issue['patterns']:
                print(f"      - {desc}: {count}x")

        if len(issues_found) > 10:
            print(f"\n... and {len(issues_found) - 10} more")

        # Export detailed report
        report_path = Path("temp/unrelated_objects_report.json")
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump({
                'summary': {
                    'total_unrelated': len(results),
                    'high_confidence': len(high_conf),
                    'medium_confidence': len(med_conf),
                    'low_confidence': len(low_conf),
                    'with_suspicious_patterns': len(issues_found)
                },
                'by_type': {k: len(v) for k, v in by_type.items()},
                'issues': issues_found
            }, f, indent=2)

        print(f"\n💾 Detailed report saved to: {report_path}")

    else:
        print(f"\n✅ No suspicious patterns found in unrelated objects.")
        print(f"   These {len(results)} objects appear to be legitimately empty")
        print(f"   (e.g., utility SPs, stubs, or metadata objects)")

    # Recommendations
    print(f"\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if issues_found:
        print(f"""
Next Steps:
1. Investigate high-confidence objects first (confidence ≥0.85)
2. Manually review DDL for parser edge cases:
   - Complex CTEs
   - Dynamic SQL in variables
   - Temp tables (#table, @table)
   - OPENQUERY or OPENROWSET
   - PIVOT/UNPIVOT operations
3. Add test cases for confirmed parser bugs
4. Update ENHANCED_REMOVAL_PATTERNS if needed

To investigate specific object:
    python -c "from lineage_v3.core.duckdb_workspace import DuckDBWorkspace; \\
               ws = DuckDBWorkspace('data/lineage_workspace.duckdb'); \\
               result = ws.query('SELECT definition FROM definitions WHERE object_id = ?', [OBJECT_ID]); \\
               print(result[0][0])"
""")
    else:
        print(f"""
✅ All unrelated objects appear legitimate.
   No action required.
""")

print("=" * 80)
print("CHECK COMPLETE")
print("=" * 80)
