#!/usr/bin/env python3
"""Test semicolon addition on real SP (spLoadHumanResourcesObjects)."""

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
print("SEMICOLON ADDITION TEST: spLoadHumanResourcesObjects")
print("="*80)

# Count original statements
declare_count = len(re.findall(r'\bDECLARE\s+@\w+', original_ddl))
set_count = len(re.findall(r'\bSET\s+@\w+\s*=', original_ddl))
insert_count = len(re.findall(r'\bINSERT\s+INTO\s+', original_ddl))

print(f"\nOriginal DDL:")
print(f"  Size: {len(original_ddl):,} characters")
print(f"  DECLARE statements: {declare_count}")
print(f"  SET statements: {set_count}")
print(f"  INSERT statements: {insert_count}")

# Approach 1: Current (removal)
print(f"\n{'='*80}")
print("Approach 1: Statement Removal (Current)")
print(f"{'='*80}")

cleaned_removal = original_ddl
cleaned_removal = re.sub(r'\bDECLARE\s+@\w+[^\n]*\n', '-- DECLARE removed\n', cleaned_removal)
cleaned_removal = re.sub(r'\bSET\s+@\w+\s*=\s*[^\n;]+[;\n]?', '', cleaned_removal)

declare_after = len(re.findall(r'\bDECLARE\s+@\w+', cleaned_removal))
set_after = len(re.findall(r'\bSET\s+@\w+\s*=', cleaned_removal))
insert_after = len(re.findall(r'\bINSERT\s+INTO\s+', cleaned_removal))

print(f"After removal:")
print(f"  Size: {len(cleaned_removal):,} characters ({(1-len(cleaned_removal)/len(original_ddl))*100:.1f}% reduction)")
print(f"  DECLARE statements: {declare_after} (removed {declare_count - declare_after})")
print(f"  SET statements: {set_after} (removed {set_count - set_after})")
print(f"  INSERT statements: {insert_after} (preserved {insert_after})")

# Approach 2: Add semicolons (user's suggestion)
print(f"\n{'='*80}")
print("Approach 2: Semicolon Addition (User's Suggestion)")
print(f"{'='*80}")

cleaned_semicolon = original_ddl

# Patterns that need semicolons
patterns = [
    (r'(\bDECLARE\s+@\w+[^\n;]+)(?<!;)\n', 'DECLARE'),
    (r'(\bSET\s+@\w+\s*=\s*[^\n;]+)(?<!;)\n', 'SET'),
    (r'(\bINSERT\s+INTO\s+[^\n;]+)(?<!;)\n', 'INSERT'),
    (r'(\bEXEC\s+\w+[^\n;]*)(?<!;)\n', 'EXEC'),
    (r'(\bUPDATE\s+[^\n;]+)(?<!;)\n', 'UPDATE'),
    (r'(\bDELETE\s+[^\n;]+)(?<!;)\n', 'DELETE'),
    (r'(\bCREATE\s+TABLE[^\n;]+)(?<!;)\n', 'CREATE TABLE'),
    (r'(\bDROP\s+TABLE[^\n;]+)(?<!;)\n', 'DROP TABLE'),
]

additions = {}
for pattern, stmt_type in patterns:
    before_count = len(re.findall(pattern, cleaned_semicolon))
    cleaned_semicolon = re.sub(pattern, r'\1;\n', cleaned_semicolon)
    after_count = len(re.findall(pattern, cleaned_semicolon))
    if before_count > 0:
        additions[stmt_type] = before_count

print(f"After adding semicolons:")
print(f"  Size: {len(cleaned_semicolon):,} characters (added {len(cleaned_semicolon) - len(original_ddl):,} chars)")
print(f"  Semicolons added to:")
for stmt_type, count in sorted(additions.items(), key=lambda x: -x[1]):
    print(f"    - {count} {stmt_type} statements")

# Check for double semicolons
double_semi = len(re.findall(r';;', cleaned_semicolon))
print(f"  Double semicolons (;;): {double_semi} {'✅' if double_semi == 0 else '⚠️'}")

# Show sample of transformed SQL
print(f"\n{'='*80}")
print("Sample Output (First 50 lines)")
print(f"{'='*80}")
print('\n'.join(cleaned_semicolon.split('\n')[:50]))

# Save for comparison
output_file = Path('spLoadHumanResourcesObjects_WITH_SEMICOLONS.sql')
with open(output_file, 'w') as f:
    f.write(cleaned_semicolon)
print(f"\n✅ Saved to: {output_file}")

print(f"\n{'='*80}")
print("COMPARISON")
print(f"{'='*80}")
print(f"""
Approach 1 (Removal):
  Size: {len(cleaned_removal):,} chars (-{len(original_ddl) - len(cleaned_removal):,})
  Statements removed: {declare_count + set_count - declare_after - set_after}
  Statements preserved: {insert_after}

Approach 2 (Semicolons):
  Size: {len(cleaned_semicolon):,} chars (+{len(cleaned_semicolon) - len(original_ddl):,})
  Statements removed: 0
  Statements preserved: {declare_count + set_count + insert_count}
  Semicolons added: {sum(additions.values())}

Recommendation: Test Approach 2 with SQLGlot to see if properly delimited
statements parse better than removal approach.
""")
