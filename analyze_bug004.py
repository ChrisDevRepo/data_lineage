#!/usr/bin/env python3
"""Analyze BUG-004: Why 231/349 SPs found 0 tables"""

import json
from collections import defaultdict

# Load smoke test results
with open('evaluation_baselines/real_data_results/smoke_test_results.json') as f:
    results = json.load(f)

print("="*80)
print("BUG-004 ANALYSIS: Poor Smoke Test Results")
print("="*80)
print()

# Overall statistics
total_sps = len(results)
zero_parser = [r for r in results if r['parser_count'] == 0]
zero_expected = [r for r in results if r['expected_count'] == 0]

print(f"Total SPs: {total_sps}")
print(f"SPs where parser found 0 tables: {len(zero_parser)} ({len(zero_parser)/total_sps*100:.1f}%)")
print(f"SPs where smoke test expected 0 tables: {len(zero_expected)} ({len(zero_expected)/total_sps*100:.1f}%)")
print()

# Categorize zero-parser SPs
print("="*80)
print("CATEGORIZING ZERO-PARSER SPs")
print("="*80)
print()

# Category 1: Orchestrators (expected 0, parser got 0) - CORRECT
orchestrators = [r for r in zero_parser if r['expected_count'] == 0]

# Category 2: Parsing failures (expected > 0, parser got 0) - BUG
parsing_failures = [r for r in zero_parser if r['expected_count'] > 0]

print(f"Category 1: Orchestrators (expected=0, parser=0) - CORRECT")
print(f"  Count: {len(orchestrators)}")
print(f"  Examples:")
for r in orchestrators[:5]:
    print(f"    {r['object_name']:60s} Expected: {r['expected_count']:2d}  Parser: {r['parser_count']:2d}")
print()

print(f"Category 2: Parsing Failures (expected>0, parser=0) - NEEDS FIX")
print(f"  Count: {len(parsing_failures)}")
print(f"  Examples (worst first):")
worst_failures = sorted(parsing_failures, key=lambda x: x['expected_count'], reverse=True)
for r in worst_failures[:10]:
    tables = ', '.join(r['real_tables'][:3])
    if len(r['real_tables']) > 3:
        tables += f", ... (+{len(r['real_tables'])-3} more)"
    print(f"    {r['object_name']:60s} Expected: {r['expected_count']:2d}  Tables: {tables}")
print()

# Analyze SQLGlot correlation
if parsing_failures:
    sqlglot_success_failures = [r for r in parsing_failures if r['sqlglot_success']]
    sqlglot_fail_failures = [r for r in parsing_failures if not r['sqlglot_success']]

    print("SQLGlot Correlation in Parsing Failures:")
    print(f"  SQLGlot succeeded but parser got 0: {len(sqlglot_success_failures)} ({len(sqlglot_success_failures)/len(parsing_failures)*100:.1f}%)")
    print(f"  SQLGlot failed and parser got 0:    {len(sqlglot_fail_failures)} ({len(sqlglot_fail_failures)/len(parsing_failures)*100:.1f}%)")
    print()
else:
    print("✅ No parsing failures found!")
    print()

# Expected table count distribution
if parsing_failures:
    print("Expected Table Distribution (for parsing failures):")
    expected_dist = defaultdict(int)
    for r in parsing_failures:
        expected_dist[r['expected_count']] += 1

    for count in sorted(expected_dist.keys())[:10]:
        print(f"  Expected {count:2d} tables: {expected_dist[count]:3d} SPs")
    print()
else:
    print("No parsing failures to analyze.")
    print()

# Summary
print("="*80)
print("SUMMARY")
print("="*80)
print()
print(f"✅ Orchestrators (correct behavior): {len(orchestrators)}")
print(f"❌ Real parsing failures: {len(parsing_failures)}")
print()
print(f"Parsing failure rate: {len(parsing_failures)}/{total_sps} = {len(parsing_failures)/total_sps*100:.1f}%")
print()

# Recommendations
print("RECOMMENDATIONS:")
print()
print("1. Orchestrator Detection:")
print(f"   - {len(orchestrators)} SPs correctly identified as orchestrators")
print("   - These should get 100% confidence (not penalized for 0 tables)")
print()
print("2. Parsing Improvements Needed:")
if parsing_failures:
    sqlglot_success_failures = [r for r in parsing_failures if r['sqlglot_success']]
    sqlglot_fail_failures = [r for r in parsing_failures if not r['sqlglot_success']]
    print(f"   - {len(parsing_failures)} SPs failed to extract any tables")
    print(f"   - {len(sqlglot_fail_failures)} failed due to SQLGlot parsing")
    print(f"   - {len(sqlglot_success_failures)} failed despite SQLGlot success (regex issue?)")
else:
    print(f"   - {len(parsing_failures)} SPs failed to extract any tables")
    print("   ✅ Excellent! All SPs successfully extracted tables or are orchestrators")
print()
print("3. High-Priority Failures (expected ≥5 tables):")
high_priority = [r for r in parsing_failures if r['expected_count'] >= 5]
if high_priority:
    print(f"   - {len(high_priority)} SPs expected ≥5 tables but got 0")
    print("   - These should be analyzed first for parser improvements")
else:
    print(f"   - {len(high_priority)} SPs expected ≥5 tables but got 0")
    print("   ✅ No high-priority failures")
print()

# Save detailed categorization
output = {
    'total_sps': total_sps,
    'zero_parser_count': len(zero_parser),
    'orchestrators': [r['object_name'] for r in orchestrators],
    'parsing_failures': [
        {
            'object_name': r['object_name'],
            'object_id': r['object_id'],
            'expected_count': r['expected_count'],
            'real_tables': r['real_tables'],
            'sqlglot_success': r['sqlglot_success']
        }
        for r in parsing_failures
    ],
    'high_priority_failures': [
        {
            'object_name': r['object_name'],
            'object_id': r['object_id'],
            'expected_count': r['expected_count'],
            'real_tables': r['real_tables']
        }
        for r in high_priority
    ]
}

with open('evaluation_baselines/real_data_results/bug004_categorization.json', 'w') as f:
    json.dump(output, f, indent=2)

print("="*80)
print(f"✅ Detailed categorization saved to: evaluation_baselines/real_data_results/bug004_categorization.json")
print("="*80)
