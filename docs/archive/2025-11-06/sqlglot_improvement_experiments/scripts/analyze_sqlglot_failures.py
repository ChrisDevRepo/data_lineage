#!/usr/bin/env python3
"""Analyze SQLGlot failure patterns from parse log."""

import re
from collections import defaultdict
from pathlib import Path

log_file = Path('/tmp/parse_output.log')
if not log_file.exists():
    print("❌ Parse log not found")
    exit(1)

with open(log_file, 'r') as f:
    log_content = f.read()

print("="*80)
print("SQLGLOT FAILURE ANALYSIS")
print("="*80)

# Extract all unsupported syntax messages
failures = re.findall(r"'([^']+)' contains unsupported syntax\. Falling back", log_content)

print(f"\nTotal fallback messages: {len(failures)}")

# Categorize by pattern
categories = defaultdict(list)

for failure in failures:
    # Categorize by what the fragment starts with
    fragment = failure.strip()

    if fragment.startswith('CREATE PROC'):
        categories['Truncated CREATE PROC'].append(fragment[:80])
    elif fragment.startswith('DECLARE'):
        categories['DECLARE fragments'].append(fragment[:80])
    elif fragment.startswith('SET'):
        categories['SET fragments'].append(fragment[:80])
    elif fragment.startswith('BEGIN'):
        categories['BEGIN fragments'].append(fragment[:80])
    elif fragment.startswith('END'):
        categories['END fragments'].append(fragment[:80])
    elif fragment.startswith('EXEC') or 'EXEC' in fragment[:20]:
        categories['EXEC fragments'].append(fragment[:80])
    elif fragment.startswith('PRINT'):
        categories['PRINT fragments'].append(fragment[:80])
    elif fragment.startswith('IF') or fragment.startswith('ELSE'):
        categories['IF/ELSE fragments'].append(fragment[:80])
    elif 'SELECT' in fragment and len(fragment) < 50:
        categories['SELECT fragments'].append(fragment[:80])
    elif len(fragment) < 10:
        categories['Random fragments (< 10 chars)'].append(fragment)
    else:
        categories['Other'].append(fragment[:80])

# Print summary
print(f"\n{'='*80}")
print("FAILURE CATEGORIES")
print(f"{'='*80}")

for category, fragments in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f"\n{category}: {len(fragments)} occurrences")
    print("-" * 60)
    # Show first 5 examples
    for fragment in fragments[:5]:
        print(f"  • {fragment}")
    if len(fragments) > 5:
        print(f"  ... and {len(fragments) - 5} more")

# Count preprocessing validation failures
validation_failures = re.findall(r'Preprocessing validation failed for object (\d+)', log_content)
print(f"\n{'='*80}")
print(f"PREPROCESSING VALIDATION FAILURES: {len(validation_failures)}")
print(f"{'='*80}")

# Count objects with "Preprocessing removed table references"
removed_refs = re.findall(r'Preprocessing removed table references! Original: (\d+) tables, Cleaned: (\d+) tables', log_content)
print(f"\nObjects where preprocessing removed ALL table references: {len(removed_refs)}")

lost_tables = {}
for orig, cleaned in removed_refs:
    lost = int(orig) - int(cleaned)
    if lost not in lost_tables:
        lost_tables[lost] = 0
    lost_tables[lost] += 1

print("\nTable loss distribution:")
for lost_count in sorted(lost_tables.keys(), reverse=True):
    print(f"  Lost {lost_count} tables: {lost_tables[lost_count]} SPs")

print(f"\n{'='*80}")
print("ACTIONABLE INSIGHTS")
print(f"{'='*80}")

# Calculate impact
total_validation_failures = len(validation_failures)
total_fallbacks = len(failures)

print(f"""
1. Preprocessing validation failed for {total_validation_failures} objects
   → Parser fell back to ORIGINAL DDL (not preprocessed)
   → These might succeed if preprocessing didn't break them

2. SQLGlot produced {total_fallbacks} fallback messages
   → Individual statements couldn't be parsed
   → Fell back to regex extraction (0.50 confidence)

3. Leading semicolons caused:
   - Truncated CREATE PROC statements: {len(categories.get('Truncated CREATE PROC', []))}
   - Random fragments (<10 chars): {len(categories.get('Random fragments (< 10 chars)', []))}
   - BEGIN/END orphans: {len(categories.get('BEGIN fragments', [])) + len(categories.get('END fragments', []))}

RECOMMENDATION:
- If we fix statement splitting → could recover ~{total_validation_failures} SPs
- Simple regex adjustment: Remove leading semicolons from multi-line statements
- Or revert to NO preprocessing (let SQLGlot parse original DDL)
""")
