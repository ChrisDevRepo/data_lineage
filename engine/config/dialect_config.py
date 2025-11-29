"""
Dialect configuration for multi-database support.

Supported dialects (data warehouse / analytics platforms):
- tsql: Microsoft SQL Server / Azure Synapse / Fabric (default)

Note: Fabric uses T-SQL dialect (same as SQL Server/Synapse).

Version: 1.0.3
Date: 2025-11-23
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class SQLDialect(str, Enum):
    """
    Supported SQL dialects for data warehouse / analytics platforms.

    Focus on databases with complex ETL and data lineage requirements:
    - TSQL: SQL Server, Azure SQL, Synapse Analytics, Fabric (default)

    Note: Fabric uses TSQL dialect (same connector as SQL Server/Synapse).
    Note: OLTP databases (MySQL, etc.) excluded - lineage focus is analytics/DW.
    """
    TSQL = "tsql"           # SQL Server, Azure SQL, Synapse Analytics, Fabric


@dataclass
class DialectMetadata:
    """Metadata about a SQL dialect"""
    dialect: SQLDialect
    display_name: str
    description: str
    metadata_source: str  # 'dmv', 'information_schema', 'system_tables'
    supports_stored_procedures: bool = True
    supports_views: bool = True
    supports_functions: bool = True


# Registry of dialect metadata
DIALECT_METADATA: Dict[SQLDialect, DialectMetadata] = {
    SQLDialect.TSQL: DialectMetadata(
        dialect=SQLDialect.TSQL,
        display_name="T-SQL (SQL Server / Azure SQL / Synapse / Fabric)",
        description="Microsoft SQL Server, Azure SQL Database, Azure Synapse Analytics, and Microsoft Fabric",
        metadata_source="dmv",  # sys.objects, sys.sql_modules (same for all T-SQL platforms)
        supports_stored_procedures=True,
        supports_views=True,
        supports_functions=True
    ),
}


def get_dialect_metadata(dialect: SQLDialect) -> DialectMetadata:
    """
    Get metadata for a specific dialect.

    Args:
        dialect: SQL dialect enum

    Returns:
        DialectMetadata for the dialect

    Raises:
        ValueError: If dialect is not in registry
    """
    if dialect not in DIALECT_METADATA:
        raise ValueError(f"Unsupported dialect: {dialect}")
    return DIALECT_METADATA[dialect]


def validate_dialect(dialect_str: str) -> SQLDialect:
    """
    Validate and return dialect enum from string.

    Args:
        dialect_str: Dialect string (e.g., 'tsql')

    Returns:
        SQLDialect enum

    Raises:
        ValueError: If dialect string is not supported

    Examples:
        >>> validate_dialect('tsql')
        <SQLDialect.TSQL: 'tsql'>

        >>> validate_dialect('invalid')
        ValueError: Unsupported SQL dialect: 'invalid'. Supported: tsql
    """
    try:
        return SQLDialect(dialect_str.lower())
    except ValueError:
        supported = ", ".join([d.value for d in SQLDialect])
        raise ValueError(
            f"Unsupported SQL dialect: '{dialect_str}'. "
            f"Supported dialects: {supported}"
        )


def list_supported_dialects() -> list:
    """
    List all supported SQL dialects.

    Returns:
        List of SQLDialect enums
    """
    return list(SQLDialect)
