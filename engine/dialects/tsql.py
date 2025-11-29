"""
T-SQL Dialect Implementation.

Supports all T-SQL platforms (same syntax, metadata queries):
- Microsoft SQL Server 2016+
- Azure SQL Database
- Azure Synapse Analytics
- Microsoft Fabric

All platforms share the same T-SQL dialect - minor platform differences
are handled within this single implementation.

Author: vibecoding
Version: 1.1.0
Date: 2025-11-23
"""

from typing import List, Optional
from engine.dialects.base import (
    BaseDialect,
    MetadataSource,
    DynamicSQLPattern
)


class TSQLDialect(BaseDialect):
    """T-SQL dialect for SQL Server, Azure SQL, Synapse Analytics, and Fabric."""

    @property
    def name(self) -> str:
        return "tsql"

    @property
    def display_name(self) -> str:
        return "Microsoft SQL Server / Azure SQL / Azure Synapse / Fabric"

    # -------------------------------------------------------------------------
    # Metadata Extraction
    # -------------------------------------------------------------------------

    @property
    def metadata_source(self) -> MetadataSource:
        return MetadataSource.DMV

    @property
    def objects_query(self) -> str:
        return """
            SELECT
                o.object_id as database_object_id,
                SCHEMA_NAME(o.schema_id) as schema_name,
                o.name as object_name,
                o.type_desc as object_type,
                o.create_date as created_at,
                o.modify_date as modified_at
            FROM sys.objects o
            WHERE o.type IN ('P', 'V', 'FN', 'IF', 'TF')
              AND o.is_ms_shipped = 0
            ORDER BY o.schema_id, o.name
        """

    @property
    def definitions_query(self) -> str:
        return """
            SELECT
                sm.object_id as database_object_id,
                sm.definition as sql_code
            FROM sys.sql_modules sm
            WHERE sm.definition IS NOT NULL
        """

    # -------------------------------------------------------------------------
    # Query Log Analysis
    # -------------------------------------------------------------------------

    @property
    def query_logs_enabled(self) -> bool:
        return True

    @property
    def query_logs_extraction_query(self) -> Optional[str]:
        return """
            SELECT
                dest.text AS query_text,
                deqs.execution_count,
                deqs.last_execution_time,
                deqs.total_worker_time / 1000000.0 AS total_cpu_seconds,
                OBJECT_NAME(dest.objectid, dest.dbid) AS object_name
            FROM sys.dm_exec_query_stats AS deqs
            CROSS APPLY sys.dm_exec_sql_text(deqs.sql_handle) AS dest
            WHERE dest.text IS NOT NULL
              AND deqs.last_execution_time >= DATEADD(day, -7, GETDATE())
              AND dest.objectid IS NOT NULL
            ORDER BY deqs.execution_count DESC
        """

    @property
    def dynamic_sql_patterns(self) -> List[DynamicSQLPattern]:
        return [
            DynamicSQLPattern(
                pattern=r'@\w+',
                description="T-SQL parameter usage",
                examples=[
                    "SELECT * FROM @table_name",
                    "EXEC sp_executesql @sql"
                ]
            ),
            DynamicSQLPattern(
                pattern=r'EXEC(?:UTE)?\s+sp_executesql',
                description="Dynamic SQL execution via sp_executesql",
                examples=[
                    "EXEC sp_executesql @sql",
                    "EXECUTE sp_executesql @stmt, @params"
                ]
            ),
            DynamicSQLPattern(
                pattern=r'EXECUTE\s*\(',
                description="EXECUTE() dynamic SQL function",
                examples=[
                    "EXECUTE('SELECT * FROM ' + @table)",
                    "EXEC('DROP TABLE ' + @table_name)"
                ]
            ),
            DynamicSQLPattern(
                pattern=r'\$\{[^}]+\}',
                description="Template variable interpolation",
                examples=[
                    "SELECT * FROM ${schema}.${table}",
                    "WHERE date = '${process_date}'"
                ]
            ),
        ]

    # -------------------------------------------------------------------------
    # SQL Parsing Configuration
    # -------------------------------------------------------------------------

    @property
    def case_sensitive(self) -> bool:
        return False

    @property
    def identifier_quote_start(self) -> str:
        return "["

    @property
    def identifier_quote_end(self) -> str:
        return "]"

    @property
    def string_quote(self) -> str:
        return "'"

    @property
    def statement_terminator(self) -> str:
        return ";"

    @property
    def batch_separator(self) -> Optional[str]:
        return "GO"

    @property
    def line_comment(self) -> str:
        return "--"

    @property
    def block_comment_start(self) -> str:
        return "/*"

    @property
    def block_comment_end(self) -> str:
        return "*/"
