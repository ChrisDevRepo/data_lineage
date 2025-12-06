"""
Custom exception hierarchy for Data Lineage Visualizer.

All exceptions inherit from LineageError to allow catching all app-specific errors.
"""

from typing import Optional, Dict, Type


class LineageError(Exception):
    """Base class for all lineage exceptions."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.details = details or {}
        super().__init__(message)


# ============================================================================
# PARSING ERRORS
# ============================================================================

class ParsingError(LineageError):
    """Base class for parsing errors."""
    pass


class DDLNotFoundError(ParsingError):
    """
    Raised when DDL (CREATE PROCEDURE/VIEW/FUNCTION) is not found for an object.
    """
    pass


class InvalidSQLError(ParsingError):
    """
    Raised when SQL is syntactically invalid or malformed.
    """
    pass


# ============================================================================
# CATALOG ERRORS
# ============================================================================

class CatalogError(LineageError):
    """Base class for catalog/schema errors."""
    pass


class InvalidSchemaError(CatalogError):
    """
    Raised when schema name is invalid or suspicious.
    """
    pass


class InvalidObjectError(CatalogError):
    """
    Raised when object reference is invalid (name, ID, type, etc.).
    """
    pass


class CatalogResolutionError(CatalogError):
    """
    Raised when unable to resolve table/object reference to catalog.
    """
    pass


# ============================================================================
# WORKSPACE ERRORS
# ============================================================================

class WorkspaceError(LineageError):
    """Base class for DuckDB workspace errors."""
    pass


class WorkspaceNotConnectedError(WorkspaceError):
    """
    Raised when attempting operation on disconnected DuckDB workspace.
    """
    pass


class WorkspaceFileNotFoundError(WorkspaceError):
    """
    Raised when required parquet file is missing.
    """
    pass


class WorkspaceMappingError(WorkspaceError):
    """
    Raised when file mapping is missing or incorrect.
    """
    pass


# ============================================================================
# CONFIGURATION ERRORS
# ============================================================================

class ConfigurationError(LineageError):
    """Base class for configuration errors."""
    pass


class InvalidDialectError(ConfigurationError):
    """
    Raised when SQL dialect is invalid or unsupported.
    """
    pass


class InvalidSettingError(ConfigurationError):
    """
    Raised when configuration setting is invalid.
    """
    pass


# ============================================================================
# RULE ENGINE ERRORS
# ============================================================================

class RuleEngineError(LineageError):
    """Base class for rule engine errors."""
    pass


class RuleLoadError(RuleEngineError):
    """
    Raised when unable to load YAML rule file.
    """
    pass


class RuleValidationError(RuleEngineError):
    """
    Raised when rule fails validation (missing fields, invalid pattern, etc.).
    """
    pass


class RuleExecutionError(RuleEngineError):
    """
    Raised when rule fails during execution.
    """
    pass


# ============================================================================
# BACKGROUND JOB ERRORS
# ============================================================================

class JobError(LineageError):
    """Base class for background job errors."""
    pass


class JobNotFoundError(JobError):
    """Base class for Job Not Found errors."""
    pass


class JobFailedError(JobError):
    """Base class for Job Failed errors."""
    pass


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(LineageError):
    """Base class for input validation errors."""
    pass


class InvalidIdentifierError(ValidationError):
    """
    Raised when identifier (schema, table, column name) is invalid.
    """
    pass


class SQLInjectionRiskError(ValidationError):
    """
    Raised when input contains SQL injection indicators.
    """
    pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_exception_for_error_type(error_type: str) -> type[LineageError]:
    """
    Get exception class by error type string.

    Useful for dynamically raising exceptions based on configuration.

    Args:
        error_type: Error type name (e.g., "DDLNotFoundError")

    Returns:
        Exception class

    Raises:
        ValueError: If error_type is not a valid exception class
    """
    exception_map = {
        'ParsingError': ParsingError,
        'DDLNotFoundError': DDLNotFoundError,
        'InvalidSQLError': InvalidSQLError,
        'CatalogError': CatalogError,
        'InvalidSchemaError': InvalidSchemaError,
        'InvalidObjectError': InvalidObjectError,
        'CatalogResolutionError': CatalogResolutionError,
        'WorkspaceError': WorkspaceError,
        'WorkspaceNotConnectedError': WorkspaceNotConnectedError,
        'WorkspaceFileNotFoundError': WorkspaceFileNotFoundError,
        'WorkspaceMappingError': WorkspaceMappingError,
        'ConfigurationError': ConfigurationError,
        'InvalidDialectError': InvalidDialectError,
        'InvalidSettingError': InvalidSettingError,
        'RuleEngineError': RuleEngineError,
        'RuleLoadError': RuleLoadError,
        'RuleValidationError': RuleValidationError,
        'RuleExecutionError': RuleExecutionError,
        'JobError': JobError,
        'JobNotFoundError': JobNotFoundError,
        'JobFailedError': JobFailedError,
        'ValidationError': ValidationError,
        'InvalidIdentifierError': InvalidIdentifierError,
        'SQLInjectionRiskError': SQLInjectionRiskError,
    }

    if error_type not in exception_map:
        raise ValueError(
            f"Unknown error type: {error_type}. "
            f"Available: {', '.join(exception_map.keys())}"
        )

    return exception_map[error_type]
