#!/usr/bin/env python3
"""
Test: WARN mode for BOTH uncleaned AND cleaned SQL
===================================================

Current approach:
- WARN mode (uncleaned) → 310 SPs
- STRICT mode (cleaned) → 39 SPs

User's insight:
- WARN mode (uncleaned) → Primary
- WARN mode (cleaned) → Fallback (instead of STRICT)

Question: Does cleaned + WARN extract more tables than cleaned + STRICT?
If YES: We can simplify cleaning rules (don't need STRICT-perfect SQL)
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

print(f"Testing WARN mode on both uncleaned and cleaned SQL...")
print(f"Goal: See if cleaned + WARN is better than cleaned + STRICT\n")


def extract_unique_tables(parsed_statements):
    """Extract UNIQUE table references with schema only"""
    tables = set()

    if not parsed_statements:
        return tables

    for stmt in parsed_statements:
        for table in stmt.find_all(sqlglot.exp.Table):
            if table.db:
                full_name = f"{table.db.lower()}.{table.name.lower()}"
                tables.add(full_name)

    return tables


# Compare three approaches
results = []

for idx, row in sps.iterrows():
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']
    cleaned = engine.apply_all(ddl)

    # Approach 1: WARN (uncleaned)
    try:
        parsed_warn = sqlglot.parse(ddl, dialect='tsql', error_level=ErrorLevel.WARN)
        tables_warn = extract_unique_tables(parsed_warn)
    except:
        tables_warn = set()

    # Approach 2: STRICT (cleaned) - current fallback
    try:
        parsed_strict = sqlglot.parse(cleaned, dialect='tsql')  # STRICT mode
        tables_strict = extract_unique_tables(parsed_strict)
    except:
        tables_strict = set()

    # Approach 3: WARN (cleaned) - proposed fallback
    try:
        parsed_warn_clean = sqlglot.parse(cleaned, dialect='tsql', error_level=ErrorLevel.WARN)
        tables_warn_clean = extract_unique_tables(parsed_warn_clean)
    except:
        tables_warn_clean = set()

    results.append({
        'sp_name': sp_name,
        'warn_uncleaned': len(tables_warn),
        'strict_cleaned': len(tables_strict),
        'warn_cleaned': len(tables_warn_clean),
        'best_current': max(len(tables_warn), len(tables_strict)),
        'best_proposed': max(len(tables_warn), len(tables_warn_clean))
    })

# Analyze results
results_df = pd.DataFrame(results)

print("=" * 80)
print("RESULTS: WARN vs STRICT for Cleaned SQL")
print("=" * 80)

print(f"\nTotal Tables Extracted:")
print(f"  WARN (uncleaned):    {results_df['warn_uncleaned'].sum()}")
print(f"  STRICT (cleaned):    {results_df['strict_cleaned'].sum()}")
print(f"  WARN (cleaned):      {results_df['warn_cleaned'].sum()}")

print(f"\nBest-Effort Totals:")
print(f"  Current (WARN + STRICT):  {results_df['best_current'].sum()}")
print(f"  Proposed (WARN + WARN):   {results_df['best_proposed'].sum()}")

print(f"\n{'Metric':<40} {'Current':<15} {'Proposed':<15} {'Diff':<10}")
print("-" * 80)
print(f"{'Total tables':<40} {results_df['best_current'].sum():<15} {results_df['best_proposed'].sum():<15} {results_df['best_proposed'].sum() - results_df['best_current'].sum():<10}")

# Find cases where WARN (cleaned) > STRICT (cleaned)
warn_clean_better = results_df[results_df['warn_cleaned'] > results_df['strict_cleaned']]
print(f"\n{len(warn_clean_better)} SPs where WARN (cleaned) > STRICT (cleaned):")
if len(warn_clean_better) > 0:
    print(f"\n{'SP Name':<60} {'STRICT':<10} {'WARN':<10} {'Diff':<10}")
    print("-" * 90)
    for _, row in warn_clean_better.head(20).iterrows():
        diff = row['warn_cleaned'] - row['strict_cleaned']
        print(f"{row['sp_name']:<60} {row['strict_cleaned']:<10} {row['warn_cleaned']:<10} {diff:+d}")

# Find cases where STRICT (cleaned) > WARN (cleaned)
strict_better = results_df[results_df['strict_cleaned'] > results_df['warn_cleaned']]
print(f"\n{len(strict_better)} SPs where STRICT (cleaned) > WARN (cleaned):")
if len(strict_better) > 0:
    print(f"\n{'SP Name':<60} {'WARN':<10} {'STRICT':<10} {'Diff':<10}")
    print("-" * 90)
    for _, row in strict_better.head(20).iterrows():
        diff = row['strict_cleaned'] - row['warn_cleaned']
        print(f"{row['sp_name']:<60} {row['warn_cleaned']:<10} {row['strict_cleaned']:<10} {diff:+d}")

print("\n" + "=" * 80)
print("ANALYSIS: Can we simplify cleaning rules?")
print("=" * 80)

# Calculate how many SPs benefit from current vs proposed
current_wins = len(results_df[results_df['best_current'] > results_df['best_proposed']])
proposed_wins = len(results_df[results_df['best_proposed'] > results_df['best_current']])
tie = len(results_df[results_df['best_proposed'] == results_df['best_current']])

print(f"""
CURRENT APPROACH (WARN uncleaned + STRICT cleaned):
- Total tables: {results_df['best_current'].sum()}
- Better for: {current_wins} SPs

PROPOSED APPROACH (WARN uncleaned + WARN cleaned):
- Total tables: {results_df['best_proposed'].sum()}
- Better for: {proposed_wins} SPs
- Tie: {tie} SPs

DIFFERENCE: {results_df['best_proposed'].sum() - results_df['best_current'].sum():+d} tables

CONCLUSION:
""")

if results_df['best_proposed'].sum() >= results_df['best_current'].sum():
    print("""
✅ YES! Use WARN mode for both uncleaned and cleaned SQL!

BENEFITS:
1. Simpler cleaning rules - Don't need STRICT-perfect SQL
2. More forgiving - WARN mode handles edge cases better
3. Consistent approach - Same error handling for both paths
4. Potential for more aggressive cleaning (remove more noise)

SIMPLIFIED RULE ENGINE:
- Current: 17 rules focused on making SQL STRICT-parseable
- Proposed: Fewer rules focused on removing noise only
- Example: Can remove entire IF OBJECT_ID blocks without worrying about syntax errors

NEXT STEP: Test simplified rule engine with WARN-only approach
""")
else:
    regressions = results_df['best_current'].sum() - results_df['best_proposed'].sum()
    print(f"""
⚠️  STRICT mode still needed for {strict_better} SPs

REGRESSIONS: -{regressions} tables with WARN-only approach

CONCLUSION: Keep current approach (WARN + STRICT fallback)
""")

# Save detailed results
results_df.to_json('evaluation/warn_vs_strict_comparison.json', orient='records', indent=2)
print(f"\n✓ Detailed results saved to evaluation/warn_vs_strict_comparison.json")
