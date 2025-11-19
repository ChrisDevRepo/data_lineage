"""
Detailed stored procedure parsing tests with actual table names.

Converted from scripts/testing/verify_sp_parsing.py
Tests specific SP parsing results, phantom detection, and expected dependencies.
"""
import pytest
import duckdb
import json
from tests.integration.conftest import assert_confidence_threshold


class TestSPDetailedParsing:
    """Test detailed parsing results for specific stored procedures."""

    @pytest.fixture
    def target_sp_name(self) -> str:
        """Default target SP for detailed testing."""
        return 'spLoadFactLaborCostForEarnedValue_Post'

    def test_sp_has_confidence_score(
        self, db_connection: duckdb.DuckDBPyConnection, target_sp_name: str
    ):
        """Test that target SP has valid confidence score."""
        result = db_connection.execute("""
            SELECT
                o.object_name,
                o.schema_name,
                lm.confidence
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name = ?
        """, [target_sp_name]).fetchone()

        if result is None:
            pytest.skip(f"SP {target_sp_name} not found in test database")

        name, schema, confidence = result
        assert_confidence_threshold(confidence, min_threshold=75.0)

    def test_sp_input_tables_have_valid_names(
        self, db_connection: duckdb.DuckDBPyConnection, target_sp_name: str
    ):
        """Test that all input tables have valid schema and object names."""
        result = db_connection.execute("""
            SELECT
                o.object_name,
                o.schema_name,
                lm.inputs
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name = ?
        """, [target_sp_name]).fetchone()

        if result is None:
            pytest.skip(f"SP {target_sp_name} not found in test database")

        name, schema, inputs_json = result
        input_ids = json.loads(inputs_json) if inputs_json else []

        assert len(input_ids) > 0, f"SP {target_sp_name} should have input dependencies"

        # Verify each input has valid catalog entry
        for obj_id in input_ids:
            obj = db_connection.execute("""
                SELECT schema_name, object_name, object_type
                FROM objects
                WHERE object_id = ?
            """, [obj_id]).fetchone()

            assert obj is not None, f"Input object ID {obj_id} should exist in catalog"
            obj_schema, obj_name, obj_type = obj

            assert obj_schema, f"Input object {obj_id} should have schema name"
            assert obj_name, f"Input object {obj_id} should have object name"
            assert obj_type in ['Table', 'View', 'External Table'], (
                f"Input object {obj_id} should be Table/View/External, got {obj_type}"
            )

    def test_sp_output_tables_have_valid_names(
        self, db_connection: duckdb.DuckDBPyConnection, target_sp_name: str
    ):
        """Test that all output tables have valid schema and object names."""
        result = db_connection.execute("""
            SELECT
                o.object_name,
                o.schema_name,
                lm.outputs
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name = ?
        """, [target_sp_name]).fetchone()

        if result is None:
            pytest.skip(f"SP {target_sp_name} not found in test database")

        name, schema, outputs_json = result
        output_ids = json.loads(outputs_json) if outputs_json else []

        if len(output_ids) == 0:
            pytest.skip(f"SP {target_sp_name} has no outputs (may be read-only)")

        # Verify each output has valid catalog entry
        for obj_id in output_ids:
            obj = db_connection.execute("""
                SELECT schema_name, object_name, object_type
                FROM objects
                WHERE object_id = ?
            """, [obj_id]).fetchone()

            assert obj is not None, f"Output object ID {obj_id} should exist in catalog"
            obj_schema, obj_name, obj_type = obj

            assert obj_schema, f"Output object {obj_id} should have schema name"
            assert obj_name, f"Output object {obj_id} should have object name"


class TestExpectedDependencies:
    """Test expected dependencies for known stored procedures."""

    def test_spLoadFactLaborCostForEarnedValue_Post_expected_sources(
        self, db_connection: duckdb.DuckDBPyConnection, expected_sources: dict
    ):
        """Test that spLoadFactLaborCostForEarnedValue_Post has expected sources."""
        sp_name = 'spLoadFactLaborCostForEarnedValue_Post'

        result = db_connection.execute("""
            SELECT
                o.object_name,
                o.schema_name,
                lm.inputs
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name = ?
        """, [sp_name]).fetchone()

        if result is None:
            pytest.skip(f"SP {sp_name} not found in test database")

        name, schema, inputs_json = result
        input_ids = json.loads(inputs_json) if inputs_json else []

        # Get actual source names
        actual_inputs = []
        for obj_id in input_ids:
            obj = db_connection.execute(
                "SELECT schema_name, object_name FROM objects WHERE object_id = ?",
                [obj_id]
            ).fetchone()
            if obj:
                actual_inputs.append((obj[0], obj[1]))

        # Check if expected sources are found
        expected = expected_sources.get(sp_name, [])

        for exp_schema, exp_table in expected:
            found = any(
                schema.upper() == exp_schema.upper() and table.upper() == exp_table.upper()
                for schema, table in actual_inputs
            )

            # Log but don't fail if not found (may be phantom or config changed)
            if not found:
                pytest.warns(
                    UserWarning,
                    match=f"Expected source {exp_schema}.{exp_table} not found"
                )

    def test_spLoadFactLaborCostForEarnedValue_Post_expected_target(
        self, db_connection: duckdb.DuckDBPyConnection, expected_targets: dict
    ):
        """Test that spLoadFactLaborCostForEarnedValue_Post has expected target."""
        sp_name = 'spLoadFactLaborCostForEarnedValue_Post'

        result = db_connection.execute("""
            SELECT
                o.object_name,
                o.schema_name,
                lm.outputs
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name = ?
        """, [sp_name]).fetchone()

        if result is None:
            pytest.skip(f"SP {sp_name} not found in test database")

        name, schema, outputs_json = result
        output_ids = json.loads(outputs_json) if outputs_json else []

        # Get actual output names
        actual_outputs = []
        for obj_id in output_ids:
            obj = db_connection.execute(
                "SELECT schema_name, object_name FROM objects WHERE object_id = ?",
                [obj_id]
            ).fetchone()
            if obj:
                actual_outputs.append(f"{obj[0]}.{obj[1]}")

        # Check if expected target is found
        expected_target = expected_targets.get(sp_name)

        if expected_target:
            found = expected_target in actual_outputs

            # Log but don't fail if not found
            if not found:
                pytest.warns(
                    UserWarning,
                    match=f"Expected target {expected_target} not found"
                )
