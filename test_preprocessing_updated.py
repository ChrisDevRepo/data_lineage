#!/usr/bin/env python3
"""Test UPDATED preprocessing patterns."""

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
declare_count = len(re.findall(r'\bDECLARE\s+@\w+', ddl, re.IGNORECASE))
set_count = len(re.findall(r'\bSET\s+@\w+\s*=', ddl, re.IGNORECASE))
insert_count = len(re.findall(r'\bINSERT\s+INTO', ddl, re.IGNORECASE))
print(f"DECLARE statements: {declare_count}")
print(f"SET statements: {set_count}")
print(f"INSERT statements: {insert_count}")

print()
print("="*80)
print("APPLYING UPDATED PATTERNS")
print("="*80)

# Apply DECLARE removal
declare_pattern = r'\bDECLARE\s+@\w+[^\n]*\n'
cleaned = re.sub(declare_pattern, '-- DECLARE removed\n', ddl, flags=re.IGNORECASE)
declare_after = len(re.findall(r'\bDECLARE\s+@\w+', cleaned, re.IGNORECASE))
print(f"✅ DECLARE removal: {declare_count} → {declare_after} (removed {declare_count - declare_after})")

# Apply UPDATED SET removal (new pattern)
set_pattern = r'\bSET\s+@\w+\s*=\s*[^\n;]+[;\n]?'
cleaned = re.sub(set_pattern, '', cleaned, flags=re.IGNORECASE)
set_after = len(re.findall(r'\bSET\s+@\w+\s*=', cleaned, re.IGNORECASE))
print(f"✅ SET removal: {set_count} → {set_after} (removed {set_count - set_after})")

# Apply SET NOCOUNT removal
cleaned = re.sub(r'\bSET\s+(NOCOUNT|XACT_ABORT)\s+(ON|OFF)\b', '', cleaned, flags=re.IGNORECASE)

insert_after = len(re.findall(r'\bINSERT\s+INTO', cleaned, re.IGNORECASE))

print()
print("="*80)
print("FINAL CLEANED DDL STATS")
print("="*80)
print(f"Original length: {len(ddl)} characters")
print(f"Cleaned length: {len(cleaned)} characters")
print(f"Reduction: {100 * (len(ddl) - len(cleaned)) / len(ddl):.1f}%")
print(f"INSERT statements preserved: {insert_after}/{insert_count}")

# Save cleaned version
with open('spLoadHumanResourcesObjects_CLEANED_v2.sql', 'w') as f:
    f.write(cleaned)

print(f"\n✅ Cleaned DDL saved to: spLoadHumanResourcesObjects_CLEANED_v2.sql")

# Show sample of cleaned DDL (first INSERT statement)
print()
print("="*80)
print("SAMPLE OF CLEANED DDL (First INSERT)")
print("="*80)
insert_match = re.search(r'(INSERT\s+INTO[^\n]+\n(?:[^\n]+\n){0,10})', cleaned, re.IGNORECASE)
if insert_match:
    print(insert_match.group(1))
