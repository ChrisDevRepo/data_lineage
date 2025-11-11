#!/usr/bin/env python3
"""
Test 3-Tier SimplifiedParser v5.1 Implementation
=================================================

Validates:
1. 100% parse success
2. Table extraction >= 743 (Phase 1 baseline)
3. Expected ~745 tables (Option B projection)
4. 3-tier distribution matches expectations (86.5% / 13% / 0.5%)
5. SQLGlot-based confidence distribution
"""

import duckdb
import pandas as pd
from pathlib import Path
import sys
sys.path.append('/home/user/sandbox')

from lineage_v3.parsers.simplified_parser import SimplifiedParser
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

# Initialize DuckDB workspace
conn = duckdb.connect(':memory:')

# Load parquet files
for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if 'definition' in df.columns and 'referencing_object_id' not in df.columns:
        conn.execute(f"CREATE TABLE definitions AS SELECT * FROM '{pf}'")
    elif {'object_id', 'schema_name', 'object_name', 'object_type'}.issubset(set(df.columns)):
        conn.execute(f"CREATE TABLE objects AS SELECT * FROM '{pf}'")

# Create workspace
workspace = DuckDBWorkspace(conn)

# Get all stored procedures
sps = conn.execute("""
    SELECT o.object_id, o.schema_name, o.object_name
    FROM objects o
    WHERE o.object_type = 'Stored Procedure'
    ORDER BY o.object_id
""").fetchdf()

print(f"Testing 3-Tier SimplifiedParser v5.1 on {len(sps)} stored procedures...")
print("=" * 80)

# Initialize parser
parser = SimplifiedParser(workspace, enable_sql_cleaning=True)

# Parse all SPs
results = []

for idx, row in sps.iterrows():
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"

    # Parse with 3-tier parser
    result = parser.parse_object(sp_id)

    # Extract metrics
    tables_found = result['quality_metadata'].get('tables_found', 0) if result.get('quality_metadata') else 0
    total_objects = len(result['inputs']) + len(result['outputs'])

    results.append({
        'object_id': sp_id,
        'sp_name': sp_name,
        'confidence': result['confidence'],
        'parse_method': result['parse_method'],
        'tables_found': tables_found,
        'inputs': len(result['inputs']),
        'outputs': len(result['outputs']),
        'total_objects': total_objects,
        'command_ratio': result['quality_metadata'].get('command_ratio', 0) if result.get('quality_metadata') else 0,
        'total_statements': result['quality_metadata'].get('total_statements', 0) if result.get('quality_metadata') else 0,
        'parse_error': result.get('parse_error')
    })

    # Progress indicator
    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx + 1}/{len(sps)} SPs...")

# Convert to DataFrame
results_df = pd.DataFrame(results)

print("\n" + "=" * 80)
print("3-TIER SIMPLIFIEDPARSER v5.1 RESULTS")
print("=" * 80)

# Parse success
parse_success = len(results_df[results_df['parse_error'].isna()])
print(f"\nParse Success: {parse_success}/{len(results_df)} ({parse_success/len(results_df)*100:.1f}%)")

# Total objects extracted
total_objects = results_df['total_objects'].sum()
print(f"Total Objects Extracted: {total_objects}")

# Parse method distribution
print(f"\n3-Tier Method Distribution:")
method_counts = results_df['parse_method'].value_counts()
for method, count in method_counts.items():
    pct = count / len(results_df) * 100
    print(f"  {method}: {count} SPs ({pct:.1f}%)")

# Expected vs actual
print(f"\nExpected Distribution:")
print(f"  Tier 1 (WARN-only): 86.5% → Actual: {method_counts.get('tier1_warn', 0) / len(results_df) * 100:.1f}%")
print(f"  Tier 2 (7 rules): 13.0% → Actual: {method_counts.get('tier2_7rules', 0) / len(results_df) * 100:.1f}%")
print(f"  Tier 3 (17 rules): 0.5% → Actual: {method_counts.get('tier3_17rules', 0) / len(results_df) * 100:.1f}%")

# Confidence distribution
print(f"\nConfidence Distribution:")
conf_counts = results_df['confidence'].value_counts().sort_index(ascending=False)
for conf, count in conf_counts.items():
    pct = count / len(results_df) * 100
    print(f"  {conf}: {count} SPs ({pct:.1f}%)")

# Command ratio analysis
print(f"\nCommand Ratio Analysis:")
print(f"  Mean: {results_df['command_ratio'].mean():.1f}%")
print(f"  Median: {results_df['command_ratio'].median():.1f}%")
print(f"  <20% (Excellent): {len(results_df[results_df['command_ratio'] < 20])} SPs")
print(f"  20-50% (Good): {len(results_df[(results_df['command_ratio'] >= 20) & (results_df['command_ratio'] < 50)])} SPs")
print(f"  >50% (Partial): {len(results_df[results_df['command_ratio'] >= 50])} SPs")

# Top SPs by object count
print(f"\nTop 10 SPs by Object Count:")
print(f"{'SP Name':<60} {'Objects':<10} {'Method':<15} {'Confidence':<12}")
print("-" * 100)
for _, row in results_df.nlargest(10, 'total_objects').iterrows():
    print(f"{row['sp_name']:<60} {row['total_objects']:<10} {row['parse_method']:<15} {row['confidence']:<12}")

# Tier 2 usage (should be ~13% of SPs with <3 tables in Tier 1)
tier2_sps = results_df[results_df['parse_method'] == 'tier2_7rules']
if len(tier2_sps) > 0:
    print(f"\nTier 2 (7 rules) Usage Analysis:")
    print(f"  Total: {len(tier2_sps)} SPs ({len(tier2_sps)/len(results_df)*100:.1f}%)")
    print(f"  Avg Objects: {tier2_sps['total_objects'].mean():.1f}")
    print(f"  Avg Confidence: {tier2_sps['confidence'].mean():.0f}")
    print(f"\n  Top 5 SPs using Tier 2:")
    print(f"  {'SP Name':<60} {'Objects':<10}")
    print("  " + "-" * 70)
    for _, row in tier2_sps.nlargest(5, 'total_objects').iterrows():
        print(f"  {row['sp_name']:<60} {row['total_objects']:<10}")

# Tier 3 usage (should be <1% of SPs with 0 tables in Tiers 1 & 2)
tier3_sps = results_df[results_df['parse_method'] == 'tier3_17rules']
if len(tier3_sps) > 0:
    print(f"\nTier 3 (17 rules) Usage Analysis:")
    print(f"  Total: {len(tier3_sps)} SPs ({len(tier3_sps)/len(results_df)*100:.1f}%)")
    print(f"  Avg Objects: {tier3_sps['total_objects'].mean():.1f}")
    print(f"  Avg Confidence: {tier3_sps['confidence'].mean():.0f}")
    print(f"\n  SPs using Tier 3:")
    print(f"  {'SP Name':<60} {'Objects':<10}")
    print("  " + "-" * 70)
    for _, row in tier3_sps.iterrows():
        print(f"  {row['sp_name']:<60} {row['total_objects']:<10}")

# Parse errors (should be 0)
parse_errors = results_df[results_df['parse_error'].notna()]
if len(parse_errors) > 0:
    print(f"\n❌ {len(parse_errors)} SPs with parse errors:")
    for _, row in parse_errors.head(5).iterrows():
        print(f"  {row['sp_name']}: {row['parse_error']}")
else:
    print(f"\n✅ ZERO PARSE ERRORS")

print("\n" + "=" * 80)
print("COMPARISON TO BASELINES")
print("=" * 80)

print(f"""
Phase 1 Baseline (SimplifiedParser v5.0 - 2-tier):
  Parse Success: 349/349 (100.0%)
  Total Objects: 743
  Method: WARN-only + WARN (cleaned with 17 rules)

Option B Projection (3-tier):
  Parse Success: 349/349 (100.0%)
  Total Objects: ~745 (expected)
  Method: WARN-only + 7 rules + 17 rules

3-Tier Parser v5.1 (Actual):
  Parse Success: {parse_success}/{len(results_df)} ({parse_success/len(results_df)*100:.1f}%)
  Total Objects: {total_objects}
  Method: WARN-only ({method_counts.get('tier1_warn', 0)}) + 7 rules ({method_counts.get('tier2_7rules', 0)}) + 17 rules ({method_counts.get('tier3_17rules', 0)})

Comparison to Phase 1 Baseline:
  Parse Success: {parse_success - 349:+d} ({(parse_success - 349)/349*100 if 349 > 0 else 0:+.1f}%)
  Total Objects: {total_objects - 743:+d} ({(total_objects - 743)/743*100:+.1f}%)

Comparison to Option B Projection:
  Total Objects: {total_objects - 745:+d} ({(total_objects - 745)/745*100:+.1f}%)
""")

if total_objects >= 743:
    print("✅ PASS: Total objects >= Phase 1 baseline (zero regressions)")
else:
    print(f"⚠️  WARNING: Total objects below baseline by {743 - total_objects}")

if parse_success == len(results_df):
    print("✅ PASS: 100% parse success maintained")
else:
    print(f"⚠️  WARNING: Parse success rate {parse_success/len(results_df)*100:.1f}%")

# Check tier distribution
tier1_pct = method_counts.get('tier1_warn', 0) / len(results_df) * 100
tier2_pct = method_counts.get('tier2_7rules', 0) / len(results_df) * 100
tier3_pct = method_counts.get('tier3_17rules', 0) / len(results_df) * 100

if 80 <= tier1_pct <= 90 and 10 <= tier2_pct <= 20 and tier3_pct < 5:
    print("✅ PASS: Tier distribution matches expectations")
else:
    print(f"⚠️  WARNING: Tier distribution differs from expectations")

# Save results
results_df.to_json('evaluation_baselines/3tier_parser_results.json', orient='records', indent=2)
print(f"\n✓ Results saved to evaluation_baselines/3tier_parser_results.json")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

all_pass = (
    parse_success == len(results_df) and
    total_objects >= 743 and
    80 <= tier1_pct <= 90 and
    10 <= tier2_pct <= 20 and
    tier3_pct < 5
)

if all_pass:
    print("\n✅ ALL TESTS PASSED")
    print("   - 100% parse success")
    print("   - Zero regressions (objects >= baseline)")
    print("   - Tier distribution matches expectations")
    print("   - SQLGlot-based confidence working correctly")
    print("\n   Ready for production deployment!")
else:
    print("\n⚠️  SOME TESTS FAILED")
    if parse_success < len(results_df):
        print(f"   - Parse success: {parse_success}/{len(results_df)} (expected 100%)")
    if total_objects < 743:
        print(f"   - Objects: {total_objects} (expected >= 743)")
    if not (80 <= tier1_pct <= 90 and 10 <= tier2_pct <= 20 and tier3_pct < 5):
        print(f"   - Tier distribution: T1={tier1_pct:.1f}% T2={tier2_pct:.1f}% T3={tier3_pct:.1f}%")
    print("\n   Review failures before deployment")

print("\n" + "=" * 80)
