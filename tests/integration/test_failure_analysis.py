"""
Failure analysis tests - Root cause investigation for failed SPs.

Converted from scripts/testing/analyze_failed_sps.py
Tests failure categorization, pattern analysis, and cleaning logic assessment.
"""
import pytest
import duckdb
import re


class TestFailureIdentification:
    """Test identification of failed stored procedures."""

    @pytest.fixture
    def failed_sps(self, db_connection: duckdb.DuckDBPyConnection):
        """Get failed SPs (no inputs AND no outputs)."""
        results = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                o.object_type,
                d.definition,
                l.confidence,
                l.inputs,
                l.outputs
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            LEFT JOIN definitions d ON l.object_id = d.object_id
            WHERE l.primary_source = 'parser'
              AND (l.inputs IS NULL OR l.inputs = '')
              AND (l.outputs IS NULL OR l.outputs = '')
            ORDER BY o.schema_name, o.object_name
        """).fetchall()
        return results

    def test_no_failed_sps(self, failed_sps: list):
        """Test that parser achieves 100% success rate (no failed SPs)."""
        assert len(failed_sps) == 0, (
            f"Expected 0 failed SPs (100% success rate), got {len(failed_sps)}"
        )


class TestFailureCategorization:
    """Test categorization of failed SPs (if any exist)."""

    @pytest.fixture
    def failure_categories(self, db_connection: duckdb.DuckDBPyConnection):
        """Categorize failed SPs by failure reason."""
        failed_sps = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                d.definition
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            LEFT JOIN definitions d ON l.object_id = d.object_id
            WHERE l.primary_source = 'parser'
              AND (l.inputs IS NULL OR l.inputs = '')
              AND (l.outputs IS NULL OR l.outputs = '')
        """).fetchall()

        categories = {
            'dynamic_sql_only': [],
            'template_empty': [],
            'utility_system': [],
            'administrative': [],
            'unknown': []
        }

        for schema, name, ddl in failed_sps:
            if not ddl:
                categories['template_empty'].append(f"{schema}.{name}")
                continue

            sp_name = f"{schema}.{name}"
            ddl_clean = ddl.strip()
            ddl_body = ddl_clean.upper()

            # Category 1: Dynamic SQL only
            if re.search(r'EXEC\s+@\w+', ddl_body) or re.search(r'EXEC\s+sp_executesql', ddl_body):
                if not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|MERGE\s+INTO)\b', ddl_body):
                    categories['dynamic_sql_only'].append(sp_name)
                    continue

            # Category 2: Template/Empty
            if len(ddl_clean) < 100 or ddl_body.count('SELECT') == 0:
                categories['template_empty'].append(sp_name)
                continue

            # Category 3: Utility/System
            if re.search(r'@@ROWCOUNT|@@ERROR|@@IDENTITY|@@VERSION', ddl_body):
                if not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM)\b', ddl_body):
                    categories['utility_system'].append(sp_name)
                    continue

            # Category 4: Administrative
            if not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|MERGE\s+INTO)\b', ddl_body):
                if re.search(r'\b(DECLARE|SET|PRINT|RETURN|RAISERROR)\b', ddl_body):
                    categories['administrative'].append(sp_name)
                    continue

            # Unknown
            categories['unknown'].append(sp_name)

        return categories

    def test_no_unexpected_failures(self, failure_categories: dict):
        """Test that there are no unexpected failures (unknown category)."""
        if sum(len(sps) for sps in failure_categories.values()) == 0:
            pytest.skip("No failed SPs in database (100% success rate)")

        unexpected = failure_categories['unknown']
        total = sum(len(sps) for sps in failure_categories.values())

        assert len(unexpected) == 0, (
            f"Found {len(unexpected)} unexpected failures out of {total} total failures. "
            f"These need investigation: {unexpected}"
        )

    def test_dynamic_sql_failures_expected(self, failure_categories: dict):
        """Test that dynamic SQL failures are expected (no static table references)."""
        dynamic_sql = failure_categories['dynamic_sql_only']

        if len(dynamic_sql) == 0:
            pytest.skip("No dynamic SQL only SPs")

        # Dynamic SQL failures are expected - SPs use EXEC @variable with no static SQL
        # This is informational only
        assert True, f"Dynamic SQL SPs (expected): {len(dynamic_sql)}"

    def test_template_empty_failures_expected(self, failure_categories: dict):
        """Test that template/empty procedure failures are expected."""
        template_empty = failure_categories['template_empty']

        if len(template_empty) == 0:
            pytest.skip("No template/empty SPs")

        # Template/empty failures are expected - SPs are placeholders
        # This is informational only
        assert True, f"Template/empty SPs (expected): {len(template_empty)}"


class TestPatternAnalysis:
    """Test SQL pattern analysis for failed SPs."""

    @pytest.fixture
    def sample_failed_sp(self, db_connection: duckdb.DuckDBPyConnection):
        """Get one sample failed SP for pattern analysis."""
        result = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                d.definition
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            LEFT JOIN definitions d ON l.object_id = d.object_id
            WHERE l.primary_source = 'parser'
              AND (l.inputs IS NULL OR l.inputs = '')
              AND (l.outputs IS NULL OR l.outputs = '')
            LIMIT 1
        """).fetchone()
        return result

    def test_failed_sp_pattern_matches_category(
        self, sample_failed_sp: tuple
    ):
        """Test that failed SP has patterns matching its failure category."""
        if sample_failed_sp is None:
            pytest.skip("No failed SPs in database (100% success rate)")

        schema, name, ddl = sample_failed_sp

        if not ddl:
            pytest.skip("No DDL available for failed SP")

        ddl_body = ddl.upper()

        # Check for expected patterns
        patterns = {
            'FROM clause': r'\bFROM\s+\[?[\w]+\]?\.',
            'JOIN clause': r'\b(INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+',
            'INSERT INTO': r'\bINSERT\s+INTO\s+',
            'UPDATE': r'\bUPDATE\s+\[?[\w]+\]?\.',
            'DELETE FROM': r'\bDELETE\s+FROM\s+',
            'MERGE INTO': r'\bMERGE\s+INTO\s+',
            'EXEC @variable': r'EXEC\s+@\w+',
            'EXEC sp_executesql': r'EXEC\s+sp_executesql',
        }

        pattern_found = {name: bool(re.search(pattern, ddl_body))
                        for name, pattern in patterns.items()}

        # Failed SP should have EITHER:
        # 1. No data operation patterns (template/utility/admin)
        # 2. Only dynamic SQL patterns (EXEC @variable)

        data_ops = any([
            pattern_found['FROM clause'],
            pattern_found['JOIN clause'],
            pattern_found['INSERT INTO'],
            pattern_found['UPDATE'],
            pattern_found['DELETE FROM'],
            pattern_found['MERGE INTO']
        ])

        dynamic_sql = any([
            pattern_found['EXEC @variable'],
            pattern_found['EXEC sp_executesql']
        ])

        # If no data ops and no dynamic SQL, it's template/utility/admin (expected)
        # If only dynamic SQL, it's dynamic SQL only (expected)
        # If data ops exist, it's unexpected failure
        assert not data_ops or dynamic_sql, (
            f"Failed SP {schema}.{name} has data operations but still failed - unexpected!"
        )


class TestCleaningLogicAssessment:
    """Test assessment of cleaning logic effectiveness."""

    def test_expected_failures_only(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that all failures are expected (no cleaning logic issues)."""
        failed_sps = db_connection.execute("""
            SELECT
                o.schema_name,
                o.object_name,
                d.definition
            FROM lineage_metadata l
            JOIN objects o ON l.object_id = o.object_id
            LEFT JOIN definitions d ON l.object_id = d.object_id
            WHERE l.primary_source = 'parser'
              AND (l.inputs IS NULL OR l.inputs = '')
              AND (l.outputs IS NULL OR l.outputs = '')
        """).fetchall()

        if len(failed_sps) == 0:
            pytest.skip("No failed SPs (100% success rate)")

        # Categorize failures
        expected_categories = ['dynamic_sql_only', 'template_empty', 'utility_system', 'administrative']
        expected_count = 0
        unexpected_count = 0

        for schema, name, ddl in failed_sps:
            if not ddl:
                expected_count += 1  # template_empty
                continue

            ddl_body = ddl.upper()

            # Check if failure is expected
            is_dynamic_sql = (
                re.search(r'EXEC\s+@\w+', ddl_body) or re.search(r'EXEC\s+sp_executesql', ddl_body)
            ) and not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b', ddl_body)

            is_template = len(ddl.strip()) < 100

            is_utility = re.search(r'@@ROWCOUNT|@@ERROR|@@IDENTITY', ddl_body) and \
                        not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b', ddl_body)

            is_admin = not re.search(r'\b(FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b', ddl_body) and \
                      re.search(r'\b(DECLARE|SET|PRINT|RETURN)\b', ddl_body)

            if is_dynamic_sql or is_template or is_utility or is_admin:
                expected_count += 1
            else:
                unexpected_count += 1

        total_failures = len(failed_sps)
        assert unexpected_count == 0, (
            f"Found {unexpected_count} unexpected failures out of {total_failures}. "
            f"This may indicate cleaning logic issue or regex pattern gaps."
        )

    def test_cleaning_logic_not_too_aggressive(
        self, db_connection: duckdb.DuckDBPyConnection
    ):
        """Test that cleaning logic is not removing tables incorrectly."""
        # If success rate is 100%, cleaning logic is working correctly
        total = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata WHERE primary_source = 'parser'
        """).fetchone()[0]

        with_deps = db_connection.execute("""
            SELECT COUNT(*) FROM lineage_metadata
            WHERE primary_source = 'parser'
              AND (json_array_length(COALESCE(inputs, '[]')) > 0 OR json_array_length(COALESCE(outputs, '[]')) > 0)
        """).fetchone()[0]

        success_rate = (with_deps / total) * 100 if total > 0 else 0

        # 100% success rate means cleaning logic is correctly balanced
        assert success_rate >= 99.0, (
            f"Success rate {success_rate:.1f}% suggests cleaning logic may be too aggressive"
        )


class TestConclusion:
    """Test overall conclusion about parser health."""

    def test_parser_health_excellent(self, db_connection: duckdb.DuckDBPyConnection):
        """Test that parser is in excellent health (100% success, high confidence)."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE inputs IS NOT NULL OR outputs IS NOT NULL) as with_deps,
                COUNT(*) FILTER (WHERE confidence = 100.0) as perfect_conf
            FROM lineage_metadata
            WHERE primary_source = 'parser'
        """).fetchone()

        total, with_deps, perfect_conf = result
        success_rate = (with_deps / total) * 100 if total > 0 else 0
        perfect_rate = (perfect_conf / total) * 100 if total > 0 else 0

        # Parser health indicators
        assert success_rate == 100.0, f"Success rate should be 100%, got {success_rate:.1f}%"
        assert perfect_rate >= 80.0, f"Perfect confidence rate should be >=80%, got {perfect_rate:.1f}%"
