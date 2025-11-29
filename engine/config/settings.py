"""
Centralized Settings Module
============================

Type-safe configuration management using Pydantic Settings.

This replaces scattered os.getenv() calls with a single source of truth,
providing type safety, validation, and better testability.

Author: Vibecoding
Version: 2.1.0 - Multi-dialect support added
Date: 2025-11-11
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path


class PathSettings(BaseSettings):
    """
    File system paths configuration.

    Paths for workspace files, output directories, and data storage.
    """
    workspace_file: Path = Field(
        default=Path("lineage_workspace.duckdb"),
        description="DuckDB workspace database file"
    )
    output_dir: Path = Field(
        default=Path("lineage_output"),
        description="Output directory for JSON files"
    )
    parquet_dir: Path = Field(
        default=Path("parquet_snapshots"),
        description="Default directory for Parquet snapshots"
    )

    model_config = SettingsConfigDict(
        env_prefix='PATH_',
        case_sensitive=False
    )


class DatabaseConnectorSettings(BaseSettings):
    """
    Database connection settings for direct metadata extraction (v0.10.0).

    When enabled, allows users to refresh stored procedure metadata
    directly from the database instead of uploading files.

    Security: Connection strings should be stored in environment variables,
    preferably using Azure Key Vault or Docker secrets in production.
    """
    enabled: bool = Field(
        default=False,
        description="Enable direct database connection for metadata refresh"
    )
    connection_string: str = Field(
        default="",
        description="Database connection string (format varies by dialect)"
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Query timeout in seconds"
    )
    ssl_enabled: bool = Field(
        default=True,
        description="Require SSL/TLS for database connections"
    )

    model_config = SettingsConfigDict(
        env_prefix='DB_',
        case_sensitive=False
    )


class Settings(BaseSettings):
    """
    Main application settings.

    Aggregates all configuration sections and provides a single
    entry point for the entire application configuration.

    Usage:
        from engine.config import settings

        # Type-safe access
        print(settings.paths.workspace_file)  # Path("lineage_workspace.duckdb")
        print(settings.dialect)  # SQLDialect enum
    """
    # Nested configuration sections
    paths: PathSettings = Field(
        default_factory=PathSettings
    )
    db: DatabaseConnectorSettings = Field(
        default_factory=DatabaseConnectorSettings,
        description="Database connection settings for direct metadata refresh (v0.10.0)"
    )

    # API Configuration
    allowed_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed origins for CORS (FastAPI CORSMiddleware)"
    )

    # Top-level application settings
    run_mode: Literal["demo", "debug", "production"] = Field(
        default="production",
        description="Runtime mode: demo (sample data), debug (verbose logging), production (optimized)"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    skip_query_logs: bool = Field(
        default=False,
        description="Skip query log analysis"
    )
    log_retention_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Number of days to retain log files (cleanup triggered on import)"
    )

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        return self.run_mode == "demo"

    @property
    def is_debug_mode(self) -> bool:
        """Check if running in debug mode"""
        return self.run_mode == "debug" or self.debug_mode

    @property
    def is_production_mode(self) -> bool:
        """Check if running in production mode"""
        return self.run_mode == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert comma-separated allowed_origins to list (for FastAPI CORS)"""
        return [origin.strip() for origin in self.allowed_origins.split(',')]

    # SQL Dialect Configuration (v2.1.0 - Multi-dialect support)
    sql_dialect: str = Field(
        default="tsql",
        description="SQL dialect for parser and metadata extraction (tsql, postgres, snowflake, bigquery). Note: Fabric uses tsql dialect."
    )

    # Global Schema Exclusion (v4.3.0 - Universal filter)
    excluded_schemas: str = Field(
        default="sys,dummy,information_schema,tempdb,master,msdb,model",
        description="Comma-separated list of schemas to ALWAYS exclude from ALL processing (metadata, objects)"
    )

    @field_validator('sql_dialect')
    @classmethod
    def validate_sql_dialect(cls, v: str) -> str:
        """Validate SQL dialect is supported"""
        from engine.config.dialect_config import validate_dialect
        # This will raise ValueError if invalid
        validate_dialect(v)
        return v.lower()

    @property
    def dialect(self):
        """Get validated SQLDialect enum"""
        from engine.config.dialect_config import validate_dialect
        return validate_dialect(self.sql_dialect)

    @property
    def excluded_schema_set(self) -> set[str]:
        """Parse comma-separated excluded schemas (universal filter)"""
        return {s.strip().lower() for s in self.excluded_schemas.split(',') if s.strip()}

    model_config = SettingsConfigDict(
        env_file='../.env',  # Backend runs from api/ directory, .env is in parent (project root)
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignore extra env vars not defined here
    )


# Singleton instance - import this throughout the application
settings = Settings()
