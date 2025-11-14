#!/usr/bin/env python3
"""Check for duplicate object IDs in inputs/outputs arrays."""

import duckdb
import json
from collections import Counter

conn = duckdb.connect('data/lineage_workspace.duckdb', read_only=True)

print('=' * 80)
print('VERIFYING DUPLICATE OBJECT IDs IN INPUTS/OUTPUTS')
print('=' * 80)

# Get all lineage metadata
results = conn.execute('''
    SELECT
        o.schema_name || '.' || o.object_name as sp_name,
        lm.inputs,
        lm.outputs
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    WHERE o.object_type = 'Stored Procedure'
''').fetchall()

total_inputs = 0
total_outputs = 0
unique_inputs = 0
unique_outputs = 0
max_inputs = 0
max_outputs = 0

sps_with_dup_inputs = []
sps_with_dup_outputs = []

for sp_name, inputs_json, outputs_json in results:
    inputs = json.loads(inputs_json) if inputs_json else []
    outputs = json.loads(outputs_json) if outputs_json else []

    total_inputs += len(inputs)
    total_outputs += len(outputs)

    unique_inp = len(set(inputs))
    unique_out = len(set(outputs))

    unique_inputs += unique_inp
    unique_outputs += unique_out

    max_inputs = max(max_inputs, unique_inp)
    max_outputs = max(max_outputs, unique_out)

    # Check for duplicates
    if len(inputs) != unique_inp:
        dup_count = len(inputs) - unique_inp
        sps_with_dup_inputs.append((sp_name, len(inputs), unique_inp, dup_count))

    if len(outputs) != unique_out:
        dup_count = len(outputs) - unique_out
        sps_with_dup_outputs.append((sp_name, len(outputs), unique_out, dup_count))

total_sps = len(results)

print(f'\nTotal SPs: {total_sps}')
print(f'\nTOTAL COUNTS (with potential duplicates):')
print(f'  Total inputs: {total_inputs}')
print(f'  Total outputs: {total_outputs}')
print(f'  Average inputs per SP: {total_inputs / total_sps:.2f}')
print(f'  Average outputs per SP: {total_outputs / total_sps:.2f}')

print(f'\nUNIQUE COUNTS (deduplicated):')
print(f'  Total UNIQUE inputs: {unique_inputs}')
print(f'  Total UNIQUE outputs: {unique_outputs}')
print(f'  Average UNIQUE inputs per SP: {unique_inputs / total_sps:.2f}')
print(f'  Average UNIQUE outputs per SP: {unique_outputs / total_sps:.2f}')
print(f'  Max UNIQUE inputs: {max_inputs}')
print(f'  Max UNIQUE outputs: {max_outputs}')

if total_inputs != unique_inputs or total_outputs != unique_outputs:
    print(f'\nWARNING - DUPLICATES DETECTED:')
    print(f'  Duplicate input IDs: {total_inputs - unique_inputs}')
    print(f'  Duplicate output IDs: {total_outputs - unique_outputs}')
    print(f'  SPs with duplicate inputs: {len(sps_with_dup_inputs)}')
    print(f'  SPs with duplicate outputs: {len(sps_with_dup_outputs)}')

    if sps_with_dup_inputs:
        print(f'\n  Top 5 SPs with duplicate inputs:')
        for sp_name, total, unique, dups in sorted(sps_with_dup_inputs, key=lambda x: x[3], reverse=True)[:5]:
            print(f'    {sp_name}: {total} total, {unique} unique ({dups} duplicates)')

    if sps_with_dup_outputs:
        print(f'\n  Top 5 SPs with duplicate outputs:')
        for sp_name, total, unique, dups in sorted(sps_with_dup_outputs, key=lambda x: x[3], reverse=True)[:5]:
            print(f'    {sp_name}: {total} total, {unique} unique ({dups} duplicates)')
else:
    print(f'\nOK - NO DUPLICATES - All object IDs are unique!')

# Check specific high-output SP
print(f'\n' + '=' * 80)
print('VERIFYING spLoadDWH (reported 89 outputs)')
print('=' * 80)

result = conn.execute('''
    SELECT
        o.object_name,
        lm.outputs
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    WHERE o.object_name = 'spLoadDWH'
      AND o.schema_name = 'CONSUMPTION_PRIMA_2'
''').fetchone()

if result:
    obj_name, outputs_json = result
    outputs = json.loads(outputs_json) if outputs_json else []

    unique_outputs_count = len(set(outputs))

    print(f'\nCONSUMPTION_PRIMA_2.spLoadDWH:')
    print(f'  Total outputs: {len(outputs)}')
    print(f'  Unique outputs: {unique_outputs_count}')

    if len(outputs) != unique_outputs_count:
        print(f'  WARNING: Has {len(outputs) - unique_outputs_count} duplicate output IDs')

        # Find duplicates
        counts = Counter(outputs)
        duplicates = {obj_id: count for obj_id, count in counts.items() if count > 1}

        print(f'\n  Duplicate output IDs:')
        for obj_id, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
            obj = conn.execute('SELECT schema_name, object_name FROM objects WHERE object_id = ?', [obj_id]).fetchone()
            if obj:
                print(f'    {obj_id} ({obj[0]}.{obj[1]}): appears {count} times')
    else:
        print(f'  OK - All outputs are unique!')

conn.close()
print('\n' + '=' * 80)
