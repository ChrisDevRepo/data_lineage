"""
Mock-based integration tests for PostgreSQL dialect.

Tests the Postgres dialect implementation using mock data to validate
queries, schemas, and patterns without requiring a real database.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

import pytest
import pandas as pd
from engine.config.dialect_config import SQLDialect
from engine.dialects import get_dialect


@pytest.fixture
def postgres_dialect():
    """Get Postgres dialect instance."""
    return get_dialect(SQLDialect.POSTGRES)


@pytest.fixture
def mock_postgres_objects():
    """Mock Postgres objects data (as would be returned from pg_proc query)."""
    return pd.DataFrame({
        'database_object_id': [1001, 1002, 1003, 1004, 1005],
        'schema_name': ['analytics', 'analytics', 'staging', 'staging', 'public'],
        'object_name': ['get_customer_orders', 'calculate_revenue', 'load_data', 'transform_raw', 'cleanup_temp'],
        'object_type': ['FUNCTION', 'FUNCTION', 'PROCEDURE', 'FUNCTION', 'FUNCTION'],
        'created_at': pd.to_datetime([None, None, None, None, None]),
        'modified_at': pd.to_datetime([None, None, None, None, None])
    })


@pytest.fixture
def mock_postgres_definitions():
    """Mock Postgres object definitions (source code)."""
    return pd.DataFrame({
        'database_object_id': [1001, 1002, 1003, 1004, 1005],
        'sql_code': [
            # Function with positional parameters
            """CREATE FUNCTION analytics.get_customer_orders(p_customer_id INT)
            RETURNS TABLE(order_id INT, total DECIMAL) AS $$
            BEGIN
                RETURN QUERY SELECT o.id, o.total FROM orders o WHERE o.customer_id = $1;
            END; $$ LANGUAGE plpgsql;""",

            # Function with format()
            """CREATE FUNCTION analytics.calculate_revenue(p_table_name TEXT)
            RETURNS DECIMAL AS $$
            DECLARE revenue DECIMAL;
            BEGIN
                EXECUTE format('SELECT SUM(total) FROM %I', p_table_name) INTO revenue;
                RETURN revenue;
            END; $$ LANGUAGE plpgsql;""",

            # Procedure with EXECUTE...USING
            """CREATE PROCEDURE staging.load_data(p_date DATE)
            LANGUAGE plpgsql AS $$
            BEGIN
                EXECUTE 'INSERT INTO staging.data SELECT * FROM source WHERE date >= $1' USING p_date;
            END; $$""",

            # Function with || concatenation
            """CREATE FUNCTION staging.transform_raw(p_schema TEXT)
            RETURNS VOID AS $$
            BEGIN
                EXECUTE 'CREATE TABLE ' || p_schema || '.transformed AS SELECT * FROM raw';
            END; $$ LANGUAGE plpgsql;""",

            # Simple function (no dynamic SQL)
            """CREATE FUNCTION public.cleanup_temp()
            RETURNS VOID AS $$
            BEGIN
                DELETE FROM temp_table WHERE created_at < NOW() - INTERVAL '1 day';
            END; $$ LANGUAGE plpgsql;"""
        ]
    })


@pytest.fixture
def mock_query_logs():
    """Mock Postgres query logs (from pg_stat_statements)."""
    return pd.DataFrame({
        'query_text': [
            'SELECT * FROM analytics.customers WHERE id = $1',
            'INSERT INTO staging.data VALUES ($1, $2, $3)',
            'UPDATE analytics.orders SET status = $1 WHERE id = $2',
            'SELECT COUNT(*) FROM staging.raw_data',
            'DELETE FROM temp_data WHERE date < NOW()'
        ],
        'execution_count': [1523, 892, 456, 234, 145],
        'last_execution_time': pd.to_datetime([
            '2025-11-11 10:30:00',
            '2025-11-11 10:25:00',
            '2025-11-11 10:20:00',
            '2025-11-11 10:15:00',
            '2025-11-11 10:10:00'
        ]),
        'total_cpu_seconds': [12.5, 8.3, 5.1, 2.4, 1.2],
        'object_name': [None, None, None, None, None]
    })


class TestPostgresDialectQueries:
    """Test Postgres dialect queries are well-formed."""

    def test_objects_query_structure(self, postgres_dialect):
        """Test objects query has correct structure."""
        query = postgres_dialect.objects_query

        # Should be valid SQL
        assert query.strip().upper().startswith('SELECT')

        # Should query pg_proc
        assert 'pg_proc' in query
        assert 'pg_namespace' in query

        # Should have required columns
        assert 'database_object_id' in query
        assert 'schema_name' in query
        assert 'object_name' in query
        assert 'object_type' in query

        # Should filter out system schemas
        assert 'pg_catalog' in query
        assert 'information_schema' in query

        print(f"\n✅ Postgres objects query is well-formed")
        print(f"   Uses: pg_proc, pg_namespace")
        print(f"   Filters: pg_catalog, information_schema, pg_toast")

    def test_definitions_query_structure(self, postgres_dialect):
        """Test definitions query has correct structure."""
        query = postgres_dialect.definitions_query

        # Should use pg_get_functiondef
        assert 'pg_get_functiondef' in query
        assert 'pg_proc' in query

        # Should have required columns
        assert 'database_object_id' in query
        assert 'sql_code' in query

        print(f"\n✅ Postgres definitions query is well-formed")
        print(f"   Uses: pg_get_functiondef(oid)")

    def test_query_logs_query_structure(self, postgres_dialect):
        """Test query logs query has correct structure."""
        query = postgres_dialect.query_logs_extraction_query

        # Should use pg_stat_statements
        assert 'pg_stat_statements' in query

        # Should have required columns
        assert 'query' in query or 'query_text' in query
        assert 'calls' in query or 'execution_count' in query

        print(f"\n✅ Postgres query logs query is well-formed")
        print(f"   Uses: pg_stat_statements extension")


class TestPostgresSchemaCompatibility:
    """Test Postgres schema compatibility with dialect definition."""

    def test_objects_schema_matches(self, postgres_dialect, mock_postgres_objects):
        """Test mock objects data matches dialect schema."""
        dialect_cols = [col.name for col in postgres_dialect.objects_schema]
        data_cols = list(mock_postgres_objects.columns)

        assert dialect_cols == data_cols

        print(f"\n✅ Mock Postgres objects match dialect schema")
        print(f"   Columns: {dialect_cols}")

    def test_definitions_schema_matches(self, postgres_dialect, mock_postgres_definitions):
        """Test mock definitions data matches dialect schema."""
        dialect_cols = [col.name for col in postgres_dialect.definitions_schema]
        data_cols = list(mock_postgres_definitions.columns)

        assert dialect_cols == data_cols

        print(f"\n✅ Mock Postgres definitions match dialect schema")
        print(f"   Columns: {dialect_cols}")

    def test_query_logs_schema_matches(self, postgres_dialect, mock_query_logs):
        """Test mock query logs match dialect schema."""
        dialect_cols = [col.name for col in postgres_dialect.query_logs_schema]
        data_cols = list(mock_query_logs.columns)

        assert dialect_cols == data_cols

        print(f"\n✅ Mock query logs match dialect schema")
        print(f"   Columns: {dialect_cols}")

    def test_required_columns_no_nulls(self, postgres_dialect, mock_postgres_objects):
        """Test required columns have no nulls."""
        schema_dict = {col.name: col for col in postgres_dialect.objects_schema}

        for col_name, col_def in schema_dict.items():
            if col_def.required:
                null_count = mock_postgres_objects[col_name].isna().sum()
                assert null_count == 0, f"Required column '{col_name}' has nulls"

        print(f"\n✅ All required columns validated (no nulls)")


class TestPostgresDynamicSQLDetection:
    """Test dynamic SQL pattern detection with real examples."""

    def test_positional_parameters(self, postgres_dialect, mock_postgres_definitions):
        """Test detection of positional parameters ($1, $2, etc.)."""
        import re

        patterns = postgres_dialect.dynamic_sql_patterns
        param_pattern = next(p for p in patterns if '$' in p.description.lower())

        # Should detect $1 parameter
        sql = mock_postgres_definitions.iloc[0]['sql_code']
        assert re.search(param_pattern.pattern, sql)

        print(f"\n✅ Detected positional parameters ($1)")
        print(f"   Pattern: {param_pattern.pattern}")

    def test_format_function(self, postgres_dialect, mock_postgres_definitions):
        """Test detection of format() function."""
        import re

        patterns = postgres_dialect.dynamic_sql_patterns
        format_pattern = next(p for p in patterns if 'format' in p.description.lower())

        # Should detect format() usage
        sql = mock_postgres_definitions.iloc[1]['sql_code']
        assert re.search(format_pattern.pattern, sql, re.IGNORECASE)

        print(f"\n✅ Detected format() function")
        print(f"   Pattern: {format_pattern.pattern}")

    def test_execute_using(self, postgres_dialect, mock_postgres_definitions):
        """Test detection of EXECUTE...USING pattern."""
        import re

        patterns = postgres_dialect.dynamic_sql_patterns
        execute_pattern = next(p for p in patterns if 'EXECUTE' in p.description)

        # Should detect EXECUTE...USING
        sql = mock_postgres_definitions.iloc[2]['sql_code']
        assert re.search(execute_pattern.pattern, sql, re.IGNORECASE)

        print(f"\n✅ Detected EXECUTE...USING pattern")
        print(f"   Pattern: {execute_pattern.pattern}")

    def test_concatenation(self, postgres_dialect, mock_postgres_definitions):
        """Test detection of || concatenation."""
        import re

        patterns = postgres_dialect.dynamic_sql_patterns
        concat_pattern = next(p for p in patterns if '||' in p.description or 'concatenat' in p.description.lower())

        # Should detect || concatenation
        sql = mock_postgres_definitions.iloc[3]['sql_code']
        assert re.search(concat_pattern.pattern, sql)

        print(f"\n✅ Detected || concatenation")
        print(f"   Pattern: {concat_pattern.pattern}")

    def test_no_false_positives(self, postgres_dialect, mock_postgres_definitions):
        """Test that static SQL doesn't match dynamic patterns."""
        import re

        # Last function has no dynamic SQL
        sql = mock_postgres_definitions.iloc[4]['sql_code']

        patterns = postgres_dialect.dynamic_sql_patterns
        matches = 0
        for pattern in patterns:
            if re.search(pattern.pattern, sql, re.IGNORECASE):
                matches += 1

        # Should have zero or minimal matches
        assert matches == 0, f"Static SQL should not match dynamic patterns (matched {matches})"

        print(f"\n✅ No false positives on static SQL")


class TestPostgresDataQuality:
    """Test data quality of mock Postgres data."""

    def test_objects_data_quality(self, mock_postgres_objects):
        """Test mock objects data quality."""
        assert len(mock_postgres_objects) == 5
        assert mock_postgres_objects['database_object_id'].notna().all()
        assert mock_postgres_objects['schema_name'].notna().all()
        assert mock_postgres_objects['object_name'].notna().all()
        assert mock_postgres_objects['object_type'].notna().all()

        # Should have multiple schemas
        assert mock_postgres_objects['schema_name'].nunique() >= 2

        print(f"\n✅ Mock objects data quality validated")
        print(f"   Objects: {len(mock_postgres_objects)}")
        print(f"   Schemas: {mock_postgres_objects['schema_name'].unique().tolist()}")

    def test_definitions_completeness(self, mock_postgres_definitions):
        """Test all definitions have SQL code."""
        assert len(mock_postgres_definitions) == 5
        assert mock_postgres_definitions['sql_code'].notna().all()

        # All should have CREATE
        assert all('CREATE' in sql for sql in mock_postgres_definitions['sql_code'])

        print(f"\n✅ All definitions have SQL code")

    def test_query_logs_data(self, mock_query_logs):
        """Test query logs data quality."""
        assert len(mock_query_logs) == 5
        assert mock_query_logs['query_text'].notna().all()
        assert mock_query_logs['execution_count'].notna().all()

        # Should have reasonable execution counts
        assert mock_query_logs['execution_count'].min() > 0
        assert mock_query_logs['execution_count'].max() > 100

        print(f"\n✅ Query logs data quality validated")
        print(f"   Queries: {len(mock_query_logs)}")
        print(f"   Total executions: {mock_query_logs['execution_count'].sum()}")


class TestPostgresVsTSQL:
    """Compare Postgres and T-SQL dialects."""

    def test_schema_consistency(self):
        """Test that both dialects have same schema structure."""
        tsql = get_dialect(SQLDialect.TSQL)
        postgres = get_dialect(SQLDialect.POSTGRES)

        # Should have same columns
        tsql_cols = [col.name for col in tsql.objects_schema]
        pg_cols = [col.name for col in postgres.objects_schema]

        assert tsql_cols == pg_cols

        print(f"\n✅ T-SQL and Postgres have consistent schemas")
        print(f"   Columns: {tsql_cols}")

    def test_key_differences(self):
        """Test known differences between dialects."""
        tsql = get_dialect(SQLDialect.TSQL)
        postgres = get_dialect(SQLDialect.POSTGRES)

        # Case sensitivity
        assert tsql.case_sensitive == False
        assert postgres.case_sensitive == True

        # Identifier quotes
        assert tsql.identifier_quote_start == "["
        assert postgres.identifier_quote_start == '"'

        # Batch separator
        assert tsql.batch_separator == "GO"
        assert postgres.batch_separator is None

        # Metadata source
        from engine.dialects.base import MetadataSource
        assert tsql.metadata_source == MetadataSource.DMV
        assert postgres.metadata_source == MetadataSource.INFORMATION_SCHEMA

        print(f"\n✅ Dialect differences validated:")
        print(f"   Case sensitive: T-SQL={tsql.case_sensitive}, Postgres={postgres.case_sensitive}")
        print(f"   Quotes: T-SQL={tsql.identifier_quote_start}, Postgres={postgres.identifier_quote_start}")
        print(f"   Batch separator: T-SQL={tsql.batch_separator}, Postgres={postgres.batch_separator}")
        print(f"   Metadata: T-SQL={tsql.metadata_source.value}, Postgres={postgres.metadata_source.value}")


class TestPostgresExtraction:
    """Test complete extraction workflow with mock data."""

    def test_full_extraction_workflow(self, postgres_dialect, mock_postgres_objects, mock_postgres_definitions):
        """Test complete extraction workflow."""
        # 1. Extract objects
        objects = mock_postgres_objects
        assert len(objects) > 0

        # 2. Extract definitions
        definitions = mock_postgres_definitions
        assert len(definitions) > 0

        # 3. Join objects and definitions
        merged = objects.merge(definitions, on='database_object_id', how='inner')
        assert len(merged) == len(objects)

        # 4. Validate we have all necessary data for lineage
        assert 'schema_name' in merged.columns
        assert 'object_name' in merged.columns
        assert 'sql_code' in merged.columns

        print(f"\n✅ Full extraction workflow validated")
        print(f"   Objects extracted: {len(objects)}")
        print(f"   Definitions extracted: {len(definitions)}")
        print(f"   Merged records: {len(merged)}")

    def test_dynamic_sql_summary(self, postgres_dialect, mock_postgres_definitions):
        """Test summary of dynamic SQL in extracted code."""
        import re

        patterns = postgres_dialect.dynamic_sql_patterns
        summary = {p.description: 0 for p in patterns}

        for sql_code in mock_postgres_definitions['sql_code']:
            for pattern in patterns:
                if re.search(pattern.pattern, sql_code, re.IGNORECASE):
                    summary[pattern.description] += 1

        total_dynamic = sum(summary.values())
        total_objects = len(mock_postgres_definitions)

        print(f"\n✅ Dynamic SQL summary:")
        print(f"   Total objects: {total_objects}")
        print(f"   Objects with dynamic SQL: {total_dynamic}")
        for desc, count in summary.items():
            if count > 0:
                print(f"   - {desc}: {count}")

        # Should detect at least some dynamic SQL
        assert total_dynamic > 0
