"""
Confidence analysis tests - Why some SPs have lower confidence.

Converted from scripts/testing/analyze_lower_confidence_sps.py
Tests confidence distribution and analyzes SPs with confidence 85 and 75.
"""
import pytest
import duckdb
import json
import re


class TestConfidenceDistribution:
    """Test confidence distribution and success rates."""

    def test_success_rate_is_100_percent(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that parser achieves 100% success rate."""
        total = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata WHERE primary_source = 'parser'
        """).fetchone()[0]

        with_deps = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE primary_source = 'parser'
              AND (json_array_length(COALESCE(inputs, '[]')) > 0 OR json_array_length(COALESCE(outputs, '[]')) > 0)
        """).fetchone()[0]

        success_rate = (with_deps / total) * 100 if total > 0 else 0
        assert success_rate == 100.0, f"Expected 100% success rate, got {success_rate:.1f}%"

    def test_confidence_100_majority(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that majority of SPs have confidence 100."""
        total = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata WHERE primary_source = 'parser'
        """).fetchone()[0]

        conf_100 = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE primary_source = 'parser' AND confidence = 100.0
        """).fetchone()[0]

        percentage = (conf_100 / total) * 100 if total > 0 else 0
        assert percentage >= 80.0, (
            f"Expected >=80% SPs with confidence 100, got {percentage:.1f}%"
        )

    def test_confidence_85_acceptable(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that confidence 85 SPs are within acceptable range (<15%)."""
        total = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata WHERE primary_source = 'parser'
        """).fetchone()[0]

        conf_85 = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE primary_source = 'parser' AND confidence = 85.0
        """).fetchone()[0]

        percentage = (conf_85 / total) * 100 if total > 0 else 0
        assert percentage < 15.0, (
            f"Expected <15% SPs with confidence 85, got {percentage:.1f}%"
        )

    def test_confidence_75_acceptable(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that confidence 75 SPs are within acceptable range (<15%)."""
        total = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata WHERE primary_source = 'parser'
        """).fetchone()[0]

        conf_75 = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE primary_source = 'parser' AND confidence = 75.0
        """).fetchone()[0]

        percentage = (conf_75 / total) * 100 if total > 0 else 0
        assert percentage < 15.0, (
            f"Expected <15% SPs with confidence 75, got {percentage:.1f}%"
        )


class TestConfidence85Analysis:
    """Test analysis of SPs with confidence 85 (70-89% completeness)."""

    @pytest.fixture
    def conf_85_sps(self, db_connection: duckdb.DuckDBPyConnection):
        """Get SPs with confidence 85 for analysis."""
        results = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                l.confidence,
                l.inputs,
                l.outputs,
                l.expected_count,
                l.found_count
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            WHERE l.primary_source = 'parser'
              AND l.confidence = 85.0
            ORDER BY o.schema_name, o.object_name
            LIMIT 10
        """).fetchall()
        return results

    def test_conf_85_sps_have_dependencies(
        self, conf_85_sps: list
    ):
        """Test that confidence 85 SPs have at least some dependencies."""
        if len(conf_85_sps) == 0:
            pytest.skip("No confidence 85 SPs in database (excellent!)")

        for schema, name, conf, inputs, outputs, expected, found in conf_85_sps:
            input_list = json.loads(inputs) if inputs else []
            output_list = json.loads(outputs) if outputs else []
            total = len(input_list) + len(output_list)

            assert total > 0, (
                f"Confidence 85 SP {schema}.{name} should have dependencies"
            )

    def test_conf_85_completeness_range(
        self, conf_85_sps: list
    ):
        """Test that confidence 85 SPs have 70-89% completeness."""
        if len(conf_85_sps) == 0:
            pytest.skip("No confidence 85 SPs in database")

        for schema, name, conf, inputs, outputs, expected, found in conf_85_sps:
            if expected and found and expected > 0:
                completeness = (found / expected) * 100
                assert 70 <= completeness < 90, (
                    f"Confidence 85 SP {schema}.{name} should have 70-89% completeness, "
                    f"got {completeness:.1f}%"
                )


class TestConfidence75Analysis:
    """Test analysis of SPs with confidence 75 (50-69% completeness)."""

    @pytest.fixture
    def conf_75_sps(self, db_connection: duckdb.DuckDBPyConnection):
        """Get SPs with confidence 75 for analysis."""
        results = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                l.confidence,
                l.inputs,
                l.outputs,
                l.expected_count,
                l.found_count
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            WHERE l.primary_source = 'parser'
              AND l.confidence = 75.0
            ORDER BY o.schema_name, o.object_name
            LIMIT 10
        """).fetchall()
        return results

    def test_conf_75_sps_have_dependencies(
        self, conf_75_sps: list
    ):
        """Test that confidence 75 SPs have at least some dependencies."""
        if len(conf_75_sps) == 0:
            pytest.skip("No confidence 75 SPs in database (excellent!)")

        for schema, name, conf, inputs, outputs, expected, found in conf_75_sps:
            input_list = json.loads(inputs) if inputs else []
            output_list = json.loads(outputs) if outputs else []
            total = len(input_list) + len(output_list)

            assert total > 0, (
                f"Confidence 75 SP {schema}.{name} should have dependencies"
            )

    def test_conf_75_completeness_range(
        self, conf_75_sps: list
    ):
        """Test that confidence 75 SPs have 50-69% completeness."""
        if len(conf_75_sps) == 0:
            pytest.skip("No confidence 75 SPs in database")

        for schema, name, conf, inputs, outputs, expected, found in conf_75_sps:
            if expected and found and expected > 0:
                completeness = (found / expected) * 100
                assert 50 <= completeness < 70, (
                    f"Confidence 75 SP {schema}.{name} should have 50-69% completeness, "
                    f"got {completeness:.1f}%"
                )


class TestPatternAnalysis:
    """Test SQL pattern analysis for lower confidence SPs."""

    @pytest.fixture
    def sample_lower_confidence_sp(self, db_connection: duckdb.DuckDBPyConnection):
        """Get one sample SP with confidence < 100 for pattern analysis."""
        result = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                d.definition,
                l.confidence
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            LEFT JOIN definitions d ON l.object_id = d.object_id
            WHERE l.primary_source = 'parser'
              AND l.confidence < 100.0
              AND l.confidence >= 75.0
            ORDER BY l.confidence DESC
            LIMIT 1
        """).fetchone()

        return result

    def test_lower_confidence_sp_has_sql_patterns(
        self, sample_lower_confidence_sp: tuple
    ):
        """Test that lower confidence SPs have identifiable SQL patterns."""
        if sample_lower_confidence_sp is None:
            pytest.skip("No lower confidence SPs in database (all perfect!)")

        schema, name, ddl, confidence = sample_lower_confidence_sp

        if not ddl:
            pytest.skip(f"No DDL available for {schema}.{name}")

        ddl_upper = ddl.upper()

        # Count SQL patterns
        patterns = {
            'FROM': r'\bFROM\s+',
            'JOIN': r'\bJOIN\s+',
            'INSERT': r'\bINSERT\s+INTO\s+',
            'UPDATE': r'\bUPDATE\s+',
            'DELETE': r'\bDELETE\s+FROM\s+',
        }

        pattern_counts = {}
        for pattern_name, pattern_regex in patterns.items():
            matches = re.findall(pattern_regex, ddl_upper)
            pattern_counts[pattern_name] = len(matches)

        # At least one data operation pattern should exist
        total_patterns = sum(pattern_counts.values())
        assert total_patterns > 0, (
            f"Lower confidence SP {schema}.{name} should have data operation patterns"
        )


class TestCleaningLogicAssessment:
    """Test assessment of cleaning logic effectiveness."""

    def test_expected_count_populated(self, db_connection: duckdb.DuckDBPyConnection):
        """Test if expected_count and found_count are populated."""
        has_counts = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE primary_source = 'parser'
              AND expected_count IS NOT NULL
              AND found_count IS NOT NULL
        """).fetchone()[0]

        # This is informational - some systems may not populate these fields
        if has_counts == 0:
            pytest.skip("expected_count and found_count not populated (DEBUG logging disabled)")

    def test_lower_confidence_reasons_identifiable(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that lower confidence SPs have identifiable reasons."""
        lower_conf = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                l.confidence,
                l.expected_count,
                l.found_count
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            WHERE l.primary_source = 'parser'
              AND l.confidence < 100.0
              AND l.confidence >= 75.0
            LIMIT 5
        """).fetchall()

        if len(lower_conf) == 0:
            pytest.skip("No lower confidence SPs in database")

        # For each lower confidence SP, we should be able to calculate completeness
        for schema, name, conf, expected, found in lower_conf:
            if expected and found and expected > 0:
                completeness = (found / expected) * 100

                # Verify confidence matches completeness brackets
                if completeness >= 90:
                    assert conf == 100.0
                elif completeness >= 70:
                    assert conf == 85.0
                elif completeness >= 50:
                    assert conf == 75.0
                else:
                    assert conf == 0.0
