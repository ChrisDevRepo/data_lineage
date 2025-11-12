#!/usr/bin/env python3
"""
Check parsing results after regex-first fix.
"""
import duckdb
import json

conn = duckdb.connect('data/lineage_workspace.duckdb')

print("="*80)
print("PARSING RESULTS AFTER REGEX-FIRST BASELINE FIX")
print("="*80)
print()

# Overall stats
print("📊 OVERALL STATISTICS")
print("-"*80)

total_sps = conn.execute("""
    SELECT COUNT(*) FROM objects WHERE object_type = 'Stored Procedure'
""").fetchone()[0]

sps_with_deps = conn.execute("""
    SELECT COUNT(DISTINCT object_id)
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    AND (inputs IS NOT NULL OR outputs IS NOT NULL)
""").fetchone()[0]

sps_with_inputs = conn.execute("""
    SELECT COUNT(DISTINCT object_id)
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    AND inputs IS NOT NULL
""").fetchone()[0]

sps_with_outputs = conn.execute("""
    SELECT COUNT(DISTINCT object_id)
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    AND outputs IS NOT NULL
""").fetchone()[0]

print(f"Total SPs: {total_sps}")
print(f"SPs with dependencies: {sps_with_deps} ({sps_with_deps/total_sps*100:.1f}%)")
print(f"SPs with inputs: {sps_with_inputs} ({sps_with_inputs/total_sps*100:.1f}%)")
print(f"SPs with outputs: {sps_with_outputs} ({sps_with_outputs/total_sps*100:.1f}%)")
print()

# Confidence distribution
print("📈 CONFIDENCE DISTRIBUTION")
print("-"*80)

confidence_dist = conn.execute("""
    SELECT
        confidence,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    GROUP BY confidence
    ORDER BY confidence DESC
""").fetchall()

for conf, count, pct in confidence_dist:
    bar = "█" * int(pct / 2)
    print(f"Confidence {int(conf):3d}: {int(count):4d} SPs ({pct:5.1f}%) {bar}")
print()

# Average dependencies
print("📦 AVERAGE DEPENDENCIES PER SP")
print("-"*80)

avg_inputs = conn.execute("""
    SELECT AVG(json_array_length(inputs))
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    AND inputs IS NOT NULL
""").fetchone()[0]

avg_outputs = conn.execute("""
    SELECT AVG(json_array_length(outputs))
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
    AND outputs IS NOT NULL
""").fetchone()[0]

print(f"Average inputs per SP: {avg_inputs:.2f}")
print(f"Average outputs per SP: {avg_outputs:.2f}")
print()

# Test specific SPs
print("🔬 TEST CASE VALIDATION")
print("-"*80)

test_sps = [
    'spLoadFactLaborCostForEarnedValue_Post',
    'spLoadDimTemplateType'
]

for sp_name in test_sps:
    result = conn.execute("""
        SELECT
            o.object_name,
            o.schema_name,
            lm.inputs,
            lm.outputs,
            lm.confidence
        FROM objects o
        JOIN lineage_metadata lm ON o.object_id = lm.object_id
        WHERE o.object_name = ?
    """, [sp_name]).fetchone()

    if result:
        name, schema, inputs_json, outputs_json, confidence = result
        sources = json.loads(inputs_json) if inputs_json else []
        targets = json.loads(outputs_json) if outputs_json else []

        print(f"✅ {schema}.{name}")
        print(f"   Inputs: {len(sources)} tables")
        for src in sources[:5]:
            print(f"     - {src}")
        if len(sources) > 5:
            print(f"     ... and {len(sources) - 5} more")
        print(f"   Outputs: {len(targets)} tables")
        for tgt in targets:
            print(f"     - {tgt}")
        print(f"   Confidence: {confidence}")
        print()
    else:
        print(f"❌ {sp_name} - NOT FOUND")
        print()

# Top SPs by dependency count
print("🏆 TOP 10 SPs BY DEPENDENCY COUNT")
print("-"*80)

top_sps = conn.execute("""
    SELECT
        o.schema_name || '.' || o.object_name as sp_full_name,
        json_array_length(COALESCE(lm.inputs, '[]')) as input_count,
        json_array_length(COALESCE(lm.outputs, '[]')) as output_count,
        lm.confidence
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    WHERE o.object_type = 'Stored Procedure'
    ORDER BY (json_array_length(COALESCE(lm.inputs, '[]')) + json_array_length(COALESCE(lm.outputs, '[]'))) DESC
    LIMIT 10
""").fetchall()

for sp_name, inputs, outputs, conf in top_sps:
    total = inputs + outputs
    print(f"{sp_name:60s} | IN: {int(inputs):2d} | OUT: {int(outputs):2d} | CONF: {int(conf):3d}")

print()
print("="*80)

conn.close()
