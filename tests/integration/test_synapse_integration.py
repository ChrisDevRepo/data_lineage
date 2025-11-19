"""
Integration tests for T-SQL dialect with real Synapse data.

Tests the T-SQL dialect implementation against actual Synapse parquet snapshots
to ensure schema compatibility and query validation.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

import pytest
import pandas as pd
import glob
from pathlib import Path
from engine.config.dialect_config import SQLDialect
from engine.dialects import get_dialect


class TestSynapseIntegration:
    """Integration tests with real Synapse parquet data."""

    @pytest.fixture
    def synapse_parquet_files(self):
        """Find Synapse parquet files in temp directory."""
        files = glob.glob('./temp/*.parquet')
        if not files:
            pytest.skip("No Synapse parquet files found in ./temp/")
        return files

    @pytest.fixture
    def synapse_data(self, synapse_parquet_files):
        """Load Synapse objects data from parquet."""
        # Load first parquet file as sample
        df = pd.read_parquet(synapse_parquet_files[0])

        # Check if this is the expected Synapse DMV format
        # If it's a different format (e.g., command_text only), skip these tests
        expected_cols = {'object_id', 'schema_name', 'object_name', 'object_type'}
        actual_cols = set(df.columns)

        if not expected_cols.issubset(actual_cols):
            pytest.skip(
                f"Parquet data has different format. "
                f"Expected columns: {expected_cols}, "
                f"Actual columns: {actual_cols}. "
                f"These tests require direct Synapse DMV export format."
            )

        return df

    @pytest.fixture
    def tsql_dialect(self):
        """Get T-SQL dialect instance."""
        return get_dialect(SQLDialect.TSQL)

    def test_synapse_parquet_files_exist(self, synapse_parquet_files):
        """Test that Synapse parquet files exist."""
        assert len(synapse_parquet_files) > 0
        print(f"\n✅ Found {len(synapse_parquet_files)} Synapse parquet files")

    def test_synapse_data_loaded(self, synapse_data):
        """Test that Synapse data loads successfully."""
        assert synapse_data is not None
        assert len(synapse_data) > 0
        print(f"\n✅ Loaded {len(synapse_data)} Synapse objects")

    def test_synapse_schema_columns(self, synapse_data):
        """Test that Synapse data has expected columns (old schema)."""
        expected_cols = ['object_id', 'schema_name', 'object_name', 'object_type', 'create_date', 'modify_date']
        actual_cols = list(synapse_data.columns)

        assert actual_cols == expected_cols
        print(f"\n✅ Synapse schema has expected columns: {actual_cols}")

    def test_synapse_object_types(self, synapse_data):
        """Test that Synapse data contains expected object types."""
        object_types = synapse_data['object_type'].unique()

        # Should have stored procedures
        assert any('Procedure' in str(t) for t in object_types)

        print(f"\n✅ Found object types: {list(object_types)}")

    def test_tsql_schema_compatibility(self, tsql_dialect, synapse_data):
        """Test that T-SQL dialect schema is compatible with Synapse data."""
        dialect_schema = tsql_dialect.objects_schema
        dialect_cols = [col.name for col in dialect_schema]

        # Map old schema to new schema
        column_mapping = {
            'object_id': 'database_object_id',
            'create_date': 'created_at',
            'modify_date': 'modified_at'
        }

        # Rename Synapse columns to new schema
        renamed_data = synapse_data.rename(columns=column_mapping)

        # Check all dialect columns exist after renaming
        for col_name in dialect_cols:
            assert col_name in renamed_data.columns, f"Missing column: {col_name}"

        print(f"\n✅ Synapse data compatible with T-SQL dialect schema")
        print(f"   Old → New mapping: {column_mapping}")

    def test_synapse_data_quality(self, synapse_data):
        """Test basic data quality of Synapse parquet."""
        # Should have no nulls in required columns
        assert synapse_data['object_id'].notna().all()
        assert synapse_data['schema_name'].notna().all()
        assert synapse_data['object_name'].notna().all()
        assert synapse_data['object_type'].notna().all()

        # Should have reasonable number of objects
        assert len(synapse_data) > 100  # Production should have many objects

        print(f"\n✅ Data quality checks passed")
        print(f"   Total objects: {len(synapse_data)}")
        print(f"   Schemas: {synapse_data['schema_name'].nunique()}")
        print(f"   Object types: {synapse_data['object_type'].nunique()}")

    def test_synapse_stored_procedures(self, synapse_data):
        """Test that we have stored procedures in the data."""
        procs = synapse_data[synapse_data['object_type'].str.contains('Procedure', case=False, na=False)]

        assert len(procs) > 0
        print(f"\n✅ Found {len(procs)} stored procedures")

        # Show sample procedures
        sample_procs = procs.head(5)[['schema_name', 'object_name']]
        print(f"\n   Sample procedures:")
        for _, row in sample_procs.iterrows():
            print(f"   - {row['schema_name']}.{row['object_name']}")

    def test_tsql_query_structure(self, tsql_dialect):
        """Test that T-SQL objects query has correct structure."""
        query = tsql_dialect.objects_query

        # Should be valid SQL
        assert query.strip().upper().startswith('SELECT')

        # Should have required column aliases
        assert 'database_object_id' in query
        assert 'schema_name' in query
        assert 'object_name' in query
        assert 'object_type' in query
        assert 'created_at' in query
        assert 'modified_at' in query

        # Should query sys.objects
        assert 'sys.objects' in query

        print(f"\n✅ T-SQL objects query is well-formed")
        print(f"\n   Query preview:")
        print(f"   {query.strip()[:200]}...")

    def test_backward_compatibility_mapping(self, synapse_data, tsql_dialect):
        """Test complete backward compatibility workflow."""
        # 1. Load old schema data
        old_data = synapse_data.copy()

        # 2. Apply column mapping for backward compatibility
        column_mapping = {
            'object_id': 'database_object_id',
            'create_date': 'created_at',
            'modify_date': 'modified_at'
        }
        new_data = old_data.rename(columns=column_mapping)

        # 3. Validate against dialect schema
        dialect_schema = {col.name: col for col in tsql_dialect.objects_schema}

        for col_name in dialect_schema.keys():
            assert col_name in new_data.columns, f"Missing: {col_name}"

            # Check data types are compatible
            col_schema = dialect_schema[col_name]
            if col_schema.required:
                assert new_data[col_name].notna().all(), f"Required column has nulls: {col_name}"

        print(f"\n✅ Backward compatibility mapping works end-to-end")
        print(f"   Old columns: {list(old_data.columns)}")
        print(f"   New columns: {list(new_data.columns)}")


class TestTSQLQueryLogs:
    """Test T-SQL query logs functionality."""

    @pytest.fixture
    def tsql_dialect(self):
        """Get T-SQL dialect instance."""
        return get_dialect(SQLDialect.TSQL)

    def test_query_logs_query_structure(self, tsql_dialect):
        """Test that query logs extraction query is valid."""
        query = tsql_dialect.query_logs_extraction_query

        assert query is not None
        assert 'sys.dm_exec_query_stats' in query
        assert 'sys.dm_exec_sql_text' in query

        # Should have required output columns
        assert 'query_text' in query
        assert 'execution_count' in query

        print(f"\n✅ Query logs extraction query is well-formed")

    def test_dynamic_sql_pattern_validation(self, tsql_dialect):
        """Test dynamic SQL patterns against real examples."""
        patterns = tsql_dialect.dynamic_sql_patterns

        # Test patterns against sample SQL
        test_cases = [
            ("SELECT * FROM @table_name", True, "Should match @parameters"),
            ("EXEC sp_executesql @sql", True, "Should match sp_executesql"),
            ("EXECUTE('DROP TABLE ' + @table)", True, "Should match EXECUTE()"),
            ("SELECT * FROM users WHERE id = 1", False, "Should not match static SQL"),
        ]

        import re

        for sql, should_match, description in test_cases:
            matched = False
            for pattern in patterns:
                if re.search(pattern.pattern, sql, re.IGNORECASE):
                    matched = True
                    break

            assert matched == should_match, f"Failed: {description} - SQL: {sql}"

        print(f"\n✅ Dynamic SQL patterns validated against {len(test_cases)} test cases")
