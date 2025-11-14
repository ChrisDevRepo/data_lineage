# Test Fixtures

This directory contains shared test fixtures and test data for the Data Lineage Visualizer test suite.

## Structure

```
tests/fixtures/
├── conftest.py           # Shared pytest fixtures (auto-loaded)
├── README.md             # This file
├── user_verified_cases/  # User-reported test cases (regression prevention)
└── baselines/            # Baseline validation snapshots
```

## Available Fixtures

### Temporary Directories

**`temp_dir`** - Temporary directory (auto-cleaned)
```python
def test_file_creation(temp_dir):
    test_file = temp_dir / "test.txt"
    test_file.write_text("hello")
    assert test_file.exists()
```

**`temp_workspace_dir`** - Workspace structure (data/, jobs/, results/)
```python
def test_workspace(temp_workspace_dir):
    data_dir = temp_workspace_dir / "data"
    assert data_dir.exists()
```

### Database Fixtures

**`temp_duckdb`** - In-memory DuckDB connection
```python
def test_query(temp_duckdb):
    temp_duckdb.execute("CREATE TABLE test (id INT)")
    temp_duckdb.execute("INSERT INTO test VALUES (1), (2)")
    result = temp_duckdb.execute("SELECT COUNT(*) FROM test").fetchone()
    assert result[0] == 2
```

**`sample_objects_table`** - Pre-populated objects table
```python
def test_object_query(sample_objects_table):
    result = sample_objects_table.execute(
        "SELECT COUNT(*) FROM objects WHERE object_type = 'Table'"
    ).fetchone()
    assert result[0] == 3
```

### SQL & Parser Fixtures

**`sample_sql_statements`** - Dictionary of test SQL statements
```python
def test_parser(sample_sql_statements):
    sql = sample_sql_statements["simple_insert"]
    result = parse(sql)
    assert len(result["inputs"]) > 0
```

**`sample_create_procedure`** - Complete CREATE PROCEDURE statement
```python
def test_procedure_parsing(sample_create_procedure):
    assert "CREATE PROCEDURE" in sample_create_procedure
    result = parse(sample_create_procedure)
```

**`expected_parse_results`** - Expected parsing outputs for validation
```python
def test_parser_output(sample_create_procedure, expected_parse_results):
    result = parse(sample_create_procedure)
    expected = expected_parse_results["spLoadFactSales"]
    assert result["inputs"] == expected["inputs"]
```

### Configuration Fixtures

**`mock_settings`** - Mock configuration for testing
```python
def test_with_config(mock_settings):
    assert mock_settings["sql_dialect"] == "tsql"
```

## Adding New Fixtures

### Step 1: Add to conftest.py

```python
@pytest.fixture
def your_fixture_name():
    """
    Description of what this fixture provides.

    Example:
        def test_something(your_fixture_name):
            # Usage example
    """
    # Setup
    fixture_data = create_test_data()

    # Return or yield
    yield fixture_data

    # Optional cleanup (only if using yield)
    cleanup()
```

### Step 2: Document in README

Add the fixture to this README with:
- Name and signature
- Description
- Usage example

### Step 3: Test the Fixture

```python
def test_your_fixture(your_fixture_name):
    """Validate fixture works correctly"""
    assert your_fixture_name is not None
```

## Fixture Scope

By default, fixtures have **function** scope (created fresh for each test).

Other scopes:
- `@pytest.fixture(scope="function")` - Default, new instance per test
- `@pytest.fixture(scope="class")` - Shared across test class
- `@pytest.fixture(scope="module")` - Shared across test file
- `@pytest.fixture(scope="session")` - Shared across entire test run

Example:
```python
@pytest.fixture(scope="session")
def expensive_setup():
    """Run once per test session (expensive operation)"""
    return load_large_dataset()
```

## Best Practices

1. **Keep fixtures simple** - One fixture, one responsibility
2. **Use descriptive names** - `temp_duckdb` not `db`
3. **Document with examples** - Show how to use the fixture
4. **Clean up resources** - Use `yield` for cleanup
5. **Avoid test data in fixtures** - Use fixtures to create infrastructure, not data
6. **Compose fixtures** - Build complex fixtures from simple ones

### Good Example

```python
@pytest.fixture
def temp_parquet_file(temp_dir):
    """Creates a temporary parquet file (builds on temp_dir)"""
    file_path = temp_dir / "test.parquet"
    # Create file
    yield file_path
    # No cleanup needed (temp_dir handles it)
```

### Bad Example

```python
@pytest.fixture
def everything():
    """Does too much, unclear purpose"""
    db = create_db()
    files = create_files()
    config = load_config()
    return (db, files, config)  # Which is which?
```

## User-Verified Cases

See [user_verified_cases/README.md](user_verified_cases/README.md) for regression test fixtures based on user-reported bugs.

## Baselines

See [baselines/README.md](baselines/README.md) for baseline validation snapshots.

---

**Last Updated:** 2025-11-14
**Version:** 1.0.0
