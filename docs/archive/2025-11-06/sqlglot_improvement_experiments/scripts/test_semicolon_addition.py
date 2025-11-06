#!/usr/bin/env python3
"""Test adding semicolons vs removing statements."""

import re

# Sample SQL (similar to spLoadHumanResourcesObjects)
sample_sql = """
DECLARE @RowCount INT
SET @RowCount = (SELECT COUNT(*) FROM dbo.SourceTable)
INSERT INTO dbo.TargetTable SELECT * FROM dbo.SourceTable
"""

print("="*80)
print("APPROACH COMPARISON: Semicolon Addition vs Statement Removal")
print("="*80)

# Approach 1: Current (removal)
print("\n1. Current Approach (Remove DECLARE/SET):")
print("-" * 60)
cleaned_v1 = sample_sql
cleaned_v1 = re.sub(r'\bDECLARE\s+@\w+[^\n]*\n', '', cleaned_v1)
cleaned_v1 = re.sub(r'\bSET\s+@\w+\s*=\s*[^\n;]+[;\n]?', '', cleaned_v1)
print(cleaned_v1)
print(f"Statement count: ~1 (only INSERT)")

# Approach 2: Add semicolons (user's suggestion)
print("\n2. User's Approach (Add Semicolons):")
print("-" * 60)
cleaned_v2 = sample_sql

# Add semicolon after DECLARE if missing
cleaned_v2 = re.sub(
    r'(\bDECLARE\s+@\w+[^\n;]*)\n',
    r'\1;\n',
    cleaned_v2
)

# Add semicolon after SET if missing
cleaned_v2 = re.sub(
    r'(\bSET\s+@\w+\s*=\s*[^\n;]+)\n',
    r'\1;\n',
    cleaned_v2
)

# Add semicolon after INSERT if missing
cleaned_v2 = re.sub(
    r'(\bINSERT\s+INTO\s+[^\n;]+)\n',
    r'\1;\n',
    cleaned_v2
)

print(cleaned_v2)
print(f"Statement count: ~3 (all statements preserved with semicolons)")

# Test double semicolons
print("\n3. Test: What if statement already has semicolon?")
print("-" * 60)
sql_with_semicolon = "DECLARE @count INT;\nINSERT INTO table SELECT * FROM source\n"
result = re.sub(r'(\bDECLARE\s+@\w+[^\n;]*)\n', r'\1;\n', sql_with_semicolon)
result = re.sub(r'(\bINSERT\s+INTO\s+[^\n;]+)\n', r'\1;\n', result)
print(result)
if ';;' in result:
    print("⚠️  Creates double semicolon (;;)")
else:
    print("✅ No double semicolons")

# Better pattern that checks for existing semicolon
print("\n4. Improved Pattern (Avoid Double Semicolons):")
print("-" * 60)
sql_mixed = """DECLARE @count INT
DECLARE @date DATETIME;
SET @count = 100
INSERT INTO table SELECT * FROM source;
"""
print("Input:")
print(sql_mixed)

# Pattern: Add semicolon only if not already present
improved = sql_mixed
improved = re.sub(
    r'(\bDECLARE\s+@\w+[^\n;]+)(?<!;)\n',  # Negative lookbehind for ;
    r'\1;\n',
    improved
)
improved = re.sub(
    r'(\bSET\s+@\w+\s*=\s*[^\n;]+)(?<!;)\n',
    r'\1;\n',
    improved
)
improved = re.sub(
    r'(\bINSERT\s+INTO\s+[^\n;]+)(?<!;)\n',
    r'\1;\n',
    improved
)

print("\nOutput:")
print(improved)
if ';;' in improved:
    print("❌ Still creates double semicolons")
else:
    print("✅ No double semicolons!")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)
print("""
User's approach (add semicolons) has several advantages:

✅ Addresses root cause (delimiter ambiguity)
✅ Keeps DECLARE/SET (better for debugging)
✅ Simpler than block extraction (Plan B)
✅ Might improve parsing beyond current removal approach

Implementation:
- Use negative lookbehind (?<!;) to avoid double semicolons
- Apply to DECLARE, SET, and all statement types
- SQLGlot will handle properly delimited statements

Next step: Test on actual spLoadHumanResourcesObjects DDL
""")
