"""
Dialect Registry and Factory.

Provides centralized access to dialect implementations using the
Factory pattern.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

import logging
from typing import Dict, Type
from engine.config.dialect_config import SQLDialect
from engine.dialects.base import BaseDialect
from engine.dialects.tsql import TSQLDialect
from engine.dialects.postgres import PostgresDialect

logger = logging.getLogger(__name__)


# Dialect registry: Maps SQLDialect enum to implementation class
DIALECT_REGISTRY: Dict[SQLDialect, Type[BaseDialect]] = {
    SQLDialect.TSQL: TSQLDialect,
    SQLDialect.POSTGRES: PostgresDialect,
    # Future dialects:
    # SQLDialect.FABRIC: FabricDialect,
    # SQLDialect.ORACLE: OracleDialect,
    # SQLDialect.SNOWFLAKE: SnowflakeDialect,
    # SQLDialect.REDSHIFT: RedshiftDialect,
    # SQLDialect.BIGQUERY: BigQueryDialect,
}


class DialectRegistry:
    """
    Registry for dialect implementations.

    Provides factory methods for creating dialect instances.
    Follows the Singleton pattern - only one registry exists.
    """

    _instance = None
    _dialect_cache: Dict[SQLDialect, BaseDialect] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, dialect: SQLDialect) -> BaseDialect:
        """
        Get dialect implementation for a SQL dialect.

        Args:
            dialect: SQL dialect enum

        Returns:
            Dialect implementation instance

        Raises:
            NotImplementedError: If dialect not yet implemented

        Example:
            >>> from engine.config.dialect_config import SQLDialect
            >>> from engine.dialects import get_dialect
            >>>
            >>> dialect = get_dialect(SQLDialect.TSQL)
            >>> print(dialect.display_name)
            'Microsoft SQL Server / Azure Synapse'
            >>> print(dialect.objects_query[:50])
            '\n            SELECT\n                o.object_id as datab'
        """
        # Check cache first
        if dialect in self._dialect_cache:
            logger.debug(f"Returning cached dialect instance: {dialect.value}")
            return self._dialect_cache[dialect]

        # Check registry
        if dialect not in DIALECT_REGISTRY:
            available = ", ".join([d.value for d in DIALECT_REGISTRY.keys()])
            raise NotImplementedError(
                f"Dialect '{dialect.value}' not yet implemented. "
                f"Available dialects: {available}"
            )

        # Instantiate and cache
        dialect_class = DIALECT_REGISTRY[dialect]
        instance = dialect_class()
        self._dialect_cache[dialect] = instance

        logger.info(f"Loaded dialect: {instance.display_name}")
        return instance

    def is_implemented(self, dialect: SQLDialect) -> bool:
        """Check if a dialect is implemented."""
        return dialect in DIALECT_REGISTRY

    def list_implemented(self) -> list[SQLDialect]:
        """List all implemented dialects."""
        return list(DIALECT_REGISTRY.keys())


# Singleton instance
_registry = DialectRegistry()


def get_dialect(dialect: SQLDialect) -> BaseDialect:
    """
    Get dialect implementation (convenience function).

    Args:
        dialect: SQL dialect enum

    Returns:
        Dialect implementation instance

    Example:
        >>> from engine.config.dialect_config import SQLDialect
        >>> from engine.dialects import get_dialect
        >>>
        >>> tsql = get_dialect(SQLDialect.TSQL)
        >>> print(tsql.metadata_source)
        <MetadataSource.DMV: 'dmv'>
        >>>
        >>> pg = get_dialect(SQLDialect.POSTGRES)
        >>> print(pg.case_sensitive)
        True
    """
    return _registry.get(dialect)


def is_dialect_implemented(dialect: SQLDialect) -> bool:
    """Check if a dialect is implemented."""
    return _registry.is_implemented(dialect)


def list_implemented_dialects() -> list[SQLDialect]:
    """List all implemented dialects."""
    return _registry.list_implemented()
