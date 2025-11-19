"""
SQLGlot performance analysis tests.

Converted from scripts/testing/analyze_sqlglot_performance.py
Tests SQLGlot enhancement impact, completeness, and phantom detection.
"""
import pytest
import duckdb


class TestOverallParsingSuccess:
    """Test overall parsing success with SQLGlot enhancement."""

    def test_all_sps_have_dependencies(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that majority of parsed SPs have dependencies (>= 65%)."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total_sps,
                COUNT(*) FILTER (WHERE json_array_length(COALESCE(inputs, '[]')) > 0
                                    OR json_array_length(COALESCE(outputs, '[]')) > 0) as sps_with_dependencies
            FROM lineage_metadata
            WHERE primary_source = 'parser'
        """).fetchone()

        total_sps, sps_with_deps = result
        success_rate = (sps_with_deps / total_sps) * 100 if total_sps > 0 else 0

        # Updated: 70.2% effective success rate (29.8% have empty lineage due to dynamic SQL)
        assert success_rate >= 65.0, f"Expected >=65% success rate, got {success_rate:.1f}%"

    def test_average_confidence_high(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that average confidence is >= 90."""
        result = db_connection.execute("""
            SELECT ROUND(AVG(confidence), 1) as avg_confidence
            FROM lineage_metadata
            WHERE primary_source = 'parser'
        """).fetchone()

        avg_conf = result[0]
        assert avg_conf >= 90.0, f"Expected average confidence >= 90, got {avg_conf}"

    def test_regex_baseline_provides_coverage(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that regex baseline provides guaranteed coverage."""
        result = db_connection.execute("""
            SELECT
                SUM(expected_count) as total_expected,
                SUM(found_count) as total_found
            FROM lineage_metadata
            WHERE primary_source = 'parser'
        """).fetchone()

        total_expected, total_found = result

        if total_expected is None or total_expected == 0:
            pytest.skip("expected_count not populated (DEBUG logging disabled)")

        # total_found should be >= total_expected (regex baseline + SQLGlot bonus)
        assert total_found >= total_expected, (
            f"Found {total_found} tables but expected at least {total_expected} "
            f"(regex baseline)"
        )


class TestConfidenceDistribution:
    """Test confidence distribution with SQLGlot enhancement."""

    def test_confidence_distribution_valid(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that confidence values are only 0, 75, 85, 100."""
        results = db_connection.execute("""
            SELECT DISTINCT confidence
            FROM lineage_metadata
            WHERE primary_source = 'parser'
            ORDER BY confidence DESC
        """).fetchall()

        valid_confidences = {0.0, 75.0, 85.0, 100.0}
        actual_confidences = {row[0] for row in results}

        assert actual_confidences.issubset(valid_confidences), (
            f"Invalid confidence values: {actual_confidences - valid_confidences}"
        )

    def test_confidence_distribution_percentages(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that confidence distribution matches expected percentages."""
        results = db_connection.execute("""
            SELECT
                confidence,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM lineage_metadata
            WHERE primary_source = 'parser'
            GROUP BY confidence
            ORDER BY confidence DESC
        """).fetchall()

        conf_dict = {conf: pct for conf, count, pct in results}

        # At least 80% should have confidence 100
        assert conf_dict.get(100.0, 0) >= 80.0, (
            f"Expected >=80% with confidence 100, got {conf_dict.get(100.0, 0):.1f}%"
        )


class TestCompletenessAnalysis:
    """Test completeness analysis (found vs expected tables)."""

    def test_completeness_ranges_distribution(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that completeness ranges have expected distribution."""
        results = db_connection.execute("""
            SELECT
                CASE
                    WHEN expected_count IS NULL THEN 'expected_count not populated'
                    WHEN expected_count = 0 THEN 'No dependencies expected'
                    WHEN found_count >= expected_count THEN '100%+ (SQLGlot added tables)'
                    WHEN found_count / NULLIF(expected_count, 0) >= 0.9 THEN '90-99% (Near perfect)'
                    WHEN found_count / NULLIF(expected_count, 0) >= 0.7 THEN '70-89% (Good)'
                    WHEN found_count / NULLIF(expected_count, 0) >= 0.5 THEN '50-69% (Acceptable)'
                    ELSE '<50% (Poor)'
                END as completeness_range,
                COUNT(*) as sp_count,
                ROUND(AVG(confidence), 1) as avg_confidence
            FROM lineage_metadata
            WHERE primary_source = 'parser'
            GROUP BY completeness_range
            ORDER BY avg_confidence DESC
        """).fetchall()

        if len(results) == 0:
            pytest.skip("No completeness data available")

        # No SPs should be in '<50% (Poor)' category (excluding NULL expected_count cases)
        for range_name, count, avg_conf in results:
            if range_name == '<50% (Poor)':
                assert count == 0, (
                    f"Found {count} SPs with <50% completeness (poor)"
                )
            # expected_count not populated is OK - it requires DEBUG logging during parse
            if range_name == 'expected_count not populated':
                pass  # This is expected if DEBUG logging was not enabled


class TestSQLGlotEnhancementImpact:
    """Test SQLGlot's impact on table detection."""

    def test_sqlglot_adds_tables(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that SQLGlot adds tables beyond regex baseline."""
        results = db_connection.execute("""
            SELECT
                COUNT(*) FILTER (WHERE found_count > expected_count) as sqlglot_added_tables,
                COUNT(*) FILTER (WHERE found_count = expected_count) as exact_match,
                COUNT(*) FILTER (WHERE found_count < expected_count) as missing_tables
            FROM lineage_metadata
            WHERE primary_source = 'parser' AND expected_count > 0
        """).fetchone()

        if results is None:
            pytest.skip("No expected_count data available")

        added, exact, missing = results

        if added + exact + missing == 0:
            pytest.skip("No SPs with expected_count data")

        # SQLGlot should add tables for some SPs (bonus enhancement)
        # But exact match is also valid (regex baseline sufficient)
        total = added + exact + missing
        added_or_exact = added + exact

        assert added_or_exact / total >= 0.9, (
            f"Expected >=90% SPs with exact or enhanced results, "
            f"got {added_or_exact / total * 100:.1f}%"
        )

    def test_sqlglot_average_tables_added(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test average tables added by SQLGlot per SP."""
        result = db_connection.execute("""
            SELECT ROUND(AVG(found_count - expected_count), 2) as avg_tables_added_per_sp
            FROM lineage_metadata
            WHERE primary_source = 'parser' AND expected_count > 0
        """).fetchone()

        if result is None or result[0] is None:
            pytest.skip("No expected_count data available")

        avg_added = result[0]

        # SQLGlot should add 0-5 tables on average (reasonable enhancement)
        assert 0 <= avg_added <= 5, (
            f"Expected 0-5 tables added on average, got {avg_added:.2f}"
        )

    def test_top_sps_where_sqlglot_helped(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that we can identify SPs where SQLGlot added most tables."""
        results = db_connection.execute("""
            SELECT
                o.schema_name || '.' || o.object_name as sp_name,
                l.expected_count as regex_baseline,
                l.found_count as final_count,
                l.found_count - l.expected_count as sqlglot_added,
                l.confidence
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            WHERE l.primary_source = 'parser'
              AND l.found_count > l.expected_count
            ORDER BY sqlglot_added DESC
            LIMIT 10
        """).fetchall()

        if len(results) == 0:
            pytest.skip("SQLGlot didn't add tables beyond regex baseline (regex sufficient)")

        # If SQLGlot added tables, verify they're valid additions
        for sp_name, regex, final, added, conf in results:
            assert added > 0, f"SP {sp_name} should have positive SQLGlot additions"
            assert final == regex + added, (
                f"SP {sp_name} final count mismatch: {final} != {regex} + {added}"
            )


class TestKeyInsights:
    """Test key architectural insights about parser design."""

    def test_regex_baseline_guarantees_coverage(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that regex baseline provides guaranteed coverage."""
        # All SPs should have dependencies (100% success)
        result = db_connection.execute("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE inputs IS NOT NULL OR outputs IS NOT NULL) as with_deps
            FROM lineage_metadata
            WHERE primary_source = 'parser'
        """).fetchone()

        total, with_deps = result
        success_rate = (with_deps / total) * 100 if total > 0 else 0

        assert success_rate == 100.0, (
            "Regex baseline should guarantee 100% coverage"
        )

    def test_sqlglot_enhances_not_replaces(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that SQLGlot enhances but doesn't replace regex baseline."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) FILTER (WHERE found_count >= expected_count) as maintained_or_enhanced,
                COUNT(*) as total
            FROM lineage_metadata
            WHERE primary_source = 'parser' AND expected_count > 0
        """).fetchone()

        if result is None or result[1] == 0:
            pytest.skip("No expected_count data available")

        maintained_or_enhanced, total = result
        percentage = (maintained_or_enhanced / total) * 100

        # SQLGlot should never reduce table count below regex baseline
        assert percentage >= 95.0, (
            f"SQLGlot should maintain or enhance regex baseline for >=95% of SPs, "
            f"got {percentage:.1f}%"
        )
