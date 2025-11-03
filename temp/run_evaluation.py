#!/usr/bin/env python3
"""
Run parser evaluation against baseline.

Evaluates regex and SQLGlot parsing methods against expected dependencies
from the baseline snapshot.
"""

import duckdb
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set

# Add lineage_v3 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace
from lineage_v3.parsers.quality_aware_parser import QualityAwareParser


def calculate_metrics(found: Set[int], expected: Set[int]) -> Dict[str, float]:
    """Calculate precision, recall, F1 score."""
    if not found and not expected:
        # Both empty = perfect match
        return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0}

    if not found:
        # Found nothing, expected something
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

    if not expected:
        # Found something, expected nothing (all false positives)
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

    tp = len(found & expected)  # True positives
    fp = len(found - expected)  # False positives
    fn = len(expected - found)  # False negatives

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4)
    }


def run_evaluation(baseline_name: str, mode: str = "full"):
    """Run evaluation on baseline objects."""

    baseline_path = Path("evaluation_baselines") / f"{baseline_name}.duckdb"

    if not baseline_path.exists():
        print(f"❌ Error: Baseline '{baseline_name}' not found at {baseline_path}")
        sys.exit(1)

    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    report_path = Path("optimization_reports") / f"{run_id}.json"

    print(f"📊 Running evaluation: {run_id}")
    print(f"   Baseline: {baseline_name}")
    print(f"   Mode: {mode}")
    print()

    # Connect to baseline
    baseline_conn = duckdb.connect(str(baseline_path), read_only=True)

    # Create workspace (uses production lineage_workspace.duckdb)
    workspace = DuckDBWorkspace("lineage_workspace.duckdb")
    workspace.connect()  # Must connect before using
    parser = QualityAwareParser(workspace)

    # Load baseline objects
    print("📥 Loading baseline objects...")
    objects = baseline_conn.execute("""
        SELECT
            object_id,
            object_name,
            schema_name,
            object_type,
            ddl_text,
            expected_inputs,
            expected_outputs
        FROM baseline_objects
        ORDER BY object_id
    """).fetchall()

    print(f"   Found {len(objects)} objects")
    print()

    results = []
    regex_total = {'tp': 0, 'fp': 0, 'fn': 0}
    sqlglot_total = {'tp': 0, 'fp': 0, 'fn': 0}

    print("🔍 Evaluating objects...")
    for idx, obj in enumerate(objects, 1):
        object_id, object_name, schema_name, object_type, ddl_text, expected_inputs_json, expected_outputs_json = obj

        # Parse expected values
        expected_inputs = set(json.loads(expected_inputs_json) if expected_inputs_json else [])
        expected_outputs = set(json.loads(expected_outputs_json) if expected_outputs_json else [])

        # Run regex extraction
        regex_result = parser.extract_regex_dependencies(ddl_text)
        regex_inputs = set(parser._resolve_table_names(regex_result['sources_validated']))
        regex_outputs = set(parser._resolve_table_names(regex_result['targets_validated']))

        # Run SQLGlot extraction
        sqlglot_result = parser.extract_sqlglot_dependencies(ddl_text)
        sqlglot_inputs = set(parser._resolve_table_names(sqlglot_result['sources_validated']))
        sqlglot_outputs = set(parser._resolve_table_names(sqlglot_result['targets_validated']))

        # Calculate metrics
        regex_input_metrics = calculate_metrics(regex_inputs, expected_inputs)
        regex_output_metrics = calculate_metrics(regex_outputs, expected_outputs)
        regex_overall_f1 = (regex_input_metrics['f1'] + regex_output_metrics['f1']) / 2

        sqlglot_input_metrics = calculate_metrics(sqlglot_inputs, expected_inputs)
        sqlglot_output_metrics = calculate_metrics(sqlglot_outputs, expected_outputs)
        sqlglot_overall_f1 = (sqlglot_input_metrics['f1'] + sqlglot_output_metrics['f1']) / 2

        # Accumulate totals
        regex_total['tp'] += len(regex_inputs & expected_inputs) + len(regex_outputs & expected_outputs)
        regex_total['fp'] += len(regex_inputs - expected_inputs) + len(regex_outputs - expected_outputs)
        regex_total['fn'] += len(expected_inputs - regex_inputs) + len(expected_outputs - regex_outputs)

        sqlglot_total['tp'] += len(sqlglot_inputs & expected_inputs) + len(sqlglot_outputs & expected_outputs)
        sqlglot_total['fp'] += len(sqlglot_inputs - expected_inputs) + len(sqlglot_outputs - expected_outputs)
        sqlglot_total['fn'] += len(expected_inputs - sqlglot_inputs) + len(expected_outputs - sqlglot_outputs)

        result = {
            'object_id': object_id,
            'object_name': f"{schema_name}.{object_name}",
            'object_type': object_type,
            'expected_inputs': len(expected_inputs),
            'expected_outputs': len(expected_outputs),
            'regex': {
                'inputs_found': len(regex_inputs),
                'outputs_found': len(regex_outputs),
                'input_metrics': regex_input_metrics,
                'output_metrics': regex_output_metrics,
                'overall_f1': round(regex_overall_f1, 4)
            },
            'sqlglot': {
                'inputs_found': len(sqlglot_inputs),
                'outputs_found': len(sqlglot_outputs),
                'input_metrics': sqlglot_input_metrics,
                'output_metrics': sqlglot_output_metrics,
                'overall_f1': round(sqlglot_overall_f1, 4)
            }
        }

        results.append(result)

        if idx % 10 == 0:
            print(f"   Progress: {idx}/{len(objects)} ({100*idx/len(objects):.1f}%)")

    print(f"   Progress: {len(objects)}/{len(objects)} (100.0%)")
    print()

    # Calculate aggregate statistics
    regex_micro_precision = regex_total['tp'] / (regex_total['tp'] + regex_total['fp']) if (regex_total['tp'] + regex_total['fp']) > 0 else 0
    regex_micro_recall = regex_total['tp'] / (regex_total['tp'] + regex_total['fn']) if (regex_total['tp'] + regex_total['fn']) > 0 else 0
    regex_micro_f1 = 2 * regex_micro_precision * regex_micro_recall / (regex_micro_precision + regex_micro_recall) if (regex_micro_precision + regex_micro_recall) > 0 else 0

    sqlglot_micro_precision = sqlglot_total['tp'] / (sqlglot_total['tp'] + sqlglot_total['fp']) if (sqlglot_total['tp'] + sqlglot_total['fp']) > 0 else 0
    sqlglot_micro_recall = sqlglot_total['tp'] / (sqlglot_total['tp'] + sqlglot_total['fn']) if (sqlglot_total['tp'] + sqlglot_total['fn']) > 0 else 0
    sqlglot_micro_f1 = 2 * sqlglot_micro_precision * sqlglot_micro_recall / (sqlglot_micro_precision + sqlglot_micro_recall) if (sqlglot_micro_precision + sqlglot_micro_recall) > 0 else 0

    regex_macro_f1 = sum(r['regex']['overall_f1'] for r in results) / len(results) if results else 0
    sqlglot_macro_f1 = sum(r['sqlglot']['overall_f1'] for r in results) / len(results) if results else 0

    # Count high confidence objects (≥0.85)
    regex_high_conf = sum(1 for r in results if r['regex']['overall_f1'] >= 0.85)
    sqlglot_high_conf = sum(1 for r in results if r['sqlglot']['overall_f1'] >= 0.85)

    # Generate report
    report = {
        'run_id': run_id,
        'baseline_name': baseline_name,
        'mode': mode,
        'timestamp': datetime.now().isoformat(),
        'total_objects': len(objects),
        'summary': {
            'regex': {
                'micro_precision': round(regex_micro_precision, 4),
                'micro_recall': round(regex_micro_recall, 4),
                'micro_f1': round(regex_micro_f1, 4),
                'macro_f1': round(regex_macro_f1, 4),
                'high_confidence_count': regex_high_conf,
                'high_confidence_pct': round(100 * regex_high_conf / len(results), 2) if results else 0
            },
            'sqlglot': {
                'micro_precision': round(sqlglot_micro_precision, 4),
                'micro_recall': round(sqlglot_micro_recall, 4),
                'micro_f1': round(sqlglot_micro_f1, 4),
                'macro_f1': round(sqlglot_macro_f1, 4),
                'high_confidence_count': sqlglot_high_conf,
                'high_confidence_pct': round(100 * sqlglot_high_conf / len(results), 2) if results else 0
            }
        },
        'objects': results
    }

    # Save report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Create symlink to latest
    latest_path = Path("optimization_reports") / "latest.json"
    if latest_path.exists():
        latest_path.unlink()
    latest_path.symlink_to(report_path.name)

    # Display summary
    print("✅ Evaluation completed!")
    print()
    print("📈 Summary:")
    print()
    print("Regex Method:")
    print(f"  Micro F1: {report['summary']['regex']['micro_f1']}")
    print(f"  Macro F1: {report['summary']['regex']['macro_f1']}")
    print(f"  High Confidence (≥0.85): {regex_high_conf}/{len(results)} ({report['summary']['regex']['high_confidence_pct']}%)")
    print()
    print("SQLGlot Method:")
    print(f"  Micro F1: {report['summary']['sqlglot']['micro_f1']}")
    print(f"  Macro F1: {report['summary']['sqlglot']['macro_f1']}")
    print(f"  High Confidence (≥0.85): {sqlglot_high_conf}/{len(results)} ({report['summary']['sqlglot']['high_confidence_pct']}%)")
    print()
    print(f"📁 Report saved: {report_path}")
    print(f"   Latest: {latest_path}")

    baseline_conn.close()
    workspace.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_evaluation.py <baseline_name> [mode]")
        print("  mode: full (default) or incremental")
        sys.exit(1)

    baseline_name = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "full"
    run_evaluation(baseline_name, mode)
