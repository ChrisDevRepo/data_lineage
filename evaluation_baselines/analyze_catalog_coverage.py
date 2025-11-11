#!/usr/bin/env python3
"""
Catalog Coverage Analysis
==========================

Analyzes:
1. How many parsed table references exist in our catalog
2. How many parsed table references DON'T exist in catalog
3. Which schemas are referenced but not in catalog
4. Examples of missing tables by schema
"""

import duckdb
import pandas as pd
from pathlib import Path
import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel
import sys
sys.path.append('/home/user/sandbox')

from lineage_v3.parsers.sql_cleaning_rules import RuleEngine

# Initialize
conn = duckdb.connect(':memory:')
engine_17 = RuleEngine()

# Load parquet files
for pf in Path('temp').glob('*.parquet'):
    df = conn.execute(f"SELECT * FROM '{pf}' LIMIT 1").fetchdf()
    if 'definition' in df.columns and 'referencing_object_id' not in df.columns:
        defs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()
    elif {'object_id', 'schema_name', 'object_name', 'object_type'}.issubset(set(df.columns)):
        objs_df = conn.execute(f"SELECT * FROM '{pf}'").fetchdf()

# Merge and filter SPs
defs_for_merge = defs_df[['object_id', 'definition']]
merged = defs_for_merge.merge(objs_df[['object_id', 'object_type', 'schema_name', 'object_name']], on='object_id')
sps = merged[merged['object_type'] == 'Stored Procedure']

print(f"Analyzing catalog coverage for {len(sps)} stored procedures...")
print("=" * 80)

# Create catalog sets
catalog_full_names = set(objs_df.apply(lambda r: f"{r['schema_name'].lower()}.{r['object_name'].lower()}", axis=1))
catalog_schemas = set(objs_df['schema_name'].str.lower().unique())

print(f"\nCatalog Statistics:")
print(f"  Total objects in catalog: {len(objs_df)}")
print(f"  Unique schemas in catalog: {len(catalog_schemas)}")
print(f"  Schemas: {', '.join(sorted(catalog_schemas))}")

def extract_unique_tables(parsed_statements):
    """Extract UNIQUE table references with schema"""
    sources = set()
    targets = set()

    if not parsed_statements:
        return sources, targets

    for stmt in parsed_statements:
        if type(stmt).__name__ == 'Command':
            continue

        if isinstance(stmt, (exp.Insert, exp.Update, exp.Delete, exp.Merge)):
            table = stmt.find(exp.Table)
            if table and table.db:
                full_name = f"{table.db.lower()}.{table.name.lower()}"
                targets.add(full_name)

        for table in stmt.find_all(exp.Table):
            if table.db:
                full_name = f"{table.db.lower()}.{table.name.lower()}"
                sources.add(full_name)

    sources = sources - targets
    return sources, targets


def parse_with_best_effort(ddl):
    """Try WARN-only and WARN+cleaning, return best"""

    # Tier 1: WARN-only
    try:
        parsed_t1 = sqlglot.parse(ddl, dialect='tsql', error_level=ErrorLevel.WARN)
        sources_t1, targets_t1 = extract_unique_tables(parsed_t1)
        tables_t1 = sources_t1.union(targets_t1)
    except:
        tables_t1 = set()

    # Tier 2: WARN + 17 rules
    try:
        cleaned = engine_17.apply_all(ddl)
        parsed_t2 = sqlglot.parse(cleaned, dialect='tsql', error_level=ErrorLevel.WARN)
        sources_t2, targets_t2 = extract_unique_tables(parsed_t2)
        tables_t2 = sources_t2.union(targets_t2)
    except:
        tables_t2 = set()

    # Return whichever found more
    if len(tables_t2) > len(tables_t1):
        return tables_t2, 'cleaned'
    else:
        return tables_t1, 'warn'


# Parse all SPs and collect all table references
all_parsed_tables = set()
all_parsed_schemas = set()
sp_count = 0

for idx, row in sps.iterrows():
    ddl = row['definition']
    tables, method = parse_with_best_effort(ddl)

    all_parsed_tables.update(tables)

    # Extract schemas from parsed tables
    for table in tables:
        if '.' in table:
            schema = table.split('.')[0]
            all_parsed_schemas.add(schema)

    sp_count += 1
    if sp_count % 50 == 0:
        print(f"  Processed {sp_count}/{len(sps)} SPs...")

print(f"\n" + "=" * 80)
print("CATALOG COVERAGE ANALYSIS")
print("=" * 80)

# Find tables IN catalog vs NOT IN catalog
tables_in_catalog = all_parsed_tables & catalog_full_names
tables_not_in_catalog = all_parsed_tables - catalog_full_names

print(f"\nParsed Table References:")
print(f"  Total unique tables parsed: {len(all_parsed_tables)}")
print(f"  Tables IN catalog: {len(tables_in_catalog)} ({len(tables_in_catalog)/len(all_parsed_tables)*100:.1f}%)")
print(f"  Tables NOT in catalog: {len(tables_not_in_catalog)} ({len(tables_not_in_catalog)/len(all_parsed_tables)*100:.1f}%)")

# Schema analysis
schemas_in_catalog = all_parsed_schemas & catalog_schemas
schemas_not_in_catalog = all_parsed_schemas - catalog_schemas

print(f"\nSchema Coverage:")
print(f"  Total schemas referenced: {len(all_parsed_schemas)}")
print(f"  Schemas IN catalog: {len(schemas_in_catalog)} ({len(schemas_in_catalog)/len(all_parsed_schemas)*100:.1f}%)")
print(f"  Schemas NOT in catalog: {len(schemas_not_in_catalog)} ({len(schemas_not_in_catalog)/len(all_parsed_schemas)*100:.1f}%)")

if schemas_not_in_catalog:
    print(f"\n  Missing schemas: {', '.join(sorted(schemas_not_in_catalog))}")

# Break down missing tables by schema
print(f"\nMissing Tables by Schema:")
print("-" * 80)

missing_by_schema = {}
for table in tables_not_in_catalog:
    if '.' in table:
        schema = table.split('.')[0]
        if schema not in missing_by_schema:
            missing_by_schema[schema] = []
        missing_by_schema[schema].append(table)

for schema in sorted(missing_by_schema.keys()):
    tables = missing_by_schema[schema]
    in_catalog = "✅ YES" if schema in catalog_schemas else "❌ NO"
    print(f"\n  Schema: {schema} (In catalog: {in_catalog})")
    print(f"  Missing tables: {len(tables)}")
    print(f"  Examples:")
    for table in sorted(tables)[:10]:  # Show first 10
        print(f"    - {table}")
    if len(tables) > 10:
        print(f"    ... and {len(tables) - 10} more")

# Potential reasons for missing tables
print(f"\n" + "=" * 80)
print("POTENTIAL REASONS FOR MISSING TABLES")
print("=" * 80)

print(f"""
1. **Temporary Tables (#temp)**
   - Parsed as regular tables but not in catalog
   - Example: #TempOrders → tempdb..#TempOrders

2. **Cross-Database References**
   - SPs reference tables in other databases not in catalog
   - Example: ExternalDB.dbo.Orders

3. **System Tables**
   - References to system views/tables (sys.*, INFORMATION_SCHEMA.*)
   - Filtered out of catalog but may appear in parsed results

4. **Schema Filtering**
   - Catalog may only include specific schemas
   - Missing schemas: {', '.join(sorted(schemas_not_in_catalog)) if schemas_not_in_catalog else 'None'}

5. **Parsing Errors**
   - Incorrect table names extracted due to SQL complexity
   - Example: Variable names mistaken for table names

6. **Dynamic Tables**
   - Tables referenced in dynamic SQL that don't exist yet
   - Or tables that were dropped but SP not updated
""")

# Impact on confidence scoring
print(f"\n" + "=" * 80)
print("IMPACT ON LINEAGE CONFIDENCE")
print("=" * 80)

coverage_pct = (len(tables_in_catalog) / len(all_parsed_tables) * 100) if all_parsed_tables else 0

print(f"""
Current catalog coverage: {coverage_pct:.1f}%

Impact on confidence scoring:
- Tables IN catalog → Can validate existence → Higher confidence
- Tables NOT in catalog → Cannot validate → May be excluded from lineage

Recommendation:
- If missing schemas are important → Add them to DMV query
- If temp tables expected → Mark as low-confidence but include
- If cross-database refs expected → Document as known limitation
""")

# Save detailed results
results = {
    'summary': {
        'total_parsed_tables': len(all_parsed_tables),
        'tables_in_catalog': len(tables_in_catalog),
        'tables_not_in_catalog': len(tables_not_in_catalog),
        'coverage_pct': coverage_pct,
        'schemas_in_catalog': sorted(list(schemas_in_catalog)),
        'schemas_not_in_catalog': sorted(list(schemas_not_in_catalog))
    },
    'missing_tables': {schema: tables for schema, tables in missing_by_schema.items()},
    'tables_in_catalog': sorted(list(tables_in_catalog)),
    'tables_not_in_catalog': sorted(list(tables_not_in_catalog))
}

import json
with open('evaluation_baselines/catalog_coverage_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Detailed results saved to evaluation_baselines/catalog_coverage_analysis.json")
print("=" * 80)
