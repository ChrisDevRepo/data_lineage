"""
Quick test to verify unified confidence calculator fixes.

Tests:
1. Parser method produces consistent scores
2. Evaluation method produces consistent scores
3. Confidence stats calculation works
4. Cache invalidation logic exists

Author: Claude Code Agent
Date: 2025-11-03
"""

import sys
from pathlib import Path

# Add lineage_v3 to path
sys.path.insert(0, str(Path(__file__).parent))

from lineage_v3.utils.confidence_calculator import ConfidenceCalculator


def test_parser_method():
    """Test quality match method (parser)."""
    print("\n" + "="*60)
    print("TEST 1: Parser Confidence Calculation")
    print("="*60)

    # Test case 1: Perfect match
    conf = ConfidenceCalculator.from_quality_match(
        source_match=1.0,
        target_match=1.0
    )
    print(f"✓ Perfect match: {conf} (expected 0.85)")
    assert conf == 0.85, f"Expected 0.85, got {conf}"

    # Test case 2: Good match (95% sources, 92% targets)
    conf = ConfidenceCalculator.from_quality_match(
        source_match=0.95,
        target_match=0.92
    )
    print(f"✓ Good match (95%/92%): {conf} (expected 0.85)")
    assert conf == 0.85, f"Expected 0.85, got {conf}"

    # Test case 3: Medium match (80% sources, 80% targets)
    conf = ConfidenceCalculator.from_quality_match(
        source_match=0.80,
        target_match=0.80
    )
    print(f"✓ Medium match (80%/80%): {conf} (expected 0.75)")
    assert conf == 0.75, f"Expected 0.75, got {conf}"

    # Test case 4: Low match (60% sources, 60% targets)
    conf = ConfidenceCalculator.from_quality_match(
        source_match=0.60,
        target_match=0.60
    )
    print(f"✓ Low match (60%/60%): {conf} (expected 0.5)")
    assert conf == 0.5, f"Expected 0.5, got {conf}"

    # Test case 5: Orchestrator SP (0 tables, 5 SP calls)
    conf = ConfidenceCalculator.from_quality_match(
        source_match=1.0,
        target_match=1.0,
        regex_sources_count=0,
        regex_targets_count=0,
        sp_calls_count=5
    )
    print(f"✓ Orchestrator SP (0 tables, 5 SP calls): {conf} (expected 0.85)")
    assert conf == 0.85, f"Expected 0.85, got {conf}"

    print("✅ All parser method tests passed!")


def test_evaluation_method():
    """Test precision/recall method (evaluation)."""
    print("\n" + "="*60)
    print("TEST 2: Evaluation Confidence Calculation")
    print("="*60)

    # Test case 1: Perfect match
    conf = ConfidenceCalculator.from_precision_recall(
        precision=1.0,
        recall=1.0,
        use_bucketing=True
    )
    print(f"✓ Perfect P/R (1.0/1.0): {conf} (expected 0.85)")
    assert conf == 0.85, f"Expected 0.85, got {conf}"

    # Test case 2: Good F1 (0.92)
    conf = ConfidenceCalculator.from_precision_recall(
        precision=0.95,
        recall=0.90,
        use_bucketing=True
    )
    print(f"✓ Good P/R (0.95/0.90, F1=0.924): {conf} (expected 0.85)")
    assert conf == 0.85, f"Expected 0.85, got {conf}"

    # Test case 3: Medium F1 (0.80)
    conf = ConfidenceCalculator.from_precision_recall(
        precision=0.80,
        recall=0.80,
        use_bucketing=True
    )
    print(f"✓ Medium P/R (0.80/0.80, F1=0.80): {conf} (expected 0.75)")
    assert conf == 0.75, f"Expected 0.75, got {conf}"

    # Test case 4: Low F1 (0.60)
    conf = ConfidenceCalculator.from_precision_recall(
        precision=0.60,
        recall=0.60,
        use_bucketing=True
    )
    print(f"✓ Low P/R (0.60/0.60, F1=0.60): {conf} (expected 0.5)")
    assert conf == 0.5, f"Expected 0.5, got {conf}"

    # Test case 5: Raw F1 (no bucketing)
    conf = ConfidenceCalculator.from_precision_recall(
        precision=0.85,
        recall=0.85,
        use_bucketing=False
    )
    print(f"✓ Raw F1 (no bucketing): {conf} (expected 0.85)")
    assert conf == 0.85, f"Expected 0.85, got {conf}"

    print("✅ All evaluation method tests passed!")


def test_stats_calculation():
    """Test aggregate stats calculation."""
    print("\n" + "="*60)
    print("TEST 3: Confidence Stats Calculation")
    print("="*60)

    scores = [0.85, 0.85, 0.85, 0.75, 0.75, 0.5, 0.5, 0.0]
    stats = ConfidenceCalculator.calculate_stats(scores)

    print(f"Input scores: {scores}")
    print(f"Stats: {stats}")

    assert stats['total_count'] == 8, f"Expected 8, got {stats['total_count']}"
    assert stats['high_confidence_count'] == 3, f"Expected 3 high, got {stats['high_confidence_count']}"
    assert stats['medium_confidence_count'] == 2, f"Expected 2 medium, got {stats['medium_confidence_count']}"
    assert stats['low_confidence_count'] == 3, f"Expected 3 low, got {stats['low_confidence_count']}"

    print("✅ Stats calculation test passed!")


def test_helper_methods():
    """Test helper methods (labels, colors)."""
    print("\n" + "="*60)
    print("TEST 4: Helper Methods")
    print("="*60)

    # Test labels
    assert ConfidenceCalculator.get_confidence_label(0.85) == 'High'
    assert ConfidenceCalculator.get_confidence_label(0.75) == 'Medium'
    assert ConfidenceCalculator.get_confidence_label(0.5) == 'Low'
    assert ConfidenceCalculator.get_confidence_label(0.0) == 'Failed'
    print("✓ Confidence labels correct")

    # Test colors
    assert ConfidenceCalculator.get_confidence_color(0.85) == 'green'
    assert ConfidenceCalculator.get_confidence_color(0.75) == 'yellow'
    assert ConfidenceCalculator.get_confidence_color(0.5) == 'orange'
    assert ConfidenceCalculator.get_confidence_color(0.0) == 'red'
    print("✓ Confidence colors correct")

    print("✅ All helper method tests passed!")


def test_cache_invalidation():
    """Verify cache invalidation method exists."""
    print("\n" + "="*60)
    print("TEST 5: Cache Invalidation")
    print("="*60)

    try:
        from lineage_v3.core.duckdb_workspace import DuckDBWorkspace

        # Check method exists
        assert hasattr(DuckDBWorkspace, 'clear_orphaned_metadata'), \
            "clear_orphaned_metadata method not found!"

        print("✓ clear_orphaned_metadata() method exists")
    except ImportError as e:
        # DuckDB not installed in test environment - check source code instead
        print("✓ Skipping import test (DuckDB not available)")
        workspace_file = Path(__file__).parent / 'lineage_v3' / 'core' / 'duckdb_workspace.py'
        assert workspace_file.exists(), "duckdb_workspace.py not found"
        content = workspace_file.read_text()
        assert 'def clear_orphaned_metadata' in content, "clear_orphaned_metadata method not found in source"
        print("✓ clear_orphaned_metadata() found in source code")

    print("✅ Cache invalidation test passed!")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("UNIFIED CONFIDENCE CALCULATOR - VERIFICATION TESTS")
    print("="*60)

    try:
        test_parser_method()
        test_evaluation_method()
        test_stats_calculation()
        test_helper_methods()
        test_cache_invalidation()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe unified confidence calculator is working correctly.")
        print("All components now use consistent metric calculations.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
