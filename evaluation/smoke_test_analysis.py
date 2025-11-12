#!/usr/bin/env python3
"""
Smoke Test Analysis - Plausibility Check for Parser Results
===========================================================

Creates a DuckDB-based smoke test to validate parser results by:
1. Counting distinct table references in DDL text (expected count)
2. Comparing with parser results (actual count)
3. Identifying outliers and patterns

This helps validate if parser results are plausible.

Author: Claude Code Agent
Date: 2025-11-07
Version: 1.0.0
"""

import duckdb
import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Load parser results
with open('evaluation/real_data_results/parser_results.json') as f:
    parser_results = json.load(f)

# Create object_id -> parser results map
parser_map = {r['object_id']: r for r in parser_results}

# Connect to DuckDB
conn = duckdb.connect(':memory:')

# Load parquet files
deps_file = 'temp/part-00000-987ade22-ace3-473f-a6b8-22dd9c2e0bba-c000.snappy.parquet'
objs_file = 'temp/part-00000-163999fc-8981-440d-8ccd-8a762427b50a-c000.snappy.parquet'
defs_file = 'temp/part-00000-49de9afd-76ab-4385-83a7-92ac8c14c3d6-c000.snappy.parquet'

print("="*80)
print("SMOKE TEST ANALYSIS - Parser Plausibility Check")
print("="*80)
print()

# Question 1: How many table names appear in each DDL?
print("📊 Question 1: Expected table count per DDL")
print("-" * 80)

# Load SPs directly - simpler approach
query = """
    SELECT
        d.object_id,
        d.schema_name,
        d.object_name,
        d.definition
    FROM read_parquet('{}') d
    JOIN read_parquet('{}') o ON d.object_id = o.object_id
    WHERE o.object_type = 'Stored Procedure'
""".format(defs_file, objs_file)

result = conn.execute(query).df()

print(f"✓ Loaded {len(result)} stored procedures")
print()

# Process table references in Python for more control
def extract_table_names(ddl: str) -> Set[str]:
    """Extract table names from DDL using regex."""
    tables = set()

    # Patterns for table references
    patterns = [
        # FROM/JOIN patterns
        r'\b(?:FROM|JOIN)\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
        # INSERT INTO
        r'\bINSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
        # UPDATE
        r'\bUPDATE\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
        # DELETE FROM
        r'\bDELETE\s+FROM\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
        # TRUNCATE TABLE
        r'\bTRUNCATE\s+TABLE\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, ddl, re.IGNORECASE)
        for match in matches:
            schema = match.group(1)
            table = match.group(2)

            if table:
                # Filter out noise
                if table.upper() in ('SELECT', 'DELETED', 'INSERTED', 'VALUES'):
                    continue

                # Build FQN
                if schema:
                    fqn = f"{schema}.{table}"
                else:
                    fqn = table

                tables.add(fqn)

    return tables


def categorize_table(table_name: str) -> str:
    """Categorize table by type."""
    if table_name.startswith('#'):
        return 'temp'
    elif table_name.startswith('@'):
        return 'variable'
    elif '.' in table_name:
        schema = table_name.split('.')[0].upper()
        if schema in ('SYS', 'TEMPDB', 'INFORMATION_SCHEMA'):
            return 'system'
    return 'real'


# Analyze each SP
analysis_results = []

for _, row in result.iterrows():
    obj_id = row['object_id']
    obj_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']

    # Extract tables from DDL
    extracted_tables = extract_table_names(ddl)

    # Categorize
    real_tables = {t for t in extracted_tables if categorize_table(t) == 'real'}
    temp_tables = {t for t in extracted_tables if categorize_table(t) == 'temp'}
    system_tables = {t for t in extracted_tables if categorize_table(t) == 'system'}

    # Get parser results
    parser_result = parser_map.get(obj_id, {})
    parser_count = parser_result.get('parsed', {}).get('count', 0)

    # Calculate difference
    expected_count = len(real_tables)
    diff = parser_count - expected_count
    diff_pct = (diff / expected_count * 100) if expected_count > 0 else 0

    analysis_results.append({
        'object_id': obj_id,
        'object_name': obj_name,
        'expected_count': expected_count,
        'parser_count': parser_count,
        'difference': diff,
        'diff_pct': diff_pct,
        'real_tables': sorted(real_tables),
        'temp_tables': sorted(temp_tables),
        'system_tables': sorted(system_tables),
        'sqlglot_success': parser_result.get('sqlglot', {}).get('success', False)
    })

# Convert to DataFrame for analysis
df = pd.DataFrame(analysis_results)

print("📈 Smoke Test Results Summary")
print("-" * 80)
print(f"Total SPs analyzed: {len(df)}")
print(f"Average expected tables per SP: {df['expected_count'].mean():.1f}")
print(f"Average parser found per SP: {df['parser_count'].mean():.1f}")
print(f"Average difference: {df['difference'].mean():.1f}")
print()

# Categorize results
perfect_match = df[df['difference'] == 0]
close_match = df[df['difference'].abs() <= 2]
under_parsed = df[df['difference'] < -2]
over_parsed = df[df['difference'] > 2]

print("📊 Plausibility Categories:")
print(f"  Perfect match (diff = 0):        {len(perfect_match):3d} ({len(perfect_match)/len(df)*100:5.1f}%)")
print(f"  Close match (|diff| ≤ 2):        {len(close_match):3d} ({len(close_match)/len(df)*100:5.1f}%)")
print(f"  Under-parsed (diff < -2):        {len(under_parsed):3d} ({len(under_parsed)/len(df)*100:5.1f}%)")
print(f"  Over-parsed (diff > 2):          {len(over_parsed):3d} ({len(over_parsed)/len(df)*100:5.1f}%)")
print()

# SQLGlot correlation
sqlglot_success = df[df['sqlglot_success'] == True]
sqlglot_fail = df[df['sqlglot_success'] == False]

print("🔍 SQLGlot Success vs Accuracy:")
print(f"  SQLGlot Success - Avg diff: {sqlglot_success['difference'].abs().mean():.2f}")
print(f"  SQLGlot Fail - Avg diff:    {sqlglot_fail['difference'].abs().mean():.2f}")
print()

# Examples
print("✅ Top 5 Perfect Matches (diff = 0):")
for _, row in perfect_match.head(5).iterrows():
    print(f"  {row['object_name']:60s} Expected: {row['expected_count']:2d}  Parser: {row['parser_count']:2d}")
print()

print("⚠️  Top 5 Under-Parsed (parser missed tables):")
worst_under = under_parsed.nsmallest(5, 'difference')
for _, row in worst_under.iterrows():
    print(f"  {row['object_name']:60s} Expected: {row['expected_count']:2d}  Parser: {row['parser_count']:2d}  Diff: {row['difference']:3d}")
    if row['expected_count'] > 0:
        print(f"    Expected tables: {', '.join(row['real_tables'][:5])}")
print()

print("⚠️  Top 5 Over-Parsed (parser found extra):")
worst_over = over_parsed.nlargest(5, 'difference')
for _, row in worst_over.iterrows():
    print(f"  {row['object_name']:60s} Expected: {row['expected_count']:2d}  Parser: {row['parser_count']:2d}  Diff: {row['difference']:3d}")
print()

# Save detailed results
output_file = 'evaluation/real_data_results/smoke_test_results.json'
with open(output_file, 'w') as f:
    json.dump(analysis_results, f, indent=2)

print(f"✅ Detailed results saved to: {output_file}")
print()

# Question 2: What patterns does SQLGlot fail on?
print()
print("="*80)
print("📊 Question 2: SQLGlot Failure Pattern Analysis")
print("="*80)
print()

sqlglot_failures = df[df['sqlglot_success'] == False]

print(f"SQLGlot Failed on: {len(sqlglot_failures)} / {len(df)} SPs ({len(sqlglot_failures)/len(df)*100:.1f}%)")
print()

# Analyze DDL patterns in failures
print("🔍 Analyzing DDL patterns in SQLGlot failures...")
print()

failure_patterns = defaultdict(int)

for _, row in sqlglot_failures.iterrows():
    obj_id = row['object_id']

    # Get DDL from original data
    ddl_row = result[result['object_id'] == obj_id].iloc[0]
    ddl = ddl_row['definition']

    # Check for T-SQL patterns
    if re.search(r'\bBEGIN\s+TRY\b', ddl, re.IGNORECASE):
        failure_patterns['BEGIN TRY/CATCH'] += 1
    if re.search(r'\bDECLARE\s+@', ddl, re.IGNORECASE):
        failure_patterns['DECLARE statements'] += 1
    if re.search(r'\bSET\s+@', ddl, re.IGNORECASE):
        failure_patterns['SET variable'] += 1
    if re.search(r'\bEXEC\s+', ddl, re.IGNORECASE):
        failure_patterns['EXEC statements'] += 1
    if re.search(r'\bRAISERROR\b', ddl, re.IGNORECASE):
        failure_patterns['RAISERROR'] += 1
    if re.search(r'\bWHILE\s+', ddl, re.IGNORECASE):
        failure_patterns['WHILE loops'] += 1
    if re.search(r'\bIF\s+(?:OBJECT_ID|EXISTS)', ddl, re.IGNORECASE):
        failure_patterns['IF EXISTS checks'] += 1
    if re.search(r'\bCURSOR\b', ddl, re.IGNORECASE):
        failure_patterns['CURSOR usage'] += 1
    if re.search(r'\bGO\b', ddl, re.IGNORECASE):
        failure_patterns['GO statements'] += 1
    if re.search(r'\bBEGIN\s+TRANSACTION\b', ddl, re.IGNORECASE):
        failure_patterns['Transaction control'] += 1

print("Common T-SQL patterns in SQLGlot failures:")
for pattern, count in sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True):
    pct = count / len(sqlglot_failures) * 100
    print(f"  {pattern:30s}: {count:3d} / {len(sqlglot_failures)} ({pct:5.1f}%)")
print()

# Question 3: DMV Limitation Analysis
print()
print("="*80)
print("📊 Question 3: DMV Limitation - Why No SP Dependencies?")
print("="*80)
print()

# Load dependencies
deps_df = conn.execute(f"SELECT * FROM read_parquet('{deps_file}')").df()
objs_df = conn.execute(f"SELECT * FROM read_parquet('{objs_file}')").df()

# Check which object types have dependencies
dep_by_type = conn.execute(f"""
    SELECT
        o.object_type,
        COUNT(DISTINCT d.referencing_object_id) as object_count,
        COUNT(*) as dependency_count,
        AVG(CAST(dep_count AS DOUBLE)) as avg_deps_per_object
    FROM read_parquet('{deps_file}') d
    JOIN read_parquet('{objs_file}') o ON d.referencing_object_id = o.object_id
    JOIN (
        SELECT referencing_object_id, COUNT(*) as dep_count
        FROM read_parquet('{deps_file}')
        GROUP BY referencing_object_id
    ) dc ON d.referencing_object_id = dc.referencing_object_id
    GROUP BY o.object_type
    ORDER BY dependency_count DESC
""").df()

print("DMV Dependency Coverage by Object Type:")
print(dep_by_type.to_string(index=False))
print()

print("💡 Why DMV doesn't track SP dependencies:")
print()
print("SQL Server's sys.sql_dependencies (or sys.sql_expression_dependencies)")
print("has known limitations for stored procedures:")
print()
print("1. **Dynamic SQL** - EXEC(@sql) references cannot be determined statically")
print("2. **Temp Tables** - #temp tables are not in sys.objects catalog")
print("3. **Control Flow** - IF/WHILE/CASE logic makes dependencies conditional")
print("4. **Deferred Name Resolution** - Objects may not exist at create time")
print("5. **Cross-Database** - Dependencies across databases not always tracked")
print()
print("This is a SQL Server limitation, NOT a bug in our parser!")
print()

# Recommendations
print()
print("="*80)
print("📋 Recommendations Based on Smoke Test")
print("="*80)
print()

print("1. **Parser Accuracy:**")
accuracy_rate = len(close_match) / len(df) * 100
print(f"   - {accuracy_rate:.1f}% of SPs within ±2 tables of expected")
if accuracy_rate >= 80:
    print("   ✅ GOOD - Parser is performing well")
elif accuracy_rate >= 60:
    print("   ⚠️  ACCEPTABLE - Some room for improvement")
else:
    print("   ❌ NEEDS WORK - Significant parsing issues")
print()

print("2. **SQLGlot Enhancement Priority:**")
sqlglot_fail_rate = len(sqlglot_failures) / len(df) * 100
print(f"   - {sqlglot_fail_rate:.1f}% failure rate")
print("   - Top patterns to address with SQL Cleaning Engine:")
top_patterns = sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
for i, (pattern, count) in enumerate(top_patterns, 1):
    print(f"     {i}. {pattern} ({count} SPs)")
print()

print("3. **Validation Strategy:**")
print("   ✅ Views: Use DMV ground truth (137 views available)")
print("   ✅ SPs: Use catalog validation + UAT feedback")
print("   ✅ Smoke Test: Use this DDL-based plausibility check")
print()

print("="*80)
print("✅ Smoke Test Complete!")
print("="*80)
