#!/usr/bin/env python3
"""
Analyze why 62 SPs still fail after SQL Cleaning Engine
========================================================

Identifies patterns in SQLGlot failures to guide next improvements.
"""

import duckdb
import pandas as pd
from pathlib import Path
import re
import json
from collections import Counter

# Load data
conn = duckdb.connect(':memory:')

# Find definitions file
for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if 'definition' in df.columns and 'referencing_object_id' not in df.columns:
        defs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
        break

# Find objects file
for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if {'object_id', 'schema_name', 'object_name', 'object_type'}.issubset(set(df.columns)):
        objs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
        break

# Merge
merged = defs_df.merge(objs_df[['object_id', 'object_type', 'schema_name', 'object_name']], on='object_id')
sps = merged[merged['object_type'] == 'Stored Procedure']

# Load improvement details to find failing SPs
with open('evaluation/sqlglot_improvement_results/improvement_details.json') as f:
    improvement_data = json.load(f)

# Get SPs that still fail
still_failing_ids = [
    sp['object_id'] for sp in improvement_data['details']
    if not sp['baseline_success'] and not sp['improved_success']
]

print(f"Analyzing {len(still_failing_ids)} SPs that still fail after cleaning...\n")

# Analyze patterns
patterns = {
    'WHILE loops': [],
    'IF EXISTS blocks': [],
    'IF statement count': [],
    'Temp table operations (#)': [],
    'DROP TABLE': [],
    'CURSOR usage': [],
    'Dynamic SQL (sp_executesql/EXEC(@)': [],
    'Multiple CTEs': [],
    'CASE WHEN complexity': [],
    'BEGIN/END nesting depth': [],
    'Window functions': [],
    'CREATE TABLE (temp)': [],
    'ALTER TABLE': [],
    'INSERT INTO #temp': [],
}

for sp_id in still_failing_ids:
    sp_row = sps[sps['object_id'] == sp_id]
    if sp_row.empty:
        continue

    ddl = sp_row.iloc[0]['definition']

    # Count patterns
    patterns['WHILE loops'].append(len(re.findall(r'\bWHILE\b', ddl, re.IGNORECASE)))
    patterns['IF EXISTS blocks'].append(len(re.findall(r'\bIF\s+(?:NOT\s+)?EXISTS\b', ddl, re.IGNORECASE)))
    patterns['IF statement count'].append(len(re.findall(r'\bIF\b', ddl, re.IGNORECASE)))
    patterns['Temp table operations (#)'].append(ddl.count('#'))
    patterns['DROP TABLE'].append(len(re.findall(r'\bDROP\s+TABLE\b', ddl, re.IGNORECASE)))
    patterns['CURSOR usage'].append(len(re.findall(r'\bCURSOR\b', ddl, re.IGNORECASE)))
    patterns['Dynamic SQL (sp_executesql/EXEC(@)'].append(
        len(re.findall(r'\bsp_executesql\b', ddl, re.IGNORECASE)) +
        len(re.findall(r'\bEXEC\s*\(', ddl, re.IGNORECASE))
    )
    patterns['Multiple CTEs'].append(len(re.findall(r'\bWITH\s+\w+\s+AS\s*\(', ddl, re.IGNORECASE)))
    patterns['CASE WHEN complexity'].append(len(re.findall(r'\bCASE\s+WHEN\b', ddl, re.IGNORECASE)))
    patterns['BEGIN/END nesting depth'].append(len(re.findall(r'\bBEGIN\b', ddl, re.IGNORECASE)))
    patterns['Window functions'].append(len(re.findall(r'\bOVER\s*\(', ddl, re.IGNORECASE)))
    patterns['CREATE TABLE (temp)'].append(len(re.findall(r'\bCREATE\s+TABLE\s+#', ddl, re.IGNORECASE)))
    patterns['ALTER TABLE'].append(len(re.findall(r'\bALTER\s+TABLE\b', ddl, re.IGNORECASE)))
    patterns['INSERT INTO #temp'].append(len(re.findall(r'\bINSERT\s+(?:INTO\s+)?#', ddl, re.IGNORECASE)))

# Calculate statistics
print("=" * 80)
print("FAILURE PATTERN ANALYSIS")
print("=" * 80)

for pattern_name, counts in patterns.items():
    total_sps_with_pattern = sum(1 for c in counts if c > 0)
    percentage = (total_sps_with_pattern / len(still_failing_ids)) * 100
    avg_count = sum(counts) / len(counts) if counts else 0
    max_count = max(counts) if counts else 0

    if total_sps_with_pattern > 0:
        print(f"\n{pattern_name}:")
        print(f"  SPs with this pattern: {total_sps_with_pattern}/{len(still_failing_ids)} ({percentage:.1f}%)")
        print(f"  Average occurrences: {avg_count:.1f}")
        print(f"  Max occurrences: {max_count}")

# Top issues
print("\n" + "=" * 80)
print("TOP 3 FAILURE CAUSES")
print("=" * 80)

top_patterns = sorted(
    [(name, sum(1 for c in counts if c > 0)) for name, counts in patterns.items()],
    key=lambda x: x[1],
    reverse=True
)[:3]

for rank, (pattern, count) in enumerate(top_patterns, 1):
    percentage = (count / len(still_failing_ids)) * 100
    print(f"{rank}. {pattern}: {count}/{len(still_failing_ids)} SPs ({percentage:.1f}%)")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

print("""
Based on the analysis above, to improve SQLGlot success rate further:

1. **IF EXISTS/IF NOT EXISTS handling** - Current rules don't handle nested IF blocks
   - Add rule to extract core logic from IF EXISTS wrappers
   - Example: IF EXISTS (...) BEGIN <core logic> END

2. **Temp table management** - Heavy temp table usage confuses SQLGlot
   - Add rule to remove temp table creation (CREATE TABLE #temp)
   - Add rule to remove DROP TABLE #temp statements
   - Keep INSERT INTO #temp / SELECT FROM #temp for lineage

3. **WHILE loop extraction** - Procedural loops need handling
   - Add rule to extract DML from WHILE loop bodies
   - Focus on INSERT/UPDATE/DELETE inside loops

4. **Multiple BEGIN/END block flattening** - Complex nesting breaks parser
   - Add rule to flatten nested BEGIN/END when not part of control flow
   - Preserve only TRY/CATCH BEGIN/END pairs

5. **Dynamic SQL (sp_executesql/EXEC(@var))** - Cannot be resolved statically
   - These will remain unparseable (inherent limitation)
   - Document as expected limitation

Next priority rules to add (based on impact):
- Priority 1: IF EXISTS/IF NOT EXISTS extraction (affects most failing SPs)
- Priority 2: Temp table operation cleanup
- Priority 3: WHILE loop content extraction
- Priority 4: BEGIN/END flattening for non-control-flow blocks
""")

print("\n" + "=" * 80)
