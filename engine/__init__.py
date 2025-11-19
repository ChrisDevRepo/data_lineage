"""
Vibecoding Lineage Parser v3

A DMV-first data lineage extraction system for Azure Synapse Dedicated SQL Pool.
Uses DuckDB, SQLGlot, and Microsoft Agent Framework for high-accuracy lineage analysis.

Architecture:
    1. Helper Extractor: Synapse DMVs → Parquet snapshots
    2. Core Engine: DuckDB workspace for relational queries
    3. Parser: SQLGlot AST traversal for gap-filling
    4. AI Fallback: Microsoft Agent Framework multi-agent pipeline
    5. Output: Internal (int) + Frontend (string) JSON formats

Author: Vibecoding Team
Version: 0.9.0
License: MIT
"""

__version__ = "0.9.0"
__author__ = "Vibecoding Team"

# Core modules
from engine.exceptions import (
    LineageError,
    ParsingError,
    DDLNotFoundError,
    SQLGlotParsingError,
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
    "SQLGlotParsingError",
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
