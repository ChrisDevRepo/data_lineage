"""
Parsers Module - Production SQL Parsing (v0.9.0)

This module provides SQL parsing capabilities for extracting table-level
lineage from stored procedures, views, and functions.

Active Components:
    - quality_aware_parser: Main production parser with SQLGlot + regex baseline
    - YAML rule engine: Dialect-specific preprocessing rules (engine/rules/)
    - query_log_validator: Cross-validates parsed SPs with query log evidence
    - comment_hints_parser: Extracts @LINEAGE_INPUTS/@LINEAGE_OUTPUTS hints

Architecture (4 Phases):
    1. Regex Baseline: Pattern-based table extraction (fast, quality check)
    2. YAML Rules: Dialect-specific SQL preprocessing (17 TSQL rules)
    3. SQLGlot AST: Abstract syntax tree parsing (handles complex SQL)
    4. Confidence Calc: Score based on completeness (0, 75, 85, 100)

YAML Rule Engine (v0.9.0 - New!):
    - 17 TSQL rules migrated from Python (100% coverage)
    - Power users can extend without Python coding
    - Multi-dialect ready (tsql, snowflake, bigquery, oracle, etc.)
    - Multi-step pattern support for complex transformations
    - See engine/rules/README.md for complete documentation

Performance:
    - Overall accuracy: 95.5% (729/763 objects)
    - Stored procedures: 97.0% (196/202 SPs)
    - Speed: ~350 SPs in <30 seconds

Deprecated Parsers:
    - sqlglot_parser: Moved to deprecated/ (replaced by quality_aware_parser)
    - enhanced_sqlglot_parser: Moved to deprecated/ (replaced by quality_aware_parser)
    - dual_parser: Moved to deprecated/ (replaced by quality_aware_parser)
    - ai_disambiguator: Removed in v4.0.0 (focusing on slim architecture)
    - sql_cleaning_rules: Removed in v0.9.0 (migrated to YAML)

Author: Vibecoding
Version: 0.9.0
Date: 2025-11-19
"""

from .quality_aware_parser import QualityAwareParser
from .query_log_validator import QueryLogValidator

__all__ = [
    'QualityAwareParser',
    'QueryLogValidator'
]
