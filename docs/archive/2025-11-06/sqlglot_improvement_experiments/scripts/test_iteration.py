#!/usr/bin/env python3
"""Test current iteration and report results."""

import sys
from pathlib import Path

# Add parent directory to path to import lineage modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lineage_v3.services.lineage_workspace_service import LineageWorkspaceService


def test_iteration(iteration_name: str):
    """Test current iteration and report results."""

    print(f"\nTesting Iteration: {iteration_name}")
    print("=" * 60)

    # Initialize workspace
    workspace = LineageWorkspaceService()

    # Get all SPs from workspace
    try:
        sps = workspace.get_all_objects(object_type='Stored Procedure')
    except Exception as e:
        print(f"❌ Error getting SPs from workspace: {e}")
        print("\nMake sure you've run a full parse first:")
        print("  cd /home/chris/sandbox")
        print("  python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh")
        return 0

    if not sps:
        print("❌ No stored procedures found in workspace")
        print("\nMake sure you've run a full parse first:")
        print("  cd /home/chris/sandbox")
        print("  python lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh")
        return 0

    # Count confidence levels
    high_conf = 0
    medium_conf = 0
    low_conf = 0

    for sp in sps:
        conf = sp.get('confidence', 0.5)
        if conf >= 0.85:
            high_conf += 1
        elif conf >= 0.75:
            medium_conf += 1
        else:
            low_conf += 1

    total = len(sps)

    # Print results
    print(f"\nResults:")
    print(f"  High Confidence (≥0.85):     {high_conf:3d}/{total} ({high_conf/total*100:5.1f}%)")
    print(f"  Medium Confidence (0.75-0.84): {medium_conf:3d}/{total} ({medium_conf/total*100:5.1f}%)")
    print(f"  Low Confidence (<0.75):      {low_conf:3d}/{total} ({low_conf/total*100:5.1f}%)")

    print(f"\n{'=' * 60}")

    # Compare with baseline (86 SPs)
    baseline = 86
    diff = high_conf - baseline

    if diff > 0:
        print(f"✅ IMPROVEMENT: +{diff} SPs vs baseline ({high_conf} vs {baseline})")
    elif diff == 0:
        print(f"⚠️ NO CHANGE: {high_conf} SPs (same as baseline)")
    else:
        print(f"❌ REGRESSION: {diff} SPs vs baseline ({high_conf} vs {baseline})")

    print()

    return high_conf


def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        iteration_name = sys.argv[1]
    else:
        iteration_name = "Unknown"

    test_iteration(iteration_name)


if __name__ == "__main__":
    main()
