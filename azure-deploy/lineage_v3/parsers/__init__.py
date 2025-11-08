"""
Parsers Module - Production SQL Parsing (v4.0.0 - Slim)

This module provides SQL parsing capabilities for extracting table-level
lineage from T-SQL stored procedures, views, and functions.

Active Parsers:
    - quality_aware_parser: Main production parser with SQLGlot + regex baseline
    - query_log_validator: Cross-validates parsed SPs with query log evidence (0.85 → 0.95 boost)

Architecture:
    - Regex baseline for quality checking
    - SQLGlot AST parsing with preprocessing
    - Rule engine for data cleansing (future enhancement)

Deprecated Parsers:
    - sqlglot_parser: Moved to deprecated/ (replaced by quality_aware_parser)
    - enhanced_sqlglot_parser: Moved to deprecated/ (replaced by quality_aware_parser)
    - dual_parser: Moved to deprecated/ (replaced by quality_aware_parser)
    - ai_disambiguator: Removed in v4.0.0 (focusing on slim architecture)

Author: Vibecoding
Version: 4.0.0 (Slim - No AI)
Date: 2025-11-03
"""

from .quality_aware_parser import QualityAwareParser
from .query_log_validator import QueryLogValidator

__all__ = [
    'QualityAwareParser',
    'QueryLogValidator'
]
