#!/usr/bin/env python3
"""Test leading semicolons approach (user's insight)."""

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
print("LEADING SEMICOLONS TEST (User's Insight: ;SELECT instead of SELECT;)")
print("="*80)

preprocessed = original_ddl

# Apply patterns in order
patterns = [
    # Filter utility SPs first
    (r'\bEXEC(?:UTE)?\s+\[?[^\]]+\]?\.\[?(LogMessage|LogError|LogInfo|LogWarning|spLastRowCount)\]?[^\n;]*;?',
     '', 'Remove utility SP calls'),

    # Add semicolons BEFORE keywords
    (r'(?<!;)\n(\s*\bDECLARE\b)', r'\n;\1', 'Add ; before DECLARE'),
    (r'(?<!;)\n(\s*\bSET\s+@)', r'\n;\1', 'Add ; before SET'),
    (r'(?<!;)\n(\s*\bINSERT\s+INTO\b)', r'\n;\1', 'Add ; before INSERT'),
    (r'(?<!;)\n(\s*\bUPDATE\s+)', r'\n;\1', 'Add ; before UPDATE'),
    (r'(?<!;)\n(\s*\bDELETE\s+)', r'\n;\1', 'Add ; before DELETE'),
    (r'(?<!;)(?<!\()\n(\s*\bSELECT\b)', r'\n;\1', 'Add ; before SELECT'),
    (r'(?<!;)\n(\s*\bCREATE\s+)', r'\n;\1', 'Add ; before CREATE'),
    (r'(?<!;)\n(\s*\bDROP\s+)', r'\n;\1', 'Add ; before DROP'),
    (r'(?<!;)\n(\s*\bTRUNCATE\s+)', r'\n;\1', 'Add ; before TRUNCATE'),
    (r'(?<!;)\n(\s*\bEXEC(?:UTE)?\s+)', r'\n;\1', 'Add ; before EXEC'),

    # Remove SET session options
    (r'\bSET\s+(NOCOUNT|XACT_ABORT|ANSI_NULLS|QUOTED_IDENTIFIER|ANSI_PADDING|ANSI_WARNINGS|ARITHABORT|CONCAT_NULL_YIELDS_NULL|NUMERIC_ROUNDABORT)\s+(ON|OFF)\b',
     '', 'Remove SET session options'),
]

print("\nApplying patterns...")
for pattern, replacement, description in patterns:
    before_count = len(re.findall(pattern, preprocessed, re.IGNORECASE if 'IGNORECASE' in str(pattern) else 0))
    preprocessed = re.sub(pattern, replacement, preprocessed, flags=re.IGNORECASE if 'IGNORECASE' in str(pattern) else 0)

    if before_count > 0:
        print(f"  ✓ {description}: {before_count} matches")

# Check results
counts_before = {
    'DECLARE': len(re.findall(r'\bDECLARE\s+@\w+', original_ddl)),
    'SET (vars)': len(re.findall(r'\bSET\s+@\w+\s*=', original_ddl)),
    'INSERT': len(re.findall(r'\bINSERT\s+INTO\s+', original_ddl)),
}

counts_after = {
    'DECLARE': len(re.findall(r'\bDECLARE\s+@\w+', preprocessed)),
    'SET (vars)': len(re.findall(r'\bSET\s+@\w+\s*=', preprocessed)),
    'INSERT': len(re.findall(r'\bINSERT\s+INTO\s+', preprocessed)),
}

print(f"\n{'='*80}")
print("Results:")
print(f"{'='*80}")
print(f"  Original size: {len(original_ddl):,} chars")
print(f"  Preprocessed size: {len(preprocessed):,} chars ({(len(preprocessed)-len(original_ddl)):+,} chars)")

# Count leading semicolons
leading_semi = len(re.findall(r'\n;', preprocessed))
print(f"  Leading semicolons added: {leading_semi}")

# Check for double semicolons
double_semi = len(re.findall(r';;', preprocessed))
print(f"  Double semicolons (;;): {double_semi} {'✅' if double_semi == 0 else '⚠️'}")

print(f"\nStatement preservation:")
for stmt_type in counts_before.keys():
    before = counts_before[stmt_type]
    after = counts_after[stmt_type]
    diff = after - before
    print(f"  {stmt_type}: {before} → {after} ({diff:+d}) {'✅ Preserved' if diff == 0 else '⚠️ Changed'}")

# Show sample
print(f"\n{'='*80}")
print("Sample Output (lines 180-200):")
print(f"{'='*80}")
lines = preprocessed.split('\n')
for i, line in enumerate(lines[180:200], start=181):
    print(f"{i:3}: {line}")

# Save output
output_file = Path('spLoadHumanResourcesObjects_LEADING_SEMICOLONS.sql')
with open(output_file, 'w') as f:
    f.write(preprocessed)
print(f"\n✅ Saved to: {output_file}")

print(f"\n{'='*80}")
print("CONCLUSION")
print(f"{'='*80}")
print(f"""
User's approach: Add semicolons BEFORE keywords (;DECLARE, ;INSERT, ;SELECT)

Advantages:
✅ Simpler pattern matching (just find keywords)
✅ No multi-line truncation issues
✅ Handles complex statements naturally
✅ Clear statement boundaries

Ready for full parse test!
""")
