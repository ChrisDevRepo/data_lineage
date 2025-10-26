# Vibecoding Lineage Parser v3 - Documentation

**Version:** 3.0.0
**Status:** In Development (Phase 1 Complete)
**Last Updated:** 2025-10-26

---

## Quick Links

- **Main Specification:** [../lineage_specs_v2.md](../lineage_specs_v2.md) (v2.1)
- **Project Guide:** [../CLAUDE.md](../CLAUDE.md)
- **Environment Setup:** [../.env.template](../.env.template)
- **Requirements:** [../requirements.txt](../requirements.txt)

---

## Documentation Index

### Getting Started
1. [Installation Guide](#installation-guide)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)

### Architecture
4. [System Architecture](ARCHITECTURE.md) - Coming Soon
5. [Data Flow](DATA_FLOW.md) - Coming Soon
6. [Confidence Model](CONFIDENCE_MODEL.md) - Coming Soon

### Usage
7. [CLI Reference](CLI_REFERENCE.md) - Coming Soon
8. [Parquet Schema](PARQUET_SCHEMA.md) - Coming Soon
9. [JSON Output Format](JSON_OUTPUT_FORMAT.md) - Coming Soon

### Development
10. [Development Guide](DEVELOPMENT_GUIDE.md) - Coming Soon
11. [Testing Guide](TESTING_GUIDE.md) - Coming Soon
12. [Contributing](CONTRIBUTING.md) - Coming Soon

### Legacy Documentation
- [v2 Archived Docs](../deprecated/) - Old v2 implementation

---

## Installation Guide

### Prerequisites

- Python >= 3.10
- Azure Synapse Dedicated SQL Pool (for DMV extraction in dev)
- Azure AI Foundry endpoint (for AI fallback)

### Steps

```bash
# 1. Clone repository
cd /path/to/ws-psidwh

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.template .env
# Edit .env with your credentials

# 5. Validate setup
python lineage_v3/main.py validate
```

---

## Quick Start

### Development Mode (With Synapse Access)

```bash
# Step 1: Extract DMV metadata to Parquet
python lineage_v3/main.py extract --output parquet_snapshots/

# Step 2: Run lineage analysis
python lineage_v3/main.py run --parquet parquet_snapshots/

# Output files generated in lineage_output/:
# - lineage.json (internal format with int object_ids)
# - frontend_lineage.json (frontend format with string node_ids)
# - lineage_summary.json (coverage statistics)
```

### Production Mode (Pre-exported Parquet)

```bash
# Obtain Parquet files from DBA team
# Place in parquet_snapshots/ directory:
# - objects.parquet
# - dependencies.parquet
# - definitions.parquet
# - query_logs.parquet (optional)

# Run lineage analysis
python lineage_v3/main.py run --parquet parquet_snapshots/
```

---

## Environment Configuration

### Required Variables (.env)

```bash
# Azure Synapse (Dev Only)
SYNAPSE_SERVER=<your-server>.sql.azuresynapse.net
SYNAPSE_DATABASE=<database-name>
SYNAPSE_USERNAME=<username>
SYNAPSE_PASSWORD=<password>

# Azure AI Foundry
AI_FOUNDRY_ENDPOINT=<endpoint-url>
AI_FOUNDRY_API_KEY=<api-key>
AI_FOUNDRY_DEPLOYMENT_NAME=<model-name>

# DuckDB
DUCKDB_PATH=lineage_workspace.duckdb

# Output
OUTPUT_DIR=lineage_output
OUTPUT_FORMAT=both  # internal|frontend|both
```

### Optional Variables

```bash
# Incremental Load
ENABLE_INCREMENTAL_LOAD=true
FORCE_FULL_REFRESH=false

# Parser Configuration
MIN_CONFIDENCE_THRESHOLD=0.5
SKIP_QUERY_LOG_ANALYSIS=false
AI_MAX_RETRIES=3
AI_TIMEOUT_SECONDS=30

# Logging
LOG_LEVEL=INFO
ENABLE_RICH_CONSOLE=true
```

---

## Output Files

### lineage.json (Internal Format)

Integer `object_id` based format for internal processing:

```json
{
  "id": 1001,
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "inputs": [2002],
  "outputs": [3003],
  "provenance": {
    "primary_source": "dmv",
    "confidence": 1.0
  }
}
```

### frontend_lineage.json (Frontend Format)

String `node_X` based format for React Flow visualization:

```json
{
  "id": "node_0",
  "name": "DimCustomers",
  "schema": "CONSUMPTION_FINANCE",
  "object_type": "Table",
  "description": "",
  "data_model_type": "Dimension",
  "inputs": ["node_1"],
  "outputs": ["node_2", "node_3"]
}
```

### lineage_summary.json (Statistics)

Coverage and quality metrics:

```json
{
  "total_objects": 2500,
  "coverage_percent": 0.95,
  "unresolved_objects": 125,
  "confidence_counts": {
    "dmv": 1800,
    "query_log": 300,
    "parser": 200,
    "ai": 75
  },
  "object_type_counts": {
    "Table": 1500,
    "View": 850,
    "Stored Procedure": 150
  }
}
```

---

## Common Issues

### "Module not found" Errors

```bash
pip install -r requirements.txt
python lineage_v3/main.py validate
```

### ".env file not found"

```bash
cp .env.template .env
# Edit .env with your credentials
```

### "Parquet files not found"

**Dev Environment:**
```bash
python lineage_v3/main.py extract
```

**Production:**
- Obtain pre-exported Parquet files from DBA team
- Place in `parquet_snapshots/` directory

---

## Support

For issues or questions:
- **Specification:** [../lineage_specs_v2.md](../lineage_specs_v2.md)
- **Project Guide:** [../CLAUDE.md](../CLAUDE.md)
- **v2 Migration:** [../deprecated/README_DEPRECATED.md](../deprecated/README_DEPRECATED.md)

---

**Last Updated:** 2025-10-26
