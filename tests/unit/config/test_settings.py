"""
Unit tests for settings configuration with SQL dialect support.

Tests that settings properly validate and expose SQL dialect configuration.
"""

import pytest
import os
from lineage_v3.config.settings import Settings
from lineage_v3.config.dialect_config import SQLDialect


class TestSettingsDialectConfiguration:
    """Test SQL dialect configuration in Settings"""

    def test_default_dialect_is_tsql(self):
        """Test default dialect is T-SQL"""
        settings = Settings()
        assert settings.sql_dialect == "tsql"
        assert settings.dialect == SQLDialect.TSQL

    def test_dialect_property_returns_enum(self):
        """Test dialect property returns SQLDialect enum"""
        settings = Settings(sql_dialect="postgres")
        assert isinstance(settings.dialect, SQLDialect)
        assert settings.dialect == SQLDialect.POSTGRES

    def test_valid_dialects_accepted(self):
        """Test all valid dialects are accepted"""
        valid_dialects = ["tsql", "fabric", "postgres", "oracle", "snowflake", "redshift", "bigquery"]

        for dialect_str in valid_dialects:
            settings = Settings(sql_dialect=dialect_str)
            assert settings.sql_dialect == dialect_str
            assert settings.dialect == SQLDialect(dialect_str)

    def test_dialect_case_insensitive(self):
        """Test dialect validation is case-insensitive"""
        # Uppercase
        settings = Settings(sql_dialect="TSQL")
        assert settings.sql_dialect == "tsql"  # Normalized to lowercase
        assert settings.dialect == SQLDialect.TSQL

        # Mixed case
        settings = Settings(sql_dialect="Postgres")
        assert settings.sql_dialect == "postgres"
        assert settings.dialect == SQLDialect.POSTGRES

    def test_invalid_dialect_raises_error(self):
        """Test invalid dialect raises validation error"""
        with pytest.raises(ValueError, match="Unsupported SQL dialect"):
            Settings(sql_dialect="invalid")

        with pytest.raises(ValueError, match="Unsupported SQL dialect"):
            Settings(sql_dialect="mongodb")

    def test_dialect_from_env_variable(self, monkeypatch):
        """Test dialect can be set from SQL_DIALECT env variable"""
        # Set environment variable
        monkeypatch.setenv("SQL_DIALECT", "postgres")

        # Create new settings instance
        settings = Settings()

        assert settings.sql_dialect == "postgres"
        assert settings.dialect == SQLDialect.POSTGRES

    def test_dialect_env_case_insensitive(self, monkeypatch):
        """Test env variable is case-insensitive"""
        monkeypatch.setenv("SQL_DIALECT", "FABRIC")
        settings = Settings()

        assert settings.sql_dialect == "fabric"
        assert settings.dialect == SQLDialect.FABRIC


class TestSettingsBackwardCompatibility:
    """Test that existing settings functionality is preserved"""

    def test_parser_settings_still_work(self):
        """Test parser settings unchanged"""
        settings = Settings()
        assert settings.parser.confidence_high == 0.85
        assert settings.parser.confidence_medium == 0.75
        assert settings.parser.confidence_low == 0.5

    def test_path_settings_still_work(self):
        """Test path settings unchanged"""
        settings = Settings()
        assert settings.paths.workspace_file.name == "lineage_workspace.duckdb"
        assert settings.paths.output_dir.name == "lineage_output"

    def test_log_level_still_works(self):
        """Test log level setting unchanged"""
        settings = Settings()
        assert settings.log_level == "INFO"

        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"

    def test_debug_mode_still_works(self):
        """Test debug mode setting unchanged"""
        settings = Settings()
        assert settings.debug_mode is False

        settings = Settings(debug_mode=True)
        assert settings.debug_mode is True
