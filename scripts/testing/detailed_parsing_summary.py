#!/usr/bin/env python3
"""
Comprehensive parsing results summary.
Provides detailed breakdown of parsing success, SQLGlot performance, and external objects.
"""

import glob
from engine.core.duckdb_workspace import DuckDBWorkspace
from engine.parsers.quality_aware_parser import QualityAwareParser
from engine.config.settings import Settings

def main():
    settings = Settings()

    # Find parquet files
    parquet_files = glob.glob('./temp/*.parquet')
    if not parquet_files:
        print("❌ No parquet files found in ./temp/")
        return

    # Create workspace and parse
    print("Loading parquet files and parsing...")
    workspace = DuckDBWorkspace(parquet_files, settings)
    parser = QualityAwareParser(workspace, enable_sql_cleaning=True)

    # Parse all SPs
    sp_ids = workspace.get_all_stored_procedure_ids()

    print("=" * 80)
    print("COMPREHENSIVE PARSING RESULTS SUMMARY")
    print("=" * 80)

    # 1. Overall Statistics
    print("\n📊 OVERALL STATISTICS")
    print("-" * 80)

    result = workspace.conn.execute("""
        SELECT
            COUNT(*) as total_sps,
            COUNT(*) FILTER (WHERE inputs IS NOT NULL OR outputs IS NOT NULL) as with_deps,
            COUNT(*) FILTER (WHERE inputs IS NULL AND outputs IS NULL) as no_deps,
            COUNT(*) FILTER (WHERE json_array_length(COALESCE(inputs, '[]')) = 0
                              AND json_array_length(COALESCE(outputs, '[]')) = 0) as empty_lineage
        FROM lineage_metadata
        WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    """).fetchone()

    total, with_deps, no_deps, empty = result
    print(f"Total Stored Procedures: {total}")
    print(f"  ✅ With dependencies: {with_deps} ({with_deps/total*100:.1f}%)")
    print(f"  ❌ No dependencies (NULL): {no_deps} ({no_deps/total*100:.1f}%)")
    print(f"  ⚠️  Empty lineage (0 inputs AND 0 outputs): {empty} ({empty/total*100:.1f}%)")

    # Success rate
    success_rate = (total - empty) / total * 100 if total > 0 else 0
    print(f"\n🎯 EFFECTIVE SUCCESS RATE: {success_rate:.1f}%")

    # 2. Input/Output Statistics
    print("\n📥📤 INPUT/OUTPUT STATISTICS")
    print("-" * 80)

    result = workspace.conn.execute("""
        SELECT
            COUNT(*) FILTER (WHERE json_array_length(COALESCE(inputs, '[]')) > 0) as with_inputs,
            COUNT(*) FILTER (WHERE json_array_length(COALESCE(outputs, '[]')) > 0) as with_outputs,
            COUNT(*) FILTER (WHERE json_array_length(COALESCE(inputs, '[]')) > 0
                              AND json_array_length(COALESCE(outputs, '[]')) > 0) as with_both,
            COUNT(*) FILTER (WHERE json_array_length(COALESCE(inputs, '[]')) = 0) as no_inputs,
            COUNT(*) FILTER (WHERE json_array_length(COALESCE(outputs, '[]')) = 0) as no_outputs
        FROM lineage_metadata
        WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    """).fetchone()

    with_inputs, with_outputs, with_both, no_inputs, no_outputs = result
    print(f"  📥 With inputs: {with_inputs} ({with_inputs/total*100:.1f}%)")
    print(f"  📤 With outputs: {with_outputs} ({with_outputs/total*100:.1f}%)")
    print(f"  ✅ With both: {with_both} ({with_both/total*100:.1f}%)")
    print(f"  ⚠️  No inputs: {no_inputs} ({no_inputs/total*100:.1f}%)")
    print(f"  ⚠️  No outputs: {no_outputs} ({no_outputs/total*100:.1f}%)")

    # 3. Confidence Distribution
    print("\n🎯 CONFIDENCE DISTRIBUTION")
    print("-" * 80)

    results = workspace.conn.execute("""
        SELECT
            confidence,
            COUNT(*) as count
        FROM lineage_metadata
        WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
        GROUP BY confidence
        ORDER BY confidence DESC
    """).fetchall()

    for conf, count in results:
        pct = count / total * 100
        if conf == 100:
            label = "Perfect (≥90% completeness)"
        elif conf == 85:
            label = "Good (70-89% completeness)"
        elif conf == 75:
            label = "Acceptable (50-69% completeness)"
        else:
            label = "Failed (<50% or parse error)"
        print(f"  Confidence {int(conf):3d}: {count:3d} SPs ({pct:5.1f}%) - {label}")

    # 4. SQLGlot Analysis
    print("\n🔍 SQLGLOT PARSING ANALYSIS")
    print("-" * 80)

    result = workspace.conn.execute("""
        SELECT COUNT(*) FROM lineage_metadata WHERE expected_count IS NOT NULL AND expected_count > 0
    """).fetchone()[0]

    if result > 0:
        result = workspace.conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE found_count > expected_count) as enhanced,
                COUNT(*) FILTER (WHERE found_count = expected_count) as exact,
                COUNT(*) FILTER (WHERE found_count < expected_count) as less,
                ROUND(AVG(found_count - expected_count), 2) as avg_added
            FROM lineage_metadata
            WHERE expected_count > 0
        """).fetchone()

        total_analyzed, enhanced, exact, less, avg_added = result
        print(f"Total SPs analyzed (with expected_count): {total_analyzed}")
        print(f"  ✨ SQLGlot enhanced (found > expected): {enhanced} ({enhanced/total_analyzed*100:.1f}%)")
        print(f"  ✅ Exact match (found = expected): {exact} ({exact/total_analyzed*100:.1f}%)")
        print(f"  ⚠️  Found less (regression): {less} ({less/total_analyzed*100:.1f}%)")
        print(f"  📊 Average tables added by SQLGlot: +{avg_added:.2f} per SP")

        # Parse success rate (could parse vs couldn't)
        parse_success_rate = (enhanced + exact) / total_analyzed * 100
        print(f"\n  🎯 SQLGlot parse success rate: {parse_success_rate:.1f}%")
    else:
        print("  ⚠️  expected_count not populated (DEBUG logging was disabled)")
        print("  Cannot determine SQLGlot enhancement impact.")
        print("  To enable: Set LOG_LEVEL=DEBUG in .env")

    # 5. Phantom Objects
    print("\n🔗 PHANTOM/EXTERNAL OBJECTS")
    print("-" * 80)

    tables = workspace.conn.execute("SHOW TABLES").fetchall()
    table_names = [row[0] for row in tables]

    if 'phantom_objects' in table_names:
        count = workspace.conn.execute("SELECT COUNT(*) FROM phantom_objects").fetchone()[0]

        if count > 0:
            print(f"Total phantom objects found: {count}")

            # By schema
            results = workspace.conn.execute("""
                SELECT schema_name, COUNT(*) as cnt
                FROM phantom_objects
                GROUP BY schema_name
                ORDER BY cnt DESC
            """).fetchall()

            print("\nPhantom objects by schema:")
            for schema, cnt in results:
                print(f"  {schema}: {cnt} objects")

            # Sample
            results = workspace.conn.execute("""
                SELECT schema_name, object_name, object_type
                FROM phantom_objects
                LIMIT 10
            """).fetchall()

            print("\nSample phantom objects:")
            for schema, name, obj_type in results:
                print(f"  🔗 {schema}.{name} ({obj_type})")
        else:
            print("✅ No phantom objects (all dependencies resolved)")
    else:
        print("No phantom_objects table (external dependency tracking disabled)")

    # 6. Problem SPs
    print("\n⚠️  STORED PROCEDURES WITH ISSUES")
    print("-" * 80)

    # Empty lineage
    results = workspace.conn.execute("""
        SELECT o.schema_name || '.' || o.object_name as sp_name, lm.confidence
        FROM objects o
        JOIN lineage_metadata lm ON o.object_id = lm.object_id
        WHERE o.object_type = 'Stored Procedure'
            AND json_array_length(COALESCE(lm.inputs, '[]')) = 0
            AND json_array_length(COALESCE(lm.outputs, '[]')) = 0
        LIMIT 10
    """).fetchall()

    if results:
        print(f"SPs with EMPTY lineage (0 inputs AND 0 outputs): {len(results)}")
        for sp_name, conf in results:
            print(f"  ❌ {sp_name} (confidence: {conf})")
    else:
        print("✅ No SPs with empty lineage!")

    # Low confidence
    results = workspace.conn.execute("""
        SELECT o.schema_name || '.' || o.object_name as sp_name, lm.confidence
        FROM objects o
        JOIN lineage_metadata lm ON o.object_id = lm.object_id
        WHERE o.object_type = 'Stored Procedure'
            AND lm.confidence < 85
        ORDER BY lm.confidence
        LIMIT 5
    """).fetchall()

    if results:
        print(f"\nSPs with confidence < 85 (first 5):")
        for sp_name, conf in results:
            print(f"  ⚠️  {sp_name} (confidence: {conf})")

    # 7. Average Dependencies
    print("\n📈 AVERAGE DEPENDENCIES PER SP")
    print("-" * 80)

    result = workspace.conn.execute("""
        SELECT
            ROUND(AVG(json_array_length(COALESCE(inputs, '[]'))), 2) as avg_in,
            ROUND(AVG(json_array_length(COALESCE(outputs, '[]'))), 2) as avg_out,
            MAX(json_array_length(COALESCE(inputs, '[]'))) as max_in,
            MAX(json_array_length(COALESCE(outputs, '[]'))) as max_out
        FROM lineage_metadata
        WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    """).fetchone()

    avg_in, avg_out, max_in, max_out = result
    print(f"Average inputs per SP: {avg_in:.2f} (max: {max_in})")
    print(f"Average outputs per SP: {avg_out:.2f} (max: {max_out})")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
