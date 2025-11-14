"""
Database-wide validation tests for parser results.

Converted from scripts/testing/check_parsing_results.py
Tests overall parsing statistics, confidence distribution, and test cases.
"""
import pytest
import duckdb
import json
from tests.integration.conftest import assert_success_rate_100_percent, assert_confidence_distribution_valid


class TestOverallStatistics:
    """Test overall parsing success statistics."""

    def test_all_sps_have_dependencies(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that 100% of SPs have dependencies (inputs or outputs)."""
        total_sps = db_connection.execute("""
            SELECT COUNT(*) FROM objects WHERE object_type = 'Stored Procedure'
        """).fetchone()[0]

        sps_with_deps = db_connection.execute("""
            SELECT COUNT(DISTINCT object_id)
            FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            AND (inputs IS NOT NULL OR outputs IS NOT NULL)
        """).fetchone()[0]

        assert_success_rate_100_percent(sps_with_deps, total_sps)

    def test_sps_with_inputs_percentage(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that majority of SPs have input dependencies."""
        total_sps = db_connection.execute("""
            SELECT COUNT(*) FROM objects WHERE object_type = 'Stored Procedure'
        """).fetchone()[0]

        sps_with_inputs = db_connection.execute("""
            SELECT COUNT(DISTINCT object_id)
            FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            AND inputs IS NOT NULL
        """).fetchone()[0]

        input_percentage = (sps_with_inputs / total_sps) * 100
        assert input_percentage > 80.0, f"Expected >80% SPs with inputs, got {input_percentage:.1f}%"

    def test_sps_with_outputs_percentage(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that majority of SPs have output dependencies."""
        total_sps = db_connection.execute("""
            SELECT COUNT(*) FROM objects WHERE object_type = 'Stored Procedure'
        """).fetchone()[0]

        sps_with_outputs = db_connection.execute("""
            SELECT COUNT(DISTINCT object_id)
            FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            AND outputs IS NOT NULL
        """).fetchone()[0]

        output_percentage = (sps_with_outputs / total_sps) * 100
        assert output_percentage > 50.0, f"Expected >50% SPs with outputs, got {output_percentage:.1f}%"


class TestConfidenceDistribution:
    """Test confidence score distribution."""

    def test_confidence_values_are_valid(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that only valid confidence values (0, 75, 85, 100) are present."""
        confidence_dist = db_connection.execute("""
            SELECT
                confidence,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
            FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            GROUP BY confidence
            ORDER BY confidence DESC
        """).fetchall()

        assert_confidence_distribution_valid(confidence_dist)

    def test_majority_have_perfect_confidence(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that at least 80% of SPs have confidence 100."""
        total_sps = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
        """).fetchone()[0]

        perfect_confidence = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            AND confidence = 100.0
        """).fetchone()[0]

        perfect_percentage = (perfect_confidence / total_sps) * 100
        assert perfect_percentage >= 80.0, (
            f"Expected >=80% SPs with confidence 100, got {perfect_percentage:.1f}%"
        )

    def test_no_zero_confidence_sps(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that zero SPs have confidence 0 (parse failures)."""
        zero_confidence = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            AND confidence = 0.0
        """).fetchone()[0]

        assert zero_confidence == 0, f"Expected 0 SPs with confidence 0, got {zero_confidence}"


class TestAverageDependencies:
    """Test average dependency counts."""

    def test_average_inputs_per_sp(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that average inputs per SP is within expected range (2-5)."""
        avg_inputs = db_connection.execute("""
            SELECT AVG(json_array_length(inputs))
            FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            AND inputs IS NOT NULL
        """).fetchone()[0]

        assert avg_inputs is not None, "Average inputs should not be None"
        assert 2.0 <= avg_inputs <= 5.0, f"Expected avg inputs 2-5, got {avg_inputs:.2f}"

    def test_average_outputs_per_sp(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that average outputs per SP is within expected range (1-3)."""
        avg_outputs = db_connection.execute("""
            SELECT AVG(json_array_length(outputs))
            FROM lineage_metadata
            WHERE object_id IN (SELECT object_id FROM objects WHERE object_type = 'Stored Procedure')
            AND outputs IS NOT NULL
        """).fetchone()[0]

        assert avg_outputs is not None, "Average outputs should not be None"
        assert 1.0 <= avg_outputs <= 3.0, f"Expected avg outputs 1-3, got {avg_outputs:.2f}"


class TestSpecificStoredProcedures:
    """Test specific known stored procedures."""

    @pytest.mark.parametrize("sp_name", [
        'spLoadFactLaborCostForEarnedValue_Post',
        'spLoadDimTemplateType'
    ])
    def test_sp_exists_and_parsed(self, db_connection: duckdb.DuckDBPyConnection, sp_name: str):
        """Test that specific SP exists and was parsed successfully."""
        result = db_connection.execute("""
            SELECT
                o.object_name,
                o.schema_name,
                lm.inputs,
                lm.outputs,
                lm.confidence
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name = ?
        """, [sp_name]).fetchone()

        assert result is not None, f"SP {sp_name} not found in database"

        name, schema, inputs_json, outputs_json, confidence = result
        assert confidence >= 75.0, f"SP {sp_name} has low confidence: {confidence}"

        # Parse JSON
        sources = json.loads(inputs_json) if inputs_json else []
        targets = json.loads(outputs_json) if outputs_json else []

        assert len(sources) > 0 or len(targets) > 0, (
            f"SP {sp_name} has no dependencies"
        )

    def test_spLoadFactLaborCostForEarnedValue_Post_has_expected_dependencies(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that spLoadFactLaborCostForEarnedValue_Post has expected sources."""
        sp_name = 'spLoadFactLaborCostForEarnedValue_Post'

        result = db_connection.execute("""
            SELECT
                o.object_name,
                o.schema_name,
                lm.inputs,
                lm.outputs,
                lm.confidence
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name = ?
        """, [sp_name]).fetchone()

        if result is None:
            pytest.skip(f"SP {sp_name} not found in test database")

        name, schema, inputs_json, outputs_json, confidence = result
        sources = json.loads(inputs_json) if inputs_json else []

        # Expected sources
        expected = [
            "CONSUMPTION_POWERBI.FactLaborCostForEarnedValue",
            "CONSUMPTION_ClinOpsFinance.CadenceBudget_LaborCost_PrimaContractUtilization_Junc"
        ]

        # Get actual source names
        actual_sources = []
        for obj_id in sources:
            obj = db_connection.execute(
                "SELECT schema_name, object_name FROM objects WHERE object_id = ?",
                [obj_id]
            ).fetchone()
            if obj:
                actual_sources.append(f"{obj[0]}.{obj[1]}")

        # Check if at least one expected source is found
        found_count = sum(1 for exp in expected if exp in actual_sources)
        assert found_count > 0, (
            f"Expected to find at least one of {expected}, "
            f"but got {actual_sources}"
        )


class TestTopStoredProcedures:
    """Test top SPs by dependency count."""

    def test_top_10_sps_by_dependency_count(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that we can retrieve top 10 SPs by dependency count."""
        top_sps = db_connection.execute("""
            SELECT
                o.schema_name || '.' || o.object_name as sp_full_name,
                json_array_length(COALESCE(lm.inputs, '[]')) as input_count,
                json_array_length(COALESCE(lm.outputs, '[]')) as output_count,
                lm.confidence
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_type = 'Stored Procedure'
            ORDER BY (json_array_length(COALESCE(lm.inputs, '[]')) + json_array_length(COALESCE(lm.outputs, '[]'))) DESC
            LIMIT 10
        """).fetchall()

        assert len(top_sps) == 10, f"Expected 10 top SPs, got {len(top_sps)}"

        for sp_name, inputs, outputs, conf in top_sps:
            total = inputs + outputs
            assert total > 0, f"Top SP {sp_name} should have dependencies"
            assert conf >= 75.0, f"Top SP {sp_name} should have confidence >= 75"

    def test_highest_dependency_sp_has_at_least_5_deps(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that SP with most dependencies has at least 5 total dependencies."""
        top_sp = db_connection.execute("""
            SELECT
                o.schema_name || '.' || o.object_name as sp_full_name,
                json_array_length(COALESCE(lm.inputs, '[]')) as input_count,
                json_array_length(COALESCE(lm.outputs, '[]')) as output_count
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_type = 'Stored Procedure'
            ORDER BY (json_array_length(COALESCE(lm.inputs, '[]')) + json_array_length(COALESCE(lm.outputs, '[]'))) DESC
            LIMIT 1
        """).fetchone()

        assert top_sp is not None, "Should have at least one SP"
        sp_name, inputs, outputs = top_sp
        total = inputs + outputs

        assert total >= 5, (
            f"Expected highest dependency SP to have >=5 deps, "
            f"{sp_name} has {total}"
        )
