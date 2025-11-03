"""
Validation module for AI inference results.
Provides multi-layer validation to ensure accuracy before accepting AI suggestions.
"""

from .validation_engine import ValidationEngine, ValidationResult

__all__ = ['ValidationEngine', 'ValidationResult']
