"""
Abstract base class for SQL dialect implementations.

Each dialect defines database-specific behavior for metadata extraction,
query log analysis, and SQL parsing configuration.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class MetadataSource(str, Enum):
    """Type of metadata source used by the dialect."""
    DMV = "dmv"  # Dynamic Management Views (SQL Server)
    INFORMATION_SCHEMA = "information_schema"  # ANSI standard
    SYSTEM_TABLES = "system_tables"  # Database-specific system tables


@dataclass
class ColumnSchema:
    """Schema definition for a DataFrame column."""
    name: str
    dtype: str  # pandas dtype: int64, string, datetime64, float64
    required: bool = True
    description: str = ""


@dataclass
class DynamicSQLPattern:
    """Pattern for detecting dynamic SQL in query logs."""
    pattern: str
    description: str
    examples: List[str]


class BaseDialect(ABC):
    """
    Abstract base class for SQL dialect implementations.

    Each dialect must implement methods for:
    - Metadata extraction (objects, definitions)
    - Query log analysis
    - SQL parsing configuration

    This follows the Strategy pattern - different implementations
    for different database platforms.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Dialect name (tsql, postgres, etc.)."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable display name."""
        pass

    @property
    @abstractmethod
    def sqlglot_dialect(self) -> str:
        """SQLGlot dialect identifier."""
        pass

    # -------------------------------------------------------------------------
    # Metadata Extraction
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def metadata_source(self) -> MetadataSource:
        """Type of metadata source (DMV, INFORMATION_SCHEMA, etc.)."""
        pass

    @property
    @abstractmethod
    def objects_query(self) -> str:
        """
        SQL query to extract database objects.

        Must return columns:
        - database_object_id: Unique identifier (int64)
        - schema_name: Schema/namespace (string)
        - object_name: Object name (string)
        - object_type: Type (PROCEDURE, FUNCTION, VIEW, etc.)
        - created_at: Creation timestamp (datetime64, nullable)
        - modified_at: Modification timestamp (datetime64, nullable)
        """
        pass

    @property
    @abstractmethod
    def definitions_query(self) -> str:
        """
        SQL query to extract object definitions (source code).

        Must return columns:
        - database_object_id: Matches objects_query (int64)
        - sql_code: Source code (string)
        """
        pass

    @property
    def objects_schema(self) -> List[ColumnSchema]:
        """Expected schema for objects DataFrame."""
        return [
            ColumnSchema("database_object_id", "int64", required=True),
            ColumnSchema("schema_name", "string", required=True),
            ColumnSchema("object_name", "string", required=True),
            ColumnSchema("object_type", "string", required=True),
            ColumnSchema("created_at", "datetime64", required=False),
            ColumnSchema("modified_at", "datetime64", required=False),
        ]

    @property
    def definitions_schema(self) -> List[ColumnSchema]:
        """Expected schema for definitions DataFrame."""
        return [
            ColumnSchema("database_object_id", "int64", required=True),
            ColumnSchema("sql_code", "string", required=True),
        ]

    # -------------------------------------------------------------------------
    # Query Log Analysis
    # -------------------------------------------------------------------------

    @property
    def query_logs_enabled(self) -> bool:
        """Whether query log analysis is supported."""
        return True

    @property
    def query_logs_extraction_query(self) -> Optional[str]:
        """
        SQL query to extract query execution logs.

        Must return columns:
        - query_text: Full SQL query (string)
        - execution_count: Number of executions (int64)
        - last_execution_time: Last run timestamp (datetime64, nullable)
        - total_cpu_seconds: Total CPU time (float64, nullable)
        - object_name: Associated stored procedure (string, nullable)
        """
        return None

    @property
    def query_logs_parquet_path(self) -> str:
        """Default path for query logs Parquet file."""
        return "parquet_snapshots/query_logs.parquet"

    @property
    def query_logs_schema(self) -> List[ColumnSchema]:
        """Expected schema for query logs DataFrame."""
        return [
            ColumnSchema("query_text", "string", required=True,
                        description="Full SQL query text"),
            ColumnSchema("execution_count", "int64", required=True,
                        description="Number of times executed"),
            ColumnSchema("last_execution_time", "datetime64", required=False,
                        description="Last execution timestamp"),
            ColumnSchema("total_cpu_seconds", "float64", required=False,
                        description="Total CPU time in seconds"),
            ColumnSchema("object_name", "string", required=False,
                        description="Associated stored procedure name"),
        ]

    @property
    @abstractmethod
    def dynamic_sql_patterns(self) -> List[DynamicSQLPattern]:
        """
        Patterns for detecting dynamic SQL in query logs.

        These patterns help identify queries that construct SQL dynamically,
        which is important for accurate lineage detection.
        """
        pass

    # -------------------------------------------------------------------------
    # SQL Parsing Configuration
    # -------------------------------------------------------------------------

    @property
    def case_sensitive(self) -> bool:
        """Whether identifiers are case-sensitive."""
        return False

    @property
    def identifier_quote_start(self) -> str:
        """Starting quote character for identifiers."""
        return '"'

    @property
    def identifier_quote_end(self) -> str:
        """Ending quote character for identifiers."""
        return '"'

    @property
    def string_quote(self) -> str:
        """Quote character for string literals."""
        return "'"

    @property
    def statement_terminator(self) -> str:
        """Statement terminator character."""
        return ";"

    @property
    def batch_separator(self) -> Optional[str]:
        """Batch separator (e.g., GO in T-SQL), if any."""
        return None

    @property
    def line_comment(self) -> str:
        """Line comment prefix."""
        return "--"

    @property
    def block_comment_start(self) -> str:
        """Block comment start marker."""
        return "/*"

    @property
    def block_comment_end(self) -> str:
        """Block comment end marker."""
        return "*/"

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.display_name}>"
