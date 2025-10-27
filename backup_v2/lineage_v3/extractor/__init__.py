"""
Synapse DMV Extractor Module

Production-ready utility to export Azure Synapse metadata (DMVs) to Parquet files.
This tool is designed for external users who need to generate Parquet snapshots
for use with the Vibecoding Lineage Parser v2.0.

Modules:
    - synapse_dmv_extractor: Main extractor class and CLI
        - SynapseDMVExtractor: Core extraction class
        - main(): CLI entry point

Usage:
    # As standalone script
    python lineage_v3/extractor/synapse_dmv_extractor.py --output parquet_snapshots/

    # As imported module
    from lineage_v3.extractor.synapse_dmv_extractor import SynapseDMVExtractor

    extractor = SynapseDMVExtractor(
        server='yourserver.sql.azuresynapse.net',
        database='yourdatabase',
        username='youruser',
        password='yourpassword',
        output_dir='parquet_snapshots'
    )
    extractor.extract_all()
"""

from .synapse_dmv_extractor import SynapseDMVExtractor

__all__ = ['SynapseDMVExtractor']
