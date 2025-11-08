#!/usr/bin/env python3
"""
Test script for v2.1.0 simplified confidence calculator.

Tests all scenarios from CONFIDENCE_MODEL_SIMPLIFIED.md
"""

import sys
sys.path.insert(0, '/home/user/sandbox')

from lineage_v3.utils.confidence_calculator import ConfidenceCalculator

def test_calculator():
    """Test the v2.1.0 simplified confidence calculator."""

    print("Testing v2.1.0 Simplified Confidence Calculator")
    print("=" * 60)
    print()

    # Test 1: Perfect match (100%)
    print("Test 1: Perfect Match")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=8,
        found_tables=8
    )
    print(f"  Expected: 100, Got: {result['confidence']}")
    print(f"  Breakdown: {result['breakdown']}")
    assert result['confidence'] == 100, "Perfect match should be 100%"
    print("  ✓ PASSED\n")

    # Test 2: Good match (90% -> 100%)
    print("Test 2: Good Match (90%)")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=10,
        found_tables=9
    )
    print(f"  Expected: 100, Got: {result['confidence']}")
    print(f"  Breakdown: {result['breakdown']}")
    assert result['confidence'] == 100, "90% should map to 100%"
    print("  ✓ PASSED\n")

    # Test 3: Most found (70% -> 85%)
    print("Test 3: Most Found (70%)")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=10,
        found_tables=7
    )
    print(f"  Expected: 85, Got: {result['confidence']}")
    print(f"  Breakdown: {result['breakdown']}")
    assert result['confidence'] == 85, "70% should map to 85%"
    print("  ✓ PASSED\n")

    # Test 4: Partial (50% -> 75%)
    print("Test 4: Partial (50%)")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=10,
        found_tables=5
    )
    print(f"  Expected: 75, Got: {result['confidence']}")
    print(f"  Breakdown: {result['breakdown']}")
    assert result['confidence'] == 75, "50% should map to 75%"
    print("  ✓ PASSED\n")

    # Test 5: Too incomplete (20% -> 0%)
    print("Test 5: Too Incomplete (20%)")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=10,
        found_tables=2
    )
    print(f"  Expected: 0, Got: {result['confidence']}")
    print(f"  Breakdown: {result['breakdown']}")
    assert result['confidence'] == 0, "20% should map to 0%"
    print("  ✓ PASSED\n")

    # Test 6: Parse failed
    print("Test 6: Parse Failed")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=False,
        expected_tables=8,
        found_tables=1,
        parse_failure_reason="Dynamic SQL: sp_executesql @variable"
    )
    print(f"  Expected: 0, Got: {result['confidence']}")
    print(f"  Breakdown: {result['breakdown']}")
    assert result['confidence'] == 0, "Parse failure should be 0%"
    assert 'failure_reason' in result['breakdown'], "Should include failure reason"
    print("  ✓ PASSED\n")

    # Test 7: Orchestrator (special case)
    print("Test 7: Orchestrator (only EXEC, no tables)")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=0,
        found_tables=0,
        is_orchestrator=True
    )
    print(f"  Expected: 100, Got: {result['confidence']}")
    print(f"  Breakdown: {result['breakdown']}")
    assert result['confidence'] == 100, "Orchestrator should be 100%"
    assert result['breakdown']['is_orchestrator'] == True
    print("  ✓ PASSED\n")

    # Test 8: Edge case - 69% (should be 75%)
    print("Test 8: Edge Case - 69% (should be 75%)")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=100,
        found_tables=69
    )
    print(f"  Expected: 75, Got: {result['confidence']}")
    print(f"  Completeness: {result['breakdown']['completeness_pct']}%")
    assert result['confidence'] == 75, "69% should map to 75%"
    print("  ✓ PASSED\n")

    # Test 9: Edge case - 89% (should be 85%)
    print("Test 9: Edge Case - 89% (should be 85%)")
    result = ConfidenceCalculator.calculate_simple(
        parse_succeeded=True,
        expected_tables=100,
        found_tables=89
    )
    print(f"  Expected: 85, Got: {result['confidence']}")
    print(f"  Completeness: {result['breakdown']['completeness_pct']}%")
    assert result['confidence'] == 85, "89% should map to 85%"
    print("  ✓ PASSED\n")

    print("=" * 60)
    print("✓ All tests passed!")
    print()
    print("Summary:")
    print("  - Only 4 values returned: 0, 75, 85, 100")
    print("  - No complex calculations or hidden bonuses")
    print("  - Transparent completeness-based logic")
    print("  - Special handling for orchestrators and parse failures")

if __name__ == '__main__':
    test_calculator()
