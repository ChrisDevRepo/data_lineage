"""
Unit tests for SQLGlot Parser

Tests the SQLGlot-based SQL parsing logic that extracts table lineage from DDL.

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-26
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core import DuckDBWorkspace
from lineage_v3.parsers import SQLGlotParser


@pytest.fixture
def workspace():
    """Create temporary in-memory DuckDB workspace for testing."""
    ws = DuckDBWorkspace(workspace_path=':memory:')
    yield ws
    ws.close()


@pytest.fixture
def populated_workspace(workspace):
    """Create workspace with sample test data."""
    # Create sample objects
    workspace.conn.execute("""
        INSERT INTO objects VALUES
        (1, 'dbo', 'SP_Test', 'Stored Procedure', '2025-10-26 00:00:00'),
        (2, 'dbo', 'SourceTable', 'Table', '2025-10-26 00:00:00'),
        (3, 'CONSUMPTION_FINANCE', 'TargetTable', 'Table', '2025-10-26 00:00:00'),
        (4, 'dbo', 'JoinTable', 'Table', '2025-10-26 00:00:00')
    """)

    # Create DDL with simple SELECT
    workspace.conn.execute("""
        INSERT INTO definitions VALUES
        (1, 'CREATE PROCEDURE SP_Test AS SELECT * FROM dbo.SourceTable')
    """)

    return workspace


class TestSQLGlotParser:
    """Test suite for SQLGlotParser class."""

    def test_extract_simple_from_clause(self, populated_workspace):
        """Test extraction of simple FROM clause."""
        parser = SQLGlotParser(populated_workspace)
        result = parser.parse_object(object_id=1)

        # Should extract SourceTable as input
        assert result['confidence'] == 0.85
        assert result['source'] == 'parser'
        assert 2 in result['inputs']  # SourceTable object_id

    def test_extract_join_clause(self, workspace):
        """Test extraction of JOIN clauses."""
        # Create SP with JOIN
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Join', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'Table1', 'Table', '2025-10-26 00:00:00'),
            (3, 'dbo', 'Table2', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Join AS
             SELECT * FROM dbo.Table1
             JOIN dbo.Table2 ON Table1.id = Table2.id')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should extract both tables
        assert 2 in result['inputs']
        assert 3 in result['inputs']
        assert len(result['inputs']) == 2

    def test_extract_insert_into(self, workspace):
        """Test extraction of INSERT INTO target table."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Insert', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'SourceTable', 'Table', '2025-10-26 00:00:00'),
            (3, 'dbo', 'TargetTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Insert AS
             INSERT INTO dbo.TargetTable
             SELECT * FROM dbo.SourceTable')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should extract SourceTable as input and TargetTable as output
        assert 2 in result['inputs']
        assert 3 in result['outputs']

    def test_extract_update_statement(self, workspace):
        """Test extraction of UPDATE target table."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Update', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'TargetTable', 'Table', '2025-10-26 00:00:00'),
            (3, 'dbo', 'SourceTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Update AS
             UPDATE dbo.TargetTable
             SET col = val
             FROM dbo.SourceTable
             WHERE TargetTable.id = SourceTable.id')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should extract both tables
        assert 2 in result['outputs']  # UPDATE target
        assert 3 in result['inputs']   # FROM source

    def test_extract_merge_statement(self, workspace):
        """Test extraction of MERGE target and source tables."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Merge', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'TargetTable', 'Table', '2025-10-26 00:00:00'),
            (3, 'dbo', 'SourceTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Merge AS
             MERGE INTO dbo.TargetTable AS t
             USING dbo.SourceTable AS s
             ON t.id = s.id
             WHEN MATCHED THEN UPDATE SET t.val = s.val')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should extract both tables
        assert 2 in result['outputs']  # MERGE target
        assert 3 in result['inputs']   # USING source

    def test_extract_with_schema_qualifier(self, workspace):
        """Test extraction of schema-qualified table names."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Schema', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'CONSUMPTION_FINANCE', 'DimCustomers', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Schema AS
             SELECT * FROM CONSUMPTION_FINANCE.DimCustomers')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should resolve schema-qualified name
        assert 2 in result['inputs']

    def test_extract_default_dbo_schema(self, workspace):
        """Test that unqualified table names default to dbo schema."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Unqualified', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'MyTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Unqualified AS
             SELECT * FROM MyTable')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should resolve to dbo.MyTable
        assert 2 in result['inputs']

    def test_filter_system_tables(self, workspace):
        """Test that system tables are excluded."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_System', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'UserTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_System AS
             SELECT o.name
             FROM sys.objects o
             JOIN dbo.UserTable u ON o.object_id = u.id')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should only include UserTable, not sys.objects
        assert 2 in result['inputs']
        assert len(result['inputs']) == 1

    def test_filter_temp_tables(self, workspace):
        """Test that temp tables are excluded."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Temp', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'RealTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Temp AS
             CREATE TABLE #temp (id INT);
             INSERT INTO #temp SELECT id FROM dbo.RealTable;
             SELECT * FROM #temp')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should only include RealTable, not #temp
        assert 2 in result['inputs']

    def test_handle_parse_error(self, workspace):
        """Test handling of malformed SQL."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Invalid', 'Stored Procedure', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Invalid AS
             THIS IS NOT VALID SQL;;;')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should return zero confidence but not crash
        assert result['confidence'] == 0.0
        assert result['parse_error'] is not None

    def test_handle_missing_ddl(self, workspace):
        """Test handling of objects with no DDL definition."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_NoDDL', 'Stored Procedure', '2025-10-26 00:00:00')
        """)

        # No definition inserted

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should return zero confidence
        assert result['confidence'] == 0.0
        assert 'No DDL definition found' in result['parse_error']

    def test_handle_unresolved_table_names(self, workspace):
        """Test that unresolved table names are excluded from results."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_External', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'LocalTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_External AS
             SELECT * FROM dbo.LocalTable
             UNION ALL
             SELECT * FROM dbo.NonExistentTable')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should only include LocalTable
        assert 2 in result['inputs']
        assert len(result['inputs']) == 1

    def test_case_insensitive_resolution(self, workspace):
        """Test case-insensitive table name resolution."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Case', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'DBO', 'MyTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_Case AS
             SELECT * FROM dbo.mytable')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should resolve despite case differences
        assert 2 in result['inputs']

    def test_parse_batch(self, workspace):
        """Test batch parsing of multiple objects."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_1', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'SP_2', 'Stored Procedure', '2025-10-26 00:00:00'),
            (3, 'dbo', 'Table1', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_1 AS SELECT * FROM dbo.Table1'),
            (2, 'CREATE PROCEDURE SP_2 AS SELECT * FROM dbo.Table1')
        """)

        parser = SQLGlotParser(workspace)
        results = parser.parse_batch([1, 2])

        # Should return results for both objects
        assert len(results) == 2
        assert results[0]['object_id'] == 1
        assert results[1]['object_id'] == 2

    def test_extract_cte(self, workspace):
        """Test extraction of tables from CTEs."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_CTE', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'SourceTable', 'Table', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO definitions VALUES
            (1, 'CREATE PROCEDURE SP_CTE AS
             WITH cte AS (SELECT * FROM dbo.SourceTable)
             SELECT * FROM cte')
        """)

        parser = SQLGlotParser(workspace)
        result = parser.parse_object(object_id=1)

        # Should extract SourceTable from CTE
        assert 2 in result['inputs']

    def test_get_parse_statistics(self, workspace):
        """Test parser statistics retrieval."""
        # Create successful and failed parses
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Success', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'SP_Failed', 'Stored Procedure', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO lineage_metadata VALUES
            (1, 'parser', 0.85, '[3]', '[4]', '2025-10-26 00:00:00'),
            (2, 'parser', 0.0, '[]', '[]', '2025-10-26 00:00:00')
        """)

        parser = SQLGlotParser(workspace)
        stats = parser.get_parse_statistics()

        assert stats['total_parsed'] == 2
        assert stats['successful_parses'] == 1
        assert stats['failed_parses'] == 1
        assert stats['success_rate'] == 50.0


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
