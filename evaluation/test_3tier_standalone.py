#!/usr/bin/env python3
"""
Test Production Baseline v5.1 (Standalone)
==========================================

Validates:
1. 2-tier best-effort logic works correctly
2. Table extraction = 743 (Phase 1 baseline)
3. Tier distribution: ~86.5% Tier 1, ~13.5% Tier 2
4. Uses 17-rule engine for production accuracy
"""

import duckdb
import pandas as pd
from pathlib import Path
import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel
import sys
sys.path.append('/home/user/sandbox')

from lineage_v3.parsers.sql_cleaning_rules import RuleEngine
from lineage_v3.parsers.simplified_rule_engine import SimplifiedRuleEngine

# Initialize
conn = duckdb.connect(':memory:')
engine_7 = SimplifiedRuleEngine()
engine_17 = RuleEngine()

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

print(f"Testing Production Baseline v5.1 (2-tier, 17 rules) on {len(sps)} stored procedures...")
print("=" * 80)

# Create catalog set for validation
catalog = set(objs_df.apply(lambda r: f"{r['schema_name'].lower()}.{r['object_name'].lower()}", axis=1))

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


def parse_with_3tier(ddl):
    """
    2-tier parsing approach (Production Baseline v5.1 - 17 rules)

    - Tier 1: WARN-only (always try)
    - Tier 2: WARN + 17 rules (always try for best-effort)
    - Return whichever finds more tables
    """

    # Tier 1: WARN-only (no cleaning) - ALWAYS TRY
    try:
        parsed_t1 = sqlglot.parse(ddl, dialect='tsql', error_level=ErrorLevel.WARN)
        sources_t1, targets_t1 = extract_unique_tables(parsed_t1)
        tables_t1 = len(sources_t1) + len(targets_t1)
    except:
        sources_t1, targets_t1 = set(), set()
        tables_t1 = 0

    # Tier 2: WARN + 17 rules - ALWAYS TRY (production baseline)
    try:
        cleaned_17 = engine_17.apply_all(ddl)
        parsed_t2 = sqlglot.parse(cleaned_17, dialect='tsql', error_level=ErrorLevel.WARN)
        sources_t2, targets_t2 = extract_unique_tables(parsed_t2)
        tables_t2 = len(sources_t2) + len(targets_t2)
    except:
        sources_t2, targets_t2 = set(), set()
        tables_t2 = 0

    # Return best result (whichever found more tables)
    # NO catalog validation (match Phase 1 baseline behavior)
    if tables_t2 > tables_t1:
        return sources_t2, targets_t2, 'tier2_17rules', tables_t2
    else:
        return sources_t1, targets_t1, 'tier1_warn', tables_t1


# Parse all SPs with 3-tier approach
results = []

for idx, row in sps.iterrows():
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']

    sources, targets, method, tables = parse_with_3tier(ddl)

    results.append({
        'sp_name': sp_name,
        'parse_method': method,
        'tables': tables,
        'sources': len(sources),
        'targets': len(targets)
    })

    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx + 1}/{len(sps)} SPs...")

# Convert to DataFrame
results_df = pd.DataFrame(results)

print("\n" + "=" * 80)
print("3-TIER PARSER RESULTS")
print("=" * 80)

# Total tables
total_tables = results_df['tables'].sum()
print(f"\nTotal Tables Extracted: {total_tables}")

# Parse method distribution
print(f"\n3-Tier Method Distribution:")
method_counts = results_df['parse_method'].value_counts()
for method, count in method_counts.items():
    pct = count / len(results_df) * 100
    print(f"  {method}: {count} SPs ({pct:.1f}%)")

# Expected vs actual
print(f"\nExpected Distribution:")
print(f"  Tier 1 (WARN-only): 86.5% → Actual: {method_counts.get('tier1_warn', 0) / len(results_df) * 100:.1f}%")
print(f"  Tier 2 (17 rules): 13.5% → Actual: {method_counts.get('tier2_17rules', 0) / len(results_df) * 100:.1f}%")

# Top SPs by table count
print(f"\nTop 10 SPs by Table Count:")
print(f"{'SP Name':<60} {'Tables':<10} {'Method':<15}")
print("-" * 90)
for _, row in results_df.nlargest(10, 'tables').iterrows():
    print(f"{row['sp_name']:<60} {row['tables']:<10} {row['parse_method']:<15}")

# Tier 2 usage
tier2_sps = results_df[results_df['parse_method'] == 'tier2_17rules']
if len(tier2_sps) > 0:
    print(f"\nTier 2 (17 rules) Usage Analysis:")
    print(f"  Total: {len(tier2_sps)} SPs ({len(tier2_sps)/len(results_df)*100:.1f}%)")
    print(f"  Avg Tables: {tier2_sps['tables'].mean():.1f}")
    print(f"  Total Tables: {tier2_sps['tables'].sum()}")
    print(f"\n  Top 5 SPs using Tier 2:")
    print(f"  {'SP Name':<60} {'Tables':<10}")
    print("  " + "-" * 70)
    for _, row in tier2_sps.nlargest(5, 'tables').iterrows():
        print(f"  {row['sp_name']:<60} {row['tables']:<10}")

# Tier 3 usage
tier3_sps = results_df[results_df['parse_method'] == 'tier3_17rules']
if len(tier3_sps) > 0:
    print(f"\nTier 3 (17 rules) Usage Analysis:")
    print(f"  Total: {len(tier3_sps)} SPs ({len(tier3_sps)/len(results_df)*100:.1f}%)")
    print(f"  Avg Tables: {tier3_sps['tables'].mean():.1f}")
    print(f"  Total Tables: {tier3_sps['tables'].sum()}")
    print(f"\n  SPs using Tier 3:")
    print(f"  {'SP Name':<60} {'Tables':<10}")
    print("  " + "-" * 70)
    for _, row in tier3_sps.iterrows():
        print(f"  {row['sp_name']:<60} {row['tables']:<10}")
else:
    print(f"\n✅ NO SPs REQUIRED TIER 3")

print("\n" + "=" * 80)
print("COMPARISON TO BASELINES")
print("=" * 80)

tier1_pct = method_counts.get('tier1_warn', 0) / len(results_df) * 100
tier2_pct = method_counts.get('tier2_17rules', 0) / len(results_df) * 100

print(f"""
Phase 1 Baseline (SimplifiedParser v5.0 - 2-tier):
  Total Tables: 743

Production Baseline v5.1 (2-tier with 17 rules):
  Total Tables: 743 (expected)

Current Test Run (Actual):
  Total Tables: {total_tables}
  Method: Tier 1 ({method_counts.get('tier1_warn', 0)} SPs) + Tier 2 ({method_counts.get('tier2_17rules', 0)} SPs)

Comparison to Phase 1 Baseline:
  Total Tables: {total_tables - 743:+d} ({(total_tables - 743)/743*100:+.1f}%)
""")

if total_tables >= 743:
    print("✅ PASS: Total tables >= Phase 1 baseline (zero regressions)")
else:
    print(f"⚠️  WARNING: Total tables below baseline by {743 - total_tables}")

# Check tier distribution
if 80 <= tier1_pct <= 90 and 10 <= tier2_pct <= 20:
    print("✅ PASS: Tier distribution matches expectations")
else:
    print(f"⚠️  WARNING: Tier distribution differs from expectations")
    print(f"   T1={tier1_pct:.1f}% (expected 86.5%), T2={tier2_pct:.1f}% (expected 13.5%)")

# Save results
results_df.to_json('evaluation/3tier_standalone_results.json', orient='records', indent=2)
print(f"\n✓ Results saved to evaluation/3tier_standalone_results.json")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

all_pass = (
    total_tables >= 743 and
    80 <= tier1_pct <= 90 and
    10 <= tier2_pct <= 20
)

if all_pass:
    print("\n✅ ALL TESTS PASSED")
    print("   - Zero regressions (tables >= baseline)")
    print("   - Tier distribution matches expectations")
    print("   - 2-tier best-effort parsing working correctly")
    print(f"\n   Average rules per SP: ~{(0*method_counts.get('tier1_warn',0) + 17*method_counts.get('tier2_17rules',0))/len(results_df):.1f}")
    print("\n   Ready for production deployment!")
else:
    print("\n⚠️  SOME TESTS FAILED")
    if total_tables < 743:
        print(f"   - Tables: {total_tables} (expected >= 743)")
    if not (80 <= tier1_pct <= 90 and 10 <= tier2_pct <= 20):
        print(f"   - Tier distribution: T1={tier1_pct:.1f}% T2={tier2_pct:.1f}%")
    print("\n   Review failures before deployment")

print("\n" + "=" * 80)
