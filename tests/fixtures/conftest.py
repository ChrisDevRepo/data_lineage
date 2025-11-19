"""
Shared pytest fixtures for tests

This module provides reusable fixtures that can be used across all tests.
Fixtures defined here are automatically available to all test files.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
import duckdb


# ============================================================================
# TEMPORARY DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test isolation.

    Automatically cleaned up after test completes.

    Example:
        def test_file_creation(temp_dir):
            test_file = temp_dir / "test.txt"
            test_file.write_text("hello")
            assert test_file.exists()
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_workspace_dir(temp_dir: Path) -> Path:
    """
    Create a temporary workspace directory structure.

    Creates subdirectories:
    - data/
    - jobs/
    - results/

    Example:
        def test_workspace(temp_workspace_dir):
            assert (temp_workspace_dir / "data").exists()
            assert (temp_workspace_dir / "jobs").exists()
    """
    (temp_dir / "data").mkdir()
    (temp_dir / "jobs").mkdir()
    (temp_dir / "results").mkdir()
    return temp_dir


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def temp_duckdb() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Create a temporary in-memory DuckDB connection.

    Automatically closed after test completes.

    Example:
        def test_query(temp_duckdb):
            temp_duckdb.execute("CREATE TABLE test (id INT)")
            temp_duckdb.execute("INSERT INTO test VALUES (1), (2)")
            result = temp_duckdb.execute("SELECT COUNT(*) FROM test").fetchone()
            assert result[0] == 2
    """
    conn = duckdb.connect(":memory:")
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def sample_objects_table(temp_duckdb: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """
    Create a sample objects table for testing.

    Includes:
    - 3 tables
    - 2 stored procedures
    - 1 view
    - 1 function

    Example:
        def test_object_query(sample_objects_table):
            result = sample_objects_table.execute(
                "SELECT COUNT(*) FROM objects WHERE object_type = 'Table'"
            ).fetchone()
            assert result[0] == 3
    """
    temp_duckdb.execute("""
        CREATE TABLE objects (
            object_id INTEGER PRIMARY KEY,
            object_name VARCHAR,
            schema_name VARCHAR,
            object_type VARCHAR,
            create_date TIMESTAMP,
            modify_date TIMESTAMP
        )
    """)

    temp_duckdb.execute("""
        INSERT INTO objects VALUES
        (1, 'FactSales', 'dbo', 'Table', '2024-01-01', '2024-01-01'),
        (2, 'DimProduct', 'dbo', 'Table', '2024-01-01', '2024-01-01'),
        (3, 'DimCustomer', 'dbo', 'Table', '2024-01-01', '2024-01-01'),
        (10, 'spLoadFactSales', 'dbo', 'Stored Procedure', '2024-01-01', '2024-01-01'),
        (11, 'spLoadDimProduct', 'dbo', 'Stored Procedure', '2024-01-01', '2024-01-01'),
        (20, 'vwSalesSummary', 'dbo', 'View', '2024-01-01', '2024-01-01'),
        (30, 'fnGetProductName', 'dbo', 'Function', '2024-01-01', '2024-01-01')
    """)

    return temp_duckdb


# ============================================================================
# PARSER FIXTURES
# ============================================================================

@pytest.fixture
def sample_sql_statements() -> Dict[str, str]:
    """
    Provide sample SQL statements for parser testing.

    Returns:
        Dictionary of test case name → SQL statement

    Example:
        def test_parser(sample_sql_statements):
            sql = sample_sql_statements["simple_insert"]
            # Parse and validate
    """
    return {
        "simple_insert": """
            INSERT INTO dbo.FactSales
            SELECT * FROM dbo.StagingSales
        """,
        "with_cte": """
            WITH SalesCTE AS (
                SELECT * FROM dbo.StagingSales
            )
            INSERT INTO dbo.FactSales
            SELECT * FROM SalesCTE
        """,
        "multiple_tables": """
            INSERT INTO dbo.FactSales
            SELECT
                s.SalesID,
                p.ProductID,
                c.CustomerID
            FROM dbo.StagingSales s
            JOIN dbo.DimProduct p ON s.ProductKey = p.ProductKey
            JOIN dbo.DimCustomer c ON s.CustomerKey = c.CustomerKey
        """,
        "truncate_insert": """
            TRUNCATE TABLE dbo.StagingTemp;
            INSERT INTO dbo.FactSales
            SELECT * FROM dbo.StagingSales
        """,
    }


@pytest.fixture
def sample_create_procedure() -> str:
    """
    Provide a sample CREATE PROCEDURE statement.

    Example:
        def test_procedure_parsing(sample_create_procedure):
            # Test DDL extraction logic
            assert "CREATE PROCEDURE" in sample_create_procedure
    """
    return """
    CREATE PROCEDURE dbo.spLoadFactSales
    AS
    BEGIN
        TRUNCATE TABLE dbo.StagingTemp;

        INSERT INTO dbo.FactSales
        SELECT
            s.SalesID,
            p.ProductID,
            c.CustomerID,
            s.Amount
        FROM dbo.StagingSales s
        JOIN dbo.DimProduct p ON s.ProductKey = p.ProductKey
        JOIN dbo.DimCustomer c ON s.CustomerKey = c.CustomerKey;
    END
    """


# ============================================================================
# EXPECTED RESULTS FIXTURES
# ============================================================================

@pytest.fixture
def expected_parse_results() -> Dict[str, Any]:
    """
    Provide expected parsing results for validation.

    Example:
        def test_parser_output(sample_create_procedure, expected_parse_results):
            result = parse(sample_create_procedure)
            expected = expected_parse_results["spLoadFactSales"]
            assert result["inputs"] == expected["inputs"]
    """
    return {
        "spLoadFactSales": {
            "inputs": ["dbo.StagingSales", "dbo.DimProduct", "dbo.DimCustomer"],
            "outputs": ["dbo.FactSales"],
            "confidence": 100
        }
    }


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def mock_settings() -> Dict[str, Any]:
    """
    Provide mock settings for testing.

    Example:
        def test_with_config(mock_settings):
            assert mock_settings["sql_dialect"] == "tsql"
    """
    return {
        "sql_dialect": "tsql",
        "excluded_schemas": ["sys", "tempdb", "information_schema"]
    }
