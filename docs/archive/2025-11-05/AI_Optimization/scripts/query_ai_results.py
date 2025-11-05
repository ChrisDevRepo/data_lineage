#!/usr/bin/env python3
"""
Query AI inference results directly using duckdb
"""
import sys

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed")
    print("Run: pip install duckdb")
    sys.exit(1)

conn = duckdb.connect('../lineage_v3/lineage_workspace.duckdb')

# Get AI-inferred tables
results = conn.execute("""
    SELECT
        o.schema_name || '.' || o.object_name as table_name,
        lm.confidence,
        lm.outputs as sp_ids,
        lm.primary_source
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    WHERE o.object_type = 'Table'
      AND lm.primary_source = 'ai'
    ORDER BY lm.confidence DESC
    LIMIT 20
""").fetchall()

if not results:
    print("❌ NO AI-INFERRED TABLES FOUND")
    print("\nChecking what sources exist:")
    sources = conn.execute("""
        SELECT primary_source, COUNT(*)
        FROM lineage_metadata
        GROUP BY primary_source
    """).fetchall()
    for source, count in sources:
        print(f"  - {source}: {count}")
    conn.close()
    sys.exit(0)

print('=' * 80)
print(f'TOP 20 AI-INFERRED TABLES (found {len(results)} results)')
print('=' * 80)

correct = 0
questionable = 0

for table_name, conf, sp_ids, source in results:
    print(f'\nTable: {table_name}')
    print(f'Confidence: {conf:.2f} | Source: {source}')

    table_schema = table_name.split('.')[0]
    table_clean = table_name.split('.')[1].lower().replace('_', '')

    if sp_ids and sp_ids not in ('[]', '', None):
        import json
        try:
            sp_id_list = json.loads(sp_ids) if isinstance(sp_ids, str) else sp_ids
        except:
            sp_id_list = []

        if sp_id_list:
            print(f'Matched {len(sp_id_list)} SP(s):')

        has_warnings = False
        for sp_id in sp_id_list:
            sp = conn.execute(
                'SELECT schema_name, object_name FROM objects WHERE object_id = ?',
                [sp_id]
            ).fetchone()

            if sp:
                sp_schema, sp_name = sp
                print(f'  ✅ {sp_schema}.{sp_name}')

                # Plausibility checks
                if sp_schema != table_schema:
                    print(f'     ⚠️  Different schema: {sp_schema} vs {table_schema}')
                    has_warnings = True

                sp_clean = sp_name.lower().replace('_', '').replace('spload', '')
                if table_clean not in sp_clean and sp_clean not in table_clean:
                    print(f'     ⚠️  Name mismatch')
                    has_warnings = True

            if has_warnings:
                print('  📊 Verdict: ⚠️  QUESTIONABLE')
                questionable += 1
            else:
                print('  📊 Verdict: ✅ LOOKS CORRECT')
                correct += 1
    else:
        print('  (No SPs)')

print('\n' + '=' * 80)
print('SPOT-CHECK SUMMARY')
print('=' * 80)
print(f'✅ Looks Correct: {correct}/20 ({correct/20*100:.0f}%)')
print(f'⚠️  Questionable: {questionable}/20 ({questionable/20*100:.0f}%)')

if correct/20 >= 0.90:
    print('\n✅ PASS: ≥90% accuracy - Ready for UAT')
elif correct/20 >= 0.75:
    print('\n⚠️  ITERATE: 75-89% accuracy - Add more few-shot examples')
else:
    print('\n❌ DEBUG: <75% accuracy - Review AI prompt/strategy')

conn.close()
