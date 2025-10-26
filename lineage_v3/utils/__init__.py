"""
Utilities Module

Shared utility functions and configuration management.

Modules:
    - config: Load and validate environment variables from .env
    - incremental: Track modify_date for incremental parsing
    - db_helper: Database helper for testing and verification (dev only)
"""

# Import commonly used utilities for convenience
try:
    from .db_helper import SynapseHelper
    __all__ = ['SynapseHelper']
except ImportError:
    # db_helper may not be available in production environments
    __all__ = []
