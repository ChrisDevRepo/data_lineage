"""
Unit tests for Gap Detector

Tests the gap detection logic that identifies objects with missing dependencies.

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-26
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core import DuckDBWorkspace, GapDetector


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
        (1, 'dbo', 'SP_WithGap', 'Stored Procedure', '2025-10-26 00:00:00'),
        (2, 'dbo', 'SP_Parsed', 'Stored Procedure', '2025-10-26 00:00:00'),
        (3, 'dbo', 'Table1', 'Table', '2025-10-26 00:00:00'),
        (4, 'dbo', 'View1', 'View', '2025-10-26 00:00:00')
    """)

    # Create sample definitions
    workspace.conn.execute("""
        INSERT INTO definitions VALUES
        (1, 'CREATE PROCEDURE SP_WithGap AS SELECT * FROM Table1'),
        (2, 'CREATE PROCEDURE SP_Parsed AS SELECT * FROM Table1')
    """)

    # Create metadata for only one SP (the other has a gap)
    workspace.conn.execute("""
        INSERT INTO lineage_metadata VALUES
        (2, 'dmv', 0.85, '[]', '[]', '2025-10-26 00:00:00')
    """)

    return workspace


class TestGapDetector:
    """Test suite for GapDetector class."""

    def test_detect_gaps_finds_unparsed_objects(self, populated_workspace):
        """Test that detect_gaps finds objects with no metadata entries."""
        detector = GapDetector(populated_workspace)
        gaps = detector.detect_gaps()

        # Should find SP_WithGap (object_id=1)
        assert len(gaps) == 1
        assert gaps[0]['object_id'] == 1
        assert gaps[0]['object_name'] == 'SP_WithGap'

    def test_detect_gaps_filters_by_object_type(self, populated_workspace):
        """Test that detect_gaps respects object_type filter."""
        detector = GapDetector(populated_workspace)

        # Find all gaps (not just stored procedures)
        all_gaps = detector.detect_gaps(object_type=None)

        # Should find more than just SPs
        # (Tables and Views have no metadata either, but default filter excludes them)
        assert len(all_gaps) >= 1

    def test_detect_gaps_finds_empty_dependencies(self, workspace):
        """Test that detect_gaps finds objects with metadata but no dependencies."""
        # Create object with empty dependencies
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Empty', 'Stored Procedure', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO lineage_metadata VALUES
            (1, 'dmv', 0.85, '[]', '[]', '2025-10-26 00:00:00')
        """)

        detector = GapDetector(workspace)
        gaps = detector.detect_gaps()

        # Should find SP_Empty
        assert len(gaps) == 1
        assert gaps[0]['object_id'] == 1

    def test_detect_low_confidence_gaps(self, workspace):
        """Test detection of low-confidence objects."""
        # Create objects with varying confidence
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_LowConf', 'Stored Procedure', '2025-10-26 00:00:00'),
            (2, 'dbo', 'SP_HighConf', 'Stored Procedure', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO lineage_metadata VALUES
            (1, 'ai', 0.7, '[3]', '[4]', '2025-10-26 00:00:00'),
            (2, 'dmv', 1.0, '[5]', '[6]', '2025-10-26 00:00:00')
        """)

        detector = GapDetector(workspace)
        low_conf = detector.detect_low_confidence_gaps(confidence_threshold=0.85)

        # Should only find SP_LowConf
        assert len(low_conf) == 1
        assert low_conf[0]['object_id'] == 1
        assert low_conf[0]['confidence'] == 0.7

    def test_get_gap_statistics(self, populated_workspace):
        """Test gap statistics calculation."""
        detector = GapDetector(populated_workspace)
        stats = detector.get_gap_statistics()

        # Verify statistics structure
        assert 'total_objects' in stats
        assert 'parsed_objects' in stats
        assert 'unparsed_objects' in stats
        assert 'empty_dependencies' in stats
        assert 'total_gaps' in stats
        assert 'gap_percentage' in stats
        assert 'by_object_type' in stats

        # Verify counts
        assert stats['total_objects'] == 4  # 2 SPs, 1 Table, 1 View
        assert stats['parsed_objects'] == 1  # Only SP_Parsed
        assert stats['total_gaps'] >= 1  # At least SP_WithGap

    def test_should_parse_never_parsed(self, workspace):
        """Test should_parse returns True for objects never parsed."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_New', 'Stored Procedure', '2025-10-26 00:00:00')
        """)

        detector = GapDetector(workspace)
        should_parse = detector.should_parse(object_id=1)

        assert should_parse is True

    def test_should_parse_force_reparse(self, workspace):
        """Test should_parse respects force_reparse flag."""
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Old', 'Stored Procedure', '2025-10-26 00:00:00')
        """)

        workspace.conn.execute("""
            INSERT INTO lineage_metadata VALUES
            (1, 'dmv', 1.0, '[2]', '[3]', '2025-10-26 00:00:00')
        """)

        detector = GapDetector(workspace)

        # Should not parse (already parsed and up-to-date)
        assert detector.should_parse(object_id=1) is False

        # Should parse when forced
        assert detector.should_parse(object_id=1, force_reparse=True) is True

    def test_should_parse_modified_object(self, workspace):
        """Test should_parse detects modified objects."""
        # Create object modified after last parse
        workspace.conn.execute("""
            INSERT INTO objects VALUES
            (1, 'dbo', 'SP_Modified', 'Stored Procedure', '2025-10-26 12:00:00')
        """)

        # Metadata shows earlier parse time
        workspace.conn.execute("""
            INSERT INTO lineage_metadata VALUES
            (1, 'dmv', 1.0, '[2]', '[3]', '2025-10-26 06:00:00')
        """)

        detector = GapDetector(workspace)
        should_parse = detector.should_parse(object_id=1)

        assert should_parse is True

    def test_should_parse_nonexistent_object(self, workspace):
        """Test should_parse handles nonexistent objects gracefully."""
        detector = GapDetector(workspace)
        should_parse = detector.should_parse(object_id=999)

        assert should_parse is False

    def test_gap_statistics_by_object_type(self, populated_workspace):
        """Test gap statistics breakdown by object type."""
        detector = GapDetector(populated_workspace)
        stats = detector.get_gap_statistics()

        by_type = stats['by_object_type']

        # Should have breakdown for each object type
        type_names = [row['object_type'] for row in by_type]
        assert 'Stored Procedure' in type_names
        assert 'Table' in type_names
        assert 'View' in type_names

        # Verify counts for Stored Procedures
        sp_stats = next(row for row in by_type if row['object_type'] == 'Stored Procedure')
        assert sp_stats['total'] == 2  # SP_WithGap and SP_Parsed
        assert sp_stats['parsed'] == 1  # Only SP_Parsed has metadata
        assert sp_stats['unparsed'] == 1  # SP_WithGap


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
