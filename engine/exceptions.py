"""
Custom Exception Hierarchy for Data Lineage Visualizer

Provides clear, specific exceptions for different error scenarios to improve
debugging and error handling throughout the application.

Version: 1.0.0
Date: 2025-11-14
"""


class LineageError(Exception):
    """
    Base exception for all lineage-related errors.

    All custom exceptions in this module inherit from this class,
    making it easy to catch all lineage-specific errors.
    """
    pass


# ============================================================================
# PARSING ERRORS
# ============================================================================

class ParsingError(LineageError):
    """Base class for all parsing-related errors."""
    pass


class DDLNotFoundError(ParsingError):
    """
    Raised when DDL (CREATE PROCEDURE/VIEW/FUNCTION) is not found for an object.

    Example:
        >>> if not ddl_text:
        ...     raise DDLNotFoundError(f"No DDL found for object_id={object_id}")
    """
    pass


class InvalidSQLError(ParsingError):
    """
    Raised when SQL is syntactically invalid or malformed.

    Example:
        >>> if not sql or not sql.strip():
        ...     raise InvalidSQLError("Empty SQL provided")
    """
    pass


# ============================================================================
# CATALOG & VALIDATION ERRORS
# ============================================================================

class CatalogError(LineageError):
    """Base class for catalog resolution and validation errors."""
    pass


class InvalidSchemaError(CatalogError):
    """
    Raised when schema name is invalid or suspicious.

    Example:
        >>> if schema_name in EXCLUDED_SCHEMAS:
        ...     raise InvalidSchemaError(f"Schema '{schema_name}' is excluded")
    """
    pass


class InvalidObjectError(CatalogError):
    """
    Raised when object reference is invalid (name, ID, type, etc.).

    Example:
        >>> if object_id < 0 and object_id != PHANTOM_ID:
        ...     raise InvalidObjectError(f"Invalid object_id: {object_id}")
    """
    pass


class CatalogResolutionError(CatalogError):
    """
    Raised when unable to resolve table/object reference to catalog.

    Example:
        >>> if object_id is None:
        ...     raise CatalogResolutionError(
        ...         f"Failed to resolve '{table_ref}' in catalog"
        ...     )
    """
    pass


# ============================================================================
# WORKSPACE & DATABASE ERRORS
# ============================================================================

class WorkspaceError(LineageError):
    """Base class for workspace-related errors."""
    pass


class WorkspaceNotConnectedError(WorkspaceError):
    """
    Raised when attempting operation on disconnected DuckDB workspace.

    Example:
        >>> if not self.conn:
        ...     raise WorkspaceNotConnectedError("Not connected to DuckDB workspace")
    """
    pass


class WorkspaceFileNotFoundError(WorkspaceError):
    """
    Raised when required parquet file is missing.

    Example:
        >>> if not file_path.exists():
        ...     raise WorkspaceFileNotFoundError(f"Required file not found: {file_path}")
    """
    pass


class WorkspaceMappingError(WorkspaceError):
    """
    Raised when file mapping is missing or incorrect.

    Example:
        >>> if table_name not in file_mappings:
        ...     raise WorkspaceMappingError(f"Missing file mapping for '{table_name}'")
    """
    pass


# ============================================================================
# CONFIGURATION ERRORS
# ============================================================================

class ConfigurationError(LineageError):
    """Base class for configuration-related errors."""
    pass


class InvalidDialectError(ConfigurationError):
    """
    Raised when SQL dialect is invalid or unsupported.

    Example:
        >>> if dialect not in SUPPORTED_DIALECTS:
        ...     raise InvalidDialectError(
        ...         f"Unsupported dialect: {dialect}. Supported: {SUPPORTED_DIALECTS}"
        ...     )
    """
    pass


class InvalidSettingError(ConfigurationError):
    """
    Raised when configuration setting is invalid.

    Example:
        >>> if not excluded_schemas:
        ...     raise InvalidSettingError("EXCLUDED_SCHEMAS cannot be empty")
    """
    pass


# ============================================================================
# RULE ENGINE ERRORS
# ============================================================================

class RuleEngineError(LineageError):
    """Base class for SQL cleaning rule engine errors."""
    pass


class RuleLoadError(RuleEngineError):
    """
    Raised when unable to load YAML rule file.

    Example:
        >>> if not rule_file.exists():
        ...     raise RuleLoadError(f"Rule file not found: {rule_file}")
    """
    pass


class RuleValidationError(RuleEngineError):
    """
    Raised when rule fails validation (missing fields, invalid pattern, etc.).

    Example:
        >>> if 'pattern' not in rule_data:
        ...     raise RuleValidationError(f"Rule missing 'pattern' field: {rule_file}")
    """
    pass


class RuleExecutionError(RuleEngineError):
    """
    Raised when rule fails during execution.

    Example:
        >>> try:
        ...     result = re.sub(pattern, replacement, sql)
        ... except Exception as e:
        ...     raise RuleExecutionError(f"Rule '{rule_name}' failed: {e}")
    """
    pass


# ============================================================================
# BACKGROUND JOB ERRORS
# ============================================================================

class JobError(LineageError):
    """Base class for background job errors."""
    pass


class JobNotFoundError(JobError):
    """
    Raised when job ID doesn't exist.

    Example:
        >>> if job_id not in job_status:
        ...     raise JobNotFoundError(f"Job not found: {job_id}")
    """
    pass


class JobFailedError(JobError):
    """
    Raised when background job processing fails.

    Example:
        >>> if parsing_errors > MAX_ALLOWED_ERRORS:
        ...     raise JobFailedError(
        ...         f"Job failed: {parsing_errors} parsing errors (max: {MAX_ALLOWED_ERRORS})"
        ...     )
    """
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

    Example:
        >>> if ';' in identifier:
        ...     raise InvalidIdentifierError(f"Identifier contains ';': {identifier}")
    """
    pass


class SQLInjectionRiskError(ValidationError):
    """
    Raised when input contains SQL injection indicators.

    Example:
        >>> if 'DROP TABLE' in user_input.upper():
        ...     raise SQLInjectionRiskError(f"Suspicious keyword in input: {user_input}")
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

    Example:
        >>> exc_class = get_exception_for_error_type("DDLNotFoundError")
        >>> raise exc_class("DDL not found for object 123")
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


# ============================================================================
# EXCEPTION HIERARCHY DIAGRAM
# ============================================================================

"""
Exception Hierarchy:

LineageError (base)
├── ParsingError
│   ├── DDLNotFoundError
│   └── InvalidSQLError
├── CatalogError
│   ├── InvalidSchemaError
│   ├── InvalidObjectError
│   └── CatalogResolutionError
├── WorkspaceError
│   ├── WorkspaceNotConnectedError
│   ├── WorkspaceFileNotFoundError
│   └── WorkspaceMappingError
├── ConfigurationError
│   ├── InvalidDialectError
│   └── InvalidSettingError
├── RuleEngineError
│   ├── RuleLoadError
│   ├── RuleValidationError
│   └── RuleExecutionError
├── JobError
│   ├── JobNotFoundError
│   └── JobFailedError
└── ValidationError
    ├── InvalidIdentifierError
    └── SQLInjectionRiskError
"""
