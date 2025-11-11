"""
YAML Configuration Loader for Dialect and Rule Management.

Loads dialect-specific configuration and SQL cleaning rules from YAML files.
Supports validation, caching, and graceful error handling.

Author: vibecoding
Version: 1.0.0
Date: 2025-11-11
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import yaml

from lineage_v3.config.dialect_config import SQLDialect

logger = logging.getLogger(__name__)


@dataclass
class DialectConfig:
    """Parsed dialect configuration from YAML."""

    dialect: SQLDialect
    display_name: str
    sqlglot_dialect: str

    # Metadata extraction
    metadata_source: str  # dmv | information_schema | system_tables
    objects_query: str
    definitions_query: str
    objects_schema: List[Dict[str, Any]]
    definitions_schema: List[Dict[str, Any]]

    # Query logs
    query_logs_enabled: bool
    query_logs_source: str  # dmv | parquet | csv | disabled
    query_logs_extraction_query: Optional[str]
    query_logs_parquet_path: Optional[str]
    query_logs_schema: List[Dict[str, Any]]
    dynamic_query_patterns: List[Dict[str, Any]]

    # Parsing configuration
    case_sensitive: bool
    identifier_quote_start: str
    identifier_quote_end: str
    string_quote: str
    statement_terminator: str
    batch_separator: Optional[str]
    line_comment: str
    block_comment_start: str
    block_comment_end: str

    # Raw config for extensibility
    raw_config: Dict[str, Any]


class DialectConfigLoader:
    """Loads and caches dialect configurations from YAML files."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the dialect config loader.

        Args:
            config_dir: Directory containing dialect YAML files.
                       Defaults to lineage_v3/config/dialects/
        """
        if config_dir is None:
            config_dir = Path(__file__).parent / "dialects"

        self.config_dir = config_dir
        self._cache: Dict[SQLDialect, DialectConfig] = {}

        logger.info(f"DialectConfigLoader initialized with config_dir: {config_dir}")

    def load(self, dialect: SQLDialect) -> DialectConfig:
        """
        Load configuration for a specific dialect.

        Args:
            dialect: SQL dialect to load configuration for

        Returns:
            DialectConfig object with parsed configuration

        Raises:
            FileNotFoundError: If dialect YAML file doesn't exist
            ValueError: If YAML is invalid or required fields missing
        """
        # Check cache first
        if dialect in self._cache:
            logger.debug(f"Returning cached config for dialect: {dialect.value}")
            return self._cache[dialect]

        # Load from file
        yaml_path = self.config_dir / f"{dialect.value}.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(
                f"Dialect configuration not found: {yaml_path}\n"
                f"Expected file: {dialect.value}.yaml"
            )

        logger.info(f"Loading dialect configuration from: {yaml_path}")

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {yaml_path}: {e}")

        # Validate and parse
        config = self._parse_config(dialect, raw_config)

        # Cache and return
        self._cache[dialect] = config
        logger.info(f"Successfully loaded config for dialect: {dialect.value}")

        return config

    def _parse_config(self, dialect: SQLDialect, raw: Dict[str, Any]) -> DialectConfig:
        """Parse and validate raw YAML config."""

        # Validate required top-level fields
        required_fields = ['dialect', 'display_name', 'sqlglot_dialect', 'metadata', 'query_logs', 'parsing']
        missing = [f for f in required_fields if f not in raw]
        if missing:
            raise ValueError(f"Missing required fields in dialect config: {missing}")

        # Validate dialect matches filename
        if raw['dialect'] != dialect.value:
            logger.warning(
                f"Dialect mismatch: file={dialect.value}, config={raw['dialect']}. "
                f"Using file name: {dialect.value}"
            )

        # Extract metadata config
        metadata = raw['metadata']

        # Extract query logs config
        query_logs = raw['query_logs']

        # Extract parsing config
        parsing = raw['parsing']

        return DialectConfig(
            dialect=dialect,
            display_name=raw['display_name'],
            sqlglot_dialect=raw['sqlglot_dialect'],

            # Metadata extraction
            metadata_source=metadata.get('source', 'information_schema'),
            objects_query=metadata.get('objects_query', ''),
            definitions_query=metadata.get('definitions_query', ''),
            objects_schema=metadata.get('objects_schema', []),
            definitions_schema=metadata.get('definitions_schema', []),

            # Query logs
            query_logs_enabled=query_logs.get('enabled', False),
            query_logs_source=query_logs.get('source', 'disabled'),
            query_logs_extraction_query=query_logs.get('extraction_query'),
            query_logs_parquet_path=query_logs.get('parquet_path'),
            query_logs_schema=query_logs.get('schema', []),
            dynamic_query_patterns=query_logs.get('dynamic_query_patterns', []),

            # Parsing
            case_sensitive=parsing.get('case_sensitive', False),
            identifier_quote_start=parsing.get('identifier_quote_start', '"'),
            identifier_quote_end=parsing.get('identifier_quote_end', '"'),
            string_quote=parsing.get('string_quote', "'"),
            statement_terminator=parsing.get('statement_terminator', ';'),
            batch_separator=parsing.get('batch_separator'),
            line_comment=parsing.get('line_comment', '--'),
            block_comment_start=parsing.get('block_comment_start', '/*'),
            block_comment_end=parsing.get('block_comment_end', '*/'),

            # Store raw for extensibility
            raw_config=raw
        )

    def list_available_dialects(self) -> List[SQLDialect]:
        """List all dialects that have YAML config files."""
        available = []

        for yaml_file in self.config_dir.glob('*.yaml'):
            dialect_str = yaml_file.stem
            try:
                from lineage_v3.config.dialect_config import validate_dialect
                dialect = validate_dialect(dialect_str)
                available.append(dialect)
            except ValueError:
                logger.warning(f"Unknown dialect in config directory: {dialect_str}")

        return sorted(available, key=lambda d: d.value)


# Singleton instance
_loader: Optional[DialectConfigLoader] = None


def get_dialect_config_loader() -> DialectConfigLoader:
    """Get the singleton DialectConfigLoader instance."""
    global _loader
    if _loader is None:
        _loader = DialectConfigLoader()
    return _loader


def load_dialect_config(dialect: SQLDialect) -> DialectConfig:
    """
    Convenience function to load dialect configuration.

    Args:
        dialect: SQL dialect to load

    Returns:
        DialectConfig object

    Example:
        >>> from lineage_v3.config.dialect_config import SQLDialect
        >>> from lineage_v3.config.yaml_loader import load_dialect_config
        >>>
        >>> config = load_dialect_config(SQLDialect.TSQL)
        >>> print(config.display_name)
        'Microsoft SQL Server / Azure Synapse'
        >>> print(config.objects_query[:50])
        'SELECT\\n  o.object_id as database_object_id,\\n  SCHEM'
    """
    loader = get_dialect_config_loader()
    return loader.load(dialect)
