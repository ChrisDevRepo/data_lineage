"""
SQL Dialect Implementations.

Provides database-specific implementations for metadata extraction,
query log analysis, and SQL parsing configuration.

Currently supports Microsoft SQL Server family only (SQL Server, Azure SQL, Synapse, Fabric).

Author: vibecoding
Version: 1.0.0
"""

from engine.dialects.base import (
    BaseDialect,
    MetadataSource,
    ColumnSchema,
    DynamicSQLPattern
)
from engine.dialects.tsql import TSQLDialect
from engine.dialects.registry import (
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

    # Registry functions
    'get_dialect',
    'is_dialect_implemented',
    'list_implemented_dialects',
]
