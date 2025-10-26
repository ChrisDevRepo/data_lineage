"""
Parsers Module - SQLGlot-based SQL parsing

This module provides SQL parsing capabilities using SQLGlot AST traversal
to extract table-level lineage from DDL definitions.

Modules:
    - sqlglot_parser: Step 5 - Parse DDL using SQLGlot AST traversal

Author: Vibecoding
Version: 3.0.0
Date: 2025-10-26
"""

from .sqlglot_parser import SQLGlotParser

__all__ = ['SQLGlotParser']
