#!/usr/bin/env python3
"""
Test SQLGlot-Based Confidence Scoring (No Hints Required)
==========================================================

Goal: Calculate confidence based on SQLGlot parse quality metadata
"""

import duckdb
import pandas as pd
from pathlib import Path
import sqlglot
from sqlglot.errors import ErrorLevel
import sys
sys.path.append('/home/user/sandbox')

from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

# Initialize
conn = duckdb.connect(':memory:')
engine = RuleEngine()

# Load parquet files
for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if 'definition' in df.columns and 'referencing_object_id' not in df.columns:
        defs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
        break

for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if {'object_id', 'schema_name', 'object_name', 'object_type'}.issubset(set(df.columns)):
        objs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
        break

# Merge and filter SPs
defs_for_merge = defs_df[['object_id', 'definition']]
merged = defs_for_merge.merge(objs_df[['object_id', 'object_type', 'schema_name', 'object_name']], on='object_id')
sps = merged[merged['object_type'] == 'Stored Procedure']

print(f"Testing SQLGlot-based confidence on {len(sps)} stored procedures...\n")


def extract_unique_tables(parsed_statements):
    """Extract UNIQUE table references with schema only"""
    tables = set()

    if not parsed_statements:
        return tables

    for stmt in parsed_statements:
        for table in stmt.find_all(sqlglot.exp.Table):
            if table.db:
                full_name = f"{table.db.lower()}.{table.name.lower()}"
                tables.add(full_name)

    return tables


def calculate_sqlglot_confidence(parsed_statements, tables_found):
    """
    Calculate confidence based on SQLGlot parse quality metadata

    Strategy 1: Command Node Ratio
    - Command nodes = unparseable sections (WARN mode fallback)
    - Ratio of non-Command nodes = parse quality

    Strategy 2: Table Extraction
    - If tables found > 0 → High confidence
    - If no tables found → Low confidence

    Strategy 3: Hybrid
    - If orchestrator (only EXEC) → 100
    - If Command nodes > 50% → 75 (partial parse)
    - If Command nodes 20-50% → 85 (good parse)
    - If Command nodes < 20% → 100 (excellent parse)
    - If no tables found → 0
    """

    if not parsed_statements:
        return 0, "parse_failed"

    total_stmts = len(parsed_statements)
    command_stmts = sum(1 for stmt in parsed_statements if type(stmt).__name__ == 'Command')
    parseable_stmts = total_stmts - command_stmts
    command_ratio = (command_stmts / total_stmts) * 100 if total_stmts > 0 else 0

    # Check if orchestrator (no tables, only EXEC)
    has_exec_only = all(type(stmt).__name__ == 'Command' for stmt in parsed_statements)
    is_orchestrator = has_exec_only and len(tables_found) == 0

    # Strategy 3: Hybrid approach
    if is_orchestrator:
        return 100, "orchestrator"
    elif len(tables_found) == 0:
        return 0, "no_tables_found"
    elif command_ratio > 50:
        return 75, f"high_command_ratio_{command_ratio:.0f}%"
    elif command_ratio > 20:
        return 85, f"medium_command_ratio_{command_ratio:.0f}%"
    else:
        return 100, f"low_command_ratio_{command_ratio:.0f}%"


# Test on sample SPs
results = []

for idx, row in sps.head(50).iterrows():  # Test on first 50
    sp_id = row['object_id']
    sp_name = f"{row['schema_name']}.{row['object_name']}"
    ddl = row['definition']

    # Parse with best-effort
    try:
        parsed_warn = sqlglot.parse(ddl, dialect='tsql', error_level=ErrorLevel.WARN)
        tables_warn = extract_unique_tables(parsed_warn)
    except:
        parsed_warn = []
        tables_warn = set()

    try:
        cleaned = engine.apply_all(ddl)
        parsed_clean = sqlglot.parse(cleaned, dialect='tsql')
        tables_clean = extract_unique_tables(parsed_clean)
    except:
        parsed_clean = []
        tables_clean = set()

    # Use best result
    if len(tables_clean) > len(tables_warn):
        parsed = parsed_clean
        tables = tables_clean
        method = 'cleaned'
    else:
        parsed = parsed_warn
        tables = tables_warn
        method = 'warn'

    # Calculate confidence
    confidence, reason = calculate_sqlglot_confidence(parsed, tables)

    # Analyze parse quality
    total_stmts = len(parsed)
    command_stmts = sum(1 for stmt in parsed if type(stmt).__name__ == 'Command')
    command_ratio = (command_stmts / total_stmts * 100) if total_stmts > 0 else 0

    results.append({
        'sp_name': sp_name,
        'method': method,
        'total_stmts': total_stmts,
        'command_stmts': command_stmts,
        'command_ratio': command_ratio,
        'tables_found': len(tables),
        'confidence': confidence,
        'confidence_reason': reason
    })

# Display results
results_df = pd.DataFrame(results)

print("=" * 80)
print("SQLGLOT-BASED CONFIDENCE SCORING RESULTS")
print("=" * 80)

print(f"\nConfidence Distribution:")
print(results_df['confidence'].value_counts().sort_index(ascending=False))

print(f"\n\nSample Results:")
print(f"{'SP Name':<60} {'Tbls':<6} {'Conf':<6} {'Reason':<25}")
print("-" * 100)
for _, row in results_df.head(20).iterrows():
    print(f"{row['sp_name']:<60} {row['tables_found']:<6} {row['confidence']:<6} {row['confidence_reason']:<25}")

print(f"\n\nCommand Node Analysis:")
print(f"{'Command Ratio':<20} {'Count':<10} {'Avg Tables':<15} {'Avg Confidence':<15}")
print("-" * 60)

# Group by command ratio buckets
results_df['command_bucket'] = pd.cut(
    results_df['command_ratio'],
    bins=[-1, 20, 50, 100],
    labels=['<20% (Excellent)', '20-50% (Good)', '>50% (Partial)']
)

for bucket in results_df['command_bucket'].cat.categories:
    bucket_data = results_df[results_df['command_bucket'] == bucket]
    if len(bucket_data) > 0:
        avg_tables = bucket_data['tables_found'].mean()
        avg_confidence = bucket_data['confidence'].mean()
        print(f"{bucket:<20} {len(bucket_data):<10} {avg_tables:<15.1f} {avg_confidence:<15.0f}")

print("\n" + "=" * 80)
print("COMPARISON: Hint-Based vs SQLGlot-Based Confidence")
print("=" * 80)

print("""
HINT-BASED CONFIDENCE (Current - v2.1.0):
- Requires: Manual @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints in comments
- Formula: completeness = (found_tables / expected_tables) * 100
- Confidence: 100 if ≥90%, 85 if ≥70%, 75 if ≥50%, 0 if <50%
- Pros: Accurate when hints are correct
- Cons: Most SPs don't have hints, requires manual maintenance

SQLGLOT-BASED CONFIDENCE (Proposed):
- Requires: Nothing! Uses SQLGlot parse metadata
- Formula: Based on Command node ratio and table extraction
- Confidence: 100 if <20% Commands, 85 if 20-50%, 75 if >50%, 0 if no tables
- Pros: Works for all SPs, no manual hints needed
- Cons: Less precise than ground truth hints

HYBRID APPROACH (Recommended):
- Use hint-based confidence IF hints present (most accurate)
- Fall back to SQLGlot-based confidence if no hints (automatic)
- Best of both worlds!

Confidence = hints_present ? hint_confidence() : sqlglot_confidence()
""")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

print("""
FOR PRODUCTION:
1. Remove hint-based confidence as PRIMARY approach (most SPs don't have hints)
2. Use SQLGlot-based confidence as PRIMARY approach (works for all SPs)
3. OPTIONAL: Keep hint-based as OVERRIDE if hints present (for testing/validation)

NEW CONFIDENCE CALCULATION:
def calculate_confidence(parsed_statements, tables_found, is_orchestrator, hints=None):
    # Option 1: Hints present (override - most accurate)
    if hints:
        return calculate_hint_confidence(hints, tables_found)

    # Option 2: SQLGlot-based (default - works for all)
    if is_orchestrator:
        return 100  # Only EXEC calls, no tables
    elif len(tables_found) == 0:
        return 0    # No tables found
    else:
        # Calculate based on parse quality
        command_ratio = calculate_command_ratio(parsed_statements)
        if command_ratio < 20:
            return 100  # Excellent parse
        elif command_ratio < 50:
            return 85   # Good parse
        else:
            return 75   # Partial parse

SIMPLICITY: No regex baseline needed! No hints required!
""")

# Save results
results_df.to_json('evaluation_baselines/sqlglot_confidence_results.json', orient='records', indent=2)
print(f"\n✓ Results saved to evaluation_baselines/sqlglot_confidence_results.json")
