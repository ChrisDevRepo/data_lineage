#!/usr/bin/env python3
"""Test SQLGlot's statement delimiter handling with T-SQL."""

import sqlglot
from sqlglot import parse

print("="*80)
print("TEST: SQLGlot T-SQL Statement Delimiter Handling")
print("="*80)

# Test 1: Multiple statements with newlines (production SQL)
test1 = """
DECLARE @RowCount INT
SET @RowCount = (SELECT COUNT(*) FROM dbo.SourceTable)
INSERT INTO dbo.TargetTable SELECT * FROM dbo.SourceTable
"""

print("\n1. Multiple statements with newlines (production SQL):")
print("-" * 60)
try:
    ast = parse(test1, dialect="tsql")
    print(f"✅ Parsed successfully: {len(ast)} statements")
    for i, stmt in enumerate(ast, 1):
        print(f"   {i}. {type(stmt).__name__}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 2: Multiple statements with semicolons (recommended)
test2 = """
DECLARE @RowCount INT;
SET @RowCount = (SELECT COUNT(*) FROM dbo.SourceTable);
INSERT INTO dbo.TargetTable SELECT * FROM dbo.SourceTable;
"""

print("\n2. Multiple statements with semicolons:")
print("-" * 60)
try:
    ast = parse(test2, dialect="tsql")
    print(f"✅ Parsed successfully: {len(ast)} statements")
    for i, stmt in enumerate(ast, 1):
        print(f"   {i}. {type(stmt).__name__}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: Only INSERT (DECLARE/SET removed - our approach)
test3 = """
INSERT INTO dbo.TargetTable SELECT * FROM dbo.SourceTable
"""

print("\n3. Only INSERT (DECLARE/SET removed - our approach):")
print("-" * 60)
try:
    ast = parse(test3, dialect="tsql")
    print(f"✅ Parsed successfully: {len(ast)} statements")
    for i, stmt in enumerate(ast, 1):
        print(f"   {i}. {type(stmt).__name__}")

    # Extract lineage
    if ast:
        for table in ast[0].find_all(sqlglot.exp.Table):
            print(f"   📊 Table: {table.name}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 4: Parameter in WHERE clause (user's concern)
test4 = """
SELECT * FROM dbo.SourceTable WHERE id = @param
"""

print("\n4. Parameter in WHERE clause (user's concern):")
print("-" * 60)
try:
    ast = parse(test4, dialect="tsql")
    print(f"✅ Parsed successfully: {len(ast)} statements")
    for i, stmt in enumerate(ast, 1):
        print(f"   {i}. {type(stmt).__name__}")

    # Check if parameter caused issues
    if ast:
        for table in ast[0].find_all(sqlglot.exp.Table):
            print(f"   📊 Table: {table.name}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 5: Complex parameter value (subquery in SET)
test5 = """
SET @RowCount = (SELECT COUNT(*) FROM dbo.SourceTable)
"""

print("\n5. SET with subquery (what we remove):")
print("-" * 60)
try:
    ast = parse(test5, dialect="tsql")
    print(f"✅ Parsed successfully: {len(ast)} statements")
    for i, stmt in enumerate(ast, 1):
        print(f"   {i}. {type(stmt).__name__}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("Based on GitHub issue #3095:")
print("• SQLGlot struggles with newline delimiters in multi-statement T-SQL")
print("• Semicolons are recommended but production SQL uses newlines")
print("• Removing DECLARE/SET reduces statement count → better parsing")
print("• Parameters (@variable) themselves don't break parsing")
print("="*80)
