# PySpark DMV Extractor

**Status:** 🚧 **Week 1 Implementation** (Not yet started)

## Overview

PySpark notebook for extracting DMV data from Azure Synapse Dedicated SQL Pool.

**Replaces:** `lineage_v3/extractor/synapse_dmv_extractor.py` (Python + ODBC)

**New Approach:** GUI-based extraction in Synapse Studio (no local Python installation required)

## Files

- `synapse_pyspark_dmv_extractor.py` - PySpark notebook (Synapse format)
- `synapse_pyspark_dmv_extractor.ipynb` - Jupyter notebook format (optional)
- `README_USER_GUIDE.md` - User guide with screenshots

## Usage

1. Open Synapse Studio
2. Navigate to: Develop → Notebooks
3. Click "+ Import" and select `synapse_pyspark_dmv_extractor.py`
4. Edit configuration (Cell 1):
   - SYNAPSE_SQL_POOL
   - DATABASE_NAME
   - OUTPUT_PATH (ADLS Gen2)
5. Click "Run All"
6. Download Parquet files from ADLS

## Output Files

- `objects.parquet` - Tables, Views, Stored Procedures
- `dependencies.parquet` - DMV dependencies (Views only)
- `definitions.parquet` - DDL text
- `query_logs.parquet` - Query execution logs (optional)

## Implementation Timeline

**Week 1 (5 days):**
- Day 1-2: Create PySpark script
- Day 3: Create Synapse notebook
- Day 4: Testing
- Day 5: Documentation

## Reference

See [docs/IMPLEMENTATION_SPEC_FINAL.md](../docs/IMPLEMENTATION_SPEC_FINAL.md) - Section 4
