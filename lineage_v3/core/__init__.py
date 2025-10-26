"""
Core Engine Module

DuckDB-based lineage construction engine.

Modules:
    - duckdb_workspace: DuckDB initialization and Parquet loading
    - baseline_builder: Step 2 - Build baseline from DMV dependencies
    - query_log_enhancer: Step 3 - Enhance from query logs (optional)
    - gap_detector: Step 4 - Detect unresolved stored procedures
    - lineage_merger: Step 7 - Merge all sources and build bidirectional graph
"""
