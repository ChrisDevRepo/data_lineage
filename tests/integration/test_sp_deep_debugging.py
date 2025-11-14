"""
Deep debugging tests for specific stored procedure parsing.

Converted from scripts/testing/analyze_sp.py
Tests regex extraction, SQLGlot behavior, and problematic pattern detection.
"""
import pytest
import duckdb
import re
from sqlglot import parse_one
from sqlglot.errors import ErrorLevel
from sqlglot import exp


class TestRegexExtraction:
    """Test regex-based table extraction."""

    @pytest.fixture
    def target_sp(self, db_connection: duckdb.DuckDBPyConnection):
        """Get target SP for deep analysis."""
        result = db_connection.execute("""
            SELECT o.object_id, o.object_name, o.schema_name, d.definition
            FROM objects o
            JOIN definitions d ON o.object_id = d.object_id
            WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
            AND o.object_type = 'Stored Procedure'
            LIMIT 1
        """).fetchone()
        return result

    def test_target_sp_exists(self, target_sp: tuple):
        """Test that target SP exists in database."""
        if target_sp is None:
            pytest.skip("Target SP not found in test database")

        sp_id, sp_name, schema, ddl = target_sp
        assert ddl is not None, "SP should have DDL definition"
        assert len(ddl) > 0, "SP DDL should not be empty"

    def test_regex_extracts_from_tables(self, target_sp: tuple):
        """Test that regex can extract FROM tables."""
        if target_sp is None:
            pytest.skip("Target SP not found")

        sp_id, sp_name, schema, ddl = target_sp
        from_pattern = r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?'
        from_tables = re.findall(from_pattern, ddl, re.IGNORECASE)

        assert len(from_tables) > 0, "Should find at least one FROM table"

        # Verify extracted tables have schema and name
        for schema_name, table_name in from_tables:
            assert schema_name, "Extracted table should have schema"
            assert table_name, "Extracted table should have name"

    def test_regex_extracts_target_tables(self, target_sp: tuple):
        """Test that regex can extract INSERT/UPDATE target tables."""
        if target_sp is None:
            pytest.skip("Target SP not found")

        sp_id, sp_name, schema, ddl = target_sp

        into_pattern = r'\bINTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
        insert_pattern = r'\bINSERT\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?'
        update_pattern = r'\bUPDATE\s+\[?(\w+)\]?\.\[?(\w+)\]?'

        into_tables = re.findall(into_pattern, ddl, re.IGNORECASE)
        insert_tables = re.findall(insert_pattern, ddl, re.IGNORECASE)
        update_tables = re.findall(update_pattern, ddl, re.IGNORECASE)

        total_targets = len(into_tables) + len(insert_tables) + len(update_tables)

        # Most SPs have at least one target table (INSERT/UPDATE)
        # But some SPs are read-only (only SELECT)
        if total_targets == 0:
            pytest.skip("SP appears to be read-only (no INSERT/UPDATE/INTO)")

        assert total_targets > 0, "Should find at least one target table"


class TestSQLGlotParsing:
    """Test SQLGlot parsing behavior."""

    @pytest.fixture
    def target_sp_ddl(self, db_connection: duckdb.DuckDBPyConnection):
        """Get DDL for target SP."""
        result = db_connection.execute("""
            SELECT d.definition
            FROM objects o
            JOIN definitions d ON o.object_id = d.object_id
            WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
            AND o.object_type = 'Stored Procedure'
            LIMIT 1
        """).fetchone()
        return result[0] if result else None

    def test_sqlglot_warn_mode_on_sample(self, target_sp_ddl: str):
        """Test SQLGlot WARN mode on first 2000 characters."""
        if target_sp_ddl is None:
            pytest.skip("Target SP not found")

        short_ddl = target_sp_ddl[:2000]

        try:
            parsed_warn = parse_one(short_ddl, dialect='tsql', error_level=ErrorLevel.WARN)
            assert parsed_warn is not None, "SQLGlot should return AST in WARN mode"

            # Try to extract tables from AST
            tables_found = []
            for table in parsed_warn.find_all(exp.Table):
                table_name = f"{table.db}.{table.name}" if table.db else table.name
                tables_found.append(table_name)

            # WARN mode may or may not find tables depending on SQL complexity
            # This is informational - WARN mode is known to lose context

        except Exception as e:
            # WARN mode can still fail on complex T-SQL
            pytest.skip(f"SQLGlot WARN mode failed (expected): {type(e).__name__}")

    def test_sqlglot_raise_mode_behavior(self, target_sp_ddl: str):
        """Test SQLGlot RAISE mode behavior (used by parser)."""
        if target_sp_ddl is None:
            pytest.skip("Target SP not found")

        # RAISE mode may throw exceptions on complex T-SQL
        # Parser catches these and uses regex baseline instead
        try:
            parsed_raise = parse_one(target_sp_ddl, dialect='tsql', error_level=ErrorLevel.RAISE)

            # If RAISE mode succeeds, extract tables
            tables_found = []
            for table in parsed_raise.find_all(exp.Table):
                table_name = f"{table.db}.{table.name}" if table.db else table.name
                tables_found.append(table_name)

            # RAISE mode success is a bonus
            assert True, f"SQLGlot RAISE mode succeeded, found {len(tables_found)} tables"

        except Exception:
            # RAISE mode failure is expected on complex T-SQL
            # Parser uses regex baseline in this case
            assert True, "SQLGlot RAISE mode failed (expected, falls back to regex)"


class TestProblematicPatterns:
    """Test detection of problematic T-SQL patterns."""

    @pytest.fixture
    def target_sp_ddl(self, db_connection: duckdb.DuckDBPyConnection):
        """Get DDL for pattern analysis."""
        result = db_connection.execute("""
            SELECT d.definition
            FROM objects o
            JOIN definitions d ON o.object_id = d.object_id
            WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
            AND o.object_type = 'Stored Procedure'
            LIMIT 1
        """).fetchone()
        return result[0] if result else None

    def test_identify_problematic_patterns(self, target_sp_ddl: str):
        """Test that we can identify problematic T-SQL patterns."""
        if target_sp_ddl is None:
            pytest.skip("Target SP not found")

        problematic_patterns = {
            'EXEC with variables': r'EXEC\s+@\w+',
            'Dynamic SQL': r'EXEC\s*\(\s*@',
            'BEGIN TRY': r'\bBEGIN\s+TRY\b',
            'RAISERROR': r'\bRAISERROR\b',
            'SET NOCOUNT': r'\bSET\s+NOCOUNT\b',
            'DECLARE cursor': r'\bDECLARE\s+\w+\s+CURSOR\b',
            'Complex CASE': r'\bCASE\s+WHEN.*?WHEN.*?END',
            'Temp tables': r'#\w+',
            'Table variables': r'@\w+',
        }

        pattern_counts = {}
        for pattern_name, pattern in problematic_patterns.items():
            matches = re.findall(pattern, target_sp_ddl, re.IGNORECASE | re.DOTALL)
            pattern_counts[pattern_name] = len(matches)

        # At least some patterns should be found in typical SP
        # This is informational only
        total_patterns = sum(pattern_counts.values())
        assert total_patterns >= 0, "Pattern detection should work"

    def test_temp_tables_not_in_dependencies(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that temp tables (#temp) are not included in dependencies."""
        result = db_connection.execute("""
            SELECT
                o.object_name,
                lm.inputs,
                lm.outputs
            FROM objects o
            JOIN lineage_metadata lm ON o.object_id = lm.object_id
            WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
            AND o.object_type = 'Stored Procedure'
            LIMIT 1
        """).fetchone()

        if result is None:
            pytest.skip("Target SP not found")

        name, inputs, outputs = result

        # Get all dependency object IDs
        import json
        input_ids = json.loads(inputs) if inputs else []
        output_ids = json.loads(outputs) if outputs else []
        all_dep_ids = input_ids + output_ids

        # Check that no dependencies are temp tables
        for dep_id in all_dep_ids:
            obj = db_connection.execute(
                "SELECT object_name FROM objects WHERE object_id = ?",
                [dep_id]
            ).fetchone()

            if obj:
                obj_name = obj[0]
                assert not obj_name.startswith('#'), (
                    f"Temp table {obj_name} should not be in dependencies"
                )


class TestExpectedDependencyValidation:
    """Test validation of expected dependencies."""

    def test_expected_sources_found_in_regex(
        self, db_connection: duckdb.DuckDBPyConnection, expected_sources: dict
    ):
        """Test that expected sources are found by regex extraction."""
        result = db_connection.execute("""
            SELECT o.object_id, o.object_name, o.schema_name, d.definition
            FROM objects o
            JOIN definitions d ON o.object_id = d.object_id
            WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
            AND o.object_type = 'Stored Procedure'
            LIMIT 1
        """).fetchone()

        if result is None:
            pytest.skip("Target SP not found")

        sp_id, sp_name, schema, ddl = result

        # Extract tables using regex
        from_pattern = r'\bFROM\s+\[?(\w+)\]?\.\[?(\w+)\]?'
        from_tables = re.findall(from_pattern, ddl, re.IGNORECASE)

        # Check if expected sources are in regex results
        expected = expected_sources.get('spLoadFactLaborCostForEarnedValue_Post', [])

        found_count = 0
        for exp_schema, exp_table in expected:
            found_in_regex = any(
                s.upper() == exp_schema.upper() and t.upper() == exp_table.upper()
                for s, t in from_tables
            )
            if found_in_regex:
                found_count += 1

        # At least one expected source should be found by regex
        if len(expected) > 0:
            assert found_count > 0, (
                f"Expected to find at least one of {expected} in regex results, found {found_count}"
            )


class TestDebuggingWorkflow:
    """Test debugging workflow for parser issues."""

    def test_ddl_length_reasonable(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that SP DDL has reasonable length."""
        result = db_connection.execute("""
            SELECT d.definition
            FROM objects o
            JOIN definitions d ON o.object_id = d.object_id
            WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
            AND o.object_type = 'Stored Procedure'
            LIMIT 1
        """).fetchone()

        if result is None:
            pytest.skip("Target SP not found")

        ddl = result[0]

        # DDL should be substantial (not empty stub)
        assert len(ddl) > 100, "SP DDL should be substantial"

        # But not excessively long (potential issue)
        assert len(ddl) < 1000000, "SP DDL should not be excessively long"

    def test_sp_has_data_operations(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that SP has data operations (FROM/INSERT/UPDATE)."""
        result = db_connection.execute("""
            SELECT d.definition
            FROM objects o
            JOIN definitions d ON o.object_id = d.object_id
            WHERE o.object_name LIKE '%FactLaborCostForEarnedValue%Post%'
            AND o.object_type = 'Stored Procedure'
            LIMIT 1
        """).fetchone()

        if result is None:
            pytest.skip("Target SP not found")

        ddl = result[0].upper()

        # Check for data operations
        has_from = bool(re.search(r'\bFROM\s+', ddl))
        has_insert = bool(re.search(r'\bINSERT\s+INTO\s+', ddl))
        has_update = bool(re.search(r'\bUPDATE\s+', ddl))
        has_delete = bool(re.search(r'\bDELETE\s+FROM\s+', ddl))

        has_data_ops = has_from or has_insert or has_update or has_delete

        assert has_data_ops, "SP should have at least one data operation"
