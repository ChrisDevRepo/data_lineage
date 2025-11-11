#!/usr/bin/env python3
"""
Compare Baseline (Cleaned + STRICT) vs Hybrid (WARN Primary + Cleaning Fallback)
=================================================================================

Check for regressions: SPs where hybrid approach extracts fewer tables than baseline
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

print(f"Comparing Baseline vs Hybrid on {len(sps)} stored procedures...")
print("This may take a few minutes...\n")


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


# Compare approaches for all SPs
comparisons = []

for idx, row in sps.iterrows():
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']

    # Approach 1: Baseline (Cleaned + STRICT)
    baseline_tables = set()
    baseline_success = False
    try:
        cleaned = engine.apply_all(ddl)
        parsed_baseline = sqlglot.parse(cleaned, dialect='tsql')
        baseline_tables = extract_unique_tables(parsed_baseline)
        baseline_success = True
    except Exception:
        pass

    # Approach 2: Hybrid (WARN Primary + Cleaning Fallback)
    hybrid_tables = set()
    hybrid_method = 'warn_primary'
    hybrid_success = False
    try:
        parsed_warn = sqlglot.parse(ddl, dialect='tsql', error_level=ErrorLevel.WARN)
        hybrid_tables = extract_unique_tables(parsed_warn)

        # Fallback for large SPs with poor extraction
        line_count = len(ddl.split('\n'))
        if line_count > 1500 and len(hybrid_tables) < 5:
            cleaned = engine.apply_all(ddl)
            try:
                parsed_clean = sqlglot.parse(cleaned, dialect='tsql')
                tables_clean = extract_unique_tables(parsed_clean)

                if len(tables_clean) > len(hybrid_tables):
                    hybrid_tables = tables_clean
                    hybrid_method = 'cleaned_fallback'
            except Exception:
                pass

        hybrid_success = True
    except Exception:
        # Emergency fallback
        try:
            cleaned = engine.apply_all(ddl)
            parsed_clean = sqlglot.parse(cleaned, dialect='tsql')
            hybrid_tables = extract_unique_tables(parsed_clean)
            hybrid_method = 'cleaned_emergency'
            hybrid_success = True
        except Exception:
            pass

    # Record comparison
    comparisons.append({
        'object_id': sp_id,
        'sp_name': sp_name,
        'baseline_tables': len(baseline_tables),
        'hybrid_tables': len(hybrid_tables),
        'baseline_success': baseline_success,
        'hybrid_success': hybrid_success,
        'hybrid_method': hybrid_method,
        'difference': len(hybrid_tables) - len(baseline_tables)
    })

# Analyze results
comp_df = pd.DataFrame(comparisons)

print("=" * 80)
print("REGRESSION ANALYSIS")
print("=" * 80)

# Regressions: SPs where hybrid extracts fewer tables
regressions = comp_df[comp_df['difference'] < 0].sort_values('difference')

if len(regressions) > 0:
    print(f"\n⚠️  Found {len(regressions)} regressions (hybrid < baseline):\n")
    print(f"{'SP Name':<60} {'Baseline':<10} {'Hybrid':<10} {'Diff':<10}")
    print("-" * 90)
    for _, row in regressions.head(20).iterrows():
        print(f"{row['sp_name']:<60} {row['baseline_tables']:<10} {row['hybrid_tables']:<10} {row['difference']:<10}")

    if len(regressions) > 20:
        print(f"\n... and {len(regressions) - 20} more")
else:
    print("\n✅ No regressions found! Hybrid approach is strictly better or equal for all SPs.")

print("\n" + "=" * 80)
print("IMPROVEMENT ANALYSIS")
print("=" * 80)

# Improvements: SPs where hybrid extracts more tables
improvements = comp_df[comp_df['difference'] > 0].sort_values('difference', ascending=False)

print(f"\n✅ Found {len(improvements)} improvements (hybrid > baseline):\n")
print(f"{'SP Name':<60} {'Baseline':<10} {'Hybrid':<10} {'Diff':<10}")
print("-" * 90)
for _, row in improvements.head(20).iterrows():
    print(f"{row['sp_name']:<60} {row['baseline_tables']:<10} {row['hybrid_tables']:<10} {row['difference']:<10}")

if len(improvements) > 20:
    print(f"\n... and {len(improvements) - 20} more")

print("\n" + "=" * 80)
print("OVERALL SUMMARY")
print("=" * 80)

print(f"""
Baseline (Cleaned + STRICT):
  Parse Success: {comp_df['baseline_success'].sum()}/{len(comp_df)} ({comp_df['baseline_success'].mean()*100:.1f}%)
  Total Unique Tables: {comp_df['baseline_tables'].sum()}

Hybrid (WARN Primary + Cleaning Fallback):
  Parse Success: {comp_df['hybrid_success'].sum()}/{len(comp_df)} ({comp_df['hybrid_success'].mean()*100:.1f}%)
  Total Unique Tables: {comp_df['hybrid_tables'].sum()}
  Method Distribution:
    - warn_primary: {len(comp_df[comp_df['hybrid_method'] == 'warn_primary'])}
    - cleaned_fallback: {len(comp_df[comp_df['hybrid_method'] == 'cleaned_fallback'])}
    - cleaned_emergency: {len(comp_df[comp_df['hybrid_method'] == 'cleaned_emergency'])}

Comparison:
  Regressions: {len(regressions)} SPs
  Improvements: {len(improvements)} SPs
  No Change: {len(comp_df[comp_df['difference'] == 0])} SPs

  Total Table Difference: {comp_df['difference'].sum():+d} tables ({(comp_df['difference'].sum() / comp_df['baseline_tables'].sum())*100:+.1f}%)
""")

# Save detailed comparison
comp_df.to_json('evaluation_baselines/baseline_vs_hybrid_comparison.json', orient='records', indent=2)
print(f"✓ Detailed comparison saved to evaluation_baselines/baseline_vs_hybrid_comparison.json")
