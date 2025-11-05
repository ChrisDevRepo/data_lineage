#!/usr/bin/env python3
"""
Validate AI inference results - check for false positives
"""
import sys
import os

# Add lineage_v3 to path
sys.path.insert(0, '/home/chris/sandbox/lineage_v3')

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed")
    print("Run: pip install duckdb")
    sys.exit(1)

DB_PATH = '/home/chris/sandbox/lineage_v3/lineage_workspace.duckdb'

if not os.path.exists(DB_PATH):
    print(f"❌ Database not found: {DB_PATH}")
    print("\nRun test first: ./scripts/test_ai_inference.sh")
    sys.exit(1)

conn = duckdb.connect(DB_PATH)

# Get AI-inferred tables
print('=' * 80)
print('AI INFERENCE VALIDATION')
print('=' * 80)

# Count totals
total = conn.execute("""
    SELECT COUNT(*)
    FROM lineage_metadata
    WHERE primary_source = 'ai'
""").fetchone()[0]

with_matches = conn.execute("""
    SELECT COUNT(*)
    FROM lineage_metadata
    WHERE primary_source = 'ai'
      AND outputs IS NOT NULL
      AND outputs <> '[]'
""").fetchone()[0]

empty = total - with_matches

print(f'\n📊 SUMMARY:')
print(f'  Total AI-processed tables: {total}')
print(f'  Tables with matches: {with_matches} ({with_matches/total*100:.1f}%)')
print(f'  Tables with no matches: {empty} ({empty/total*100:.1f}%)')

if with_matches == 0:
    print('\n❌ NO MATCHES FOUND')
    print('\nPossible reasons:')
    print('  1. AI is too conservative (prompt too strict)')
    print('  2. Few-shot examples don\'t cover enough patterns')
    print('  3. Unreferenced tables truly have no SP matches')
    conn.close()
    sys.exit(0)

# Get matches
results = conn.execute("""
    SELECT
        o.schema_name || '.' || o.object_name as table_name,
        lm.confidence,
        lm.outputs
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    WHERE lm.primary_source = 'ai'
      AND lm.outputs IS NOT NULL
      AND lm.outputs <> '[]'
    ORDER BY lm.confidence DESC
""").fetchall()

print(f'\n=' * 80)
print(f'MATCHES FOUND: {len(results)}')
print('=' * 80)

import json

correct = 0
questionable = 0

for table_name, conf, sp_ids in results:
    print(f'\n🎯 Table: {table_name}')
    print(f'   Confidence: {conf:.2f}')

    table_schema = table_name.split('.')[0]
    table_clean = table_name.split('.')[1].lower().replace('_', '')

    sp_id_list = json.loads(sp_ids) if isinstance(sp_ids, str) else sp_ids

    if sp_id_list:
        print(f'   Matched {len(sp_id_list)} SP(s):')

    has_warnings = False
    for sp_id in sp_id_list:
        sp = conn.execute(
            'SELECT schema_name, object_name, definition FROM objects WHERE object_id = ?',
            [sp_id]
        ).fetchone()

        if sp:
            sp_schema, sp_name, sp_definition = sp
            print(f'     ✅ {sp_schema}.{sp_name}')

            # Schema check
            if sp_schema != table_schema:
                print(f'        ⚠️  Different schema: {sp_schema} vs {table_schema}')
                has_warnings = True

            # Name similarity check
            sp_clean = sp_name.lower().replace('_', '').replace('spload', '')
            if table_clean not in sp_clean and sp_clean not in table_clean:
                print(f'        ⚠️  Name mismatch')
                has_warnings = True

            # SQL code check (if available)
            if sp_definition:
                table_name_simple = table_name.split('.')[1]
                if table_name_simple.lower() not in sp_definition.lower():
                    print(f'        ⚠️  Table "{table_name_simple}" not found in SQL code')
                    has_warnings = True
                else:
                    print(f'        ✅ Table "{table_name_simple}" found in SQL code')

    if has_warnings:
        print('   📊 Verdict: ⚠️  QUESTIONABLE')
        questionable += 1
    else:
        print('   📊 Verdict: ✅ LOOKS CORRECT')
        correct += 1

print('\n' + '=' * 80)
print('VALIDATION SUMMARY')
print('=' * 80)
print(f'✅ Looks Correct: {correct}/{len(results)} ({correct/len(results)*100:.0f}%)')
print(f'⚠️  Questionable: {questionable}/{len(results)} ({questionable/len(results)*100:.0f}%)')

precision = correct / len(results) if len(results) > 0 else 0
print(f'\n📈 Precision: {precision*100:.1f}%')

if precision >= 0.95:
    print('\n✅ EXCELLENT: ≥95% precision - Ready to increase coverage')
elif precision >= 0.75:
    print('\n⚠️  GOOD: 75-94% precision - Consider refining prompt')
else:
    print('\n❌ POOR: <75% precision - Review few-shot examples')

conn.close()
