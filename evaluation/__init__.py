"""
Evaluation Module for sub_DL_OptimizeParsing

This module provides autonomous evaluation tools for tracking parsing quality
improvements over time. It does NOT modify production parsing code.

Components:
- baseline_manager.py: Baseline CRUD operations
- evaluation_runner.py: Core evaluation logic (run all 3 methods)
- score_calculator.py: Precision/recall/F1 computation
- report_generator.py: Console + JSON report generation
- schemas.py: DuckDB schema definitions

Author: Claude Code Agent
Date: 2025-11-02
Version: 1.0
"""

__version__ = "1.0.0"
