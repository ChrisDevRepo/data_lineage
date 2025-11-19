"""
Centralized Configuration Module
=================================

Type-safe configuration management using Pydantic Settings.

This module provides a single source of truth for all configuration,
replacing scattered os.getenv() calls throughout the codebase.

Author: Vibecoding
Version: 1.0.0
Date: 2025-10-31
"""

from engine.config.settings import (
    settings,
    Settings,
    ParserSettings,
    PathSettings,
)

__all__ = [
    'settings',
    'Settings',
    'ParserSettings',
    'PathSettings',
]
