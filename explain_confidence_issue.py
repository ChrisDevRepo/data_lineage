#!/usr/bin/env python3
"""
Show the REAL problem with 75% confidence scoring.

The user's point: Input/Output lineage is CORRECT, so why warning?
"""

import re

SQL = """
TRUNCATE TABLE [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics];

INSERT INTO [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics]
SELECT * FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary]

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Interest_Summary_Metrics])
SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[SAP_Sales_Summary_Metrics])
"""

print("="*80)
print("THE REAL PROBLEM: Confidence Calculation Logic")
print("="*80)
print()

# STEP 1: Regex baseline (SMOKE TEST) - counts EVERYTHING
print("STEP 1: REGEX BASELINE (Smoke Test)")
print("-"*80)

# Count all INSERT/TRUNCATE targets
targets = re.findall(r'(?:INSERT INTO|TRUNCATE TABLE)\s+\[?(\w+)\]?\.\[?(\w+)\]?', SQL, re.IGNORECASE)
# Count all FROM sources
sources = re.findall(r'FROM\s+\[?(\w+)\]?\.\[?(\w+)\]?', SQL, re.IGNORECASE)

regex_targets = set([f"{s}.{t}" for s, t in targets])
regex_sources = set([f"{s}.{t}" for s, t in sources])

print(f"Targets found by regex: {regex_targets}")
print(f"  → SAP_Sales_Interest_Summary_Metrics appears 2x (TRUNCATE + INSERT)")
print()
print(f"Sources found by regex: {regex_sources}")
print(f"  → Includes administrative SELECT COUNT(*) queries")
print()
print(f"TOTAL EXPECTED: {len(regex_targets) + len(regex_sources)} table references")
print()

# STEP 2: Parser (AFTER CLEANING) - filters administrative queries
print("STEP 2: PARSER OUTPUT (After Dataflow Filtering)")
print("-"*80)

# Simulate parser behavior
parser_targets = {"CONSUMPTION_FINANCE.SAP_Sales_Interest_Summary_Metrics"}  # Only INSERT (TRUNCATE removed)
parser_sources = {"CONSUMPTION_FINANCE.SAP_Sales_Summary"}  # Only main FROM (SET removed)

print(f"Targets found by parser: {parser_targets}")
print(f"  → SAP_Sales_Interest_Summary_Metrics appears 1x (only INSERT)")
print(f"  → TRUNCATE was filtered out (dataflow mode)")
print()
print(f"Sources found by parser: {parser_sources}")
print(f"  → Only main SELECT FROM clause")
print(f"  → Administrative SELECT COUNT(*) filtered out")
print()
print(f"TOTAL FOUND: {len(parser_targets) + len(parser_sources)} table references")
print()

# STEP 3: CONFIDENCE CALCULATION
print("STEP 3: CONFIDENCE CALCULATION")
print("-"*80)

expected = len(regex_targets) + len(regex_sources)
found = len(parser_targets) + len(parser_sources)
completeness = (found / expected) * 100 if expected > 0 else 0

print(f"Expected (from smoke test): {expected}")
print(f"Found (by parser):          {found}")
print(f"Completeness:               {completeness:.1f}%")
print()

# v2.1.0 model
if completeness >= 90:
    confidence = 100
elif completeness >= 70:
    confidence = 85
elif completeness >= 50:
    confidence = 75
else:
    confidence = 0

print(f"Confidence: {confidence}% (⚠️ Acceptable)")
print()

# STEP 4: THE PROBLEM
print("="*80)
print("🚨 THE PROBLEM")
print("="*80)
print()
print("The confidence score compares:")
print("  ❌ What smoke test EXPECTS (includes administrative queries)")
print("  vs")
print("  ✅ What parser FINDS (filters administrative queries)")
print()
print("This is APPLES vs ORANGES comparison!")
print()
print("BUSINESS LINEAGE (what user cares about):")
print("  ✅ Input:  SAP_Sales_Summary")
print("  ✅ Output: SAP_Sales_Interest_Summary_Metrics")
print("  ✅ CORRECT! Should be 100% confidence!")
print()
print("But confidence score sees:")
print("  Expected 5 refs, found 2 refs → 40% completeness → 75% confidence")
print()
print("="*80)
print("ROOT CAUSE")
print("="*80)
print()
print("Smoke test (regex) counts:")
print("  1. TRUNCATE TABLE output          ← Filtered by parser (dataflow mode)")
print("  2. INSERT INTO output              ← Counted by parser ✓")
print("  3. SELECT FROM input               ← Counted by parser ✓")
print("  4. SELECT COUNT(*) input (admin)   ← Filtered by parser (dataflow mode)")
print("  5. SELECT COUNT(*) input (admin)   ← Filtered by parser (dataflow mode)")
print()
print("Parser is CORRECT to filter #1, #4, #5 (they're administrative noise).")
print("But confidence calculation PENALIZES parser for doing the right thing!")
print()
print("="*80)
print("THE FIX")
print("="*80)
print()
print("Option A: Confidence should ONLY compare BUSINESS TABLES")
print("  - Exclude TRUNCATE from smoke test")
print("  - Exclude administrative SELECT COUNT(*) from smoke test")
print("  - Result: Expected 2, Found 2 → 100% confidence ✓")
print()
print("Option B: Add back TRUNCATE and admin queries to parser")
print("  - More noise in lineage graph")
print("  - Result: Expected 5, Found 5 → 100% confidence")
print()
print("Option C: Accept that smoke test is pessimistic")
print("  - Keep current behavior")
print("  - 75% is 'acceptable' even though lineage is correct")
print("  - Users add hints if they want 100%")
