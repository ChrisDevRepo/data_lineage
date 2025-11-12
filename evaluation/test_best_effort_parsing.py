#!/usr/bin/env python3
"""
Test Best-Effort Parsing: Try Both WARN and Cleaned, Use Best Result
====================================================================

Strategy: Always try both approaches, return whichever extracts more tables
Goal: Zero regressions + maximum table extraction
"""

import duckdb
import pandas as pd
from pathlib import Path
import sqlglot
from sqlglot.errors import ErrorLevel
import sys
sys.path.append('/home/user/sandbox')

from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

# Initialize
conn = duckdb.connect(':memory:')
engine = RuleEngine()

# Load parquet files
for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if 'definition' in df.columns and 'referencing_object_id' not in df.columns:
        defs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
        break

for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if {'object_id', 'schema_name', 'object_name', 'object_type'}.issubset(set(df.columns)):
        objs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
        break

# Merge and filter SPs
defs_for_merge = defs_df[['object_id', 'definition']]
merged = defs_for_merge.merge(objs_df[['object_id', 'object_type', 'schema_name', 'object_name']], on='object_id')
sps = merged[merged['object_type'] == 'Stored Procedure']

print(f"Testing best-effort parsing on {len(sps)} stored procedures...")
print("Strategy: Try both WARN and Cleaned, use best result\n")


def extract_unique_tables(parsed_statements):
    """Extract UNIQUE table references with schema only"""
    tables = set()

    if not parsed_statements:
        return tables

    for stmt in parsed_statements:
        for table in stmt.find_all(sqlglot.exp.Table):
            table_name = table.name.lower()

            # Only include tables with schema (filter out CTEs)
            if table.db:
                full_name = f"{table.db.lower()}.{table_name}"
                tables.add(full_name)

    return tables


def parse_with_best_effort(sql_definition, sp_name):
    """
    Best-effort parsing: Try both WARN and Cleaned, return best result

    Returns: (tables, method_used, parse_success)
    method_used: 'warn', 'cleaned', 'both_failed'
    """
    # Approach 1: WARN (handles most cases)
    tables_warn = set()
    warn_success = False
    try:
        parsed_warn = sqlglot.parse(sql_definition, dialect='tsql', error_level=ErrorLevel.WARN)
        tables_warn = extract_unique_tables(parsed_warn)
        warn_success = True
    except Exception:
        pass

    # Approach 2: Cleaned + STRICT (handles edge cases)
    tables_clean = set()
    clean_success = False
    try:
        cleaned = engine.apply_all(sql_definition)
        parsed_clean = sqlglot.parse(cleaned, dialect='tsql')
        tables_clean = extract_unique_tables(parsed_clean)
        clean_success = True
    except Exception:
        pass

    # Return whichever found more tables
    if len(tables_clean) > len(tables_warn):
        return tables_clean, 'cleaned', clean_success
    elif warn_success:
        return tables_warn, 'warn', warn_success
    elif clean_success:
        return tables_clean, 'cleaned', clean_success
    else:
        return set(), 'both_failed', False


# Test all SPs
results = []
method_usage = {'warn': 0, 'cleaned': 0, 'both_failed': 0}

for idx, row in sps.iterrows():
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']

    # Test best-effort approach
    tables, method, success = parse_with_best_effort(ddl, sp_name)

    results.append({
        'object_id': sp_id,
        'sp_name': sp_name,
        'table_count': len(tables),
        'method': method,
        'success': success,
        'line_count': len(ddl.split('\n'))
    })

    method_usage[method] += 1

# Calculate statistics
results_df = pd.DataFrame(results)

print("=" * 80)
print("BEST-EFFORT PARSING RESULTS")
print("=" * 80)
print(f"\nOverall Parse Success: {results_df['success'].sum()}/{len(results_df)} ({results_df['success'].mean()*100:.1f}%)")
print(f"Total Unique Tables Extracted: {results_df['table_count'].sum()}")
print(f"\nMethod Distribution:")
print(f"  warn:        {method_usage['warn']} SPs ({method_usage['warn']/len(results_df)*100:.1f}%)")
print(f"  cleaned:     {method_usage['cleaned']} SPs ({method_usage['cleaned']/len(results_df)*100:.1f}%)")
print(f"  both_failed: {method_usage['both_failed']} SPs ({method_usage['both_failed']/len(results_df)*100:.1f}%)")

print("\n" + "=" * 80)
print("COMPARISON TO BASELINE")
print("=" * 80)

print("""
Baseline (Cleaned + STRICT):
  Parse Success: 250/349 (71.6%)
  Unique Tables: 249

Best-Effort (Try Both):
  Parse Success: {success}/{total} ({pct:.1f}%)
  Unique Tables: {tables}

Improvement:
  Parse Success: +{success_diff} SPs (+{success_pct_diff:.1f}%)
  Unique Tables: +{table_diff} tables (+{table_pct_diff:.1f}%)
""".format(
    success=results_df['success'].sum(),
    total=len(results_df),
    pct=results_df['success'].mean()*100,
    tables=results_df['table_count'].sum(),
    success_diff=results_df['success'].sum() - 250,
    success_pct_diff=((results_df['success'].sum() - 250) / 250) * 100,
    table_diff=results_df['table_count'].sum() - 249,
    table_pct_diff=((results_df['table_count'].sum() - 249) / 249) * 100
))

print("=" * 80)
print("CLEANED METHOD USAGE (When Cleaning Won)")
print("=" * 80)

cleaned_cases = results_df[results_df['method'] == 'cleaned'].sort_values('table_count', ascending=False)

if len(cleaned_cases) > 0:
    print(f"\n{len(cleaned_cases)} SPs benefited from cleaning:\n")
    print(f"{'SP Name':<60} {'Tables':<8} {'Lines':<8}")
    print("-" * 80)
    for _, row in cleaned_cases.head(20).iterrows():
        print(f"{row['sp_name']:<60} {row['table_count']:<8} {row['line_count']:<8}")

    if len(cleaned_cases) > 20:
        print(f"\n... and {len(cleaned_cases) - 20} more")
else:
    print("\nNo SPs benefited from cleaning - WARN mode was sufficient for all!")

# Save detailed results
results_df.to_json('evaluation/best_effort_parsing_results.json', orient='records', indent=2)
print(f"\n✓ Detailed results saved to evaluation/best_effort_parsing_results.json")

print("\n" + "=" * 80)
print("REGRESSION CHECK")
print("=" * 80)

# Load baseline comparison
import json
with open('evaluation/baseline_vs_hybrid_comparison.json') as f:
    baseline_comp = json.load(f)

baseline_df = pd.DataFrame(baseline_comp)
baseline_dict = {row['sp_name']: row['baseline_tables'] for _, row in baseline_df.iterrows()}

# Check for regressions
regressions = []
for _, row in results_df.iterrows():
    baseline_count = baseline_dict.get(row['sp_name'], 0)
    if row['table_count'] < baseline_count:
        regressions.append({
            'sp_name': row['sp_name'],
            'baseline': baseline_count,
            'best_effort': row['table_count'],
            'diff': row['table_count'] - baseline_count
        })

if len(regressions) > 0:
    print(f"\n⚠️  Found {len(regressions)} regressions:\n")
    for reg in regressions[:10]:
        print(f"  {reg['sp_name']}: {reg['baseline']} → {reg['best_effort']} ({reg['diff']:+d})")
else:
    print("\n✅ ZERO REGRESSIONS! Best-effort approach is equal or better for all SPs.")
