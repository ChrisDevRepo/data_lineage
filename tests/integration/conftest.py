"""
Shared pytest fixtures for integration tests.

These fixtures provide access to the DuckDB workspace and common test utilities.
"""
import pytest
import duckdb
from pathlib import Path
from typing import Generator


@pytest.fixture(scope="session")
def workspace_path() -> Path:
    """
    Get path to DuckDB workspace database.

    Returns:
        Path to lineage_workspace.duckdb file

    Raises:
        FileNotFoundError: If workspace file doesn't exist
    """
    path = Path("data/lineage_workspace.duckdb")
    if not path.exists():
        pytest.skip(f"Workspace database not found at {path}. Run parser first.")
    return path


@pytest.fixture(scope="function")
def db_connection(workspace_path: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Create DuckDB connection to workspace database.

    Args:
        workspace_path: Path to workspace database file

    Yields:
        DuckDB connection instance

    Note:
        Connection is automatically closed after test completes.
    """
    conn = duckdb.connect(str(workspace_path), read_only=True)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture(scope="session")
def test_sp_names() -> list[str]:
    """
    Standard test stored procedure names used across tests.

    Returns:
        List of SP names for validation
    """
    return [
        'spLoadFactLaborCostForEarnedValue_Post',
        'spLoadDimTemplateType'
    ]


@pytest.fixture(scope="session")
def expected_sources() -> dict[str, list[tuple[str, str]]]:
    """
    Expected source tables for test stored procedures.

    Returns:
        Dict mapping SP name to list of (schema, table) tuples
    """
    return {
        'spLoadFactLaborCostForEarnedValue_Post': [
            ('CONSUMPTION_POWERBI', 'FactLaborCostForEarnedValue'),
            ('CONSUMPTION_ClinOpsFinance', 'CadenceBudget_LaborCost_PrimaContractUtilization_Junc')
        ]
    }


@pytest.fixture(scope="session")
def expected_targets() -> dict[str, str]:
    """
    Expected target tables for test stored procedures.

    Returns:
        Dict mapping SP name to target table (schema.table format)
    """
    return {
        'spLoadFactLaborCostForEarnedValue_Post': 'CONSUMPTION_ClinOpsFinance.FactLaborCostForEarnedValue_Post'
    }


@pytest.fixture(scope="function")
def table_exists_checker(db_connection: duckdb.DuckDBPyConnection):
    """
    Helper function to check if table exists in database.

    Args:
        db_connection: DuckDB connection

    Returns:
        Callable that checks if table exists
    """
    def check_table_exists(table_name: str) -> bool:
        """Check if table exists in database."""
        result = db_connection.execute("SHOW TABLES").fetchall()
        table_names = [row[0] for row in result]
        return table_name in table_names

    return check_table_exists


# Assertion helpers
def assert_success_rate_100_percent(sps_with_deps: int, total_sps: int) -> None:
    """
    Assert that parser achieves 100% success rate.

    Args:
        sps_with_deps: Number of SPs with dependencies
        total_sps: Total number of SPs

    Raises:
        AssertionError: If success rate is not 100%
    """
    success_rate = (sps_with_deps / total_sps) * 100 if total_sps > 0 else 0
    assert success_rate == 100.0, (
        f"Expected 100% success rate, got {success_rate:.1f}% "
        f"({sps_with_deps}/{total_sps} SPs with dependencies)"
    )


def assert_confidence_threshold(confidence: float, min_threshold: float = 75.0) -> None:
    """
    Assert that confidence meets minimum threshold.

    Args:
        confidence: Actual confidence value (0-100)
        min_threshold: Minimum acceptable confidence (default: 75.0)

    Raises:
        AssertionError: If confidence below threshold
    """
    assert confidence >= min_threshold, (
        f"Confidence {confidence} below threshold {min_threshold}"
    )


def assert_confidence_distribution_valid(distribution: list[tuple[float, int, float]]) -> None:
    """
    Assert that confidence distribution is valid (only 0, 75, 85, 100).

    Args:
        distribution: List of (confidence, count, percentage) tuples

    Raises:
        AssertionError: If invalid confidence values found
    """
    valid_confidences = {0.0, 75.0, 85.0, 100.0}
    actual_confidences = {conf for conf, _, _ in distribution}

    invalid = actual_confidences - valid_confidences
    assert not invalid, f"Invalid confidence values found: {invalid}"
