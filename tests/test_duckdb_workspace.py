#!/usr/bin/env python3
"""
Unit tests for DuckDB Workspace Manager

Tests core functionality:
- Connection management
- Schema initialization
- Parquet loading
- Incremental load logic
- Query interface

Author: Vibecoding Team
Version: 3.0.0
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import json

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core.duckdb_workspace import DuckDBWorkspace


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp()
    workspace_path = Path(temp_dir) / "test_workspace.duckdb"

    yield workspace_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_parquet_data(tmp_path):
    """Create sample Parquet files for testing."""
    parquet_dir = tmp_path / "parquet_snapshots"
    parquet_dir.mkdir()

    # Sample objects data
    objects_df = pd.DataFrame({
        'object_id': [1001, 1002, 1003, 1004],
        'schema_name': ['dbo', 'dbo', 'CONSUMPTION_FINANCE', 'CONSUMPTION_FINANCE'],
        'object_name': ['Table1', 'Table2', 'DimCustomers', 'FactSales'],
        'type_code': ['U', 'U', 'U', 'U'],
        'object_type': ['Table', 'Table', 'Table', 'Table'],
        'create_date': [datetime(2024, 1, 1)] * 4,
        'modify_date': [datetime(2024, 1, 1), datetime(2024, 1, 15),
                       datetime(2024, 2, 1), datetime(2024, 2, 1)],
        'full_type_description': ['USER_TABLE'] * 4
    })
    objects_df.to_parquet(parquet_dir / 'objects.parquet', index=False)

    # Sample dependencies data
    deps_df = pd.DataFrame({
        'referencing_object_id': [1004, 1004],
        'referenced_object_id': [1001, 1003],
        'referenced_schema_name': ['dbo', 'CONSUMPTION_FINANCE'],
        'referenced_entity_name': ['Table1', 'DimCustomers'],
        'referenced_database_name': [None, None],
        'is_ambiguous': [False, False],
        'is_schema_bound_reference': [False, False],
        'is_caller_dependent': [False, False],
        'referencing_class_desc': ['OBJECT_OR_COLUMN'] * 2,
        'referenced_class_desc': ['OBJECT_OR_COLUMN'] * 2,
        'referencing_type': ['USER_TABLE'] * 2,
        'referenced_type': ['USER_TABLE'] * 2
    })
    deps_df.to_parquet(parquet_dir / 'dependencies.parquet', index=False)

    # Sample definitions data
    defs_df = pd.DataFrame({
        'object_id': [1001, 1002],
        'object_name': ['Table1', 'Table2'],
        'schema_name': ['dbo', 'dbo'],
        'object_type': ['USER_TABLE', 'USER_TABLE'],
        'definition': ['CREATE TABLE Table1 (id INT)', 'CREATE TABLE Table2 (id INT)'],
        'uses_ansi_nulls': [True, True],
        'uses_quoted_identifier': [True, True],
        'is_schema_bound': [False, False],
        'create_date': [datetime(2024, 1, 1), datetime(2024, 1, 1)],
        'modify_date': [datetime(2024, 1, 1), datetime(2024, 1, 15)]
    })
    defs_df.to_parquet(parquet_dir / 'definitions.parquet', index=False)

    return parquet_dir


class TestDuckDBWorkspace:
    """Test DuckDB Workspace Manager."""

    def test_initialization(self, temp_workspace):
        """Test workspace initialization."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        assert workspace.workspace_path == temp_workspace
        assert workspace.connection is None
        assert not workspace.read_only

    def test_connect_creates_file(self, temp_workspace):
        """Test that connect creates database file."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()

        assert temp_workspace.exists()
        assert workspace.connection is not None

        workspace.disconnect()

    def test_schema_initialization(self, temp_workspace):
        """Test that schema tables are created."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()

        # Check that metadata table exists
        result = workspace.query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name IN ('lineage_metadata', 'lineage_results')
        """)

        table_names = [row[0] for row in result]
        assert 'lineage_metadata' in table_names
        assert 'lineage_results' in table_names

        workspace.disconnect()

    def test_load_parquet(self, temp_workspace, sample_parquet_data):
        """Test loading Parquet files."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()

        row_counts = workspace.load_parquet(sample_parquet_data, full_refresh=True)

        # Verify row counts
        assert row_counts['objects'] == 4
        assert row_counts['dependencies'] == 2
        assert row_counts['definitions'] == 2
        assert row_counts['query_logs'] == 0  # Optional file not created

        # Verify data loaded correctly
        objects = workspace.query("SELECT COUNT(*) FROM objects")
        assert objects[0][0] == 4

        workspace.disconnect()

    def test_get_objects_to_parse_full_refresh(self, temp_workspace, sample_parquet_data):
        """Test getting objects to parse in full refresh mode."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()
        workspace.load_parquet(sample_parquet_data, full_refresh=True)

        objects = workspace.get_objects_to_parse(full_refresh=True)

        assert len(objects) == 4
        assert objects[0]['object_id'] == 1003  # Sorted by schema, name
        assert objects[0]['schema_name'] == 'CONSUMPTION_FINANCE'

        workspace.disconnect()

    def test_get_objects_to_parse_incremental(self, temp_workspace, sample_parquet_data):
        """Test incremental load logic."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()
        workspace.load_parquet(sample_parquet_data, full_refresh=True)

        # First parse - should return all objects
        objects = workspace.get_objects_to_parse(full_refresh=False)
        assert len(objects) == 4

        # Mark one object as parsed with high confidence
        workspace.update_metadata(
            object_id=1001,
            modify_date=datetime(2024, 1, 1),
            primary_source='dmv',
            confidence=1.0,
            inputs=[],
            outputs=[]
        )

        # Second parse - should skip object 1001
        objects = workspace.get_objects_to_parse(full_refresh=False)
        assert len(objects) == 3
        assert 1001 not in [obj['object_id'] for obj in objects]

        workspace.disconnect()

    def test_get_dmv_dependencies(self, temp_workspace, sample_parquet_data):
        """Test retrieving DMV dependencies."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()
        workspace.load_parquet(sample_parquet_data, full_refresh=True)

        deps = workspace.get_dmv_dependencies()

        assert len(deps) == 2
        assert deps[0]['source'] == 'dmv'
        assert deps[0]['confidence'] == 1.0
        assert deps[0]['referencing_object_id'] == 1004
        assert deps[0]['referenced_object_id'] in [1001, 1003]

        workspace.disconnect()

    def test_get_object_definition(self, temp_workspace, sample_parquet_data):
        """Test retrieving object definition."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()
        workspace.load_parquet(sample_parquet_data, full_refresh=True)

        definition = workspace.get_object_definition(1001)

        assert definition is not None
        assert 'CREATE TABLE Table1' in definition

        # Test non-existent object
        definition = workspace.get_object_definition(9999)
        assert definition is None

        workspace.disconnect()

    def test_resolve_table_names_to_ids(self, temp_workspace, sample_parquet_data):
        """Test resolving table names to object IDs."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()
        workspace.load_parquet(sample_parquet_data, full_refresh=True)

        table_names = [
            'dbo.Table1',
            'CONSUMPTION_FINANCE.DimCustomers',
            'dbo.NonExistent'
        ]

        result = workspace.resolve_table_names_to_ids(table_names)

        assert result['dbo.Table1'] == 1001
        assert result['CONSUMPTION_FINANCE.DimCustomers'] == 1003
        assert result['dbo.NonExistent'] is None

        workspace.disconnect()

    def test_update_metadata(self, temp_workspace, sample_parquet_data):
        """Test updating lineage metadata."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()
        workspace.load_parquet(sample_parquet_data, full_refresh=True)

        # Update metadata
        workspace.update_metadata(
            object_id=1001,
            modify_date=datetime(2024, 1, 1),
            primary_source='dmv',
            confidence=1.0,
            inputs=[1002, 1003],
            outputs=[1004]
        )

        # Verify metadata stored
        result = workspace.query(
            "SELECT object_id, primary_source, confidence, inputs, outputs FROM lineage_metadata WHERE object_id = ?",
            [1001]
        )

        assert len(result) == 1
        assert result[0][0] == 1001  # object_id
        assert result[0][1] == 'dmv'  # primary_source
        assert result[0][2] == 1.0  # confidence

        # Verify JSON arrays
        inputs = json.loads(result[0][3])
        outputs = json.loads(result[0][4])
        assert inputs == [1002, 1003]
        assert outputs == [1004]

        workspace.disconnect()

    def test_get_stats(self, temp_workspace, sample_parquet_data):
        """Test getting workspace statistics."""
        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()
        workspace.load_parquet(sample_parquet_data, full_refresh=True)

        # Add some metadata
        workspace.update_metadata(
            object_id=1001,
            modify_date=datetime(2024, 1, 1),
            primary_source='dmv',
            confidence=1.0,
            inputs=[],
            outputs=[]
        )

        stats = workspace.get_stats()

        assert stats['objects_count'] == 4
        assert stats['dependencies_count'] == 2
        assert stats['definitions_count'] == 2
        assert stats['lineage_metadata_count'] == 1
        assert 'source_breakdown' in stats

        workspace.disconnect()

    def test_context_manager(self, temp_workspace, sample_parquet_data):
        """Test using workspace as context manager."""
        with DuckDBWorkspace(workspace_path=str(temp_workspace)) as workspace:
            workspace.load_parquet(sample_parquet_data, full_refresh=True)
            objects = workspace.get_objects_to_parse(full_refresh=True)
            assert len(objects) == 4

        # Connection should be closed after context
        assert workspace.connection is None

    def test_missing_required_parquet(self, temp_workspace, tmp_path):
        """Test error handling for missing required Parquet files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        workspace = DuckDBWorkspace(workspace_path=str(temp_workspace))
        workspace.connect()

        with pytest.raises(FileNotFoundError, match="Required file not found"):
            workspace.load_parquet(empty_dir)

        workspace.disconnect()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
