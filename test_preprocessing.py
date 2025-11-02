#!/usr/bin/env python3
"""Test preprocessing on spLoadHumanResourcesObjects to see what's being removed."""

import sys
import re
sys.path.insert(0, '/home/chris/sandbox')

# Read the DDL
with open('spLoadHumanResourcesObjects_DDL.sql', 'r') as f:
    ddl = f.read()

print("="*80)
print("ORIGINAL DDL STATS")
print("="*80)
print(f"Total length: {len(ddl)} characters")
print(f"Total lines: {len(ddl.split(chr(10)))} lines")
print()

# Count DECLARE statements
declare_count = len(re.findall(r'\bDECLARE\s+@\w+', ddl, re.IGNORECASE))
print(f"DECLARE statements: {declare_count}")

# Count SET statements
set_count = len(re.findall(r'\bSET\s+@\w+\s*=', ddl, re.IGNORECASE))
print(f"SET statements: {set_count}")

# Count INSERT statements
insert_count = len(re.findall(r'\bINSERT\s+INTO', ddl, re.IGNORECASE))
print(f"INSERT statements: {insert_count}")

print()
print("="*80)
print("TESTING DECLARE REMOVAL PATTERN")
print("="*80)

# Test DECLARE removal pattern
declare_pattern = r'\bDECLARE\s+@\w+[^\n]*\n'
declare_matches = re.findall(declare_pattern, ddl, re.IGNORECASE)
print(f"Pattern matches: {len(declare_matches)}")
if declare_matches:
    print(f"\nFirst 5 matches:")
    for i, match in enumerate(declare_matches[:5], 1):
        print(f"  {i}. {match[:80]}...")

# Apply removal
cleaned_ddl = re.sub(declare_pattern, '-- DECLARE removed\n', ddl, flags=re.IGNORECASE)
declare_after = len(re.findall(r'\bDECLARE\s+@\w+', cleaned_ddl, re.IGNORECASE))
print(f"\nDECLARE count after removal: {declare_after} (removed: {declare_count - declare_after})")

print()
print("="*80)
print("TESTING SET REMOVAL PATTERN")
print("="*80)

# Test SET removal pattern
set_pattern = r'\bSET\s+@\w+\s*=\s*[^;]+;'
set_matches = re.findall(set_pattern, ddl, re.IGNORECASE)
print(f"Pattern matches: {len(set_matches)}")
if set_matches:
    print(f"\nFirst 5 matches:")
    for i, match in enumerate(set_matches[:5], 1):
        print(f"  {i}. {match[:80]}...")

# Apply removal
cleaned_ddl2 = re.sub(set_pattern, '', cleaned_ddl, flags=re.IGNORECASE)
set_after = len(re.findall(r'\bSET\s+@\w+\s*=', cleaned_ddl2, re.IGNORECASE))
print(f"\nSET count after removal: {set_after} (removed: {set_count - set_after})")

print()
print("="*80)
print("FINAL CLEANED DDL STATS")
print("="*80)
print(f"Original length: {len(ddl)} characters")
print(f"Cleaned length: {len(cleaned_ddl2)} characters")
print(f"Reduction: {100 * (len(ddl) - len(cleaned_ddl2)) / len(ddl):.1f}%")
print(f"INSERT statements preserved: {len(re.findall(r'INSERT\s+INTO', cleaned_ddl2, re.IGNORECASE))}")

# Save cleaned version for inspection
with open('spLoadHumanResourcesObjects_CLEANED.sql', 'w') as f:
    f.write(cleaned_ddl2)

print(f"\n✅ Cleaned DDL saved to: spLoadHumanResourcesObjects_CLEANED.sql")
