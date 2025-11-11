"""
Unit tests for SQL dialect configuration.

Tests dialect validation, metadata retrieval, and enum functionality.
"""

import pytest
from lineage_v3.config.dialect_config import (
    SQLDialect,
    DialectMetadata,
    get_dialect_metadata,
    validate_dialect,
    list_supported_dialects,
    DIALECT_METADATA
)


class TestSQLDialect:
    """Test SQLDialect enum"""

    def test_dialect_enum_values(self):
        """Test all dialect enum values are correct"""
        assert SQLDialect.TSQL.value == "tsql"
        assert SQLDialect.FABRIC.value == "fabric"
        assert SQLDialect.POSTGRES.value == "postgres"
        assert SQLDialect.ORACLE.value == "oracle"
        assert SQLDialect.SNOWFLAKE.value == "snowflake"
        assert SQLDialect.REDSHIFT.value == "redshift"
        assert SQLDialect.BIGQUERY.value == "bigquery"

    def test_dialect_enum_count(self):
        """Test we have exactly 7 supported dialects"""
        assert len(list(SQLDialect)) == 7

    def test_dialect_enum_string_coercion(self):
        """Test dialect enum can be used as string"""
        dialect = SQLDialect.TSQL
        assert dialect.value == "tsql"
        assert dialect == "tsql"


class TestValidateDialect:
    """Test validate_dialect() function"""

    def test_validate_lowercase(self):
        """Test validation with lowercase input"""
        assert validate_dialect("tsql") == SQLDialect.TSQL
        assert validate_dialect("fabric") == SQLDialect.FABRIC
        assert validate_dialect("postgres") == SQLDialect.POSTGRES

    def test_validate_uppercase(self):
        """Test validation with uppercase input"""
        assert validate_dialect("TSQL") == SQLDialect.TSQL
        assert validate_dialect("FABRIC") == SQLDialect.FABRIC
        assert validate_dialect("POSTGRES") == SQLDialect.POSTGRES

    def test_validate_mixedcase(self):
        """Test validation with mixed case input"""
        assert validate_dialect("TsQl") == SQLDialect.TSQL
        assert validate_dialect("Fabric") == SQLDialect.FABRIC
        assert validate_dialect("PoStGrEs") == SQLDialect.POSTGRES

    def test_validate_invalid_dialect(self):
        """Test validation raises ValueError for unsupported dialect"""
        with pytest.raises(ValueError, match="Unsupported SQL dialect"):
            validate_dialect("invalid")

        with pytest.raises(ValueError, match="Unsupported SQL dialect"):
            validate_dialect("mongodb")

        with pytest.raises(ValueError, match="Unsupported SQL dialect"):
            validate_dialect("")

    def test_validate_error_message_includes_supported(self):
        """Test error message lists supported dialects"""
        with pytest.raises(ValueError, match="tsql, fabric, postgres"):
            validate_dialect("invalid")


class TestDialectMetadata:
    """Test DialectMetadata and get_dialect_metadata()"""

    def test_all_dialects_have_metadata(self):
        """Test all dialects in enum have metadata entries"""
        for dialect in SQLDialect:
            metadata = get_dialect_metadata(dialect)
            assert metadata is not None
            assert isinstance(metadata, DialectMetadata)

    def test_tsql_metadata(self):
        """Test T-SQL metadata is correct"""
        metadata = get_dialect_metadata(SQLDialect.TSQL)
        assert metadata.dialect == SQLDialect.TSQL
        assert "Microsoft" in metadata.display_name
        assert metadata.metadata_source == "dmv"
        assert metadata.supports_stored_procedures is True
        assert metadata.supports_views is True
        assert metadata.supports_functions is True

    def test_fabric_metadata(self):
        """Test Microsoft Fabric metadata is correct"""
        metadata = get_dialect_metadata(SQLDialect.FABRIC)
        assert metadata.dialect == SQLDialect.FABRIC
        assert "Fabric" in metadata.display_name
        assert metadata.metadata_source == "information_schema"
        assert metadata.supports_stored_procedures is True

    def test_postgres_metadata(self):
        """Test PostgreSQL metadata is correct"""
        metadata = get_dialect_metadata(SQLDialect.POSTGRES)
        assert metadata.dialect == SQLDialect.POSTGRES
        assert "PostgreSQL" in metadata.display_name
        assert metadata.metadata_source == "information_schema"

    def test_oracle_metadata(self):
        """Test Oracle metadata is correct"""
        metadata = get_dialect_metadata(SQLDialect.ORACLE)
        assert metadata.dialect == SQLDialect.ORACLE
        assert "Oracle" in metadata.display_name
        assert metadata.metadata_source == "system_tables"

    def test_metadata_registry_complete(self):
        """Test DIALECT_METADATA registry has all dialects"""
        assert len(DIALECT_METADATA) == len(SQLDialect)


class TestListSupportedDialects:
    """Test list_supported_dialects() function"""

    def test_list_returns_all_dialects(self):
        """Test list returns all SQLDialect enums"""
        dialects = list_supported_dialects()
        assert len(dialects) == 7
        assert SQLDialect.TSQL in dialects
        assert SQLDialect.FABRIC in dialects
        assert SQLDialect.POSTGRES in dialects
        assert SQLDialect.ORACLE in dialects
        assert SQLDialect.SNOWFLAKE in dialects
        assert SQLDialect.REDSHIFT in dialects
        assert SQLDialect.BIGQUERY in dialects

    def test_list_returns_list(self):
        """Test function returns a list"""
        dialects = list_supported_dialects()
        assert isinstance(dialects, list)
        assert all(isinstance(d, SQLDialect) for d in dialects)
