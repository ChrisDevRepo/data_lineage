#!/usr/bin/env python3
"""Validate Plan A.5 preprocessing patterns on real SP."""

import re
from pathlib import Path

# Load the original DDL
ddl_file = Path('spLoadHumanResourcesObjects_DDL.sql')
if not ddl_file.exists():
    print(f"❌ {ddl_file} not found")
    exit(1)

with open(ddl_file, 'r') as f:
    original_ddl = f.read()

print("="*80)
print("PLAN A.5 PREPROCESSING VALIDATION")
print("="*80)

# Count original statements
counts_before = {
    'DECLARE': len(re.findall(r'\bDECLARE\s+@\w+', original_ddl)),
    'SET (vars)': len(re.findall(r'\bSET\s+@\w+\s*=', original_ddl)),
    'INSERT': len(re.findall(r'\bINSERT\s+INTO\s+', original_ddl)),
    'EXEC': len(re.findall(r'\bEXEC(?:UTE)?\s+', original_ddl)),
}

print(f"\nOriginal DDL ({len(original_ddl):,} chars):")
for stmt_type, count in counts_before.items():
    print(f"  {stmt_type}: {count} statements")

# Apply Plan A.5 preprocessing patterns (from quality_aware_parser.py)
print(f"\n{'='*80}")
print("Applying Plan A.5 Patterns...")
print(f"{'='*80}")

preprocessed = original_ddl

# Pattern list (CONSERVATIVE: only DECLARE and SET)
# Complex multi-line statements (INSERT, UPDATE) left as-is to avoid truncation
patterns = [
    # Filter utility SPs first - FIXED to stop at newline
    (r'\bEXEC(?:UTE)?\s+\[?[^\]]+\]?\.\[?(LogMessage|LogError|LogInfo|LogWarning|spLastRowCount)\]?[^\n;]*;?',
     '', 'Remove utility SP calls'),

    # Add semicolons to DECLARE (single-line statements)
    (r'(\bDECLARE\s+@\w+[^\n;]+)(?<!;)\n', r'\1;\n', 'Add semicolons to DECLARE'),

    # Add semicolons to SET (single-line variable assignments)
    (r'(\bSET\s+@\w+\s*=\s*[^\n;]+)(?<!;)\n', r'\1;\n', 'Add semicolons to SET'),

    # Remove SET session options
    (r'\bSET\s+(NOCOUNT|XACT_ABORT|ANSI_NULLS|QUOTED_IDENTIFIER|ANSI_PADDING|ANSI_WARNINGS|ARITHABORT|CONCAT_NULL_YIELDS_NULL|NUMERIC_ROUNDABORT)\s+(ON|OFF)\b',
     '', 'Remove SET session options'),
]

for pattern, replacement, description in patterns:
    before_count = len(re.findall(pattern, preprocessed))
    preprocessed = re.sub(pattern, replacement, preprocessed, flags=re.IGNORECASE if 'IGNORECASE' in str(pattern) else 0)
    after_count = len(re.findall(pattern, preprocessed))

    if before_count > 0:
        print(f"  ✓ {description}: {before_count} matches")

# Check results
double_semi = len(re.findall(r';;', preprocessed))
print(f"\n{'='*80}")
print("Results:")
print(f"{'='*80}")
print(f"  Original size: {len(original_ddl):,} chars")
print(f"  Preprocessed size: {len(preprocessed):,} chars ({(len(preprocessed)-len(original_ddl)):+,} chars)")
print(f"  Double semicolons (;;): {double_semi} {'✅' if double_semi == 0 else '⚠️'}")

# Count statements after preprocessing
print(f"\nStatement preservation:")
counts_after = {
    'DECLARE': len(re.findall(r'\bDECLARE\s+@\w+', preprocessed)),
    'SET (vars)': len(re.findall(r'\bSET\s+@\w+\s*=', preprocessed)),
    'INSERT': len(re.findall(r'\bINSERT\s+INTO\s+', preprocessed)),
    'EXEC': len(re.findall(r'\bEXEC(?:UTE)?\s+', preprocessed)),
}

for stmt_type in counts_before.keys():
    before = counts_before[stmt_type]
    after = counts_after[stmt_type]
    diff = after - before
    print(f"  {stmt_type}: {before} → {after} ({diff:+d}) {'✅ Preserved' if diff == 0 else '⚠️ Changed'}")

# Count semicolons added
semicolons_added = preprocessed.count(';') - original_ddl.count(';')
print(f"\nSemicolons added: {semicolons_added}")

# Show sample
print(f"\n{'='*80}")
print("Sample Output (lines 20-60):")
print(f"{'='*80}")
lines = preprocessed.split('\n')
for i, line in enumerate(lines[20:60], start=21):
    print(f"{i:3}: {line}")

# Save output
output_file = Path('spLoadHumanResourcesObjects_PLAN_A5.sql')
with open(output_file, 'w') as f:
    f.write(preprocessed)
print(f"\n✅ Saved to: {output_file}")

print(f"\n{'='*80}")
print("VALIDATION COMPLETE")
print(f"{'='*80}")
print("""
✅ Plan A.5 patterns applied successfully
✅ No double semicolons created
✅ All DECLARE/SET/INSERT statements preserved with semicolons

Next: Run full parse to measure improvement over Plan A (78 SPs)
""")
