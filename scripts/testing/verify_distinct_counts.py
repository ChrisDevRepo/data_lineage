#!/usr/bin/env python3
"""Verify if table counts in lineage are distinct or have duplicates."""

import glob
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

from engine.core.duckdb_workspace import DuckDBWorkspace
from engine.parsers.quality_aware_parser import QualityAwareParser
from engine.config.settings import Settings
import json

settings = Settings()
parquet_files = glob.glob('./temp/*.parquet')

print('Loading workspace...')
workspace = DuckDBWorkspace.from_parquet_files(parquet_files, settings)

print('\n' + '=' * 80)
print('VERIFYING DISTINCT TABLE COUNTS')
print('=' * 80)

# Get sample SPs to check
results = workspace.conn.execute('''
    SELECT
        o.schema_name || '.' || o.object_name as sp_name,
        lm.inputs,
        lm.outputs,
        json_array_length(COALESCE(lm.inputs, '[]')) as input_count,
        json_array_length(COALESCE(lm.outputs, '[]')) as output_count
    FROM objects o
    JOIN lineage_metadata lm ON o.object_id = lm.object_id
    WHERE o.object_type = 'Stored Procedure'
    ORDER BY output_count DESC
    LIMIT 5
''').fetchall()

print('\nTop 5 SPs by output count:')
for sp_name, inputs_json, outputs_json, inp_cnt, out_cnt in results:
    inputs = json.loads(inputs_json) if inputs_json else []
    outputs = json.loads(outputs_json) if outputs_json else []

    # Check for duplicates
    unique_inputs = len(set(inputs))
    unique_outputs = len(set(outputs))

    print(f'\n{sp_name}:')
    print(f'  Outputs: {out_cnt} total, {unique_outputs} unique')
    if out_cnt != unique_outputs:
        print(f'  WARNING: DUPLICATES FOUND: {out_cnt - unique_outputs} duplicate output IDs')
        print(f'  Output IDs (first 10): {outputs[:10]}')

    print(f'  Inputs: {inp_cnt} total, {unique_inputs} unique')
    if inp_cnt != unique_inputs:
        print(f'  WARNING: DUPLICATES FOUND: {inp_cnt - unique_inputs} duplicate input IDs')

# Check overall statistics
print('\n' + '=' * 80)
print('OVERALL DUPLICATE ANALYSIS')
print('=' * 80)

results = workspace.conn.execute('''
    SELECT
        COUNT(*) as total_sps
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
''').fetchone()

total_sps = results[0]
print(f'\nTotal SPs: {total_sps}')

# Manual calculation of average (checking for duplicates)
all_results = workspace.conn.execute('''
    SELECT inputs, outputs
    FROM lineage_metadata
    WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
''').fetchall()

total_inputs = 0
total_outputs = 0
total_unique_inputs = 0
total_unique_outputs = 0
sps_with_dup_inputs = 0
sps_with_dup_outputs = 0

for inputs_json, outputs_json in all_results:
    inputs = json.loads(inputs_json) if inputs_json else []
    outputs = json.loads(outputs_json) if outputs_json else []

    total_inputs += len(inputs)
    total_outputs += len(outputs)

    unique_inputs = len(set(inputs))
    unique_outputs = len(set(outputs))

    total_unique_inputs += unique_inputs
    total_unique_outputs += unique_outputs

    if len(inputs) != unique_inputs:
        sps_with_dup_inputs += 1
    if len(outputs) != unique_outputs:
        sps_with_dup_outputs += 1

avg_inputs = total_inputs / total_sps
avg_outputs = total_outputs / total_sps
avg_unique_inputs = total_unique_inputs / total_sps
avg_unique_outputs = total_unique_outputs / total_sps

print(f'\nCOUNTS (with potential duplicates):')
print(f'  Total inputs across all SPs: {total_inputs}')
print(f'  Total outputs across all SPs: {total_outputs}')
print(f'  Average inputs per SP: {avg_inputs:.2f}')
print(f'  Average outputs per SP: {avg_outputs:.2f}')

print(f'\nUNIQUE COUNTS (deduplicated):')
print(f'  Total UNIQUE inputs: {total_unique_inputs}')
print(f'  Total UNIQUE outputs: {total_unique_outputs}')
print(f'  Average UNIQUE inputs per SP: {avg_unique_inputs:.2f}')
print(f'  Average UNIQUE outputs per SP: {avg_unique_outputs:.2f}')

if total_inputs != total_unique_inputs or total_outputs != total_unique_outputs:
    print(f'\nWARNING - DUPLICATES DETECTED:')
    print(f'  Duplicate inputs: {total_inputs - total_unique_inputs}')
    print(f'  Duplicate outputs: {total_outputs - total_unique_outputs}')
    print(f'  SPs with duplicate inputs: {sps_with_dup_inputs}')
    print(f'  SPs with duplicate outputs: {sps_with_dup_outputs}')
    print(f'\n  This means the same table appears multiple times in inputs/outputs arrays.')
    print(f'  Parser should deduplicate before storing!')
else:
    print(f'\nOK - NO DUPLICATES - All counts are distinct!')

workspace.close()
print('\n' + '=' * 80)
