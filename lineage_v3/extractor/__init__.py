"""
Helper Extractor Module

Exports Azure Synapse DMV metadata to Parquet snapshots.
Used during development only - production systems provide pre-exported Parquet files.

Modules:
    - synapse_dmv_extractor: Connects to Synapse and exports DMVs to Parquet
    - schema: Parquet schema definitions for validation
"""
