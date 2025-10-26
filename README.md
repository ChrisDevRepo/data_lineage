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

### 2. Generate Data Lineage

```bash
# Run lineage analysis (incremental mode - default)
python3 lineage_v3/main.py run --parquet parquet_snapshots/

# Full refresh mode (re-parse all objects)
python3 lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

**Current Status:** Phase 4 complete - SQLGlot Parser operational
**Output:** DuckDB workspace with gap detection and parser integration (Steps 6-8 coming in Phase 5-7)

---

## 📊 Current Status

### ✅ Completed Phases

**Phase 2 - Production DMV Extractor**
- Standalone script to export Synapse metadata to Parquet
- Full CLI with .env support
- Tested and validated

**Phase 3 - Core Engine (DuckDB Workspace)** ✅
- Persistent DuckDB workspace with schema initialization
- Parquet ingestion for all 4 input files
- Incremental load metadata tracking (90%+ performance improvement)
- Query interface for DMV data access
- Full test coverage and CLI integration
- See [lineage_v3/core/README.md](lineage_v3/core/README.md)

**Phase 4 - SQLGlot Parser (Gap Detection & DDL Parsing)** ✅ **NEW**
- Gap detector identifies objects with missing dependencies
- AST-based SQL parser for T-SQL DDL extraction
- Views: 100% success rate on production data
- Stored Procedures: 12.5% success (87.5% require AI fallback - as designed)
- Critical confidence bug fixed (failed parses return 0.0, not 0.85)
- Comprehensive validation with production data
- See [lineage_v3/parsers/README.md](lineage_v3/parsers/README.md)
- See [docs/PHASE_4_COMPLETE.md](docs/PHASE_4_COMPLETE.md) for details

### 🚧 Next: Phase 5 - AI Fallback Framework (CRITICAL)

---

## 📚 Documentation

### Core Documentation
- **[lineage_specs.md](lineage_specs.md)** - Complete parser v2.0 specification
- **[CLAUDE.md](CLAUDE.md)** - Development guide and project overview
- **[requirements.txt](requirements.txt)** - Python dependencies

### Component Documentation
- **[lineage_v3/extractor/README.md](lineage_v3/extractor/README.md)** - DMV extractor guide
- **[lineage_v3/core/README.md](lineage_v3/core/README.md)** - Core engine documentation
- **[docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md)** - Complete database schema reference
- **[docs/PHASE_3_COMPLETE.md](docs/PHASE_3_COMPLETE.md)** - Phase 3 completion summary

---

**Last Updated:** 2025-10-26
**Parser Version:** 3.0.0 (Phase 3 Complete)
