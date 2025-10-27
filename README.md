# Azure Synapse Data Warehouse - Data Lineage Analysis

This repository contains SQL scripts for an Azure Synapse Analytics data warehouse implementation, along with the **Vibecoding Lineage Parser v3.0** - a DMV-first data lineage system with GUI-based workflow.

## 📁 Repository Structure (v3.0)

```
ws-psidwh/
├── Synapse_Data_Warehouse/       # Azure Synapse SQL objects
│   ├── Stored Procedures/        # ETL and data processing procedures
│   ├── Tables/                   # Table definitions
│   └── Views/                    # View definitions
│
├── extractor/                    # ✅ PySpark DMV Extractor (Week 1 Complete)
│   ├── synapse_pyspark_dmv_extractor.py  # Spark job script
│   └── README.md                 # Deployment guide
│
├── api/                          # ✅ FastAPI Backend (Week 2 Complete)
│   ├── main.py                   # 6 endpoints (tested)
│   ├── background_tasks.py       # Background processing
│   ├── models.py                 # Pydantic models
│   ├── README.md                 # API documentation
│   └── TEST_RESULTS.md           # Comprehensive tests
│
├── docker/                       # 🚧 Container Configuration (Week 2-3 Pending)
│   └── README.md                 # Implementation pending
│
├── backup_v2/                    # 📦 v2.0 Backup (CLI-based implementation)
│   ├── lineage_v3/               # Python backend (v2.0)
│   └── frontend/                 # React app (v2.0)
│
├── lineage_v3/                   # Current v2.0 implementation (will be wrapped in v3.0)
│   ├── main.py                   # CLI entry point
│   ├── core/                     # DuckDB engine
│   ├── parsers/                  # SQLGlot parser
│   ├── output/                   # JSON formatters
│   └── utils/                    # Config & helpers
│
├── frontend/                     # React Flow visualization (v2.0 - will be enhanced in v3.0)
├── parquet_snapshots/            # DMV Parquet exports (gitignored)
├── lineage_output/               # Generated lineage JSON files
│
├── docs/                         # 📚 Documentation
│   ├── IMPLEMENTATION_SPEC_FINAL.md  # ⭐ v3.0 Complete Specification
│   ├── PARSING_USER_GUIDE.md     # User guide for SQL parsing
│   ├── DUCKDB_SCHEMA.md          # Database schema reference

│
├── .env.template                 # Environment config template
├── requirements.txt              # Python dependencies
├── lineage_specs.md              # Parser v2.0 specification
├── CLAUDE.md                     # AI assistant instructions
└── README.md                     # This file
```

---

## 🚀 v3.0 Implementation Status

**Current Status:** ✅ **Specification Complete - Week 1-2 Complete**

### Timeline (4 weeks)

| Week | Feature | Status |
|------|---------|--------|
| **Week 1** | PySpark DMV Extractor | ✅ Complete |
| **Week 2-3** | Single Container Deployment | 🚧 Pending |
| **Week 4** | SQL Viewer | 🚧 Pending |

### What's Changing in v3.0

**Before (v2.0):**
```
User → Installs Python locally
     → Runs: python lineage_v3/extractor/synapse_dmv_extractor.py
     → Runs: python lineage_v3/main.py run --parquet ...
     → Uploads frontend_lineage.json to Azure Web App
     → Views graph in browser
```

**After (v3.0):**
```
User → Opens Synapse Studio (browser)
     → Runs PySpark notebook (GUI)
     → Downloads Parquet files
     → Opens web app
     → Uploads Parquet files in browser
     → Sees progress during parsing
     → Views graph + SQL definitions
```

**Key Benefits:**
- ✅ No local Python installation required
- ✅ No CLI commands
- ✅ Full GUI-based workflow
- ✅ Progress updates during parsing
- ✅ View SQL definitions in-app

---

## 📚 Documentation

### v3.0 Specification
- **[docs/IMPLEMENTATION_SPEC_FINAL.md](docs/IMPLEMENTATION_SPEC_FINAL.md)** - ⭐ **Complete v3.0 specification**
  - Architecture overview with diagrams
  - 4-week implementation timeline
  - Code examples for all features
  - Risk assessment & testing strategy
  - 2,292 lines of detailed specifications

### User Guides
- **[docs/PARSING_USER_GUIDE.md](docs/PARSING_USER_GUIDE.md)** - SQL parsing best practices
- **[docs/DUCKDB_SCHEMA.md](docs/DUCKDB_SCHEMA.md)** - Database schema reference

### v2.0 Technical Docs
- **[lineage_specs.md](lineage_specs.md)** - Parser v2.0 specification
- **[CLAUDE.md](CLAUDE.md)** - Development guide and project overview
- **[lineage_v3/core/README.md](lineage_v3/core/README.md)** - DuckDB workspace docs
- **[lineage_v3/parsers/README.md](lineage_v3/parsers/README.md)** - SQLGlot parser docs
- **[frontend/docs/](frontend/docs/)** - Frontend application docs

### Historical Docs

---

## 🏗️ v3.0 Implementation Folders

### [extractor/](extractor/)
**PySpark DMV Extractor** (Week 1)
- GUI-based extraction in Synapse Studio
- No local Python installation required
- Outputs to ADLS Gen2
- See [extractor/README.md](extractor/README.md)

### [api/](api/)
**FastAPI Backend** (Week 2-3)
- Wraps existing `lineage_v3` code (unchanged)
- Upload Parquet files via browser
- Poll for status every 2 seconds
- Returns lineage JSON with DDL text
- See [api/README.md](api/README.md)

### [docker/](docker/)
**Single Container Deployment** (Week 2-3)
- Multi-stage build: Frontend + Backend
- FastAPI serves React static files
- Ephemeral job storage in `/tmp/jobs/`
- See [docker/README.md](docker/README.md)

---

## 📋 v2.0 Current Functionality (Still Works!)

The v2.0 implementation is **fully operational** and backed up in `backup_v2/`.

### Quick Start (v2.0 CLI)

#### 1. Extract DMV Metadata

```bash
# Configure credentials
cp .env.template .env
# Edit .env with your Synapse credentials

# Extract DMV data
python3 lineage_v3/extractor/synapse_dmv_extractor.py --output parquet_snapshots/
```

#### 2. Generate Lineage

```bash
# Run lineage analysis (incremental mode)
python3 lineage_v3/main.py run --parquet parquet_snapshots/

# Full refresh mode
python3 lineage_v3/main.py run --parquet parquet_snapshots/ --full-refresh
```

**Output:** 3 JSON files in `lineage_output/`
- `lineage.json` - Internal format (integer object_ids)
- `frontend_lineage.json` - Frontend format (string node_ids)
- `lineage_summary.json` - Statistics

#### 3. Visualize

Upload `lineage_output/frontend_lineage.json` to the React app (see [frontend/README.md](frontend/README.md)).

---

## 🔄 Version History

- **v2.0** (Current) - CLI-based, DMV-first parser with DuckDB workspace ✅ **Production Ready**
- **v3.0** (In Development) - GUI-based workflow with single container deployment 🚧 **Spec Complete**

---

## 🛠️ Development

**Branch:** `feature/v3-implementation`

**v2.0 Backup:** All current code saved in `backup_v2/`

**Next Steps:**
1. Week 1: Implement PySpark DMV extractor
2. Week 2-3: Implement single container deployment
3. Week 4: Implement SQL viewer feature
4. Deploy to Azure Web App

---

**Last Updated:** 2025-10-27
**Current Version:** 2.0 (CLI-based) ✅ Production Ready
**Next Version:** 3.0 (GUI-based) 🚧 Specification Complete - Ready for Implementation
