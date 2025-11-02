"""
Centralized Settings Module
============================

Type-safe configuration management using Pydantic Settings.

This replaces scattered os.getenv() calls with a single source of truth,
providing type safety, validation, and better testability.

Author: Vibecoding
Version: 1.0.0
Date: 2025-10-31
"""

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal
from pathlib import Path


class AzureOpenAISettings(BaseSettings):
    """
    Azure OpenAI configuration for AI-assisted disambiguation.

    Optional - AI features will be disabled if not configured
    """
    endpoint: Optional[str] = Field(
        default=None,
        description="Azure OpenAI endpoint URL",
        examples=["https://your-endpoint.openai.azure.com/"]
    )
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="Azure OpenAI API key (kept secret)"
    )
    model_name: str = Field(
        default="gpt-4.1-nano",
        description="Model name to use"
    )
    deployment: str = Field(
        default="gpt-4.1-nano",
        description="Deployment name in Azure"
    )
    api_version: str = Field(
        default="2024-12-01-preview",
        description="Azure OpenAI API version"
    )

    model_config = SettingsConfigDict(
        env_prefix='AZURE_OPENAI_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',  # Ignore non-AZURE_OPENAI env vars
        protected_namespaces=()  # Allow 'model_' prefix in field names
    )


class AIDisambiguationSettings(BaseSettings):
    """
    AI-assisted SQL disambiguation configuration.

    Controls when and how AI is used to resolve ambiguous table references.
    """
    enabled: bool = Field(
        default=True,
        description="Enable AI disambiguation feature"
    )
    confidence_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Parser confidence threshold to trigger AI (SPs ≤ this value use AI)"
    )
    min_confidence: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Minimum AI confidence to accept result (below this falls back to parser)"
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts with refined prompts"
    )
    timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        description="API timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_prefix='AI_',
        case_sensitive=False
    )

    @field_validator('min_confidence')
    @classmethod
    def min_less_than_threshold(cls, v: float, info) -> float:
        """Validate that min_confidence < confidence_threshold."""
        # Note: info.data contains other field values
        threshold = info.data.get('confidence_threshold', 0.85)
        if v >= threshold:
            raise ValueError(
                f'min_confidence ({v}) must be < confidence_threshold ({threshold})'
            )
        return v


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


class Settings(BaseSettings):
    """
    Main application settings.

    Aggregates all configuration sections and provides a single
    entry point for the entire application configuration.

    Usage:
        from lineage_v3.config import settings

        # Type-safe access
        print(settings.ai.confidence_threshold)  # 0.85
        print(settings.azure_openai.deployment)  # "gpt-4.1-nano"
    """
    # Nested configuration sections
    azure_openai: AzureOpenAISettings = Field(
        default_factory=AzureOpenAISettings
    )
    ai: AIDisambiguationSettings = Field(
        default_factory=AIDisambiguationSettings
    )
    parser: ParserSettings = Field(
        default_factory=ParserSettings
    )
    paths: PathSettings = Field(
        default_factory=PathSettings
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

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignore extra env vars not defined here
    )

    @property
    def ai_available(self) -> bool:
        """Check if Azure OpenAI is properly configured and available."""
        return (
            self.ai.enabled and
            self.azure_openai.endpoint is not None and
            self.azure_openai.api_key is not None
        )


# Singleton instance - import this throughout the application
from pydantic_core import ValidationError

try:
    settings = Settings()
except ValidationError as e:
    # Graceful fallback for Pydantic nested BaseSettings validation bug
    # This happens when nested settings fail to inherit env vars properly
    error_str = str(e)
    if 'AzureOpenAISettings' in error_str or 'AZURE_OPENAI' in error_str:
        import os
        import warnings
        from pathlib import Path

        # Manually load .env file since Pydantic failed
        # Path: settings.py → config/ → lineage_v3/ → sandbox/ → .env
        env_file = Path(__file__).parent.parent.parent / '.env'
        env_vars = {}
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        endpoint = env_vars.get('AZURE_OPENAI_ENDPOINT') or os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = env_vars.get('AZURE_OPENAI_API_KEY') or os.getenv('AZURE_OPENAI_API_KEY')

        if endpoint and api_key:
            # Credentials exist in .env - manually create settings
            settings = Settings(
                azure_openai=AzureOpenAISettings(
                    endpoint=endpoint,
                    api_key=SecretStr(api_key),
                    model_name=env_vars.get('AZURE_OPENAI_MODEL_NAME', 'gpt-4.1-nano'),
                    deployment=env_vars.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1-nano'),
                    api_version=env_vars.get('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
                )
            )
        else:
            # Credentials actually missing - disable AI
            warnings.warn(
                "Azure OpenAI configuration missing. "
                "AI-assisted parsing will be disabled. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env to enable AI features.",
                UserWarning
            )
            settings = Settings(
                azure_openai=AzureOpenAISettings()  # Empty - AI disabled
            )
    else:
        # Different validation error - re-raise
        raise
except Exception as e:
    # Non-validation error - re-raise
    raise
