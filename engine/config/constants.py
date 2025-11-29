#!/usr/bin/env python3
"""
Configuration Constants
=======================

Centralized constants used across the data lineage system.
Single source of truth for default values and configuration.

Author: Vibecoding
Version: 1.0.0
Date: 2025-11-23
"""

# Default schemas to exclude from ALL processing (metadata, parsing, analysis)
# These are system schemas that should never be processed for lineage
DEFAULT_EXCLUDED_SCHEMAS = [
    'sys',
    'dummy',
    'information_schema',
    'INFORMATION_SCHEMA',  # Case variation for compatibility
    'tempdb',
    'master',
    'msdb',
    'model'
]

# Comma-separated string version (for environment variables and settings)
DEFAULT_EXCLUDED_SCHEMAS_STRING = ','.join([
    s for s in DEFAULT_EXCLUDED_SCHEMAS
    if s.lower() not in ['information_schema']  # Avoid duplicates (case-insensitive)
    or s == 'information_schema'  # Keep one lowercase version
])

# Set version (for efficient lookup)
DEFAULT_EXCLUDED_SCHEMAS_SET = {
    'sys',
    'dummy',
    'information_schema',  # Normalized to lowercase
    'tempdb',
    'master',
    'msdb',
    'model'
}
