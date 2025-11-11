"""
Dialect configuration for multi-database support.

Supported dialects (based on 2025 enterprise market share):
- tsql: Microsoft SQL Server / Azure Synapse (default)
- mysql: MySQL / MariaDB
- postgres: PostgreSQL
- oracle: Oracle Database
- snowflake: Snowflake Data Cloud
- redshift: Amazon Redshift
- bigquery: Google BigQuery

Version: 1.0.0
Date: 2025-11-11
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class SQLDialect(str, Enum):
    """
    Supported SQL dialects.

    Based on enterprise market share and stored procedure support:
    - TSQL: 27.68% market share (SQL Server/Synapse/Azure SQL)
    - FABRIC: Microsoft Fabric (Lakehouse SQL)
    - MYSQL: 40.19% relational market share
    - POSTGRES: 17.38% market share
    - ORACLE: 9.62% market share (enterprise leader)
    - SNOWFLAKE: Fastest growing data warehouse
    - REDSHIFT: AWS data warehouse
    - BIGQUERY: GCP data warehouse
    """
    TSQL = "tsql"           # SQL Server, Azure SQL, Synapse Analytics
    FABRIC = "fabric"       # Microsoft Fabric
    MYSQL = "mysql"
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
    SQLDialect.MYSQL: DialectMetadata(
        dialect=SQLDialect.MYSQL,
        display_name="MySQL / MariaDB",
        description="MySQL and MariaDB databases",
        metadata_source="information_schema",  # INFORMATION_SCHEMA.TABLES, ROUTINES
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
        dialect_str: Dialect string (e.g., 'tsql', 'mysql', 'TSQL')

    Returns:
        SQLDialect enum

    Raises:
        ValueError: If dialect string is not supported

    Examples:
        >>> validate_dialect('tsql')
        <SQLDialect.TSQL: 'tsql'>

        >>> validate_dialect('MYSQL')
        <SQLDialect.MYSQL: 'mysql'>

        >>> validate_dialect('invalid')
        ValueError: Unsupported SQL dialect: 'invalid'. Supported: tsql, mysql, postgres, oracle, snowflake, redshift, bigquery
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
