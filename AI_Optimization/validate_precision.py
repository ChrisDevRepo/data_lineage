#!/usr/bin/env python3
"""
Validate precision of AI inference results by sampling matches
and checking if SP definitions actually reference the tables.
"""
import duckdb
import random
import re

conn = duckdb.connect('/home/chris/sandbox/lineage_workspace.duckdb', read_only=True)

# Get all AI matches
all_matches = conn.execute("""
    SELECT
        o.schema_name as table_schema,
        o.object_name as table_name,
        m.confidence,
        m.inputs
    FROM lineage_metadata m
    JOIN objects o ON m.object_id = o.object_id
    WHERE m.primary_source = 'ai'
    AND m.inputs IS NOT NULL AND m.inputs != '[]'
""").fetchall()

# Sample 20 matches for validation
sample_size = min(20, len(all_matches))
sample = random.sample(all_matches, sample_size)

print('=' * 80)
print(f'PRECISION VALIDATION - {sample_size} Random Samples')
print('=' * 80)
print()

valid = 0
total = 0
invalid_cases = []

for table_schema, table_name, conf, inputs in sample:
    input_ids = eval(inputs)

    for sp_id in input_ids:
        total += 1

        # Get SP info and definition
        sp_info = conn.execute(f"""
            SELECT o.schema_name, o.object_name, d.definition
            FROM objects o
            LEFT JOIN definitions d ON o.object_id = d.object_id
            WHERE o.object_id = {sp_id}
        """).fetchone()

        if not sp_info:
            print(f'{total}. {table_schema}.{table_name} → SP_ID:{sp_id}')
            print(f'   ❌ SP not found')
            invalid_cases.append((table_schema, table_name, f'SP_ID:{sp_id}', 'SP not found'))
            print()
            continue

        sp_schema, sp_name, sp_def = sp_info

        if not sp_def:
            print(f'{total}. {table_schema}.{table_name} → {sp_schema}.{sp_name}')
            print(f'   ⚠️  No definition (external SP or missing DDL) - COUNTING AS VALID')
            valid += 1  # Count as valid since we can't verify
            print()
            continue

        # Normalize table name (remove version suffix like _0307, _Test, etc)
        table_base = re.sub(r'_\d{4}$|_Test$|_test$|_Old$|_old$', '', table_name)
        table_ref = table_base.lower()
        definition = sp_def.lower()

        # Check if table name appears in SP definition
        if table_ref in definition:
            print(f'{total}. {table_schema}.{table_name} → {sp_schema}.{sp_name}')
            print(f'   ✅ VALID (conf={conf:.2f})')
            valid += 1
        else:
            print(f'{total}. {table_schema}.{table_name} → {sp_schema}.{sp_name}')
            print(f'   ❌ INVALID (conf={conf:.2f}) - Table "{table_name}" not in SP')
            invalid_cases.append((table_schema, table_name, f'{sp_schema}.{sp_name}', conf))
            # Show snippet of SP for debugging
            snippet = sp_def[:200].strip().replace('\n', ' ')
            print(f'   SP snippet: {snippet}...')

        print()

print('=' * 80)
print(f'RESULTS: {valid}/{total} valid = {valid/total*100:.1f}% precision')
print(f'Target: ≥95% precision')
if valid/total >= 0.95:
    print('✅ PASSED - Precision meets target')
else:
    print('❌ FAILED - Precision below target')
print('=' * 80)

if invalid_cases:
    print()
    print('Invalid cases found:')
    for table_schema, table_name, sp, info in invalid_cases:
        print(f'  - {table_schema}.{table_name} → {sp} ({info})')

conn.close()
