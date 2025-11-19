"""
Unit tests for SQL dialect implementations.

Tests dialect classes for:
- Correct property values
- Valid SQL queries
- Schema definitions
- Dynamic SQL patterns

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

import pytest
from engine.config.dialect_config import SQLDialect
from engine.dialects import (
    get_dialect,
    is_dialect_implemented,
    list_implemented_dialects,
    TSQLDialect,
    PostgresDialect,
    MetadataSource
)


class TestTSQLDialect:
    """Test T-SQL dialect implementation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.dialect = TSQLDialect()

    def test_basic_properties(self):
        """Test basic dialect properties."""
        assert self.dialect.name == "tsql"
        assert self.dialect.display_name == "Microsoft SQL Server / Azure Synapse"
        assert self.dialect.sqlglot_dialect == "tsql"

    def test_metadata_source(self):
        """Test metadata source is DMV."""
        assert self.dialect.metadata_source == MetadataSource.DMV

    def test_objects_query_valid_sql(self):
        """Test objects query contains expected keywords."""
        query = self.dialect.objects_query
        assert "SELECT" in query.upper()
        assert "sys.objects" in query
        assert "database_object_id" in query
        assert "schema_name" in query
        assert "object_name" in query
        assert "object_type" in query

    def test_definitions_query_valid_sql(self):
        """Test definitions query contains expected keywords."""
        query = self.dialect.definitions_query
        assert "SELECT" in query.upper()
        assert "sys.sql_modules" in query
        assert "database_object_id" in query
        assert "sql_code" in query

    def test_objects_schema(self):
        """Test objects schema has required columns."""
        schema = self.dialect.objects_schema
        column_names = [col.name for col in schema]

        assert "database_object_id" in column_names
        assert "schema_name" in column_names
        assert "object_name" in column_names
        assert "object_type" in column_names
        assert "created_at" in column_names
        assert "modified_at" in column_names

    def test_definitions_schema(self):
        """Test definitions schema has required columns."""
        schema = self.dialect.definitions_schema
        column_names = [col.name for col in schema]

        assert "database_object_id" in column_names
        assert "sql_code" in column_names

    def test_query_logs_enabled(self):
        """Test query logs are enabled."""
        assert self.dialect.query_logs_enabled is True

    def test_query_logs_extraction_query(self):
        """Test query logs query is valid."""
        query = self.dialect.query_logs_extraction_query
        assert query is not None
        assert "sys.dm_exec_query_stats" in query
        assert "query_text" in query
        assert "execution_count" in query

    def test_query_logs_schema(self):
        """Test query logs schema has required columns."""
        schema = self.dialect.query_logs_schema
        column_names = [col.name for col in schema]

        assert "query_text" in column_names
        assert "execution_count" in column_names
        assert "last_execution_time" in column_names
        assert "total_cpu_seconds" in column_names
        assert "object_name" in column_names

    def test_dynamic_sql_patterns(self):
        """Test dynamic SQL patterns are defined."""
        patterns = self.dialect.dynamic_sql_patterns
        assert len(patterns) > 0

        # Check pattern structure
        for pattern in patterns:
            assert hasattr(pattern, 'pattern')
            assert hasattr(pattern, 'description')
            assert hasattr(pattern, 'examples')
            assert len(pattern.examples) > 0

    def test_dynamic_sql_pattern_coverage(self):
        """Test specific T-SQL patterns are covered."""
        patterns = self.dialect.dynamic_sql_patterns
        pattern_strings = [p.pattern for p in patterns]

        # Should cover @parameters
        assert any('@' in p for p in pattern_strings)

        # Should cover sp_executesql
        assert any('sp_executesql' in p for p in pattern_strings)

        # Should cover EXECUTE()
        assert any('EXECUTE' in p for p in pattern_strings)

    def test_parsing_configuration(self):
        """Test SQL parsing configuration."""
        assert self.dialect.case_sensitive is False
        assert self.dialect.identifier_quote_start == "["
        assert self.dialect.identifier_quote_end == "]"
        assert self.dialect.string_quote == "'"
        assert self.dialect.statement_terminator == ";"
        assert self.dialect.batch_separator == "GO"
        assert self.dialect.line_comment == "--"
        assert self.dialect.block_comment_start == "/*"
        assert self.dialect.block_comment_end == "*/"

    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.dialect)
        assert "TSQLDialect" in repr_str
        assert "Microsoft SQL Server" in repr_str


class TestPostgresDialect:
    """Test PostgreSQL dialect implementation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.dialect = PostgresDialect()

    def test_basic_properties(self):
        """Test basic dialect properties."""
        assert self.dialect.name == "postgres"
        assert self.dialect.display_name == "PostgreSQL"
        assert self.dialect.sqlglot_dialect == "postgres"

    def test_metadata_source(self):
        """Test metadata source is INFORMATION_SCHEMA."""
        assert self.dialect.metadata_source == MetadataSource.INFORMATION_SCHEMA

    def test_objects_query_valid_sql(self):
        """Test objects query contains expected keywords."""
        query = self.dialect.objects_query
        assert "SELECT" in query.upper()
        assert "pg_proc" in query
        assert "database_object_id" in query
        assert "schema_name" in query
        assert "object_name" in query

    def test_definitions_query_valid_sql(self):
        """Test definitions query contains expected keywords."""
        query = self.dialect.definitions_query
        assert "SELECT" in query.upper()
        assert "pg_get_functiondef" in query
        assert "database_object_id" in query
        assert "sql_code" in query

    def test_query_logs_extraction_query(self):
        """Test query logs query uses pg_stat_statements."""
        query = self.dialect.query_logs_extraction_query
        assert query is not None
        assert "pg_stat_statements" in query
        assert "query_text" in query or "query AS query_text" in query

    def test_dynamic_sql_patterns(self):
        """Test Postgres-specific patterns."""
        patterns = self.dialect.dynamic_sql_patterns
        pattern_strings = [p.pattern for p in patterns]

        # Should cover $1, $2 positional parameters
        assert any('$' in p for p in pattern_strings)

        # Should cover format() function
        assert any('format' in p for p in pattern_strings)

        # Should cover || concatenation (escaped as \|\|)
        assert any('|' in p for p in pattern_strings)

    def test_parsing_configuration(self):
        """Test Postgres parsing configuration."""
        assert self.dialect.case_sensitive is True  # Different from T-SQL!
        assert self.dialect.identifier_quote_start == '"'
        assert self.dialect.identifier_quote_end == '"'
        assert self.dialect.batch_separator is None  # No GO in Postgres


class TestDialectRegistry:
    """Test dialect registry and factory."""

    def test_get_tsql_dialect(self):
        """Test getting T-SQL dialect from registry."""
        dialect = get_dialect(SQLDialect.TSQL)
        assert isinstance(dialect, TSQLDialect)
        assert dialect.name == "tsql"

    def test_get_postgres_dialect(self):
        """Test getting Postgres dialect from registry."""
        dialect = get_dialect(SQLDialect.POSTGRES)
        assert isinstance(dialect, PostgresDialect)
        assert dialect.name == "postgres"

    def test_dialect_caching(self):
        """Test that dialect instances are cached."""
        dialect1 = get_dialect(SQLDialect.TSQL)
        dialect2 = get_dialect(SQLDialect.TSQL)
        assert dialect1 is dialect2  # Same instance

    def test_is_dialect_implemented(self):
        """Test checking if dialect is implemented."""
        assert is_dialect_implemented(SQLDialect.TSQL) is True
        assert is_dialect_implemented(SQLDialect.POSTGRES) is True
        assert is_dialect_implemented(SQLDialect.FABRIC) is False  # Not yet

    def test_list_implemented_dialects(self):
        """Test listing implemented dialects."""
        implemented = list_implemented_dialects()
        assert SQLDialect.TSQL in implemented
        assert SQLDialect.POSTGRES in implemented
        assert len(implemented) == 2  # Only TSQL and Postgres so far

    def test_unimplemented_dialect_raises_error(self):
        """Test that unimplemented dialects raise NotImplementedError."""
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            get_dialect(SQLDialect.FABRIC)


class TestSchemaValidation:
    """Test schema definitions for consistency."""

    def test_all_dialects_have_consistent_schemas(self):
        """Test that all dialects return consistent schemas."""
        tsql = TSQLDialect()
        postgres = PostgresDialect()

        # Objects schema should have same columns
        tsql_cols = [col.name for col in tsql.objects_schema]
        pg_cols = [col.name for col in postgres.objects_schema]
        assert tsql_cols == pg_cols

        # Definitions schema should have same columns
        tsql_def_cols = [col.name for col in tsql.definitions_schema]
        pg_def_cols = [col.name for col in postgres.definitions_schema]
        assert tsql_def_cols == pg_def_cols

        # Query logs schema should have same columns
        tsql_log_cols = [col.name for col in tsql.query_logs_schema]
        pg_log_cols = [col.name for col in postgres.query_logs_schema]
        assert tsql_log_cols == pg_log_cols

    def test_required_columns_marked_correctly(self):
        """Test that required columns are properly marked."""
        dialect = TSQLDialect()

        # database_object_id should always be required
        obj_schema = {col.name: col for col in dialect.objects_schema}
        assert obj_schema["database_object_id"].required is True

        # created_at/modified_at may be optional
        assert obj_schema["created_at"].required is False
        assert obj_schema["modified_at"].required is False
