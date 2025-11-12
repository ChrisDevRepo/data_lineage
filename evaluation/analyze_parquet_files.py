#!/usr/bin/env python3
"""
Analyze Parquet Files in temp/ directory
=========================================

Goal: Understand what data we have, especially query logs
"""

import duckdb
import pandas as pd
from pathlib import Path

conn = duckdb.connect(':memory:')

print("=" * 80)
print("PARQUET FILES ANALYSIS")
print("=" * 80)

parquet_files = list(Path('temp').glob('*.parquet'))
print(f"\nFound {len(parquet_files)} parquet files\n")

for i, pf in enumerate(parquet_files, 1):
    print(f"\n{'='*80}")
    print(f"File {i}: {pf.name}")
    print(f"Size: {pf.stat().st_size / 1024:.1f} KB")
    print(f"{'='*80}")

    # Load first row to inspect schema
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()

    print(f"\nColumns ({len(df.columns)}):")
    for col in df.columns:
        print(f"  - {col}")

    # Count total rows
    count = conn.execute(f"SELECT COUNT(*) as cnt FROM '{pf}'").fetchone()[0]
    print(f"\nTotal rows: {count:,}")

    # Show sample data
    print("\nSample row:")
    for col, val in df.iloc[0].items():
        if isinstance(val, str):
            display_val = val[:100] + "..." if len(val) > 100 else val
        else:
            display_val = val
        print(f"  {col}: {display_val}")

    # Identify file type
    if 'definition' in df.columns and 'referencing_object_id' not in df.columns:
        print("\n📄 FILE TYPE: Stored Procedure Definitions")
    elif 'referencing_object_id' in df.columns and 'referenced_object_id' in df.columns:
        print("\n🔗 FILE TYPE: Object Dependencies/Lineage")
    elif 'object_id' in df.columns and 'object_type' in df.columns:
        print("\n📊 FILE TYPE: Object Catalog (Tables, SPs, Views)")
    elif 'query_text' in df.columns or 'statement' in df.columns or 'sql_text' in df.columns:
        print("\n🔍 FILE TYPE: Query Logs")
        # Analyze query logs more deeply
        analyze_query_logs(pf, conn)
    else:
        print("\n❓ FILE TYPE: Unknown")


def analyze_query_logs(parquet_file, conn):
    """Analyze query log parquet file"""
    print("\n" + "="*80)
    print("QUERY LOG ANALYSIS")
    print("="*80)

    df = conn.execute(f"SELECT * FROM '{parquet_file}'").fetchdf()

    # Find query text column
    query_col = None
    for col in ['query_text', 'statement', 'sql_text', 'command_text']:
        if col in df.columns:
            query_col = col
            break

    if not query_col:
        print("⚠️  No query text column found")
        return

    print(f"\nQuery text column: '{query_col}'")
    print(f"Total queries: {len(df):,}")

    # Analyze query types
    print("\n--- Query Type Distribution ---")

    def classify_query(sql):
        if pd.isna(sql):
            return 'NULL'
        sql_upper = str(sql).upper().strip()
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('EXEC'):
            return 'EXEC'
        elif sql_upper.startswith('CREATE'):
            return 'CREATE'
        elif sql_upper.startswith('ALTER'):
            return 'ALTER'
        elif sql_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'

    df['query_type'] = df[query_col].apply(classify_query)
    print(df['query_type'].value_counts())

    # Sample queries
    print("\n--- Sample Queries (first 3) ---")
    for i, query in enumerate(df[query_col].head(3), 1):
        print(f"\n{i}. {str(query)[:200]}...")

    # Check for referenced objects
    print("\n--- Referenced Objects Analysis ---")

    # Try to extract table names from queries
    import re
    table_pattern = r'\b(?:FROM|JOIN|INTO|UPDATE)\s+(\[?\w+\]?\.\[?\w+\]?)'

    all_tables = set()
    for query in df[query_col].dropna():
        matches = re.findall(table_pattern, str(query), re.IGNORECASE)
        all_tables.update(matches)

    print(f"Unique table references found: {len(all_tables)}")
    if all_tables:
        print("\nSample tables:")
        for table in list(all_tables)[:10]:
            print(f"  - {table}")

    # Value assessment
    print("\n" + "="*80)
    print("VALUE ASSESSMENT FOR LINEAGE")
    print("="*80)

    print(f"""
Query logs can provide:
1. ✅ Actual runtime lineage (what was actually executed)
2. ✅ Dynamic SQL lineage (sp_executesql captured)
3. ✅ Ad-hoc query patterns
4. ⚠️  May have parameter placeholders (@param)
5. ⚠️  Need to deduplicate (same query executed 1000s of times)

For our use case (SP-based lineage):
- Current approach: Static analysis of SP definitions (100% coverage, 743 tables)
- Query logs add: Runtime validation, dynamic SQL capture
- Trade-off: Complexity vs. completeness

Recommendation:
- CURRENT: Static analysis is sufficient for SP definitions
- FUTURE: Query logs valuable for:
  * Validating static analysis
  * Capturing dynamic SQL (sp_executesql)
  * Identifying frequently used vs unused lineage paths
  * Ad-hoc queries not in stored procedures
""")


# Run analysis
print("\nStarting parquet file analysis...\n")
