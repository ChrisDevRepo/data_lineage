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


class ParserSettings(BaseSettings):
    """
    SQL parser quality thresholds and behavior configuration.

    These thresholds determine confidence scores for parsed stored procedures.
    """
    confidence_high: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="High confidence threshold (regex and SQLGlot agree ±10%)"
    )
    confidence_medium: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Medium confidence threshold (partial agreement ±25%)"
    )
    confidence_low: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Low confidence threshold (major difference >25%)"
    )
    threshold_good: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Good match threshold (±10% difference)"
    )
    threshold_fair: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Fair match threshold (±25% difference)"
    )

    model_config = SettingsConfigDict(
        env_prefix='PARSER_',
        case_sensitive=False
    )


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


class PhantomSettings(BaseSettings):
    """
    Phantom object configuration (v4.3.3 - REDESIGNED).

    NEW PHILOSOPHY:
    - Phantoms = EXTERNAL dependencies only (schemas NOT in our metadata database)
    - For schemas in our metadata DB, missing objects = DB quality issues (not our concern)
    - We are NOT the authority to flag missing objects in schemas we manage

    Configuration:
    - PHANTOM_EXTERNAL_SCHEMAS: External schema names (exact match, no wildcards)
    - Leave empty if no external dependencies
    """
    external_schemas: str = Field(
        default="",
        description="Comma-separated list of EXTERNAL schema names (exact match, case-insensitive, NO wildcards)",
        validation_alias='PHANTOM_EXTERNAL_SCHEMAS'
    )

    exclude_dbo_objects: str = Field(
        default="",
        description="Comma-separated list of persistent object name patterns to exclude in dbo schema (transient objects like #temp, CTEs handled by SQL cleaning)"
    )

    @property
    def include_schema_list(self) -> list[str]:
        """
        Parse external schema list (v4.3.3).

        Returns exact schema names (no wildcards).
        """
        return [s.strip() for s in self.external_schemas.split(',') if s.strip()]

    @property
    def exclude_dbo_pattern_list(self) -> list[str]:
        """Parse comma-separated dbo object patterns"""
        return [s.strip() for s in self.exclude_dbo_objects.split(',') if s.strip()]

    model_config = SettingsConfigDict(
        env_prefix='PHANTOM_',
        case_sensitive=False,
        populate_by_name=True
    )


class Settings(BaseSettings):
    """
    Main application settings.

    Aggregates all configuration sections and provides a single
    entry point for the entire application configuration.

    Usage:
        from engine.config import settings

        # Type-safe access
        print(settings.parser.confidence_high)  # 0.85
        print(settings.paths.workspace_file)  # Path("lineage_workspace.duckdb")
    """
    # Nested configuration sections
    parser: ParserSettings = Field(
        default_factory=ParserSettings
    )
    paths: PathSettings = Field(
        default_factory=PathSettings
    )
    phantom: PhantomSettings = Field(
        default_factory=PhantomSettings,
        description="Phantom object configuration (v4.3.0)"
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

    # SQL Dialect Configuration (v2.1.0 - Multi-dialect support)
    sql_dialect: str = Field(
        default="tsql",
        description="SQL dialect for parser and metadata extraction (tsql, fabric, postgres, oracle, snowflake, redshift, bigquery)"
    )

    # Global Schema Exclusion (v4.3.0 - Universal filter)
    excluded_schemas: str = Field(
        default="sys,dummy,information_schema,tempdb,master,msdb,model",
        description="Comma-separated list of schemas to ALWAYS exclude from ALL processing (metadata, objects, phantoms)"
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
