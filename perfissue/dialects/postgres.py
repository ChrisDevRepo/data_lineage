"""
PostgreSQL Dialect Implementation.

Supports:
- PostgreSQL 12+
- Amazon Redshift (Postgres-compatible, but use redshift.py for full support)

Note: Query log analysis requires pg_stat_statements extension.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

from typing import List, Optional
from lineage_v3.dialects.base import (
    BaseDialect,
    MetadataSource,
    DynamicSQLPattern
)


class PostgresDialect(BaseDialect):
    """PostgreSQL dialect for PostgreSQL databases and data warehouses."""

    @property
    def name(self) -> str:
        return "postgres"

    @property
    def display_name(self) -> str:
        return "PostgreSQL"

    @property
    def sqlglot_dialect(self) -> str:
        return "postgres"

    # -------------------------------------------------------------------------
    # Metadata Extraction
    # -------------------------------------------------------------------------

    @property
    def metadata_source(self) -> MetadataSource:
        return MetadataSource.INFORMATION_SCHEMA

    @property
    def objects_query(self) -> str:
        return """
            SELECT
                p.oid as database_object_id,
                n.nspname as schema_name,
                p.proname as object_name,
                CASE
                    WHEN p.prokind = 'f' THEN 'FUNCTION'
                    WHEN p.prokind = 'p' THEN 'PROCEDURE'
                    WHEN p.prokind = 'a' THEN 'AGGREGATE'
                    WHEN p.prokind = 'w' THEN 'WINDOW'
                    ELSE 'FUNCTION'
                END as object_type,
                NULL::timestamp as created_at,
                NULL::timestamp as modified_at
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
              AND n.nspname NOT LIKE 'pg_temp_%'
            ORDER BY n.nspname, p.proname
        """

    @property
    def definitions_query(self) -> str:
        return """
            SELECT
                p.oid as database_object_id,
                pg_get_functiondef(p.oid) as sql_code
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
              AND n.nspname NOT LIKE 'pg_temp_%'
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
                query AS query_text,
                calls AS execution_count,
                last_exec AS last_execution_time,
                total_exec_time / 1000.0 AS total_cpu_seconds,
                NULL::text AS object_name
            FROM pg_stat_statements
            WHERE query IS NOT NULL
              AND last_exec >= NOW() - INTERVAL '7 days'
              AND calls > 1
            ORDER BY calls DESC
            LIMIT 10000
        """

    @property
    def dynamic_sql_patterns(self) -> List[DynamicSQLPattern]:
        return [
            DynamicSQLPattern(
                pattern=r'\$\d+',
                description="Positional parameters ($1, $2, etc.)",
                examples=[
                    "SELECT * FROM table WHERE id = $1",
                    "INSERT INTO table VALUES ($1, $2, $3)"
                ]
            ),
            DynamicSQLPattern(
                pattern=r'EXECUTE\s+.*USING',
                description="Dynamic SQL with EXECUTE...USING",
                examples=[
                    "EXECUTE 'SELECT * FROM ' || table_name USING param1",
                    "EXECUTE format('DELETE FROM %I', table_name)"
                ]
            ),
            DynamicSQLPattern(
                pattern=r'format\s*\(',
                description="String formatting function",
                examples=[
                    "format('SELECT * FROM %I', table_name)",
                    "format('WHERE date > %L', date_value)"
                ]
            ),
            DynamicSQLPattern(
                pattern=r'\|\|',
                description="String concatenation operator",
                examples=[
                    "'SELECT * FROM ' || table_name",
                    "query_text || ' WHERE id = ' || id_value"
                ]
            ),
        ]

    # -------------------------------------------------------------------------
    # SQL Parsing Configuration
    # -------------------------------------------------------------------------

    @property
    def case_sensitive(self) -> bool:
        return True  # PostgreSQL is case-sensitive by default

    @property
    def identifier_quote_start(self) -> str:
        return '"'

    @property
    def identifier_quote_end(self) -> str:
        return '"'

    @property
    def string_quote(self) -> str:
        return "'"

    @property
    def statement_terminator(self) -> str:
        return ";"

    @property
    def batch_separator(self) -> Optional[str]:
        return None  # PostgreSQL doesn't have batch separators

    @property
    def line_comment(self) -> str:
        return "--"

    @property
    def block_comment_start(self) -> str:
        return "/*"

    @property
    def block_comment_end(self) -> str:
        return "*/"
