"""
Extract Real Production Test Cases
===================================

Combines confidence scores from lineage JSON with DDL from parquet files
to create comprehensive test cases for AI disambiguation testing.

Usage:
    python lineage_v3/ai_analyzer/extract_real_test_cases.py
"""

import json
import pandas as pd
import re
from pathlib import Path

# Input paths
LINEAGE_JSON = "data/latest_frontend_lineage.json"
DEFINITIONS_PARQUET = "parquet_snapshots/part-00000-bd25fa2d-0094-4cf8-a48f-1868715121f7-c000.snappy.parquet"
OBJECTS_PARQUET = "parquet_snapshots/part-00000-fc67bf4b-3b81-4489-ab91-13ea53c21a1d-c000.snappy.parquet"
OUTPUT_FILE = "lineage_v3/ai_analyzer/test_dataset.json"


def load_data():
    """Load lineage JSON and parquet files."""
    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)

    # Load lineage JSON for confidence scores
    with open(LINEAGE_JSON, 'r') as f:
        lineage = json.load(f)
    print(f"✅ Loaded {len(lineage)} objects from lineage JSON")

    # Load definitions parquet for DDL
    definitions = pd.read_parquet(DEFINITIONS_PARQUET)
    print(f"✅ Loaded {len(definitions)} definitions from parquet")

    # Load objects parquet for metadata
    objects_df = pd.read_parquet(OBJECTS_PARQUET)
    print(f"✅ Loaded {len(objects_df)} objects from parquet\n")

    return lineage, definitions, objects_df


def extract_confidence_from_lineage(lineage):
    """Extract confidence scores for stored procedures."""
    sp_confidence = {}

    for obj in lineage:
        if obj.get('object_type') == 'Stored Procedure':
            obj_id = obj['id']
            desc = obj.get('description', '')

            # Parse confidence from description
            match = re.search(r'Confidence:\s*([\d.]+)', desc)
            if match:
                confidence = float(match.group(1))
                sp_confidence[obj_id] = {
                    'schema': obj['schema'],
                    'name': obj['name'],
                    'confidence': confidence,
                    'inputs': obj.get('inputs', []),
                    'outputs': obj.get('outputs', [])
                }

    return sp_confidence


def find_ambiguous_references_in_ddl(ddl, all_tables):
    """
    Find unqualified table references in DDL.
    Returns list of (reference, candidates) tuples.
    """
    if not ddl or pd.isna(ddl):
        return []

    # Find FROM/JOIN clauses with unqualified table names
    # Pattern: FROM/JOIN <table> (without schema prefix)
    pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:WITH|WHERE|ON|INNER|LEFT|RIGHT|OUTER|GROUP|ORDER|$|\))'

    matches = re.findall(pattern, ddl, re.IGNORECASE)

    # Build table name index
    table_index = {}
    for schema, table in all_tables:
        if table not in table_index:
            table_index[table] = []
        table_index[table].append(f"{schema}.{table}")

    # Find ambiguous references (multiple candidates)
    ambiguous = []
    for ref in set(matches):
        ref_upper = ref.upper()
        # Skip SQL keywords
        if ref_upper in {'SELECT', 'WHERE', 'ORDER', 'GROUP', 'HAVING', 'UNION', 'VALUES', 'NOLOCK'}:
            continue

        candidates = table_index.get(ref, [])
        if len(candidates) > 1:  # Truly ambiguous
            ambiguous.append((ref, candidates))

    return ambiguous


def create_test_cases(sp_confidence, definitions, objects_df):
    """Create structured test cases with real DDL."""
    print("=" * 80)
    print("CREATING TEST CASES")
    print("=" * 80)

    # Get all tables for candidate matching
    tables_df = objects_df[objects_df['object_type'] == 'Table']
    all_tables = list(zip(tables_df['schema_name'], tables_df['object_name']))
    print(f"Found {len(all_tables)} tables for disambiguation candidates\n")

    # Merge definitions with confidence scores
    definitions_with_conf = []
    for _, row in definitions.iterrows():
        obj_id_str = str(row['object_id'])
        if obj_id_str in sp_confidence:
            conf_data = sp_confidence[obj_id_str]
            definitions_with_conf.append({
                'object_id': obj_id_str,
                'schema': conf_data['schema'],
                'name': conf_data['name'],
                'confidence': conf_data['confidence'],
                'ddl': row['definition'],
                'inputs': conf_data['inputs'],
                'outputs': conf_data['outputs']
            })

    # Sort by confidence
    definitions_with_conf.sort(key=lambda x: x['confidence'])

    # Extract LOW confidence cases (<0.85)
    low_confidence = [x for x in definitions_with_conf if x['confidence'] < 0.85]
    print(f"Low-confidence SPs (<0.85): {len(low_confidence)}")

    low_cases = []
    for sp in low_confidence[:15]:  # Take up to 15
        ambiguous = find_ambiguous_references_in_ddl(sp['ddl'], all_tables)

        if ambiguous:  # Only include if we found ambiguous refs
            ambiguous_map = {ref: candidates for ref, candidates in ambiguous}

            low_cases.append({
                "object_id": sp['object_id'],
                "schema": sp['schema'],
                "name": sp['name'],
                "confidence": sp['confidence'],
                "ddl": sp['ddl'][:1500] + "\n..." if len(sp['ddl']) > 1500 else sp['ddl'],
                "ambiguous_references": ambiguous_map,
                "parser_inputs": sp['inputs'],
                "parser_outputs": sp['outputs']
            })

    print(f"  ✅ Extracted {len(low_cases)} low-confidence cases with ambiguous refs")

    # Extract HIGH confidence cases (≥0.95 for comparison)
    high_confidence = [x for x in definitions_with_conf if x['confidence'] >= 0.95]
    print(f"\nHigh-confidence SPs (≥0.95): {len(high_confidence)}")

    high_cases = []
    for sp in high_confidence[:10]:  # Take up to 10
        ambiguous = find_ambiguous_references_in_ddl(sp['ddl'], all_tables)

        if ambiguous:
            ambiguous_map = {ref: candidates for ref, candidates in ambiguous}

            high_cases.append({
                "object_id": sp['object_id'],
                "schema": sp['schema'],
                "name": sp['name'],
                "confidence": sp['confidence'],
                "ddl": sp['ddl'][:1500] + "\n..." if len(sp['ddl']) > 1500 else sp['ddl'],
                "ambiguous_references": ambiguous_map,
                "parser_inputs": sp['inputs'],
                "parser_outputs": sp['outputs']
            })

    print(f"  ✅ Extracted {len(high_cases)} high-confidence cases with ambiguous refs")

    return low_cases, high_cases


def save_test_dataset(low_cases, high_cases):
    """Save test dataset to JSON."""
    dataset = {
        "metadata": {
            "generated_at": "2025-10-31",
            "source_lineage": LINEAGE_JSON,
            "source_definitions": DEFINITIONS_PARQUET,
            "total_low_confidence": len(low_cases),
            "total_high_confidence": len(high_cases),
            "description": "Real production SPs with confidence scores and ambiguous table references"
        },
        "low_confidence_cases": low_cases,
        "high_confidence_cases": high_cases
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(dataset, f, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ TEST DATASET SAVED: {OUTPUT_FILE}")
    print("=" * 80)
    print(f"Low-confidence cases: {len(low_cases)}")
    print(f"High-confidence cases: {len(high_cases)}")
    print("\n📋 Each case includes:")
    print("  - Stored procedure name, schema, object_id")
    print("  - Parser confidence score")
    print("  - DDL (first 1500 chars)")
    print("  - Ambiguous table references with candidates")
    print("  - Parser's actual inputs/outputs for comparison")


def main():
    """Extract real production test cases."""
    print("\n🔍 EXTRACTING REAL PRODUCTION TEST CASES FOR AI TESTING\n")

    # Load data
    lineage, definitions, objects_df = load_data()

    # Extract confidence scores
    sp_confidence = extract_confidence_from_lineage(lineage)
    print(f"Extracted confidence for {len(sp_confidence)} stored procedures\n")

    # Create test cases
    low_cases, high_cases = create_test_cases(sp_confidence, definitions, objects_df)

    # Save dataset
    save_test_dataset(low_cases, high_cases)

    print("\n📋 NEXT STEPS:")
    print("1. Review test_dataset.json for extracted cases")
    print("2. Run Phase 2 AI tests: python3 lineage_v3/ai_analyzer/test_azure_openai_phase2.py")
    print("3. Compare AI disambiguation vs parser confidence")


if __name__ == "__main__":
    main()
