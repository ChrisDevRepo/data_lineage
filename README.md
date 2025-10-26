# Azure Synapse Data Warehouse - Data Lineage Analysis

This repository contains SQL scripts for an Azure Synapse Analytics data warehouse implementation, along with the **Vibecoding Lineage Parser v2.0** - a DMV-first data lineage extraction system.

## 📁 Repository Structure

```
ws-psidwh/
├── Synapse_Data_Warehouse/       # Azure Synapse SQL objects
│   ├── Stored Procedures/        # ETL and data processing procedures
│   ├── Tables/                   # Table definitions
│   └── Views/                    # View definitions
│
├── lineage_v3/                   # Lineage Parser v2.0 (folder name historical)
│   ├── main.py                   # CLI entry point
│   ├── extractor/                # Production DMV extractor
│   │   ├── synapse_dmv_extractor.py
│   │   └── README.md
│   ├── core/                     # DuckDB engine (Phase 3)
│   ├── parsers/                  # SQLGlot parser (Phase 4)
│   ├── ai_analyzer/              # Microsoft Agent Framework (Phase 5)
│   ├── output/                   # JSON formatters (Phase 6)
│   └── utils/                    # Config & incremental support
│
├── deprecated/                   # Archived v1 implementation
├── frontend/                     # React Flow visualization app
├── parquet_snapshots/            # DMV Parquet exports (gitignored)
├── lineage_output/               # Generated lineage JSON files
├── docs/                         # Documentation
├── .env.template                 # Environment config template
├── requirements.txt              # Python dependencies
├── lineage_specs.md              # Parser v2.0 specification (spec v2.1)
├── CLAUDE.md                     # AI assistant instructions
└── README.md                     # This file
```

**Version Note:** The parser is version **2.0** (folder name `lineage_v3` refers to the third development iteration).

---

## 🚀 Quick Start

### 1. Extract DMV Metadata from Synapse

Use the Production Extractor to export metadata from your Azure Synapse database:

```bash
# Configure credentials in .env file
cp .env.template .env
# Edit .env with your Synapse credentials

# Extract DMV data to Parquet files
python3 lineage_v3/extractor/synapse_dmv_extractor.py --output parquet_snapshots/
```

**Output:** 4 Parquet files containing database metadata
See [lineage_v3/extractor/README.md](lineage_v3/extractor/README.md) for details.

### 2. Generate Data Lineage (Coming in Phase 3-8)

```bash
# Run lineage analysis (Phase 3-8 implementation)
python3 lineage_v3/main.py run --parquet parquet_snapshots/
```

---

## 📊 Current Status

### ✅ Completed: Phase 2 - Production DMV Extractor
- Standalone script to export Synapse metadata to Parquet
- Full CLI with .env support
- Tested and validated against live Synapse database

### 🚧 Next: Phase 3 - Core Engine (DuckDB workspace)

---

## 📚 Documentation

- **[lineage_specs.md](lineage_specs.md)** - Complete parser v2.0 specification
- **[CLAUDE.md](CLAUDE.md)** - Development guide
- **[lineage_v3/extractor/README.md](lineage_v3/extractor/README.md)** - DMV extractor documentation

---

**Last Updated:** 2025-10-26  
**Parser Version:** 2.0.0 (Phase 2 Complete)
