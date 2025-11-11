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
    Phantom object configuration (v4.3.0).

    Controls which schemas are eligible for phantom object creation.
    Uses INCLUDE list approach with wildcard support.
    """
    include_schemas: str = Field(
        default="CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B",
        description="Comma-separated list of schema patterns for phantom creation (wildcards supported with *)"
    )
    exclude_dbo_objects: str = Field(
        default="cte,cte_*,CTE*,ParsedData,PartitionedCompany*,#*,@*,temp_*,tmp_*,[a-z],[A-Z]",
        description="Comma-separated list of object name patterns to exclude in dbo schema"
    )

    @property
    def include_schema_list(self) -> list[str]:
        """Parse comma-separated include patterns for phantom creation"""
        return [s.strip() for s in self.include_schemas.split(',') if s.strip()]

    @property
    def exclude_dbo_pattern_list(self) -> list[str]:
        """Parse comma-separated dbo object patterns"""
        return [s.strip() for s in self.exclude_dbo_objects.split(',') if s.strip()]

    model_config = SettingsConfigDict(
        env_prefix='PHANTOM_',
        case_sensitive=False
    )


class Settings(BaseSettings):
    """
    Main application settings.

    Aggregates all configuration sections and provides a single
    entry point for the entire application configuration.

    Usage:
        from lineage_v3.config import settings

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
        from lineage_v3.config.dialect_config import validate_dialect
        # This will raise ValueError if invalid
        validate_dialect(v)
        return v.lower()

    @property
    def dialect(self):
        """Get validated SQLDialect enum"""
        from lineage_v3.config.dialect_config import validate_dialect
        return validate_dialect(self.sql_dialect)

    @property
    def excluded_schema_set(self) -> set[str]:
        """Parse comma-separated excluded schemas (universal filter)"""
        return {s.strip().lower() for s in self.excluded_schemas.split(',') if s.strip()}

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignore extra env vars not defined here
    )


# Singleton instance - import this throughout the application
settings = Settings()
