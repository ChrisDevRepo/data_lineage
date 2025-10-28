#!/usr/bin/env python3
"""
Parser Regression Test Framework
==================================

Ensures parser changes improve scores without causing regressions.

Usage:
    # Capture baseline before making changes
    python tests/parser_regression_test.py --capture-baseline baselines/baseline_20251027.json

    # After parser changes, compare results
    python tests/parser_regression_test.py --compare baselines/baseline_20251027.json lineage_output/lineage_summary.json

    # Run full regression suite
    python tests/parser_regression_test.py --full-test

Author: Vibecoding
Date: 2025-10-28
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse


@dataclass
class ObjectMetrics:
    """Metrics for a single parsed object."""
    object_id: str
    object_name: str
    schema_name: str
    confidence: float
    inputs_count: int
    outputs_count: int
    inputs: List[str]
    outputs: List[str]


@dataclass
class RegressionResult:
    """Result of regression comparison."""
    passed: bool
    total_objects: int
    regressions: List[Dict]
    improvements: List[Dict]
    unchanged: List[Dict]
    baseline_avg_confidence: float
    current_avg_confidence: float
    baseline_high_confidence_count: int
    current_high_confidence_count: int


class ParserRegressionTest:
    """Test framework for parser regression detection."""

    HIGH_CONFIDENCE_THRESHOLD = 0.85
    REGRESSION_TOLERANCE = 0.01  # Allow 1% confidence drop (floating point errors)

    def __init__(self):
        self.baseline: Dict[str, ObjectMetrics] = {}
        self.current: Dict[str, ObjectMetrics] = {}

    def capture_baseline(self, frontend_lineage_path: Path, output_path: Path) -> None:
        """
        Capture current parser state as baseline.

        Args:
            frontend_lineage_path: Path to frontend_lineage.json
            output_path: Where to save baseline snapshot
        """
        print(f"\n{'='*70}")
        print("CAPTURING PARSER BASELINE")
        print(f"{'='*70}\n")

        # Load frontend lineage
        with open(frontend_lineage_path, 'r') as f:
            data = json.load(f)

        # Extract metrics for stored procedures only
        baseline_data = {}
        sp_count = 0

        for obj in data:
            if obj.get('object_type') == 'Stored Procedure':
                sp_count += 1
                object_id = obj['id']

                # Parse confidence from description
                desc = obj.get('description', 'Confidence: 0.00')
                confidence = float(desc.replace('Confidence: ', ''))

                baseline_data[object_id] = {
                    'object_id': object_id,
                    'object_name': obj['name'],
                    'schema_name': obj['schema'],
                    'confidence': confidence,
                    'inputs_count': len(obj.get('inputs', [])),
                    'outputs_count': len(obj.get('outputs', [])),
                    'inputs': obj.get('inputs', []),
                    'outputs': obj.get('outputs', [])
                }

        # Calculate statistics
        confidences = [obj['confidence'] for obj in baseline_data.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        high_conf_count = sum(1 for c in confidences if c >= self.HIGH_CONFIDENCE_THRESHOLD)

        # Create baseline snapshot
        snapshot = {
            'metadata': {
                'captured_at': datetime.now().isoformat(),
                'frontend_lineage_path': str(frontend_lineage_path),
                'total_stored_procedures': sp_count,
                'avg_confidence': round(avg_confidence, 3),
                'high_confidence_count': high_conf_count,
                'high_confidence_pct': round(100 * high_conf_count / sp_count, 1) if sp_count > 0 else 0
            },
            'objects': baseline_data
        }

        # Save baseline
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(snapshot, f, indent=2)

        print(f"✓ Baseline captured: {sp_count} stored procedures")
        print(f"  Average Confidence: {avg_confidence:.3f}")
        print(f"  High Confidence (≥{self.HIGH_CONFIDENCE_THRESHOLD}): {high_conf_count} ({100*high_conf_count/sp_count:.1f}%)")
        print(f"\n✓ Saved to: {output_path}\n")

    def load_baseline(self, baseline_path: Path) -> None:
        """Load baseline from JSON file."""
        with open(baseline_path, 'r') as f:
            data = json.load(f)

        for obj_id, obj_data in data['objects'].items():
            self.baseline[obj_id] = ObjectMetrics(**obj_data)

        print(f"\n✓ Loaded baseline: {len(self.baseline)} objects")
        print(f"  Captured: {data['metadata']['captured_at']}")
        print(f"  Average Confidence: {data['metadata']['avg_confidence']}")
        print(f"  High Confidence: {data['metadata']['high_confidence_count']} ({data['metadata']['high_confidence_pct']}%)")

    def load_current(self, frontend_lineage_path: Path) -> None:
        """Load current parser results."""
        with open(frontend_lineage_path, 'r') as f:
            data = json.load(f)

        for obj in data:
            if obj.get('object_type') == 'Stored Procedure':
                object_id = obj['id']

                # Parse confidence
                desc = obj.get('description', 'Confidence: 0.00')
                confidence = float(desc.replace('Confidence: ', ''))

                self.current[object_id] = ObjectMetrics(
                    object_id=object_id,
                    object_name=obj['name'],
                    schema_name=obj['schema'],
                    confidence=confidence,
                    inputs_count=len(obj.get('inputs', [])),
                    outputs_count=len(obj.get('outputs', [])),
                    inputs=obj.get('inputs', []),
                    outputs=obj.get('outputs', [])
                )

        print(f"✓ Loaded current results: {len(self.current)} objects\n")

    def compare(self) -> RegressionResult:
        """
        Compare current results against baseline.

        Returns:
            RegressionResult with detailed comparison
        """
        print(f"\n{'='*70}")
        print("REGRESSION TEST RESULTS")
        print(f"{'='*70}\n")

        regressions = []
        improvements = []
        unchanged = []

        # Compare each object
        for obj_id, baseline_obj in self.baseline.items():
            if obj_id not in self.current:
                print(f"⚠ WARNING: Object {baseline_obj.object_name} missing in current results")
                continue

            current_obj = self.current[obj_id]

            # Calculate confidence change
            conf_delta = current_obj.confidence - baseline_obj.confidence

            # Check for regression
            if conf_delta < -self.REGRESSION_TOLERANCE:
                # Confidence dropped significantly
                regressions.append({
                    'object_id': obj_id,
                    'object_name': baseline_obj.object_name,
                    'schema': baseline_obj.schema_name,
                    'baseline_confidence': baseline_obj.confidence,
                    'current_confidence': current_obj.confidence,
                    'delta': conf_delta,
                    'baseline_inputs': baseline_obj.inputs_count,
                    'current_inputs': current_obj.inputs_count,
                    'baseline_outputs': baseline_obj.outputs_count,
                    'current_outputs': current_obj.outputs_count
                })

            elif conf_delta > self.REGRESSION_TOLERANCE:
                # Confidence improved
                improvements.append({
                    'object_id': obj_id,
                    'object_name': baseline_obj.object_name,
                    'schema': baseline_obj.schema_name,
                    'baseline_confidence': baseline_obj.confidence,
                    'current_confidence': current_obj.confidence,
                    'delta': conf_delta,
                    'baseline_inputs': baseline_obj.inputs_count,
                    'current_inputs': current_obj.inputs_count,
                    'baseline_outputs': baseline_obj.outputs_count,
                    'current_outputs': current_obj.outputs_count
                })

            else:
                # No significant change
                unchanged.append({
                    'object_id': obj_id,
                    'object_name': baseline_obj.object_name,
                    'confidence': current_obj.confidence
                })

        # Calculate aggregate statistics
        baseline_confidences = [obj.confidence for obj in self.baseline.values()]
        current_confidences = [obj.confidence for obj in self.current.values()]

        baseline_avg = sum(baseline_confidences) / len(baseline_confidences) if baseline_confidences else 0.0
        current_avg = sum(current_confidences) / len(current_confidences) if current_confidences else 0.0

        baseline_high_conf = sum(1 for c in baseline_confidences if c >= self.HIGH_CONFIDENCE_THRESHOLD)
        current_high_conf = sum(1 for c in current_confidences if c >= self.HIGH_CONFIDENCE_THRESHOLD)

        # Determine if test passed
        passed = len(regressions) == 0

        result = RegressionResult(
            passed=passed,
            total_objects=len(self.baseline),
            regressions=regressions,
            improvements=improvements,
            unchanged=unchanged,
            baseline_avg_confidence=baseline_avg,
            current_avg_confidence=current_avg,
            baseline_high_confidence_count=baseline_high_conf,
            current_high_confidence_count=current_high_conf
        )

        return result

    def print_results(self, result: RegressionResult) -> None:
        """Print formatted test results."""

        # Overall statistics
        print(f"📊 Overall Statistics:")
        print(f"   Total Objects: {result.total_objects}")
        print(f"   Regressions: {len(result.regressions)} ❌" if result.regressions else f"   Regressions: 0 ✓")
        print(f"   Improvements: {len(result.improvements)} ✓")
        print(f"   Unchanged: {len(result.unchanged)}")

        print(f"\n📈 Confidence Metrics:")
        avg_delta = result.current_avg_confidence - result.baseline_avg_confidence
        avg_symbol = "📈" if avg_delta > 0 else "📉" if avg_delta < 0 else "➡"
        print(f"   Average: {result.baseline_avg_confidence:.3f} → {result.current_avg_confidence:.3f} ({avg_delta:+.3f}) {avg_symbol}")

        high_conf_delta = result.current_high_confidence_count - result.baseline_high_confidence_count
        high_conf_symbol = "📈" if high_conf_delta > 0 else "📉" if high_conf_delta < 0 else "➡"
        print(f"   High Confidence (≥{self.HIGH_CONFIDENCE_THRESHOLD}): {result.baseline_high_confidence_count} → {result.current_high_confidence_count} ({high_conf_delta:+d}) {high_conf_symbol}")

        # Regressions (failures)
        if result.regressions:
            print(f"\n❌ REGRESSIONS DETECTED ({len(result.regressions)}):")
            print(f"   {'Object Name':<45} {'Baseline':>10} {'Current':>10} {'Delta':>10}")
            print(f"   {'-'*75}")
            for reg in sorted(result.regressions, key=lambda x: x['delta']):
                print(f"   {reg['object_name']:<45} {reg['baseline_confidence']:>10.2f} {reg['current_confidence']:>10.2f} {reg['delta']:>10.2f}")

        # Improvements
        if result.improvements:
            print(f"\n✅ IMPROVEMENTS ({len(result.improvements)}):")
            print(f"   {'Object Name':<45} {'Baseline':>10} {'Current':>10} {'Delta':>10}")
            print(f"   {'-'*75}")
            for imp in sorted(result.improvements, key=lambda x: -x['delta'])[:10]:  # Top 10
                print(f"   {imp['object_name']:<45} {imp['baseline_confidence']:>10.2f} {imp['current_confidence']:>10.2f} {imp['delta']:>10.2f}")
            if len(result.improvements) > 10:
                print(f"   ... and {len(result.improvements) - 10} more")

        # Final verdict
        print(f"\n{'='*70}")
        if result.passed:
            print("✅ REGRESSION TEST PASSED")
            print("   No high-confidence objects degraded.")
            if result.improvements:
                print(f"   {len(result.improvements)} objects improved!")
        else:
            print("❌ REGRESSION TEST FAILED")
            print(f"   {len(result.regressions)} objects regressed.")
            print("   Review changes before committing.")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Parser Regression Test Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture baseline before changes
  python tests/parser_regression_test.py --capture-baseline baselines/baseline_20251027.json

  # Compare after changes
  python tests/parser_regression_test.py --compare baselines/baseline_20251027.json

  # Full regression test (capture + apply changes + compare)
  python tests/parser_regression_test.py --full-test
        """
    )

    parser.add_argument(
        '--capture-baseline',
        type=Path,
        help='Capture current parser state as baseline (provide output path)'
    )

    parser.add_argument(
        '--compare',
        type=Path,
        help='Compare current results against baseline (provide baseline path)'
    )

    parser.add_argument(
        '--frontend-lineage',
        type=Path,
        default=Path('lineage_output/frontend_lineage.json'),
        help='Path to frontend_lineage.json (default: lineage_output/frontend_lineage.json)'
    )

    args = parser.parse_args()

    tester = ParserRegressionTest()

    if args.capture_baseline:
        # Capture baseline mode
        tester.capture_baseline(args.frontend_lineage, args.capture_baseline)
        return 0

    elif args.compare:
        # Compare mode
        tester.load_baseline(args.compare)
        tester.load_current(args.frontend_lineage)
        result = tester.compare()
        tester.print_results(result)

        # Exit with error code if regressions detected
        return 0 if result.passed else 1

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
