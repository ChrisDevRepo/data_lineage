"""
Extract Real Test Cases from Production Data
=============================================

Purpose: Query DuckDB workspace to find stored procedures with varying
confidence levels and extract ambiguous table references for AI testing.

Usage:
    python lineage_v3/ai_analyzer/extract_test_cases.py
"""

import duckdb
import json
import os
from pathlib import Path

# DuckDB workspace path
WORKSPACE_PATH = "lineage_workspace.duckdb"

def extract_low_confidence_sps():
    """Find stored procedures with low parser confidence (<0.85)."""
    print("=" * 80)
    print("EXTRACTING LOW-CONFIDENCE STORED PROCEDURES")
    print("=" * 80)

    if not os.path.exists(WORKSPACE_PATH):
        print(f"❌ Workspace not found: {WORKSPACE_PATH}")
        return []

    conn = duckdb.connect(WORKSPACE_PATH, read_only=True)

    # Query for SPs with low confidence
    query = """
    SELECT
        o.object_id,
        o.schema_name,
        o.object_name,
        o.object_type,
        pm.confidence,
        pm.primary_source,
        d.definition
    FROM objects o
    LEFT JOIN parse_metadata pm ON o.object_id = pm.object_id
    LEFT JOIN definitions d ON o.object_id = d.object_id
    WHERE o.object_type = 'PROCEDURE'
      AND pm.confidence < 0.85
      AND d.definition IS NOT NULL
    ORDER BY pm.confidence ASC
    LIMIT 10
    """

    results = conn.execute(query).fetchall()
    conn.close()

    print(f"\nFound {len(results)} low-confidence stored procedures:\n")

    test_cases = []
    for row in results:
        object_id, schema, name, obj_type, confidence, source, definition = row
        print(f"  • [{schema}].[{name}]")
        print(f"    Confidence: {confidence:.2f} | Source: {source}")

        test_cases.append({
            "object_id": object_id,
            "schema": schema,
            "name": name,
            "confidence": confidence,
            "primary_source": source,
            "definition": definition[:500] + "..." if len(definition) > 500 else definition
        })

    return test_cases


def extract_high_confidence_sps():
    """Find stored procedures with high parser confidence (≥0.85)."""
    print("\n" + "=" * 80)
    print("EXTRACTING HIGH-CONFIDENCE STORED PROCEDURES")
    print("=" * 80)

    if not os.path.exists(WORKSPACE_PATH):
        print(f"❌ Workspace not found: {WORKSPACE_PATH}")
        return []

    conn = duckdb.connect(WORKSPACE_PATH, read_only=True)

    # Query for SPs with high confidence
    query = """
    SELECT
        o.object_id,
        o.schema_name,
        o.object_name,
        o.object_type,
        pm.confidence,
        pm.primary_source,
        d.definition
    FROM objects o
    LEFT JOIN parse_metadata pm ON o.object_id = pm.object_id
    LEFT JOIN definitions d ON o.object_id = d.object_id
    WHERE o.object_type = 'PROCEDURE'
      AND pm.confidence >= 0.85
      AND d.definition IS NOT NULL
    ORDER BY pm.confidence DESC
    LIMIT 5
    """

    results = conn.execute(query).fetchall()
    conn.close()

    print(f"\nFound {len(results)} high-confidence stored procedures:\n")

    test_cases = []
    for row in results:
        object_id, schema, name, obj_type, confidence, source, definition = row
        print(f"  • [{schema}].[{name}]")
        print(f"    Confidence: {confidence:.2f} | Source: {source}")

        test_cases.append({
            "object_id": object_id,
            "schema": schema,
            "name": name,
            "confidence": confidence,
            "primary_source": source,
            "definition": definition[:500] + "..." if len(definition) > 500 else definition
        })

    return test_cases


def get_available_tables():
    """Get list of all available tables for disambiguation candidates."""
    if not os.path.exists(WORKSPACE_PATH):
        return []

    conn = duckdb.connect(WORKSPACE_PATH, read_only=True)

    query = """
    SELECT DISTINCT schema_name, object_name
    FROM objects
    WHERE object_type = 'TABLE'
    ORDER BY schema_name, object_name
    """

    results = conn.execute(query).fetchall()
    conn.close()

    tables = [f"{schema}.{name}" for schema, name in results]
    return tables


def save_test_dataset(low_confidence, high_confidence, tables):
    """Save extracted test cases to JSON file."""
    output_dir = Path("lineage_v3/ai_analyzer")
    output_file = output_dir / "test_dataset.json"

    dataset = {
        "metadata": {
            "total_low_confidence": len(low_confidence),
            "total_high_confidence": len(high_confidence),
            "total_tables": len(tables),
            "generated_at": "2025-10-31"
        },
        "low_confidence_cases": low_confidence,
        "high_confidence_cases": high_confidence,
        "available_tables": tables[:50]  # Limit to 50 for brevity
    }

    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ Test dataset saved to: {output_file}")
    print("=" * 80)
    print(f"  Low-confidence cases: {len(low_confidence)}")
    print(f"  High-confidence cases: {len(high_confidence)}")
    print(f"  Available tables: {len(tables)}")


def main():
    """Extract test cases from production data."""
    print("\n🔍 EXTRACTING TEST CASES FROM PRODUCTION DATA")
    print("Purpose: Find real SPs with varying confidence for AI comparison\n")

    # Extract low-confidence cases (parser struggled)
    low_confidence = extract_low_confidence_sps()

    # Extract high-confidence cases (parser did well)
    high_confidence = extract_high_confidence_sps()

    # Get available tables for disambiguation
    tables = get_available_tables()

    # Save dataset
    save_test_dataset(low_confidence, high_confidence, tables)

    print("\n📋 NEXT STEPS:")
    print("1. Review test_dataset.json for extracted cases")
    print("2. Manually identify ambiguous table references in each SP")
    print("3. Add ground truth (correct table resolutions)")
    print("4. Run enhanced AI test with real production cases")


if __name__ == "__main__":
    main()
