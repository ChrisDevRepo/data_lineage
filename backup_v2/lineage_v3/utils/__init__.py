"""
Utilities Module

Shared utility functions and configuration management.

Modules:
    - config: Load and validate environment variables from .env
    - incremental: Track modify_date for incremental parsing
    - db_helper: Synapse database helper for testing and verification (dev only)
    - duckdb_helper: DuckDB workspace helper for testing and verification (dev only)
    - validators: Input validation and sanitization
"""

# Import commonly used utilities for convenience
try:
    from .db_helper import SynapseHelper
    from .validators import sanitize_identifier, validate_object_id, validate_object_type
    __all__ = ['SynapseHelper', 'sanitize_identifier', 'validate_object_id', 'validate_object_type']
except ImportError:
    # db_helper may not be available in production environments
    try:
        from .validators import sanitize_identifier, validate_object_id, validate_object_type
        __all__ = ['sanitize_identifier', 'validate_object_id', 'validate_object_type']
    except ImportError:
        __all__ = []

# DuckDB helper is standalone - import directly when needed:
# from lineage_v3.utils.duckdb_helper import DuckDBHelper
