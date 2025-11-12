"""
SQL Dialect Implementations.

Provides database-specific implementations for metadata extraction,
query log analysis, and SQL parsing configuration.

Each dialect is a Python class that implements the BaseDialect interface,
following the Strategy pattern for different database platforms.

Author: vibecoding
Version: 1.0.0
"""

from lineage_v3.dialects.base import (
    BaseDialect,
    MetadataSource,
    ColumnSchema,
    DynamicSQLPattern
)
from lineage_v3.dialects.tsql import TSQLDialect
from lineage_v3.dialects.postgres import PostgresDialect
from lineage_v3.dialects.registry import (
    get_dialect,
    is_dialect_implemented,
    list_implemented_dialects
)

__all__ = [
    # Base classes
    'BaseDialect',
    'MetadataSource',
    'ColumnSchema',
    'DynamicSQLPattern',

    # Implementations
    'TSQLDialect',
    'PostgresDialect',

    # Registry functions
    'get_dialect',
    'is_dialect_implemented',
    'list_implemented_dialects',
]
