#!/usr/bin/env python3
"""
Test Simplified 7-Rule Engine vs Original 17-Rule Engine
=========================================================

Goal: Verify that simplified rules achieve same or better results
"""

import duckdb
import pandas as pd
from pathlib import Path
import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel
import sys
sys.path.append('/home/user/sandbox')

from lineage_v3.parsers.sql_cleaning_rules import RuleEngine as Original17RuleEngine
from lineage_v3.parsers.simplified_rule_engine import SimplifiedRuleEngine

# Initialize
conn = duckdb.connect(':memory:')
engine_17 = Original17RuleEngine()
engine_7 = SimplifiedRuleEngine()

# Load parquet files
for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if 'definition' in df.columns and 'referencing_object_id' not in df.columns:
        defs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
    elif {'object_id', 'schema_name', 'object_name', 'object_type'}.issubset(set(df.columns)):
        objs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()

# Merge and filter SPs
defs_for_merge = defs_df[['object_id', 'definition']]
merged = defs_for_merge.merge(objs_df[['object_id', 'object_type', 'schema_name', 'object_name']], on='object_id')
sps = merged[merged['object_type'] == 'Stored Procedure']

print(f"Testing Simplified 7-Rule Engine vs Original 17-Rule Engine")
print(f"Testing on {len(sps)} stored procedures...")
print("=" * 80)


def extract_unique_tables(parsed_statements):
    """Extract UNIQUE table references"""
    sources = set()
    targets = set()

    if not parsed_statements:
        return sources, targets

    for stmt in parsed_statements:
        if type(stmt).__name__ == 'Command':
            continue

        if isinstance(stmt, (exp.Insert, exp.Update, exp.Delete, exp.Merge)):
            table = stmt.find(exp.Table)
            if table and table.db:
                full_name = f"{table.db.lower()}.{table.name.lower()}"
                targets.add(full_name)

        for table in stmt.find_all(exp.Table):
            if table.db:
                full_name = f"{table.db.lower()}.{table.name.lower()}"
                sources.add(full_name)

    sources = sources - targets
    return sources, targets


# Compare both approaches
results = []

for idx, row in sps.iterrows():
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']

    # Approach 1: Original 17 rules + WARN
    try:
        cleaned_17 = engine_17.apply_all(ddl)
        parsed_17 = sqlglot.parse(cleaned_17, dialect='tsql', error_level=ErrorLevel.WARN)
        sources_17, targets_17 = extract_unique_tables(parsed_17)
        tables_17 = len(sources_17) + len(targets_17)
    except:
        tables_17 = 0

    # Approach 2: Simplified 7 rules + WARN
    try:
        cleaned_7 = engine_7.apply_all(ddl)
        parsed_7 = sqlglot.parse(cleaned_7, dialect='tsql', error_level=ErrorLevel.WARN)
        sources_7, targets_7 = extract_unique_tables(parsed_7)
        tables_7 = len(sources_7) + len(targets_7)
    except:
        tables_7 = 0

    # Approach 3: No cleaning + WARN (baseline)
    try:
        parsed_none = sqlglot.parse(ddl, dialect='tsql', error_level=ErrorLevel.WARN)
        sources_none, targets_none = extract_unique_tables(parsed_none)
        tables_none = len(sources_none) + len(targets_none)
    except:
        tables_none = 0

    results.append({
        'sp_name': sp_name,
        'tables_17_rules': tables_17,
        'tables_7_rules': tables_7,
        'tables_no_clean': tables_none,
        'diff_17_vs_7': tables_17 - tables_7,
        'best_approach': max([(tables_17, '17_rules'), (tables_7, '7_rules'),
                              (tables_none, 'no_clean')], key=lambda x: x[0])[1]
    })

    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx + 1}/{len(sps)} SPs...")

# Convert to DataFrame
results_df = pd.DataFrame(results)

print("\n" + "=" * 80)
print("SIMPLIFIED 7-RULE ENGINE TEST RESULTS")
print("=" * 80)

# Summary
total_17 = results_df['tables_17_rules'].sum()
total_7 = results_df['tables_7_rules'].sum()
total_none = results_df['tables_no_clean'].sum()

print(f"\nTotal Tables Extracted:")
print(f"  Original 17 rules: {total_17}")
print(f"  Simplified 7 rules: {total_7}")
print(f"  No cleaning: {total_none}")

print(f"\nComparison:")
print(f"  7 rules vs 17 rules: {total_7 - total_17:+d} tables ({(total_7-total_17)/total_17*100:+.1f}%)")
print(f"  7 rules vs no clean: {total_7 - total_none:+d} tables ({(total_7-total_none)/total_none*100:+.1f}%)")

# Approach distribution
print(f"\nBest Approach Distribution:")
print(results_df['best_approach'].value_counts())

# Regressions (where 7 rules < 17 rules)
regressions = results_df[results_df['diff_17_vs_7'] > 0]
if len(regressions) > 0:
    print(f"\n⚠️  {len(regressions)} SPs where 7 rules extracted FEWER tables than 17 rules:")
    print(f"{'SP Name':<60} {'17 Rules':<10} {'7 Rules':<10} {'Diff':<10}")
    print("-" * 90)
    for _, row in regressions.nlargest(10, 'diff_17_vs_7').iterrows():
        print(f"{row['sp_name']:<60} {row['tables_17_rules']:<10} {row['tables_7_rules']:<10} {row['diff_17_vs_7']:+d}")
else:
    print(f"\n✅ ZERO REGRESSIONS: 7 rules >= 17 rules for all SPs")

# Improvements (where 7 rules > 17 rules)
improvements = results_df[results_df['diff_17_vs_7'] < 0]
if len(improvements) > 0:
    print(f"\n✅ {len(improvements)} SPs where 7 rules extracted MORE tables than 17 rules:")
    print(f"{'SP Name':<60} {'17 Rules':<10} {'7 Rules':<10} {'Diff':<10}")
    print("-" * 90)
    for _, row in improvements.nlargest(10, 'diff_17_vs_7', keep='last').iterrows():
        print(f"{row['sp_name']:<60} {row['tables_17_rules']:<10} {row['tables_7_rules']:<10} {row['diff_17_vs_7']:+d}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if total_7 >= total_17:
    print(f"""
✅ PASS: Simplified 7-rule engine achieves same or better results!

Results:
- Total tables: {total_7} vs {total_17} (17 rules)
- Difference: {total_7 - total_17:+d} tables
- Regressions: {len(regressions)} SPs
- Complexity: -59% (7 rules vs 17 rules)

Recommendation: Deploy simplified 7-rule engine to production
""")
else:
    print(f"""
⚠️  WARNING: Simplified 7-rule engine has regressions

Results:
- Total tables: {total_7} vs {total_17} (17 rules)
- Difference: {total_7 - total_17:+d} tables
- Regressions: {len(regressions)} SPs

Recommendation: Review regressions before deployment
""")

# Save results
results_df.to_json('evaluation/simplified_rules_comparison.json', orient='records', indent=2)
print(f"\n✓ Results saved to evaluation/simplified_rules_comparison.json")
