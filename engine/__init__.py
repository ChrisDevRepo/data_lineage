"""
Data Lineage Visualizer v1.0.0

A data lineage extraction system for SQL databases with focus on Azure Synapse/SQL.
Uses DuckDB and YAML-based regex extraction for dependency analysis.

Architecture:
    1. Data Sources: Database Direct OR Parquet Upload
    2. Core Engine: DuckDB workspace for relational queries
    3. Parser: YAML regex extraction (business-user maintainable)
    4. Output: JSON format for frontend visualization

Author: Christian Wagner
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Vibecoding Team"

# Core modules
from engine.exceptions import (
    LineageError,
    ParsingError,
    DDLNotFoundError,
    InvalidSQLError,
    CatalogError,
    InvalidSchemaError,
    InvalidObjectError,
    CatalogResolutionError,
    WorkspaceError,
    WorkspaceNotConnectedError,
    WorkspaceFileNotFoundError,
    WorkspaceMappingError,
    ConfigurationError,
    InvalidDialectError,
    InvalidSettingError,
    RuleEngineError,
    RuleLoadError,
    RuleValidationError,
    RuleExecutionError,
    JobError,
    JobNotFoundError,
    JobFailedError,
    ValidationError,
    InvalidIdentifierError,
    SQLInjectionRiskError,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Exceptions
    "LineageError",
    "ParsingError",
    "DDLNotFoundError",
    "InvalidSQLError",
    "CatalogError",
    "InvalidSchemaError",
    "InvalidObjectError",
    "CatalogResolutionError",
    "WorkspaceError",
    "WorkspaceNotConnectedError",
    "WorkspaceFileNotFoundError",
    "WorkspaceMappingError",
    "ConfigurationError",
    "InvalidDialectError",
    "InvalidSettingError",
    "RuleEngineError",
    "RuleLoadError",
    "RuleValidationError",
    "RuleExecutionError",
    "JobError",
    "JobNotFoundError",
    "JobFailedError",
    "ValidationError",
    "InvalidIdentifierError",
    "SQLInjectionRiskError",
]
