"""
Vibecoding Lineage Parser v3

A DMV-first data lineage extraction system for Azure Synapse Dedicated SQL Pool.
Uses DuckDB, SQLGlot, and Microsoft Agent Framework for high-accuracy lineage analysis.

Architecture:
    1. Helper Extractor: Synapse DMVs → Parquet snapshots
    2. Core Engine: DuckDB workspace for relational queries
    3. Parser: SQLGlot AST traversal for gap-filling
    4. AI Fallback: Microsoft Agent Framework multi-agent pipeline
    5. Output: Internal (int) + Frontend (string) JSON formats

Author: Vibecoding Team
Version: 3.0.0
License: MIT
"""

__version__ = "3.0.0"
__author__ = "Vibecoding Team"

# Core modules will be imported here as they are developed
