"""
Connector factory for creating database-specific connectors.

Auto-selects the correct connector based on SQL_DIALECT setting.
"""

import logging
from typing import Optional
from .base import DatabaseConnector, ConfigurationError
from .tsql_connector import TsqlConnector

logger = logging.getLogger(__name__)

# Registry of available connectors
CONNECTOR_REGISTRY = {
    "tsql": TsqlConnector,
    # Future connectors:
    # "postgres": PostgresConnector,
    # "snowflake": SnowflakeConnector,
    # "bigquery": BigQueryConnector,
}


def get_connector(
    dialect: str,
    connection_string: str,
    timeout: int = 30
) -> DatabaseConnector:
    """
    Create and return the appropriate database connector.

    Args:
        dialect: Database dialect (tsql, etc.)
        connection_string: Database connection string
        timeout: Query timeout in seconds

    Returns:
        DatabaseConnector instance for the specified dialect

    Raises:
        ConfigurationError: If dialect is not supported

    Example:
        >>> connector = get_connector('tsql', 'DRIVER={...};SERVER=...;DATABASE=...')
        >>> with connector:
        ...     procedures = connector.list_procedures()
    """
    connector_class = CONNECTOR_REGISTRY.get(dialect.lower())

    if connector_class is None:
        available = ", ".join(CONNECTOR_REGISTRY.keys())
        raise ConfigurationError(
            f"Unsupported database dialect: '{dialect}'. "
            f"Available dialects: {available}. "
            f"To add support for '{dialect}', create a connector class and "
            f"add it to CONNECTOR_REGISTRY in factory.py."
        )

    logger.info(f"Creating {dialect} connector")
    return connector_class(connection_string, timeout)


def is_dialect_supported(dialect: str) -> bool:
    """Check if a dialect has a connector implementation."""
    return dialect.lower() in CONNECTOR_REGISTRY


def list_supported_dialects() -> list[str]:
    """Get list of all supported database dialects."""
    return list(CONNECTOR_REGISTRY.keys())
