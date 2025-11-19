"""
Dialect configuration for multi-database support.

Supported dialects (data warehouse / analytics platforms):
- tsql: Microsoft SQL Server / Azure Synapse (default)
- fabric: Microsoft Fabric
- postgres: PostgreSQL
- oracle: Oracle Database
- snowflake: Snowflake Data Cloud
- redshift: Amazon Redshift
- bigquery: Google BigQuery

Version: 1.0.1
Date: 2025-11-11
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class SQLDialect(str, Enum):
    """
    Supported SQL dialects for data warehouse / analytics platforms.

    Focus on databases with complex ETL and data lineage requirements:
    - TSQL: SQL Server, Azure SQL, Synapse Analytics (default)
    - FABRIC: Microsoft Fabric Lakehouse SQL
    - POSTGRES: PostgreSQL (data warehouses)
    - ORACLE: Oracle Database (enterprise data warehouse)
    - SNOWFLAKE: Snowflake Data Cloud
    - REDSHIFT: Amazon Redshift (Postgres-based)
    - BIGQUERY: Google BigQuery

    Note: OLTP databases (MySQL, etc.) excluded - lineage focus is analytics/DW.
    """
    TSQL = "tsql"           # SQL Server, Azure SQL, Synapse Analytics
    FABRIC = "fabric"       # Microsoft Fabric
    POSTGRES = "postgres"
    ORACLE = "oracle"
    SNOWFLAKE = "snowflake"
    REDSHIFT = "redshift"
    BIGQUERY = "bigquery"


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
        display_name="T-SQL (Microsoft SQL Server / Azure SQL / Azure Synapse)",
        description="Microsoft SQL Server, Azure SQL Database, and Azure Synapse Analytics",
        metadata_source="dmv",  # sys.objects, sys.sql_modules
        supports_stored_procedures=True,
        supports_views=True,
        supports_functions=True
    ),
    SQLDialect.FABRIC: DialectMetadata(
        dialect=SQLDialect.FABRIC,
        display_name="Microsoft Fabric",
        description="Microsoft Fabric Lakehouse SQL endpoint",
        metadata_source="information_schema",  # Fabric uses INFORMATION_SCHEMA
        supports_stored_procedures=True,
        supports_views=True,
        supports_functions=True
    ),
    SQLDialect.POSTGRES: DialectMetadata(
        dialect=SQLDialect.POSTGRES,
        display_name="PostgreSQL",
        description="PostgreSQL database",
        metadata_source="information_schema",  # pg_catalog, information_schema
        supports_stored_procedures=True,
        supports_views=True,
        supports_functions=True
    ),
    SQLDialect.ORACLE: DialectMetadata(
        dialect=SQLDialect.ORACLE,
        display_name="Oracle Database",
        description="Oracle Database",
        metadata_source="system_tables",  # ALL_TABLES, ALL_VIEWS, ALL_SOURCE
        supports_stored_procedures=True,
        supports_views=True,
        supports_functions=True
    ),
    SQLDialect.SNOWFLAKE: DialectMetadata(
        dialect=SQLDialect.SNOWFLAKE,
        display_name="Snowflake",
        description="Snowflake Data Cloud",
        metadata_source="information_schema",  # INFORMATION_SCHEMA + SNOWFLAKE.ACCOUNT_USAGE
        supports_stored_procedures=True,
        supports_views=True,
        supports_functions=True
    ),
    SQLDialect.REDSHIFT: DialectMetadata(
        dialect=SQLDialect.REDSHIFT,
        display_name="Amazon Redshift",
        description="Amazon Redshift Data Warehouse (Postgres-based)",
        metadata_source="information_schema",  # pg_catalog (Postgres-compatible)
        supports_stored_procedures=True,
        supports_views=True,
        supports_functions=True
    ),
    SQLDialect.BIGQUERY: DialectMetadata(
        dialect=SQLDialect.BIGQUERY,
        display_name="Google BigQuery",
        description="Google BigQuery Data Warehouse",
        metadata_source="information_schema",  # INFORMATION_SCHEMA
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
        dialect_str: Dialect string (e.g., 'tsql', 'postgres', 'TSQL')

    Returns:
        SQLDialect enum

    Raises:
        ValueError: If dialect string is not supported

    Examples:
        >>> validate_dialect('tsql')
        <SQLDialect.TSQL: 'tsql'>

        >>> validate_dialect('POSTGRES')
        <SQLDialect.POSTGRES: 'postgres'>

        >>> validate_dialect('invalid')
        ValueError: Unsupported SQL dialect: 'invalid'. Supported: tsql, fabric, postgres, oracle, snowflake, redshift, bigquery
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
