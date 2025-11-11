#!/usr/bin/env python3
"""
Test Hybrid Parsing Strategy: WARN Primary + Cleaning Fallback
==============================================================

Strategy:
1. Try uncleaned SQL with error_level=WARN (works for 99.7% of cases)
2. For very large SPs with poor extraction, try cleaning fallback
3. Use whichever approach finds more unique tables
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

# Merge and filter SPs - drop columns from defs_df that will be replaced
defs_for_merge = defs_df[['object_id', 'definition']]
merged = defs_for_merge.merge(objs_df[['object_id', 'object_type', 'schema_name', 'object_name']], on='object_id')
sps = merged[merged['object_type'] == 'Stored Procedure']

print(f"Testing hybrid parsing on {len(sps)} stored procedures...\n")


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


def parse_with_hybrid_approach(sql_definition, sp_name):
    """
    Hybrid parsing strategy

    Returns: (tables, method_used, parse_success)
    method_used: 'warn_primary', 'cleaned_fallback', 'cleaned_emergency'
    """
    # Step 1: Try WARN primary (works for most cases)
    try:
        parsed_warn = sqlglot.parse(sql_definition, dialect='tsql', error_level=ErrorLevel.WARN)
        tables_warn = extract_unique_tables(parsed_warn)

        # Step 2: Detect edge cases needing cleaning fallback
        # Criteria: Very large SP (>1500 lines) with poor extraction (<5 tables)
        line_count = len(sql_definition.split('\n'))

        if line_count > 1500 and len(tables_warn) < 5:
            # Try cleaning fallback
            cleaned = engine.apply_all(sql_definition)
            try:
                parsed_clean = sqlglot.parse(cleaned, dialect='tsql')
                tables_clean = extract_unique_tables(parsed_clean)

                # Use whichever found more tables
                if len(tables_clean) > len(tables_warn):
                    return tables_clean, 'cleaned_fallback', True
            except Exception:
                # Cleaning failed, stick with WARN
                pass

        return tables_warn, 'warn_primary', True

    except Exception as e:
        # Step 3: Emergency fallback (shouldn't happen with WARN)
        try:
            cleaned = engine.apply_all(sql_definition)
            parsed_clean = sqlglot.parse(cleaned, dialect='tsql')
            tables_clean = extract_unique_tables(parsed_clean)
            return tables_clean, 'cleaned_emergency', True
        except Exception:
            return set(), 'failed', False


# Test all SPs
results = []
fallback_cases = []

for idx, row in sps.iterrows():
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']

    # Test hybrid approach
    tables, method, success = parse_with_hybrid_approach(ddl, sp_name)

    results.append({
        'object_id': sp_id,
        'sp_name': sp_name,
        'table_count': len(tables),
        'method': method,
        'success': success,
        'line_count': len(ddl.split('\n'))
    })

    if method != 'warn_primary':
        fallback_cases.append({
            'sp_name': sp_name,
            'method': method,
            'table_count': len(tables),
            'line_count': len(ddl.split('\n'))
        })

# Calculate statistics
results_df = pd.DataFrame(results)

print("=" * 80)
print("HYBRID PARSING RESULTS")
print("=" * 80)
print(f"\nOverall Parse Success: {results_df['success'].sum()}/{len(results_df)} ({results_df['success'].mean()*100:.1f}%)")
print(f"Total Unique Tables Extracted: {results_df['table_count'].sum()}")
print(f"\nMethod Distribution:")
print(results_df['method'].value_counts())

print("\n" + "=" * 80)
print("FALLBACK CASES")
print("=" * 80)

if fallback_cases:
    print(f"\n{len(fallback_cases)} SPs used fallback cleaning:\n")
    for case in fallback_cases:
        print(f"  {case['sp_name']}")
        print(f"    Method: {case['method']}")
        print(f"    Tables: {case['table_count']}")
        print(f"    Lines: {case['line_count']}")
        print()
else:
    print("\nNo SPs required fallback - WARN mode handled everything!")

print("=" * 80)
print("COMPARISON TO BASELINE")
print("=" * 80)

print("""
Baseline (Cleaned + STRICT):
  Parse Success: 250/349 (71.6%)
  Unique Tables: 249

Hybrid Approach (WARN Primary + Cleaning Fallback):
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
print("TOP 10 SPs BY TABLE COUNT")
print("=" * 80)

top_sps = results_df.nlargest(10, 'table_count')
print(f"\n{'SP Name':<60} {'Tables':<8} {'Method':<20}")
print("-" * 90)
for _, row in top_sps.iterrows():
    print(f"{row['sp_name']:<60} {row['table_count']:<8} {row['method']:<20}")

# Save detailed results
results_df.to_json('evaluation_baselines/hybrid_parsing_results.json', orient='records', indent=2)
print(f"\n✓ Detailed results saved to evaluation_baselines/hybrid_parsing_results.json")
