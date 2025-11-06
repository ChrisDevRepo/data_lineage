#!/usr/bin/env python3
"""
Quick script to check confidence distribution in workspace.
"""
import sys
sys.path.insert(0, '/home/chris/sandbox')

from lineage_v3.core import DuckDBWorkspace

workspace_path = '/home/chris/sandbox/data/lineage_workspace.duckdb'

with DuckDBWorkspace(workspace_path=workspace_path) as db:
    # Get confidence distribution
    result = db.query("""
    SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN lm.confidence >= 0.85 THEN 1 END) as conf_85_plus,
        COUNT(CASE WHEN lm.confidence >= 0.75 THEN 1 END) as conf_75_plus,
        COUNT(CASE WHEN lm.confidence >= 0.75 AND lm.confidence < 0.85 THEN 1 END) as conf_75_to_85,
        COUNT(CASE WHEN lm.confidence < 0.75 THEN 1 END) as conf_below_75
    FROM objects o
    LEFT JOIN lineage_metadata lm ON o.object_id = lm.object_id
    """)

    if result:
        row = result[0]
        total = row[0]
        conf_85 = row[1]
        conf_75 = row[2]
        conf_75_85 = row[3]
        conf_below_75 = row[4]

        print("=" * 60)
        print("CONFIDENCE DISTRIBUTION - ALL OBJECTS")
        print("=" * 60)
        print(f"Total objects: {total}")
        print()
        print(f"High confidence (≥0.85): {conf_85} ({conf_85/total*100:.1f}%)")
        print(f"High confidence (≥0.75): {conf_75} ({conf_75/total*100:.1f}%)")
        print(f"Medium range (0.75-0.84): {conf_75_85} ({conf_75_85/total*100:.1f}%)")
        print(f"Low confidence (<0.75): {conf_below_75} ({conf_below_75/total*100:.1f}%)")
        print("=" * 60)
        print()

        # Get by object type
        by_type = db.query("""
        SELECT
            o.object_type,
            COUNT(*) as total,
            COUNT(CASE WHEN lm.confidence >= 0.85 THEN 1 END) as conf_85_plus,
            COUNT(CASE WHEN lm.confidence >= 0.75 THEN 1 END) as conf_75_plus
        FROM objects o
        LEFT JOIN lineage_metadata lm ON o.object_id = lm.object_id
        GROUP BY o.object_type
        ORDER BY o.object_type
        """)

        print("BY OBJECT TYPE:")
        print("-" * 60)
        for row in by_type:
            obj_type, total, conf_85, conf_75 = row
            print(f"{obj_type}:")
            print(f"  Total: {total}")
            print(f"  High (≥0.85): {conf_85} ({conf_85/total*100:.1f}%)")
            print(f"  High (≥0.75): {conf_75} ({conf_75/total*100:.1f}%)")
            print()
