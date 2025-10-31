"""
Extract Real Test Cases from Latest Lineage JSON
=================================================

Purpose: Analyze latest_frontend_lineage.json to find stored procedures
with varying confidence levels for AI testing comparison.

Usage:
    python lineage_v3/ai_analyzer/extract_test_cases_from_json.py
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Input/output paths
LINEAGE_JSON = "data/latest_frontend_lineage.json"
OUTPUT_FILE = "lineage_v3/ai_analyzer/test_dataset.json"

def load_lineage_data():
    """Load and parse the latest frontend lineage JSON."""
    print("=" * 80)
    print("LOADING LINEAGE DATA")
    print("=" * 80)

    with open(LINEAGE_JSON, 'r') as f:
        data = json.load(f)

    print(f"✅ Loaded {len(data)} objects from {LINEAGE_JSON}\n")
    return data


def analyze_confidence_distribution(data):
    """Analyze confidence score distribution across stored procedures."""
    print("=" * 80)
    print("CONFIDENCE DISTRIBUTION ANALYSIS")
    print("=" * 80)

    procedures = [obj for obj in data if obj.get('object_type') == 'Stored Procedure']

    # Parse confidence from description field
    confidence_scores = []
    for proc in procedures:
        desc = proc.get('description', '')
        # Format: "Confidence: 0.85" or similar
        match = re.search(r'Confidence:\s*([\d.]+)', desc)
        if match:
            confidence = float(match.group(1))
            confidence_scores.append((proc, confidence))

    # Sort by confidence
    confidence_scores.sort(key=lambda x: x[1])

    # Distribution buckets
    low = [x for x in confidence_scores if x[1] < 0.85]
    high = [x for x in confidence_scores if x[1] >= 0.85]

    print(f"Total Stored Procedures: {len(procedures)}")
    print(f"  Low Confidence (<0.85): {len(low)}")
    print(f"  High Confidence (≥0.85): {len(high)}")
    print()

    return confidence_scores, low, high


def extract_ambiguous_patterns(proc, confidence):
    """
    Identify potentially ambiguous table references in SQL.
    Look for table names without schema qualifiers.
    """
    ddl = proc.get('ddl_text', '')
    if not ddl:
        return []

    # Find unqualified table names (no schema prefix)
    # Pattern: FROM/JOIN <table_name> (without schema)
    # Avoid: FROM schema.table_name
    pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b(?!\s*\.)'

    matches = re.findall(pattern, ddl, re.IGNORECASE)

    # Filter out common keywords
    keywords = {'SELECT', 'WHERE', 'ORDER', 'GROUP', 'HAVING', 'UNION', 'EXCEPT', 'INTERSECT'}
    ambiguous = [m for m in matches if m.upper() not in keywords]

    return list(set(ambiguous))  # Unique only


def create_test_cases(confidence_scores, low, high, all_objects):
    """Create structured test cases from extracted data."""
    print("=" * 80)
    print("CREATING TEST CASES")
    print("=" * 80)

    # Get all table names for candidate matching
    tables = [obj for obj in all_objects if obj.get('object_type') == 'Table']
    table_map = {}  # Map base name to full schema.table
    for table in tables:
        base_name = table['name']
        schema = table['schema']
        full_name = f"{schema}.{base_name}"
        if base_name not in table_map:
            table_map[base_name] = []
        table_map[base_name].append(full_name)

    # Extract low-confidence cases
    low_cases = []
    print(f"\nExtracting {min(10, len(low))} low-confidence cases...")
    for proc, conf in low[:10]:
        ambiguous = extract_ambiguous_patterns(proc, conf)

        # Find candidates for each ambiguous reference
        candidates_map = {}
        for amb in ambiguous:
            candidates = table_map.get(amb, [])
            if len(candidates) > 1:  # Only if truly ambiguous
                candidates_map[amb] = candidates

        if candidates_map:  # Only include if we found ambiguities
            low_cases.append({
                "object_id": proc['id'],
                "schema": proc['schema'],
                "name": proc['name'],
                "confidence": conf,
                "ddl_snippet": proc.get('ddl_text', '')[:800] + "..." if len(proc.get('ddl_text', '')) > 800 else proc.get('ddl_text', ''),
                "ambiguous_references": candidates_map,
                "inputs": proc.get('inputs', []),
                "outputs": proc.get('outputs', [])
            })

    print(f"  Found {len(low_cases)} with ambiguous references")

    # Extract high-confidence cases (for comparison)
    high_cases = []
    print(f"\nExtracting {min(5, len(high))} high-confidence cases...")
    for proc, conf in high[-5:]:  # Take highest confidence
        ambiguous = extract_ambiguous_patterns(proc, conf)

        candidates_map = {}
        for amb in ambiguous:
            candidates = table_map.get(amb, [])
            if len(candidates) > 1:
                candidates_map[amb] = candidates

        if candidates_map:
            high_cases.append({
                "object_id": proc['id'],
                "schema": proc['schema'],
                "name": proc['name'],
                "confidence": conf,
                "ddl_snippet": proc.get('ddl_text', '')[:800] + "..." if len(proc.get('ddl_text', '')) > 800 else proc.get('ddl_text', ''),
                "ambiguous_references": candidates_map,
                "inputs": proc.get('inputs', []),
                "outputs": proc.get('outputs', [])
            })

    print(f"  Found {len(high_cases)} with ambiguous references")

    return low_cases, high_cases


def save_test_dataset(low_cases, high_cases):
    """Save extracted test cases to JSON."""
    dataset = {
        "metadata": {
            "source": LINEAGE_JSON,
            "generated_at": "2025-10-31",
            "total_low_confidence": len(low_cases),
            "total_high_confidence": len(high_cases),
            "description": "Real production stored procedures for AI disambiguation testing"
        },
        "low_confidence_cases": low_cases,
        "high_confidence_cases": high_cases
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(dataset, f, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ Test dataset saved to: {OUTPUT_FILE}")
    print("=" * 80)
    print(f"  Low-confidence cases: {len(low_cases)}")
    print(f"  High-confidence cases: {len(high_cases)}")
    print("\n📋 Each case includes:")
    print("  - SP name, schema, confidence score")
    print("  - DDL snippet (first 800 chars)")
    print("  - Ambiguous table references with candidates")
    print("  - Actual inputs/outputs from parser")


def main():
    """Extract test cases from latest lineage JSON."""
    print("\n🔍 EXTRACTING TEST CASES FROM PRODUCTION LINEAGE DATA\n")

    # Load data
    data = load_lineage_data()

    # Analyze confidence distribution
    confidence_scores, low, high = analyze_confidence_distribution(data)

    # Create test cases
    low_cases, high_cases = create_test_cases(confidence_scores, low, high, data)

    # Save dataset
    save_test_dataset(low_cases, high_cases)

    print("\n📋 NEXT STEPS:")
    print("1. Review test_dataset.json")
    print("2. Run enhanced AI test: python3 lineage_v3/ai_analyzer/test_azure_openai_phase2.py")
    print("3. Compare AI disambiguation vs parser confidence")


if __name__ == "__main__":
    main()
