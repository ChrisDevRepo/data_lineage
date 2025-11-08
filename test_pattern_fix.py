#!/usr/bin/env python3
"""
Simple pattern validation - no imports needed.
Tests DECLARE/SET regex patterns directly.
"""

import re

# NEW patterns (after fix)
NEW_DECLARE = r'DECLARE\s+@\w+.*?(?:;|\n|$)'
NEW_SET = r'SET\s+@\w+\s*=.*?(?:;|\n|$)'

# OLD patterns (before fix - for comparison)
OLD_DECLARE = r'DECLARE\s+@\w+[^;]*;?'
OLD_SET = r'SET\s+@\w+\s*=[^;]*;?'

TEST_CASES = [
    {
        "name": "User's Critical Case",
        "sql": """DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@ProcName) )

INSERT INTO STAGING_CADENCE.TRIAL_FinalCountryReallocateTS
SELECT FROM STAGING_CADENCE.TRIAL_CountryReallocateTS""",
        "must_preserve": ["INSERT INTO", "SELECT FROM"],
    },
    {
        "name": "Standard DECLARE with semicolon",
        "sql": "DECLARE @var INT = 1;\nINSERT INTO T1 SELECT FROM T2",
        "must_preserve": ["INSERT INTO", "SELECT FROM"],
    },
    {
        "name": "SET without semicolon",
        "sql": "SET @var = (SELECT COUNT(*) FROM T1)\nINSERT INTO T2",
        "must_preserve": ["INSERT INTO"],
    },
    {
        "name": "Multiple DECLAREs",
        "sql": """DECLARE @v1 INT = 1
DECLARE @v2 INT = 2
INSERT INTO Target SELECT FROM Source""",
        "must_preserve": ["INSERT INTO", "SELECT FROM"],
    },
]


def test_patterns():
    print("=" * 80)
    print("PATTERN FIX VALIDATION")
    print("=" * 80)
    print()

    all_pass = True

    for test in TEST_CASES:
        print(f"Test: {test['name']}")
        print("-" * 80)

        sql = test['sql']

        # Apply OLD patterns
        old_result = sql
        old_result = re.sub(OLD_DECLARE, '', old_result, flags=re.IGNORECASE)
        old_result = re.sub(OLD_SET, '', old_result, flags=re.IGNORECASE)

        # Apply NEW patterns
        new_result = sql
        new_result = re.sub(NEW_DECLARE, '', new_result, flags=re.IGNORECASE | re.DOTALL)
        new_result = re.sub(NEW_SET, '', new_result, flags=re.IGNORECASE | re.DOTALL)

        # Check OLD pattern (should FAIL for critical cases)
        old_preserves = all(p in old_result for p in test['must_preserve'])

        # Check NEW pattern (should PASS)
        new_preserves = all(p in new_result for p in test['must_preserve'])

        print(f"OLD pattern preserves content: {'✅' if old_preserves else '❌ (EXPECTED - this is why we needed the fix)'}")
        print(f"NEW pattern preserves content: {'✅' if new_preserves else '❌ REGRESSION!'}")

        if not new_preserves:
            all_pass = False
            print("\n⚠️ REGRESSION DETECTED!")
            print("Missing from result:")
            for p in test['must_preserve']:
                if p not in new_result:
                    print(f"  - {p}")
            print(f"\nResult: {new_result[:200]}")

        print()

    print("=" * 80)
    if all_pass:
        print("✅ ALL TESTS PASSED - Fix works correctly!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Regressions detected!")
        return 1


if __name__ == "__main__":
    exit(test_patterns())
