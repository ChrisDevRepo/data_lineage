#!/usr/bin/env python3
"""
Confidence Score Baseline Testing System

Validates parser confidence scores against established baselines.

Usage:
    # Create baseline from current parser results
    python tests/confidence_baseline_test.py --create-baseline

    # Validate against baseline (regression testing)
    python tests/confidence_baseline_test.py --validate

Features:
    - Tracks confidence scores for all parsed objects
    - Detects regressions (confidence drops)
    - Identifies improvements (confidence increases)
    - Generates detailed comparison reports
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class ConfidenceBaselineTester:
    """Test confidence scores against baseline"""

    def __init__(self, baseline_file: Path = Path("evaluation/confidence_baseline.json")):
        self.baseline_file = baseline_file
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)

    def create_baseline(self, smoke_test_file: Path) -> bool:
        """Create baseline from smoke test results"""
        print(f"Creating baseline from {smoke_test_file}...")

        try:
            with open(smoke_test_file, 'r') as f:
                smoke_results = json.load(f)

            # Extract confidence scores by object_id
            baseline = {
                "created_at": datetime.now().isoformat(),
                "source_file": str(smoke_test_file),
                "total_objects": len(smoke_results),
                "objects": {}
            }

            for obj in smoke_results:
                obj_id = obj.get('object_id')
                if not obj_id:
                    continue

                baseline["objects"][str(obj_id)] = {
                    "name": obj.get('object_name', 'Unknown'),
                    "schema": obj.get('schema_name', 'Unknown'),
                    "confidence": obj.get('confidence', 0.0),
                    "parser_tables_count": obj.get('parser_tables_count', 0),
                    "expected_tables_count": obj.get('expected_tables_count', 0),
                    "primary_source": obj.get('primary_source', 'parser')
                }

            # Save baseline
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline, f, indent=2)

            print(f"✓ Baseline created: {self.baseline_file}")
            print(f"  - Objects: {baseline['total_objects']}")
            print(f"  - Created: {baseline['created_at']}")
            return True

        except Exception as e:
            print(f"✗ Failed to create baseline: {e}")
            return False

    def validate_against_baseline(self, current_results_file: Path) -> Tuple[bool, Dict]:
        """Validate current results against baseline"""
        print(f"\nValidating against baseline: {self.baseline_file}")

        if not self.baseline_file.exists():
            print(f"✗ Baseline not found. Create baseline first with --create-baseline")
            return False, {}

        try:
            # Load baseline
            with open(self.baseline_file, 'r') as f:
                baseline = json.load(f)

            # Load current results
            with open(current_results_file, 'r') as f:
                current = json.load(f)

            # Compare
            comparison = self._compare_results(baseline, current)

            # Print report
            self._print_comparison_report(comparison)

            # Determine if validation passed
            passed = (
                comparison['regressions_count'] == 0 and
                comparison['missing_count'] == 0
            )

            return passed, comparison

        except Exception as e:
            print(f"✗ Validation failed: {e}")
            return False, {}

    def _compare_results(self, baseline: Dict, current: List[Dict]) -> Dict:
        """Compare baseline with current results"""
        comparison = {
            "total_baseline": len(baseline["objects"]),
            "total_current": len(current),
            "regressions": [],
            "improvements": [],
            "unchanged": [],
            "missing": [],
            "new": []
        }

        # Convert current to dict
        current_map = {
            str(obj.get('object_id')): obj
            for obj in current
            if obj.get('object_id')
        }

        # Compare each baseline object
        for obj_id, baseline_obj in baseline["objects"].items():
            if obj_id not in current_map:
                comparison["missing"].append({
                    "object_id": obj_id,
                    "name": baseline_obj["name"],
                    "baseline_confidence": baseline_obj["confidence"]
                })
                continue

            current_obj = current_map[obj_id]
            baseline_conf = baseline_obj["confidence"]
            current_conf = current_obj.get("confidence", 0.0)

            if current_conf < baseline_conf:
                # Regression
                comparison["regressions"].append({
                    "object_id": obj_id,
                    "name": baseline_obj["name"],
                    "schema": baseline_obj["schema"],
                    "baseline_confidence": baseline_conf,
                    "current_confidence": current_conf,
                    "drop": baseline_conf - current_conf
                })
            elif current_conf > baseline_conf:
                # Improvement
                comparison["improvements"].append({
                    "object_id": obj_id,
                    "name": baseline_obj["name"],
                    "schema": baseline_obj["schema"],
                    "baseline_confidence": baseline_conf,
                    "current_confidence": current_conf,
                    "gain": current_conf - baseline_conf
                })
            else:
                # Unchanged
                comparison["unchanged"].append({
                    "object_id": obj_id,
                    "confidence": current_conf
                })

        # Find new objects
        for obj_id in current_map:
            if obj_id not in baseline["objects"]:
                obj = current_map[obj_id]
                comparison["new"].append({
                    "object_id": obj_id,
                    "name": obj.get("object_name", "Unknown"),
                    "confidence": obj.get("confidence", 0.0)
                })

        # Add counts
        comparison["regressions_count"] = len(comparison["regressions"])
        comparison["improvements_count"] = len(comparison["improvements"])
        comparison["unchanged_count"] = len(comparison["unchanged"])
        comparison["missing_count"] = len(comparison["missing"])
        comparison["new_count"] = len(comparison["new"])

        return comparison

    def _print_comparison_report(self, comparison: Dict):
        """Print detailed comparison report"""
        print("\n" + "="*60)
        print("CONFIDENCE SCORE VALIDATION REPORT")
        print("="*60)

        print(f"\nBaseline Objects: {comparison['total_baseline']}")
        print(f"Current Objects:  {comparison['total_current']}")

        print(f"\n📊 Summary:")
        print(f"  ✓ Unchanged:    {comparison['unchanged_count']}")
        print(f"  ↑ Improvements: {comparison['improvements_count']}")
        print(f"  ↓ Regressions:  {comparison['regressions_count']}")
        print(f"  ➕ New:          {comparison['new_count']}")
        print(f"  ➖ Missing:      {comparison['missing_count']}")

        # Show regressions (critical)
        if comparison['regressions_count'] > 0:
            print(f"\n⚠️  REGRESSIONS DETECTED ({comparison['regressions_count']}):")
            for reg in comparison['regressions'][:10]:  # Show top 10
                print(f"  - {reg['schema']}.{reg['name']}")
                print(f"    Baseline: {reg['baseline_confidence']:.0f}% → Current: {reg['current_confidence']:.0f}% (drop: {reg['drop']:.0f}%)")

        # Show improvements (positive)
        if comparison['improvements_count'] > 0:
            print(f"\n✨ IMPROVEMENTS ({comparison['improvements_count']}):")
            for imp in comparison['improvements'][:5]:  # Show top 5
                print(f"  - {imp['schema']}.{imp['name']}")
                print(f"    Baseline: {imp['baseline_confidence']:.0f}% → Current: {imp['current_confidence']:.0f}% (gain: {imp['gain']:.0f}%)")

        # Show missing (warning)
        if comparison['missing_count'] > 0:
            print(f"\n⚠️  MISSING OBJECTS ({comparison['missing_count']}):")
            for missing in comparison['missing'][:5]:
                print(f"  - {missing['name']} (ID: {missing['object_id']})")

        # Overall result
        print("\n" + "="*60)
        if comparison['regressions_count'] == 0 and comparison['missing_count'] == 0:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Test confidence scores against baseline")
    parser.add_argument('--create-baseline', action='store_true', help="Create baseline from smoke test results")
    parser.add_argument('--validate', action='store_true', help="Validate current results against baseline")
    parser.add_argument('--baseline-file', type=Path, default=Path("evaluation/confidence_baseline.json"),
                        help="Path to baseline file")
    parser.add_argument('--smoke-test-file', type=Path, default=Path("smoke_test_analysis.json"),
                        help="Path to smoke test results")
    args = parser.parse_args()

    tester = ConfidenceBaselineTester(baseline_file=args.baseline_file)

    if args.create_baseline:
        success = tester.create_baseline(args.smoke_test_file)
        sys.exit(0 if success else 1)
    elif args.validate:
        success, _ = tester.validate_against_baseline(args.smoke_test_file)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
