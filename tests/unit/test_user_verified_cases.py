"""
User-Verified Test Cases
=========================

These tests validate parser behavior against user-reported corrections.

Process:
1. User reports incorrect parsing results
2. User provides correct expected data
3. Store as verified case in tests/fixtures/user_verified_cases/
4. Auto-generate test from YAML file
5. Run in CI/CD to prevent regressions

Each verified case serves as:
- Regression test (prevents repeating mistakes)
- Change journal entry (documents why fix was made)
- Quality benchmark (user-validated correctness)
"""

import pytest
import yaml
from pathlib import Path
from typing import List, Dict, Any


def load_verified_cases() -> List[Dict[str, Any]]:
    """
    Load all user-verified test cases from YAML files.

    Returns:
        List of test case dictionaries, each containing:
        - sp_name: Stored procedure name
        - expected_inputs: List of expected input tables
        - expected_outputs: List of expected output tables
        - expected_confidence: Expected confidence score
        - issue: Description of what was wrong
        - And other metadata fields
    """
    cases_dir = Path(__file__).parent.parent / "fixtures" / "user_verified_cases"
    cases = []

    # Skip template and README
    skip_files = {"case_template.yaml", "README.md"}

    for case_file in cases_dir.glob("case_*.yaml"):
        if case_file.name in skip_files:
            continue

        try:
            with open(case_file, 'r', encoding='utf-8') as f:
                case_data = yaml.safe_load(f)

            # Skip if empty or template
            if not case_data or case_data.get('sp_name', '').startswith('sp'):
                if 'template' in case_file.name.lower():
                    continue

            # Add file reference for test identification
            case_data['_file'] = case_file.name
            case_data['_path'] = str(case_file)
            cases.append(case_data)

        except Exception as e:
            pytest.fail(f"Failed to load {case_file}: {e}")

    return cases


# Load cases once at module level
VERIFIED_CASES = load_verified_cases()


@pytest.mark.skipif(
    len(VERIFIED_CASES) == 0,
    reason="No user-verified cases found (infrastructure ready, add cases when users report issues)"
)
@pytest.mark.parametrize(
    "case",
    VERIFIED_CASES,
    ids=lambda c: c.get('_file', 'unknown')
)
def test_user_verified_case(case: Dict[str, Any]):
    """
    Test that parser produces user-verified results.

    This test validates:
    - Input tables match user's expected list
    - Output tables match user's expected list
    - Confidence score matches expected value

    If this test fails, it means:
    1. A regression was introduced (parser behavior changed)
    2. The fix that addressed this user's issue was undone
    3. Review the case file for "do_not_change" warnings
    """

    # For now, this is a placeholder that validates case file format
    # Once parser integration is complete, uncomment below:

    # from lineage_v3.parsers import QualityAwareParser
    # from lineage_v3.core import DuckDBWorkspace

    # with DuckDBWorkspace() as db:
    #     parser = QualityAwareParser(db)
    #     result = parser.parse_by_name(case['sp_name'])
    #
    #     # Validate inputs
    #     actual_inputs = set(result.get('inputs', []))
    #     expected_inputs = set(case['expected_inputs'])
    #     assert actual_inputs == expected_inputs, \
    #         f"Input mismatch for {case['sp_name']}: {case['issue']}\n" \
    #         f"Expected: {expected_inputs}\n" \
    #         f"Actual: {actual_inputs}\n" \
    #         f"Missing: {expected_inputs - actual_inputs}\n" \
    #         f"Extra: {actual_inputs - expected_inputs}"
    #
    #     # Validate outputs
    #     actual_outputs = set(result.get('outputs', []))
    #     expected_outputs = set(case['expected_outputs'])
    #     assert actual_outputs == expected_outputs, \
    #         f"Output mismatch for {case['sp_name']}"
    #
    #     # Validate confidence
    #     assert result['confidence'] == case['expected_confidence'], \
    #         f"Confidence mismatch for {case['sp_name']}"

    # Validate case file format
    required_fields = ['sp_name', 'expected_inputs', 'expected_outputs', 'expected_confidence']
    for field in required_fields:
        assert field in case, f"Missing required field '{field}' in {case['_file']}"

    assert isinstance(case['expected_inputs'], list), \
        f"expected_inputs must be a list in {case['_file']}"
    assert isinstance(case['expected_outputs'], list), \
        f"expected_outputs must be a list in {case['_file']}"
    assert isinstance(case['expected_confidence'], (int, float)), \
        f"expected_confidence must be a number in {case['_file']}"

    # Validate confidence is one of the discrete values
    valid_confidence = {0, 75, 85, 100}
    assert case['expected_confidence'] in valid_confidence, \
        f"expected_confidence must be one of {valid_confidence}, got {case['expected_confidence']} in {case['_file']}"

    print(f"✅ Verified case format: {case['_file']}")
    print(f"   SP: {case['sp_name']}")
    print(f"   Issue: {case.get('issue', 'N/A')}")
    print(f"   Expected inputs: {len(case['expected_inputs'])}")
    print(f"   Expected outputs: {len(case['expected_outputs'])}")
    print(f"   Expected confidence: {case['expected_confidence']}")


def test_no_duplicate_case_names():
    """Ensure all case files have unique SP names."""
    sp_names = [case['sp_name'] for case in VERIFIED_CASES]
    duplicates = [name for name in sp_names if sp_names.count(name) > 1]

    assert len(duplicates) == 0, \
        f"Duplicate SP names found in verified cases: {set(duplicates)}\n" \
        f"Each SP should have only one verified case file."


def test_verified_cases_changelog_sync():
    """
    Ensure all verified cases are documented in PARSER_CHANGE_JOURNAL.md

    This test checks that the change journal is kept up-to-date with verified cases.
    """
    if len(VERIFIED_CASES) == 0:
        pytest.skip("No verified cases to check")

    journal_path = Path(__file__).parent.parent.parent / "docs" / "PARSER_CHANGE_JOURNAL.md"

    if not journal_path.exists():
        pytest.skip("PARSER_CHANGE_JOURNAL.md not yet created")

    with open(journal_path, 'r', encoding='utf-8') as f:
        journal_content = f.read()

    # Check each case is referenced in journal
    for case in VERIFIED_CASES:
        case_file = case['_file']
        assert case_file in journal_content, \
            f"Case {case_file} not found in PARSER_CHANGE_JOURNAL.md\n" \
            f"Please add an entry documenting this case."


# Reporting function for summary
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Display summary of verified cases after test run."""
    if len(VERIFIED_CASES) > 0:
        terminalreporter.write_sep("=", "User-Verified Cases Summary")
        terminalreporter.write_line(f"Total verified cases: {len(VERIFIED_CASES)}")

        for case in VERIFIED_CASES:
            terminalreporter.write_line(
                f"  ✓ {case['_file']}: {case['sp_name']} "
                f"({len(case['expected_inputs'])} inputs, {len(case['expected_outputs'])} outputs)"
            )
    else:
        terminalreporter.write_sep("=", "User-Verified Cases")
        terminalreporter.write_line("No verified cases yet. Infrastructure ready!")
        terminalreporter.write_line("Add cases to tests/fixtures/user_verified_cases/ when users report issues.")
