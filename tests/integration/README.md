# Integration Tests for Parser Validation

Comprehensive pytest integration tests for Data Lineage Parser v4.3.3.

## Overview

**Count:** 64 tests across 6 modules
**Purpose:** Validate parser behavior with real DuckDB workspace data
**Behavior:** Skip gracefully when workspace database not available

## Test Modules

### 1. test_database_validation.py (13 tests)

**Purpose:** Overall parsing statistics and success validation

**Test Classes:**
- `TestOverallStatistics` - 100% success rate, input/output percentages
- `TestConfidenceDistribution` - Valid values (0, 75, 85, 100), >80% perfect
- `TestAverageDependencies` - Inputs (2-5), outputs (1-3)
- `TestSpecificStoredProcedures` - Known test SPs
- `TestTopStoredProcedures` - Top 10 by dependency count

**Key Validations:**
- ✅ 100% of SPs have dependencies (no parse failures)
- ✅ Confidence distribution valid (only 0, 75, 85, 100)
- ✅ At least 80% SPs have confidence 100 (perfect)
- ✅ Zero SPs have confidence 0 (no failures)

**Example:**
```python
def test_all_sps_have_dependencies(self, db_connection):
    """Test that 100% of SPs have dependencies (inputs or outputs)."""
    total_sps = db_connection.execute(
        "SELECT COUNT(*) FROM objects WHERE object_type = 'Stored Procedure'"
    ).fetchone()[0]

    sps_with_deps = db_connection.execute("""
        SELECT COUNT(DISTINCT object_id) FROM lineage_metadata
        WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
        AND (inputs IS NOT NULL OR outputs IS NOT NULL)
    """).fetchone()[0]

    assert_success_rate_100_percent(sps_with_deps, total_sps)
```

---

### 2. test_sp_parsing_details.py (8 tests)

**Purpose:** Detailed SP parsing with table names and phantom detection

**Test Classes:**
- `TestSPDetailedParsing` - Confidence scores, table name validation
- `TestPhantomObjectDetection` - Negative IDs, phantom tracking
- `TestExpectedDependencies` - Expected sources/targets validation

**Key Validations:**
- ✅ All input/output tables have valid schema and names
- ✅ Phantom objects use negative IDs (< 0)
- ✅ Phantoms properly tracked in phantom_objects table
- ✅ Expected dependencies found for known test SPs

**Example:**
```python
def test_phantom_objects_have_negative_ids(self, db_connection):
    """Test that phantom objects use negative IDs (< 0)."""
    phantom_objects = db_connection.execute("""
        SELECT object_id, schema_name, object_name
        FROM phantom_objects
    """).fetchall()

    for obj_id, schema, name in phantom_objects:
        assert obj_id < 0, f"Phantom {schema}.{name} should have negative ID"
```

---

### 3. test_confidence_analysis.py (11 tests)

**Purpose:** Why some SPs have confidence 85 or 75 instead of 100

**Test Classes:**
- `TestConfidenceDistribution` - Success rate, confidence majority
- `TestConfidence85Analysis` - 70-89% completeness SPs
- `TestConfidence75Analysis` - 50-69% completeness SPs
- `TestPatternAnalysis` - SQL patterns in lower confidence SPs
- `TestCleaningLogicAssessment` - Cleaning logic effectiveness

**Key Validations:**
- ✅ 100% success rate (all SPs have dependencies)
- ✅ Majority (>80%) have confidence 100
- ✅ Confidence 85/75 within acceptable ranges (<15% each)
- ✅ Lower confidence SPs have identifiable patterns

**Example:**
```python
def test_confidence_85_completeness_range(self, conf_85_sps):
    """Test that confidence 85 SPs have 70-89% completeness."""
    for schema, name, conf, inputs, outputs, expected, found in conf_85_sps:
        if expected and found and expected > 0:
            completeness = (found / expected) * 100
            assert 70 <= completeness < 90, (
                f"Confidence 85 SP {schema}.{name} should have 70-89% completeness"
            )
```

---

### 4. test_sqlglot_performance.py (14 tests)

**Purpose:** SQLGlot enhancement impact and completeness analysis

**Test Classes:**
- `TestOverallParsingSuccess` - 100% success with SQLGlot
- `TestConfidenceDistribution` - Valid distribution
- `TestCompletenessAnalysis` - Found vs expected tables
- `TestSQLGlotEnhancementImpact` - Tables added by SQLGlot
- `TestPhantomObjectDetection` - Phantom tracking
- `TestKeyInsights` - Architectural validation

**Key Validations:**
- ✅ Regex baseline provides guaranteed coverage
- ✅ SQLGlot enhances but doesn't replace baseline
- ✅ Average 0-5 tables added per SP by SQLGlot
- ✅ No SPs with <50% completeness (poor quality)

**Example:**
```python
def test_sqlglot_enhances_not_replaces(self, db_connection):
    """Test that SQLGlot enhances but doesn't replace regex baseline."""
    result = db_connection.execute("""
        SELECT
            COUNT(*) FILTER (WHERE found_count >= expected_count) as maintained,
            COUNT(*) as total
        FROM lineage_metadata
        WHERE primary_source = 'parser' AND expected_count > 0
    """).fetchone()

    maintained, total = result
    percentage = (maintained / total) * 100

    assert percentage >= 95.0, "SQLGlot should maintain or enhance for >=95%"
```

---

### 5. test_failure_analysis.py (8 tests)

**Purpose:** Root cause investigation for failed SPs (if any)

**Test Classes:**
- `TestFailureIdentification` - No failed SPs (100% success)
- `TestFailureCategorization` - Dynamic SQL, templates, utility SPs
- `TestPatternAnalysis` - SQL patterns in failed SPs
- `TestCleaningLogicAssessment` - Cleaning logic validation
- `TestConclusion` - Parser health validation

**Key Validations:**
- ✅ Zero failed SPs (100% success rate)
- ✅ If failures exist, categorized correctly
- ✅ No unexpected failures (cleaning logic working)
- ✅ Success rate >= 99% (cleaning not too aggressive)

**Example:**
```python
def test_no_failed_sps(self, failed_sps):
    """Test that parser achieves 100% success rate (no failed SPs)."""
    assert len(failed_sps) == 0, (
        f"Expected 0 failed SPs (100% success rate), got {len(failed_sps)}"
    )
```

---

### 6. test_sp_deep_debugging.py (10 tests)

**Purpose:** Deep debugging for specific SP parsing behavior

**Test Classes:**
- `TestRegexExtraction` - FROM/INTO/UPDATE table extraction
- `TestSQLGlotParsing` - WARN/RAISE mode behavior
- `TestProblematicPatterns` - T-SQL patterns detection
- `TestExpectedDependencyValidation` - Expected sources validation
- `TestDebuggingWorkflow` - Debugging workflow validation

**Key Validations:**
- ✅ Regex extracts FROM tables correctly
- ✅ Regex extracts target tables (INSERT/UPDATE)
- ✅ SQLGlot RAISE mode used (correct choice)
- ✅ Temp tables (#temp) excluded from dependencies
- ✅ SPs have reasonable DDL length and data operations

**Example:**
```python
def test_regex_extracts_from_tables(self, target_sp):
    """Test that regex can extract FROM tables."""
    sp_id, sp_name, schema, ddl = target_sp
    from_pattern = r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?'
    from_tables = re.findall(from_pattern, ddl, re.IGNORECASE)

    assert len(from_tables) > 0, "Should find at least one FROM table"
```

---

## Shared Fixtures (conftest.py)

### Session Fixtures

**workspace_path** - Path to DuckDB workspace database
```python
@pytest.fixture(scope="session")
def workspace_path() -> Path:
    """Get path to DuckDB workspace database."""
    path = Path("data/lineage_workspace.duckdb")
    if not path.exists():
        pytest.skip("Workspace database not found. Run parser first.")
    return path
```

**test_sp_names** - Standard test stored procedure names
```python
@pytest.fixture(scope="session")
def test_sp_names() -> list[str]:
    """Standard test SP names for validation."""
    return [
        'spLoadFactLaborCostForEarnedValue_Post',
        'spLoadDimTemplateType'
    ]
```

**expected_sources** - Expected source tables for test SPs
```python
@pytest.fixture(scope="session")
def expected_sources() -> dict[str, list[tuple[str, str]]]:
    """Expected source tables for test stored procedures."""
    return {
        'spLoadFactLaborCostForEarnedValue_Post': [
            ('CONSUMPTION_POWERBI', 'FactLaborCostForEarnedValue'),
            ('CONSUMPTION_ClinOpsFinance', 'CadenceBudget_...')
        ]
    }
```

### Function Fixtures

**db_connection** - DuckDB connection with automatic cleanup
```python
@pytest.fixture(scope="function")
def db_connection(workspace_path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Create DuckDB connection to workspace database."""
    conn = duckdb.connect(str(workspace_path), read_only=True)
    try:
        yield conn
    finally:
        conn.close()
```

### Helper Assertions

**assert_success_rate_100_percent** - Validate 100% success
```python
def assert_success_rate_100_percent(sps_with_deps: int, total_sps: int):
    """Assert that parser achieves 100% success rate."""
    success_rate = (sps_with_deps / total_sps) * 100
    assert success_rate == 100.0, f"Expected 100%, got {success_rate:.1f}%"
```

**assert_confidence_threshold** - Validate confidence >= threshold
```python
def assert_confidence_threshold(confidence: float, min_threshold: float = 75.0):
    """Assert that confidence meets minimum threshold."""
    assert confidence >= min_threshold, f"Confidence {confidence} below {min_threshold}"
```

**assert_confidence_distribution_valid** - Validate only valid values
```python
def assert_confidence_distribution_valid(distribution):
    """Assert that confidence distribution is valid (only 0, 75, 85, 100)."""
    valid_confidences = {0.0, 75.0, 85.0, 100.0}
    actual_confidences = {conf for conf, _, _ in distribution}
    invalid = actual_confidences - valid_confidences
    assert not invalid, f"Invalid confidence values: {invalid}"
```

---

## Running Tests

### All Integration Tests

```bash
# Run all 64 tests
pytest tests/integration/ -v

# With short traceback
pytest tests/integration/ -v --tb=short

# Specific module
pytest tests/integration/test_database_validation.py -v

# Specific test class
pytest tests/integration/test_database_validation.py::TestOverallStatistics -v

# Specific test
pytest tests/integration/test_database_validation.py::TestOverallStatistics::test_all_sps_have_dependencies -v
```

### With Coverage

```bash
# Coverage for parser code
pytest tests/integration/ -v --cov=engine/parsers --cov-report=term

# HTML coverage report
pytest tests/integration/ -v --cov=engine/parsers --cov-report=html
open htmlcov/index.html
```

### Test Output Examples

**With Database:**
```bash
$ pytest tests/integration/ -v
============================== test session starts ===============================
collected 64 items

test_database_validation.py::test_all_sps_have_dependencies PASSED       [  1%]
test_database_validation.py::test_sps_with_inputs_percentage PASSED      [  3%]
test_database_validation.py::test_confidence_values_are_valid PASSED     [  4%]
...
============================== 64 passed in 12.34s ===============================
```

**Without Database (CI):**
```bash
$ pytest tests/integration/ -v
============================== test session starts ===============================
collected 64 items

test_database_validation.py::test_all_sps_have_dependencies SKIPPED      [  1%]
test_database_validation.py::test_sps_with_inputs_percentage SKIPPED     [  3%]
...
============================== 64 skipped in 0.22s ===============================

Reason: Workspace database not found at data/lineage_workspace.duckdb. Run parser first.
```

---

## Test Expectations (v4.3.3)

### Success Metrics

- ✅ **100%** SPs have dependencies (349/349)
- ✅ **82.5%** SPs at confidence 100 (perfect)
- ✅ **7.4%** SPs at confidence 85 (good)
- ✅ **10.0%** SPs at confidence 75 (acceptable)
- ✅ **0%** SPs at confidence 0 (failures)

### Average Dependencies

- ✅ **3.20** inputs per SP (2-5 range)
- ✅ **1.87** outputs per SP (1-3 range)

### Confidence Distribution

Only valid values:
- `0.0` - Parse failures (should be 0%)
- `75.0` - 50-69% completeness (acceptable, <15%)
- `85.0` - 70-89% completeness (good, <15%)
- `100.0` - ≥90% completeness (perfect, >80%)

---

## CI/CD Integration

### GitHub Actions

**Workflow:** `.github/workflows/parser-validation.yml`

**Job:** `parser-integration-tests`
```yaml
- name: Run integration tests
  run: |
    echo "🧪 Running parser integration tests..."
    pytest tests/integration/ -v --tb=short
```

**Expected Behavior in CI:**
- All 64 tests **skip** (no workspace database)
- No test failures
- Job passes successfully

**With Test Data:**
- Tests would run and validate
- Must pass for PR merge

---

## Converted from Original Scripts

These integration tests replace standalone validation scripts:

| Original Script | New Test Module | Tests |
|----------------|----------------|-------|
| `check_parsing_results.py` | `test_database_validation.py` | 13 |
| `verify_sp_parsing.py` | `test_sp_parsing_details.py` | 8 |
| `analyze_lower_confidence_sps.py` | `test_confidence_analysis.py` | 11 |
| `analyze_sqlglot_performance.py` | `test_sqlglot_performance.py` | 14 |
| `analyze_failed_sps.py` | `test_failure_analysis.py` | 8 |
| `analyze_sp.py` | `test_sp_deep_debugging.py` | 10 |

**Benefits of pytest conversion:**
- ✅ CI/CD integration
- ✅ Automatic regression detection
- ✅ Shared fixtures reduce duplication
- ✅ Clear test organization
- ✅ Coverage reporting
- ✅ Parameterized tests

---

## Troubleshooting

### All Tests Skipping

**Symptom:**
```
64 skipped in 0.22s
Reason: Workspace database not found
```

**Cause:** No `data/lineage_workspace.duckdb` file

**Solution:**
1. This is **expected** in CI without real data
2. To run locally, first parse real data:
   ```bash
   python -m engine.cli parse --input data/
   pytest tests/integration/ -v
   ```

### Import Errors

**Symptom:**
```
ImportError: No module named 'duckdb'
```

**Solution:**
```bash
pip install -r requirements/parser.txt
pip install pytest pytest-cov
```

### Test Failures with Real Data

**Symptom:** Tests fail when run with real workspace

**Common causes:**
1. Parser regression (confidence decreased)
2. Test data changed (different SPs)
3. Configuration changed (schemas excluded)

**Solution:**
1. Check parser version: v4.3.3 expected
2. Review test expectations vs actual data
3. Update expected values if data legitimately changed

---

## References

- **Parser Documentation:** `docs/PARSER_TECHNICAL_GUIDE.md`
- **CI Workflows:** `.github/workflows/README.md`
- **Original Scripts:** `scripts/testing/README.md`
- **Unit Tests:** `tests/unit/`

---

**Last Updated:** 2025-11-14
**Parser Version:** v4.3.3
**Test Count:** 64 tests across 6 modules
