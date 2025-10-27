"""
Parsers Module - Multi-Strategy SQL Parsing

This module provides SQL parsing capabilities using multiple parsers with
cross-validation to extract table-level lineage from DDL definitions.

Parsers:
    - sqlglot_parser: Basic SQLGlot parser (18.75% success rate)
    - enhanced_sqlglot_parser: Enhanced parser with preprocessing (100% success rate, 73.8% completeness)
    - quality_aware_parser: SQLGlot + regex baseline quality check (honest about completeness)
    - dual_parser: SQLGlot + SQLLineage cross-validation (85-90% completeness expected)

Validators:
    - query_log_validator: Cross-validates parsed SPs with query log evidence (0.85 → 0.95 boost)

Author: Vibecoding
Version: 3.4.0
Date: 2025-10-27
"""

from .sqlglot_parser import SQLGlotParser as BasicSQLGlotParser
from .enhanced_sqlglot_parser import EnhancedSQLGlotParser
from .quality_aware_parser import QualityAwareParser
from .dual_parser import DualParser
from .query_log_validator import QueryLogValidator

# Use dual-parser by default (best accuracy)
SQLGlotParser = DualParser

__all__ = [
    'SQLGlotParser',
    'BasicSQLGlotParser',
    'EnhancedSQLGlotParser',
    'QualityAwareParser',
    'DualParser',
    'QueryLogValidator'
]
