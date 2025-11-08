#!/usr/bin/env python3
"""
Test with FIXED pattern (handles nested parentheses).
"""

import re

SQL = """
CREATE PROC [CONSUMPTION_FINANCE].[spLoadSAPSalesInterestSummaryMetrics] AS
BEGIN

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics])

TRUNCATE TABLE [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics];

INSERT INTO [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics]
SELECT * FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary]

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics])

END
"""

print("="*80)
print("FIXED PATTERN TEST")
print("="*80)
print()

# Remove comments
ddl = re.sub(r'--[^\n]*', '', SQL)
ddl = re.sub(r'/\*.*?\*/', '', ddl, flags=re.DOTALL)

print("OLD PATTERN (broken - doesn't handle nested parens):")
print("-"*80)
old_pattern = r'(?:SET|DECLARE)\s+@\w+[^=]*=\s*\([^)]*\)'
ddl_old = re.sub(old_pattern, '', ddl, flags=re.IGNORECASE)
old_matches = re.findall(old_pattern, ddl, re.IGNORECASE)
print(f"Matches found: {len(old_matches)}")
for m in old_matches:
    print(f"  {m}")
print()

print("NEW PATTERN (fixed - handles nested parens):")
print("-"*80)
new_pattern = r'(?:SET|DECLARE)\s+@\w+.*?(?:;|\n)'
ddl_new = re.sub(new_pattern, '\n', ddl, flags=re.IGNORECASE | re.DOTALL)
new_matches = re.findall(new_pattern, ddl, re.IGNORECASE | re.DOTALL)
print(f"Matches found: {len(new_matches)}")
for m in new_matches:
    print(f"  {m[:80]}...")
print()

# Count sources on FIXED cleaned DDL
source_patterns = [
    r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?',
]

sources_old = set()
for pattern in source_patterns:
    matches = re.findall(pattern, ddl_old, re.IGNORECASE)
    for schema, table in matches:
        sources_old.add(f"{schema}.{table}")

sources_new = set()
for pattern in source_patterns:
    matches = re.findall(pattern, ddl_new, re.IGNORECASE)
    for schema, table in matches:
        sources_new.add(f"{schema}.{table}")

print("="*80)
print("SOURCES COUNTED:")
print(f"  OLD pattern: {sources_old}")
print(f"  NEW pattern: {sources_new}")
print()

# Count targets (no TRUNCATE)
target_patterns = [
    r'\bINSERT\s+(?:INTO\s+)?\[?(\w+)\]?\.\[?(\w+)\]?',
]

targets = set()
for pattern in target_patterns:
    matches = re.findall(pattern, ddl, re.IGNORECASE)
    for schema, table in matches:
        targets.add(f"{schema}.{table}")

print(f"TARGETS: {targets}")
print()

# Calculate with NEW pattern
expected = len(sources_new) + len(targets)
parser_found = 2  # 1 target + 1 source

completeness = (parser_found / expected) * 100 if expected > 0 else 0

if completeness >= 90:
    conf = 100
elif completeness >= 70:
    conf = 85
elif completeness >= 50:
    conf = 75
else:
    conf = 0

print("="*80)
print("RESULT WITH FIXED PATTERN:")
print(f"  Expected: {expected} ({len(targets)} targets + {len(sources_new)} sources)")
print(f"  Found: {parser_found}")
print(f"  Completeness: {completeness:.1f}%")
print(f"  Confidence: {conf}%")
print()

if conf == 100:
    print("✅ SUCCESS! Fix works - 100% confidence")
else:
    print(f"⚠️ Still {conf}% - investigating remaining sources...")
    print()
    print("Sources that shouldn't be counted:")
    for s in sources_new:
        if s not in {"CONSUMPTION_FINANCE.SAP_Sales_Summary"}:
            print(f"  - {s} (WHY IS THIS STILL HERE?)")
