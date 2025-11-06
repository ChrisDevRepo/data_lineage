#!/usr/bin/env python3
"""
Create baseline snapshot for parser evaluation.

This script creates a baseline from the production lineage_workspace.duckdb
containing SP DDLs, expected dependencies, and metadata for tracking parser quality.
"""

import duckdb
import hashlib
import sys
from datetime import datetime
from pathlib import Path

def create_baseline(baseline_name: str, source_db: str = "lineage_workspace.duckdb"):
    """Create baseline snapshot from production workspace."""

    baseline_path = Path("evaluation_baselines") / f"{baseline_name}.duckdb"

    if baseline_path.exists():
        print(f"❌ Error: Baseline '{baseline_name}' already exists at {baseline_path}")
        sys.exit(1)

    print(f"📊 Creating baseline: {baseline_name}")
    print(f"   Source: {source_db}")
    print(f"   Target: {baseline_path}")
    print()

    # Connect to source (read-only)
    source_conn = duckdb.connect(source_db, read_only=True)

    # Connect to new baseline
    baseline_conn = duckdb.connect(str(baseline_path))

    try:
        # Create baseline schema
        baseline_conn.execute("""
            CREATE TABLE baseline_metadata (
                baseline_name VARCHAR,
                created_at TIMESTAMP,
                source_database VARCHAR,
                total_objects INTEGER,
                description VARCHAR
            )
        """)

        baseline_conn.execute("""
            CREATE TABLE baseline_objects (
                object_id INTEGER PRIMARY KEY,
                object_name VARCHAR,
                schema_name VARCHAR,
                object_type VARCHAR,
                ddl_text TEXT,
                ddl_hash VARCHAR,
                expected_inputs VARCHAR,  -- JSON array of object_ids
                expected_outputs VARCHAR  -- JSON array of object_ids
            )
        """)

        baseline_conn.execute("""
            CREATE TABLE baseline_change_log (
                object_id INTEGER,
                changed_at TIMESTAMP,
                old_ddl_hash VARCHAR,
                new_ddl_hash VARCHAR,
                reason VARCHAR
            )
        """)

        # Extract objects with DDL and expected dependencies
        print("📥 Extracting objects from source database...")

        query = """
            SELECT
                o.object_id,
                o.object_name,
                o.schema_name,
                o.object_type,
                d.definition as ddl_text,
                lm.inputs as expected_inputs,
                lm.outputs as expected_outputs
            FROM objects o
            LEFT JOIN definitions d ON o.object_id = d.object_id
            LEFT JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_type IN ('Stored Procedure', 'View', 'Function')
              AND d.definition IS NOT NULL
            ORDER BY o.object_id
        """

        objects = source_conn.execute(query).fetchall()

        print(f"   Found {len(objects)} objects with DDL")
        print()

        # Insert objects into baseline
        object_count = 0
        for obj in objects:
            object_id, object_name, schema_name, object_type, ddl_text, inputs, outputs = obj

            # Calculate DDL hash
            ddl_hash = hashlib.sha256(ddl_text.encode('utf-8')).hexdigest()

            # Convert inputs/outputs to JSON strings (they're already stored as JSON in lineage_metadata)
            inputs_json = inputs if inputs else '[]'
            outputs_json = outputs if outputs else '[]'

            baseline_conn.execute("""
                INSERT INTO baseline_objects
                (object_id, object_name, schema_name, object_type, ddl_text, ddl_hash, expected_inputs, expected_outputs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [object_id, object_name, schema_name, object_type, ddl_text, ddl_hash, inputs_json, outputs_json])

            object_count += 1

        # Insert metadata
        baseline_conn.execute("""
            INSERT INTO baseline_metadata
            (baseline_name, created_at, source_database, total_objects, description)
            VALUES (?, ?, ?, ?, ?)
        """, [
            baseline_name,
            datetime.now(),
            source_db,
            object_count,
            f"Baseline for v4.0.0 slim parser (no AI)"
        ])

        baseline_conn.commit()

        # Get statistics
        stats = baseline_conn.execute("""
            SELECT
                object_type,
                COUNT(*) as count
            FROM baseline_objects
            GROUP BY object_type
            ORDER BY count DESC
        """).fetchall()

        print("✅ Baseline created successfully!")
        print()
        print("📈 Statistics:")
        print(f"   Total objects: {object_count}")
        for object_type, count in stats:
            print(f"   {object_type}: {count}")
        print()
        print(f"📁 Baseline file: {baseline_path}")
        print(f"   Size: {baseline_path.stat().st_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"❌ Error creating baseline: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        source_conn.close()
        baseline_conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_baseline.py <baseline_name>")
        sys.exit(1)

    baseline_name = sys.argv[1]
    create_baseline(baseline_name)
