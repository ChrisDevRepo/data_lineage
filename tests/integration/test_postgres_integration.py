"""
Integration tests for PostgreSQL dialect with Docker container.

Tests the Postgres dialect implementation against a real PostgreSQL database
running in Docker with sample stored procedures and functions.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

import pytest
import subprocess
import time
import psycopg2
import pandas as pd
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from lineage_v3.config.dialect_config import SQLDialect
from lineage_v3.dialects import get_dialect


@pytest.fixture(scope="module")
def postgres_container():
    """Start Postgres container for testing."""
    print("\n🐳 Starting Postgres test container...")

    # Start container
    result = subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.skip(f"Failed to start Postgres container: {result.stderr}")

    # Wait for container to be healthy
    max_wait = 30
    for i in range(max_wait):
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "ps"],
            capture_output=True,
            text=True
        )
        if "healthy" in result.stdout:
            print("✅ Postgres container is healthy")
            break
        time.sleep(1)
    else:
        subprocess.run(["docker-compose", "-f", "docker-compose.test.yml", "down"])
        pytest.skip("Postgres container failed to become healthy")

    yield

    # Cleanup
    print("\n🧹 Cleaning up Postgres container...")
    subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"],
        capture_output=True
    )


@pytest.fixture(scope="module")
def postgres_connection(postgres_container):
    """Create connection to test Postgres database."""
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="lineage_test",
        user="testuser",
        password="testpass123"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    yield conn

    conn.close()


@pytest.fixture(scope="module")
def sample_database(postgres_connection):
    """Create sample database objects for testing."""
    cursor = postgres_connection.cursor()

    print("\n📝 Creating sample database objects...")

    # Create schemas
    cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS staging")

    # Create sample tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics.customers (
            customer_id SERIAL PRIMARY KEY,
            customer_name VARCHAR(100),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics.orders (
            order_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES analytics.customers(customer_id),
            order_date DATE,
            total_amount DECIMAL(10,2)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.raw_orders (
            id SERIAL PRIMARY KEY,
            customer_name VARCHAR(100),
            order_data JSONB
        )
    """)

    # Create sample function
    cursor.execute("""
        CREATE OR REPLACE FUNCTION analytics.get_customer_orders(p_customer_id INT)
        RETURNS TABLE(order_id INT, order_date DATE, total_amount DECIMAL) AS $$
        BEGIN
            RETURN QUERY
            SELECT o.order_id, o.order_date, o.total_amount
            FROM analytics.orders o
            WHERE o.customer_id = p_customer_id
            ORDER BY o.order_date DESC;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create sample procedure (Postgres 11+)
    cursor.execute("""
        CREATE OR REPLACE PROCEDURE analytics.update_customer_email(
            p_customer_id INT,
            p_new_email VARCHAR(100)
        ) AS $$
        BEGIN
            UPDATE analytics.customers
            SET email = p_new_email
            WHERE customer_id = p_customer_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create ETL function with dynamic SQL
    cursor.execute("""
        CREATE OR REPLACE FUNCTION staging.load_orders_dynamic(p_table_name TEXT)
        RETURNS VOID AS $$
        BEGIN
            -- This uses dynamic SQL (concatenation pattern)
            EXECUTE 'INSERT INTO ' || p_table_name || ' SELECT * FROM staging.raw_orders';
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create function with EXECUTE...USING pattern
    cursor.execute("""
        CREATE OR REPLACE FUNCTION analytics.get_orders_by_date(p_date DATE)
        RETURNS TABLE(order_id INT, total_amount DECIMAL) AS $$
        BEGIN
            RETURN QUERY EXECUTE
                'SELECT order_id, total_amount FROM analytics.orders WHERE order_date >= $1'
            USING p_date;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Enable pg_stat_statements extension
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
    except Exception as e:
        print(f"⚠️  Could not create pg_stat_statements: {e}")

    cursor.close()

    print("✅ Sample database objects created:")
    print("   - 2 schemas: analytics, staging")
    print("   - 3 tables: customers, orders, raw_orders")
    print("   - 4 functions/procedures")

    yield

    # Cleanup handled by container teardown


class TestPostgresIntegration:
    """Integration tests for Postgres dialect."""

    @pytest.fixture
    def postgres_dialect(self):
        """Get Postgres dialect instance."""
        return get_dialect(SQLDialect.POSTGRES)

    def test_postgres_connection(self, postgres_connection):
        """Test Postgres connection works."""
        cursor = postgres_connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()

        assert "PostgreSQL" in version
        print(f"\n✅ Connected to: {version.split(',')[0]}")

    def test_extract_postgres_objects(self, postgres_connection, sample_database, postgres_dialect):
        """Test extracting database objects using Postgres dialect."""
        query = postgres_dialect.objects_query

        print(f"\n📊 Running objects extraction query...")
        df = pd.read_sql_query(query, postgres_connection)

        print(f"✅ Extracted {len(df)} database objects")
        print(f"\n   Columns: {list(df.columns)}")
        print(f"\n   Sample objects:")
        print(df[['schema_name', 'object_name', 'object_type']].head(10).to_string(index=False))

        # Validate schema
        dialect_cols = [col.name for col in postgres_dialect.objects_schema]
        for col in dialect_cols:
            assert col in df.columns, f"Missing column: {col}"

        # Should have our sample objects
        assert len(df) >= 4  # At least our 4 functions/procedures

        # Should have analytics and staging schemas
        schemas = df['schema_name'].unique()
        assert 'analytics' in schemas
        assert 'staging' in schemas

        print(f"\n✅ Schema validation passed")

    def test_extract_postgres_definitions(self, postgres_connection, sample_database, postgres_dialect):
        """Test extracting object definitions (source code)."""
        query = postgres_dialect.definitions_query

        print(f"\n📝 Running definitions extraction query...")
        df = pd.read_sql_query(query, postgres_connection)

        print(f"✅ Extracted {len(df)} object definitions")

        # Validate schema
        assert 'database_object_id' in df.columns
        assert 'sql_code' in df.columns

        # Should have SQL code
        assert df['sql_code'].notna().all()

        # Show sample definition
        sample = df.iloc[0]
        print(f"\n   Sample definition (first 200 chars):")
        print(f"   Object ID: {sample['database_object_id']}")
        print(f"   SQL Code: {sample['sql_code'][:200]}...")

        print(f"\n✅ Definitions extraction successful")

    def test_postgres_schema_compatibility(self, postgres_connection, sample_database, postgres_dialect):
        """Test that extracted data matches dialect schema exactly."""
        query = postgres_dialect.objects_query
        df = pd.read_sql_query(query, postgres_connection)

        # Check column names match exactly
        expected_cols = [col.name for col in postgres_dialect.objects_schema]
        actual_cols = list(df.columns)

        assert actual_cols == expected_cols, f"Column mismatch: {actual_cols} != {expected_cols}"

        # Check required columns have no nulls
        schema_dict = {col.name: col for col in postgres_dialect.objects_schema}
        for col_name, col_schema in schema_dict.items():
            if col_schema.required:
                null_count = df[col_name].isna().sum()
                assert null_count == 0, f"Required column '{col_name}' has {null_count} nulls"

        print(f"\n✅ Schema compatibility validated")
        print(f"   All {len(expected_cols)} columns match")
        print(f"   All required columns have no nulls")

    def test_detect_dynamic_sql_patterns(self, postgres_connection, sample_database, postgres_dialect):
        """Test dynamic SQL pattern detection."""
        # Get definitions
        query = postgres_dialect.definitions_query
        df = pd.read_sql_query(query, postgres_connection)

        # Get patterns
        patterns = postgres_dialect.dynamic_sql_patterns

        print(f"\n🔍 Testing {len(patterns)} dynamic SQL patterns...")

        import re

        pattern_matches = {p.description: 0 for p in patterns}

        for sql_code in df['sql_code']:
            for pattern in patterns:
                if re.search(pattern.pattern, sql_code, re.IGNORECASE):
                    pattern_matches[pattern.description] += 1

        print(f"\n✅ Pattern detection results:")
        for desc, count in pattern_matches.items():
            print(f"   {desc}: {count} matches")

        # Should detect at least some dynamic SQL
        total_matches = sum(pattern_matches.values())
        assert total_matches > 0, "No dynamic SQL patterns detected"

    def test_query_logs_extraction(self, postgres_connection, sample_database, postgres_dialect):
        """Test query logs extraction (if pg_stat_statements available)."""
        cursor = postgres_connection.cursor()

        # Check if pg_stat_statements is available
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            )
        """)
        has_extension = cursor.fetchone()[0]

        if not has_extension:
            pytest.skip("pg_stat_statements extension not available")

        # Run some queries to populate pg_stat_statements
        cursor.execute("SELECT * FROM analytics.customers LIMIT 1")
        cursor.execute("SELECT * FROM analytics.orders LIMIT 1")

        # Extract query logs
        query = postgres_dialect.query_logs_extraction_query
        df = pd.read_sql_query(query, postgres_connection)

        print(f"\n📊 Extracted {len(df)} query log entries")

        # Validate schema
        log_cols = [col.name for col in postgres_dialect.query_logs_schema]
        for col in log_cols:
            assert col in df.columns, f"Missing query log column: {col}"

        cursor.close()

        print(f"✅ Query logs extraction successful")


class TestPostgresParsingConfig:
    """Test Postgres parsing configuration."""

    @pytest.fixture
    def postgres_dialect(self):
        """Get Postgres dialect instance."""
        return get_dialect(SQLDialect.POSTGRES)

    def test_case_sensitivity(self, postgres_dialect):
        """Test that Postgres is marked as case-sensitive."""
        assert postgres_dialect.case_sensitive is True
        print("\n✅ Postgres correctly marked as case-sensitive")

    def test_identifier_quotes(self, postgres_dialect):
        """Test that Postgres uses double quotes for identifiers."""
        assert postgres_dialect.identifier_quote_start == '"'
        assert postgres_dialect.identifier_quote_end == '"'
        print("\n✅ Postgres identifier quotes: \"\"")

    def test_no_batch_separator(self, postgres_dialect):
        """Test that Postgres has no batch separator."""
        assert postgres_dialect.batch_separator is None
        print("\n✅ Postgres has no batch separator (unlike T-SQL's GO)")


class TestPostgresVsTSQL:
    """Compare Postgres and T-SQL dialects."""

    def test_schema_consistency(self):
        """Test that both dialects have consistent schemas."""
        tsql = get_dialect(SQLDialect.TSQL)
        postgres = get_dialect(SQLDialect.POSTGRES)

        # Object schemas should match
        tsql_cols = [col.name for col in tsql.objects_schema]
        pg_cols = [col.name for col in postgres.objects_schema]

        assert tsql_cols == pg_cols

        print("\n✅ T-SQL and Postgres have consistent object schemas")

    def test_differences(self):
        """Test known differences between dialects."""
        tsql = get_dialect(SQLDialect.TSQL)
        postgres = get_dialect(SQLDialect.POSTGRES)

        # Case sensitivity differs
        assert tsql.case_sensitive != postgres.case_sensitive

        # Identifier quotes differ
        assert tsql.identifier_quote_start != postgres.identifier_quote_start

        # Batch separator differs
        assert tsql.batch_separator == "GO"
        assert postgres.batch_separator is None

        print("\n✅ Dialect differences correctly configured:")
        print(f"   T-SQL case sensitive: {tsql.case_sensitive}")
        print(f"   Postgres case sensitive: {postgres.case_sensitive}")
        print(f"   T-SQL quotes: {tsql.identifier_quote_start}{tsql.identifier_quote_end}")
        print(f"   Postgres quotes: {postgres.identifier_quote_start}{postgres.identifier_quote_end}")
