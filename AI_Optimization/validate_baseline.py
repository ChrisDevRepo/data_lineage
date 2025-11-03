#!/usr/bin/env python3
"""
Validate GLCognosData_Test against baseline pattern
"""
import duckdb
import re

conn = duckdb.connect('/home/chris/sandbox/lineage_workspace.duckdb', read_only=True)

# Get spLoadGLCognosData_Test definition
sp_def = conn.execute("""
    SELECT d.definition
    FROM objects o
    JOIN definitions d ON o.object_id = d.object_id
    WHERE o.schema_name = 'CONSUMPTION_FINANCE'
    AND o.object_name = 'spLoadGLCognosData_Test'
""").fetchone()

if not sp_def or not sp_def[0]:
    print('SP not found')
    exit(1)

definition = sp_def[0]

# Extract table references using pattern: [schema].[table] or schema.table
insert_pattern = r'(?:insert\s+into|truncate\s+table)\s+\[?(\w+)\]?\.\[?(\w+)\]?'
from_pattern = r'(?:from|join)\s+\[?(\w+)\]?\.\[?(\w+)\]?'

inserts = re.findall(insert_pattern, definition, re.IGNORECASE)
froms = re.findall(from_pattern, definition, re.IGNORECASE)

print('=' * 80)
print('SP: spLoadGLCognosData_Test')
print('=' * 80)
print()

# Deduplicate and categorize
output_tables = set(f'{schema}.{table}' for schema, table in inserts)
input_tables = set(f'{schema}.{table}' for schema, table in froms)

# Remove outputs from inputs (if table is written to, it's primarily an output)
input_only = input_tables - output_tables

print(f'INPUT TABLES (reads FROM): {len(input_only)} unique')
for table in sorted(input_only)[:15]:
    print(f'  - {table}')
if len(input_only) > 15:
    print(f'  ... and {len(input_only) - 15} more')

print()
print(f'OUTPUT TABLES (writes TO): {len(output_tables)} unique')
for table in sorted(output_tables):
    print(f'  - {table}')

print()
print('=' * 80)
print('BASELINE COMPARISON (from spLoadGLCognosData):')
print('=' * 80)
print('Expected pattern:')
print('  Input: [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500], [STAGING_FINANCE_COGNOS].[v_CCR2PowerBI_facts]')
print('  Output: [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500], [CONSUMPTION_FINANCE].[GLCognosData]')
print()
print('Pattern analysis:')
print('  ✓ Reads from STAGING tables (v_CCR2PowerBI_facts)')
print('  ✓ Writes to CONSUMPTION tables (GLCognosData)')
print('  ✓ Uses temp/staging table (GLCognosData_HC100500) for both read/write')

print()
print('=' * 80)
print('AI INFERENCE RESULT FROM DATABASE:')
print('=' * 80)

# Get AI result for GLCognosData_Test
result = conn.execute("""
    SELECT
        m.inputs,
        m.outputs
    FROM lineage_metadata m
    JOIN objects o ON m.object_id = o.object_id
    WHERE o.schema_name = 'CONSUMPTION_FINANCE'
    AND o.object_name = 'GLCognosData_Test'
    AND m.primary_source = 'ai'
""").fetchone()

if result:
    inputs, outputs = result

    print('AI found:')
    if inputs and inputs != '[]':
        input_ids = eval(inputs)
        print(f'  Inputs ({len(input_ids)} SPs that WRITE TO table):')
        for sp_id in input_ids:
            sp = conn.execute(f'SELECT schema_name, object_name FROM objects WHERE object_id = {sp_id}').fetchone()
            if sp:
                print(f'    - {sp[0]}.{sp[1]}')

    if outputs and outputs != '[]':
        output_ids = eval(outputs)
        print(f'  Outputs ({len(output_ids)} SPs that READ FROM table):')
        for sp_id in output_ids:
            sp = conn.execute(f'SELECT schema_name, object_name FROM objects WHERE object_id = {sp_id}').fetchone()
            if sp:
                print(f'    - {sp[0]}.{sp[1]}')
else:
    print('No AI result found')

print()
print('=' * 80)
print('VALIDATION: Does spLoadGLCognosData_Test write to GLCognosData_Test?')
print('=' * 80)
if 'CONSUMPTION_FINANCE.GLCognosData_Test' in output_tables:
    print('✅ YES - GLCognosData_Test found in OUTPUT tables')
    print('   This is a VALID match')
else:
    print('❌ NO - GLCognosData_Test NOT in OUTPUT tables')
    print('   This would be a FALSE match')

conn.close()
