#!/usr/bin/env python3
"""
Deep analysis of spLoadGLCognosData_Test to understand complete lineage pattern
This will serve as a baseline for test strategy
"""
import duckdb
import re
from collections import defaultdict

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

print('=' * 80)
print('COMPLETE LINEAGE ANALYSIS: spLoadGLCognosData_Test')
print('=' * 80)
print()

# Extract all table operations with line numbers
operations = []

for i, line in enumerate(definition.split('\n'), 1):
    line_clean = line.strip().lower()

    # TRUNCATE TABLE
    if 'truncate table' in line_clean:
        match = re.search(r'truncate\s+table\s+\[?(\w+)\]?\.\[?(\w+)\]?', line_clean, re.IGNORECASE)
        if match:
            operations.append((i, 'TRUNCATE', f'{match.group(1)}.{match.group(2)}', line.strip()[:80]))

    # INSERT INTO
    elif 'insert into' in line_clean:
        match = re.search(r'insert\s+into\s+\[?(\w+)\]?\.\[?(\w+)\]?', line_clean, re.IGNORECASE)
        if match:
            operations.append((i, 'INSERT', f'{match.group(1)}.{match.group(2)}', line.strip()[:80]))

    # SELECT COUNT FROM (metadata operations)
    elif 'select count' in line_clean and 'from' in line_clean:
        match = re.search(r'from\s+\[?(\w+)\]?\.\[?(\w+)\]?', line_clean, re.IGNORECASE)
        if match:
            operations.append((i, 'COUNT', f'{match.group(1)}.{match.group(2)}', line.strip()[:80]))

    # FROM (read operations)
    elif line_clean.startswith('from') or '\tfrom' in line_clean or ' from ' in line_clean:
        match = re.search(r'from\s+\[?(\w+)\]?\.\[?(\w+)\]?', line_clean, re.IGNORECASE)
        if match:
            operations.append((i, 'FROM', f'{match.group(1)}.{match.group(2)}', line.strip()[:80]))

    # JOIN
    elif 'join' in line_clean:
        match = re.search(r'join\s+\[?(\w+)\]?\.\[?(\w+)\]?', line_clean, re.IGNORECASE)
        if match:
            operations.append((i, 'JOIN', f'{match.group(1)}.{match.group(2)}', line.strip()[:80]))

# Organize by operation type
by_operation = defaultdict(list)
for line_num, op_type, table, snippet in operations:
    by_operation[op_type].append((table, line_num, snippet))

print('TABLE OPERATIONS SUMMARY:')
print('-' * 80)
print()

# OUTPUTS (tables this SP writes TO)
print('OUTPUT TABLES (SP writes TO these):')
print()
if by_operation['TRUNCATE']:
    print('  TRUNCATE operations:')
    for table, line_num, snippet in by_operation['TRUNCATE']:
        print(f'    Line {line_num:4d}: {table}')
        print(f'              {snippet}')

if by_operation['INSERT']:
    print()
    print('  INSERT operations:')
    seen = set()
    for table, line_num, snippet in by_operation['INSERT']:
        if table not in seen:
            print(f'    Line {line_num:4d}: {table}')
            print(f'              {snippet}')
            seen.add(table)

# INPUTS (tables this SP reads FROM)
print()
print('INPUT TABLES (SP reads FROM these):')
print()
if by_operation['FROM']:
    print('  FROM operations:')
    seen = set()
    for table, line_num, snippet in by_operation['FROM'][:20]:  # First 20
        if table not in seen:
            print(f'    Line {line_num:4d}: {table}')
            print(f'              {snippet}')
            seen.add(table)
    if len(by_operation['FROM']) > 20:
        print(f'    ... and {len(by_operation["FROM"]) - 20} more FROM clauses')

if by_operation['JOIN']:
    print()
    print('  JOIN operations:')
    seen = set()
    for table, line_num, snippet in by_operation['JOIN'][:10]:  # First 10
        if table not in seen:
            print(f'    Line {line_num:4d}: {table}')
            print(f'              {snippet}')
            seen.add(table)

print()
print('=' * 80)
print('LINEAGE PATTERN ANALYSIS:')
print('=' * 80)
print()

# Get unique tables
output_tables = set()
for table, _, _ in by_operation['TRUNCATE']:
    output_tables.add(table)
for table, _, _ in by_operation['INSERT']:
    output_tables.add(table)

input_tables = set()
for table, _, _ in by_operation['FROM']:
    input_tables.add(table)
for table, _, _ in by_operation['JOIN']:
    input_tables.add(table)

# Remove temp tables and self-references
input_tables = input_tables - output_tables

print(f'Summary:')
print(f'  - Reads FROM:  {len(input_tables)} unique tables')
print(f'  - Writes TO:   {len(output_tables)} unique tables')
print()

print('OUTPUTS (Destination tables):')
for table in sorted(output_tables):
    print(f'  → {table}')

print()
print('INPUTS (Source tables):')
for table in sorted(input_tables):
    print(f'  ← {table}')

print()
print('=' * 80)
print('TARGET TABLE VALIDATION:')
print('=' * 80)
print()

target_table = 'CONSUMPTION_FINANCE.GLCognosData_Test'
if target_table in output_tables:
    print(f'✅ {target_table} is an OUTPUT table')
    print(f'   This SP WRITES TO this table')
    print()
    print('   From TABLE perspective:')
    print('     - This SP should be stored in table.inputs (data coming IN)')
    print('     - Because the SP provides data TO the table')
else:
    print(f'❌ {target_table} is NOT an output table')

print()
print('=' * 80)
print('DATABASE STORAGE VALIDATION:')
print('=' * 80)

# Get AI result
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

    print('Current database storage:')
    print(f'  table.inputs:  {inputs}')
    print(f'  table.outputs: {outputs}')
    print()

    if inputs and inputs != '[]':
        input_ids = eval(inputs)
        print(f'  table.inputs contains {len(input_ids)} SP(s):')
        for sp_id in input_ids:
            sp = conn.execute(f'SELECT schema_name, object_name FROM objects WHERE object_id = {sp_id}').fetchone()
            if sp:
                print(f'    - {sp[0]}.{sp[1]}')
                if sp[1] == 'spLoadGLCognosData_Test':
                    print(f'      ✅ CORRECT - This SP writes TO the table')

    if outputs and outputs != '[]':
        output_ids = eval(outputs)
        print(f'  table.outputs contains {len(output_ids)} SP(s):')
        for sp_id in output_ids:
            sp = conn.execute(f'SELECT schema_name, object_name FROM objects WHERE object_id = {sp_id}').fetchone()
            if sp:
                print(f'    - {sp[0]}.{sp[1]}')
else:
    print('No AI result found')

print()
print('=' * 80)
print('CONCLUSION:')
print('=' * 80)
print()
print('This SP demonstrates the correct pattern:')
print('  1. Reads FROM staging/source tables (v_CCR2PowerBI_facts)')
print('  2. Writes TO consumption tables (GLCognosData_Test)')
print('  3. Uses intermediate staging table (GLCognosData_HC100500_Test)')
print()
print('Storage semantics (from TABLE perspective):')
print('  - table.inputs  = SPs that provide data TO table (WRITE operations)')
print('  - table.outputs = SPs that consume data FROM table (READ operations)')
print()
print('Expected result for GLCognosData_Test:')
print('  ✅ table.inputs  = [spLoadGLCognosData_Test]  (SP writes to table)')
print('  ✅ table.outputs = []                         (no SPs read from table)')

conn.close()
