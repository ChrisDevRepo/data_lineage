#!/usr/bin/env python3
"""
Deep analysis of why parser fails on specific SP.
Target SP: spLoadFactLaborCostForEarnedValue_Post

Expected results:
- Target: [CONSUMPTION_ClinOpsFinance].[FactLaborCostForEarnedValue_Post]
- Sources:
  - [CONSUMPTION_POWERBI].[FactLaborCostForEarnedValue]
  - [CONSUMPTION_ClinOpsFinance].[CadenceBudget_LaborCost_PrimaContractUtilization_Junc]
"""

import sys
import duckdb
import re
from sqlglot import parse_one
from sqlglot.errors import ErrorLevel

# Extract SP definition from database
conn = duckdb.connect('data/lineage_workspace.duckdb')

# First, find the SP
sp_search = conn.execute("""
    SELECT o.object_id, o.object_name, o.schema_name, d.definition
    FROM objects o
    JOIN definitions d ON o.object_id = d.object_id
    WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
    AND o.object_type = 'Stored Procedure'
""").fetchall()

if not sp_search:
    print("❌ SP not found in database!")
    sys.exit(1)

for sp_id, sp_name, schema, ddl in sp_search:
    print(f"Found: {schema}.{sp_name} (ID: {sp_id})")
    print(f"Definition length: {len(ddl)} characters")
    print("="*80)
    print()

    # Show first 1000 chars
    print("📝 First 1000 characters of DDL:")
    print(ddl[:1000])
    print("...")
    print()
    print("="*80)
    print()

    # Step 1: Test regex extraction
    print("STEP 1: REGEX EXTRACTION")
    print("-"*80)

    # Simple regex patterns
    from_pattern = r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?'
    into_pattern = r'\bINTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
    insert_pattern = r'\bINSERT\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
    update_pattern = r'\bUPDATE\s+\[?(\w+)\]?\.\[?(\w+)\]?'

    from_tables = re.findall(from_pattern, ddl, re.IGNORECASE)
    into_tables = re.findall(into_pattern, ddl, re.IGNORECASE)
    insert_tables = re.findall(insert_pattern, ddl, re.IGNORECASE)
    update_tables = re.findall(update_pattern, ddl, re.IGNORECASE)

    print(f"FROM tables found: {len(from_tables)}")
    for schema, table in from_tables[:5]:
        print(f"  - [{schema}].[{table}]")
    if len(from_tables) > 5:
        print(f"  ... and {len(from_tables) - 5} more")

    print(f"\nINTO/INSERT/UPDATE tables found: {len(into_tables) + len(insert_tables) + len(update_tables)}")
    for schema, table in (into_tables + insert_tables + update_tables)[:5]:
        print(f"  - [{schema}].[{table}]")

    print()
    print("="*80)
    print()

    # Step 2: Test SQLGlot WARN mode
    print("STEP 2: SQLGLOT WARN MODE")
    print("-"*80)

    try:
        # Try parsing first 2000 chars to see if it's a SQL structure issue
        short_ddl = ddl[:2000]
        parsed_warn = parse_one(short_ddl, dialect='tsql', error_level=ErrorLevel.WARN)

        print("✅ SQLGlot WARN mode succeeded on first 2000 chars")
        print(f"Parsed AST type: {type(parsed_warn)}")
        print(f"AST has errors: {parsed_warn.error_level is not None if hasattr(parsed_warn, 'error_level') else 'N/A'}")

        # Try to extract tables from AST
        from sqlglot import exp

        tables_found = []
        for table in parsed_warn.find_all(exp.Table):
            table_name = f"{table.db}.{table.name}" if table.db else table.name
            tables_found.append(table_name)

        print(f"Tables found in AST: {len(tables_found)}")
        for t in tables_found[:10]:
            print(f"  - {t}")

    except Exception as e:
        print(f"❌ SQLGlot WARN mode failed: {type(e).__name__}: {str(e)[:200]}")

    print()
    print("="*80)
    print()

    # Step 3: Test on full DDL
    print("STEP 3: SQLGLOT WARN MODE ON FULL DDL")
    print("-"*80)

    try:
        parsed_warn_full = parse_one(ddl, dialect='tsql', error_level=ErrorLevel.WARN)

        print("✅ SQLGlot WARN mode succeeded on full DDL")
        print(f"Parsed AST type: {type(parsed_warn_full)}")

        # Try to extract tables
        tables_found_full = []
        for table in parsed_warn_full.find_all(exp.Table):
            table_name = f"{table.db}.{table.name}" if table.db else table.name
            tables_found_full.append(table_name)

        print(f"Tables found in full AST: {len(tables_found_full)}")
        for t in tables_found_full[:10]:
            print(f"  - {t}")
        if len(tables_found_full) > 10:
            print(f"  ... and {len(tables_found_full) - 10} more")

    except Exception as e:
        print(f"❌ SQLGlot WARN mode failed on full DDL: {type(e).__name__}: {str(e)[:200]}")

    print()
    print("="*80)
    print()

    # Step 4: Check for problematic patterns
    print("STEP 4: PROBLEMATIC PATTERNS ANALYSIS")
    print("-"*80)

    problematic_patterns = {
        'EXEC with variables': r'EXEC\s+@\w+',
        'Dynamic SQL': r'EXEC\s*\(\s*@',
        'BEGIN TRY': r'\bBEGIN\s+TRY\b',
        'RAISERROR': r'\bRAISERROR\b',
        'SET NOCOUNT': r'\bSET\s+NOCOUNT\b',
        'DECLARE cursor': r'\bDECLARE\s+\w+\s+CURSOR\b',
        'Complex CASE': r'\bCASE\s+WHEN.*?WHEN.*?END',
        'Temp tables': r'#\w+',
        'Table variables': r'@\w+',
    }

    for pattern_name, pattern in problematic_patterns.items():
        matches = re.findall(pattern, ddl, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"⚠️  Found {len(matches)} instances of: {pattern_name}")
            if len(matches) <= 3:
                for m in matches:
                    print(f"     {m[:80]}")

    print()
    print("="*80)
    print()

    # Summary
    print("SUMMARY")
    print("-"*80)
    print(f"Expected targets: CONSUMPTION_ClinOpsFinance.FactLaborCostForEarnedValue_Post")
    print(f"Expected sources:")
    print(f"  - CONSUMPTION_POWERBI.FactLaborCostForEarnedValue")
    print(f"  - CONSUMPTION_ClinOpsFinance.CadenceBudget_LaborCost_PrimaContractUtilization_Junc")
    print()
    print(f"Regex found {len(from_tables)} FROM tables")
    print(f"Regex found {len(into_tables) + len(insert_tables) + len(update_tables)} target tables")
    print()

    # Check if expected tables are in regex results
    expected_sources = [
        ('CONSUMPTION_POWERBI', 'FactLaborCostForEarnedValue'),
        ('CONSUMPTION_ClinOpsFinance', 'CadenceBudget_LaborCost_PrimaContractUtilization_Junc')
    ]

    for schema, table in expected_sources:
        found_in_regex = any(s.upper() == schema.upper() and t.upper() == table.upper()
                            for s, t in from_tables)
        status = "✅" if found_in_regex else "❌"
        print(f"{status} {schema}.{table} in regex results: {found_in_regex}")

conn.close()
