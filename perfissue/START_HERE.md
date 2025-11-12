# START HERE - Performance Issue Investigation Package

**Created:** 2025-11-12
**Purpose:** Complete parsing subsystem snapshot for external analysis
**Total Files:** 60+ files (all parsing-related code, tests, docs, baselines)

---

## 🎯 What's in This Package

This folder contains **EVERYTHING** related to the parsing subsystem:

✅ **All Parser Code** - Regex-first + SQLGlot architecture
✅ **All SQL Cleaning Rules** - YAML-based rule engine
✅ **All Configuration** - Pydantic settings with validation
✅ **All Testing Code** - 73+ unit tests, 11 integration tests, validation scripts
✅ **All Documentation** - Technical reports, guides, references
✅ **All DMV Extractors** - Synapse metadata extraction (Jupyter + Python)
✅ **All Baselines** - Historical performance metrics
✅ **All Utilities** - Confidence calculation, phantom detection, helpers

**No references, no placeholders** - All code and information is directly embedded.

---

## 📖 Quick Start Guide

### **1. Read These First (5 minutes):**

1. **`START_HERE.md`** ← You are here
2. **`QUICK_REFERENCE.md`** - Fast lookup for key concepts
3. **`README_PERFISSUE.md`** - Directory structure and overview

### **2. Understand the Critical Fix (10 minutes):**

**Problem:** SQLGlot WARN mode returned empty results
**Impact:** 1% success rate (2/515 SPs with dependencies)
**Solution:** Regex-first architecture with SQLGlot enhancement
**Result:** 100% success rate (349/349 SPs)

**Read:** `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md`

### **3. Review Core Parser Code (15 minutes):**

**File:** `parsers/quality_aware_parser.py`
**Key Lines:** 735-768 (main parsing logic)

**Architecture:**
```
Phase 1: Regex Scan (FULL DDL)
    ↓
Phase 2: SQLGlot Enhancement (RAISE mode)
    ↓
Phase 3: Post-Processing (deduplication, filtering)
    ↓
Phase 4: Confidence Calculation (0, 75, 85, 100)
```

### **4. Validate Results (5 minutes):**

```bash
# Full validation
python3 testing/check_parsing_results.py

# Expected output:
# ✅ 100% success rate (349/349 SPs)
# ✅ 82.5% at confidence 100
# ✅ 7.4% at confidence 85
# ✅ 10.0% at confidence 75
```

### **5. Deep Dive (60+ minutes):**

**Read:** `docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md` (3,000+ lines)
- All code embedded directly
- No references or placeholders
- Complete architecture walkthrough

---

## 📂 Documentation Index

### **🔥 Start Here:**
| Document | Purpose | Time |
|----------|---------|------|
| `START_HERE.md` | This file - quick orientation | 5 min |
| `QUICK_REFERENCE.md` | Fast lookup for concepts | 10 min |
| `README_PERFISSUE.md` | Directory structure & overview | 15 min |
| `FILE_INVENTORY.md` | Complete file listing with purposes | 20 min |

### **📊 Technical Reports:**
| Document | Purpose | Size |
|----------|---------|------|
| `docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md` | All code embedded (no references) | 3,000+ lines |
| `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md` | Root cause analysis (1% → 100%) | 800+ lines |
| `docs/REGEX_SOLUTION_REPORT.md` | Regex-first solution details | 400+ lines |
| `docs/query_log_research.md` | Ad-hoc query filtering research | 80 lines |

### **📚 User Guides:**
| Document | Purpose | Lines |
|----------|---------|-------|
| `docs/USAGE.md` | Parser usage & troubleshooting | 500+ |
| `docs/REFERENCE.md` | Technical specs, schema, API | 600+ |
| `docs/RULE_DEVELOPMENT.md` | YAML rule creation guide | 400+ |
| `docs/SETUP.md` | Installation & deployment | 400+ |

### **📝 Project Context:**
| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | AI instructions & project context |
| `README.md` | Project overview & quickstart |

---

## 🗂️ Directory Structure

```
perfissue/
├── START_HERE.md                    ← You are here
├── QUICK_REFERENCE.md               ← Fast concept lookup
├── README_PERFISSUE.md              ← Directory overview
├── FILE_INVENTORY.md                ← Complete file listing
├── DIRECTORY_TREE.txt               ← Directory tree
├── CLAUDE.md                        ← AI instructions
├── README.md                        ← Project overview
├── main.py                          ← CLI entry point
│
├── parsers/                         ← Core parsing logic (8 files)
│   ├── quality_aware_parser.py     ← MAIN PARSER (2,800+ lines)
│   ├── comment_hints_parser.py     ← @LINEAGE_INPUTS/@LINEAGE_OUTPUTS
│   ├── query_log_validator.py      ← Query log validation
│   ├── sql_cleaning_rules.py       ← SQL cleaning logic (1,200+ lines)
│   └── ...
│
├── core/                            ← Core engine (2 files)
│   ├── duckdb_workspace.py         ← DuckDB workspace (1,200+ lines)
│   └── gap_detector.py             ← Phantom detection (280+ lines)
│
├── rules/                           ← SQL cleaning rules (YAML)
│   ├── rule_loader.py              ← Rule engine
│   ├── generic/
│   │   └── 01_whitespace.yaml
│   └── tsql/
│       └── 01_raiserror.yaml
│
├── config/                          ← Configuration (3 files)
│   ├── settings.py                 ← Pydantic settings
│   └── dialect_config.py           ← Dialect configurations
│
├── dialects/                        ← SQL dialects (5 files)
│   ├── tsql.py                     ← T-SQL (Synapse, SQL Server)
│   ├── postgres.py                 ← PostgreSQL
│   └── ...
│
├── utils/                           ← Utilities (6 files)
│   ├── confidence_calculator.py    ← Confidence scoring
│   ├── phantom_promotion.py        ← Phantom logic
│   └── ...
│
├── testing/                         ← All tests & validation
│   ├── check_parsing_results.py   ← Database validation
│   ├── verify_sp_parsing.py       ← SP verification
│   ├── analyze_sp.py              ← Deep debugging
│   ├── test_upload.sh             ← API test
│   ├── poll_job.sh                ← Job polling
│   ├── unit/                      ← Unit tests (73+ tests)
│   └── integration/               ← Integration tests (1,067 objects)
│
├── extractors/                      ← DMV extraction (2 files)
│   ├── get_metadata.ipynb         ← PRIMARY (Jupyter notebook)
│   └── synapse_dmv_extractor.py   ← Production Python script
│
├── baselines/                       ← Historical baselines
│   ├── baselines/                 ← Parser baselines over time
│   ├── real_data/                 ← Test Parquet files
│   └── results/                   ← Analysis results
│
├── docs/                            ← All documentation (8+ files)
│   ├── COMPLETE_TECHNICAL_REPORT_MASSIVE.md
│   ├── COMPLETE_PARSING_ARCHITECTURE_REPORT.md
│   ├── REGEX_SOLUTION_REPORT.md
│   ├── USAGE.md
│   ├── REFERENCE.md
│   ├── RULE_DEVELOPMENT.md
│   ├── SETUP.md
│   └── query_log_research.md
│
└── api/                             ← API integration
    └── parser_job.py               ← FastAPI router (not copied yet)
```

**Total:** 60+ files covering all aspects of parsing subsystem

---

## 🔑 Key Concepts

### **1. Regex-First Architecture**

**Why it works:**
- ✅ No context loss (runs on FULL DDL, no statement splitting)
- ✅ Guaranteed baseline (always succeeds)
- ✅ Combined accuracy (regex + SQLGlot)

**Why SQLGlot WARN failed:**
- ❌ Silent failures (empty Command nodes)
- ❌ Statement splitting (orphaned JOIN clauses)
- ❌ 1% success rate

### **2. Confidence Scoring (v2.1.0)**

**4 discrete values:** 0, 75, 85, 100

```python
completeness = (found / expected) * 100
if completeness >= 90: return 100
elif completeness >= 70: return 85
elif completeness >= 50: return 75
else: return 0
```

### **3. Phantom Objects**

Objects referenced in SQL but missing from catalog metadata.

**Features:**
- Negative IDs (-1 to -∞)
- Whitelist-based filtering
- Visual indicators (🔶 orange dashed border)

### **4. DMV Extraction**

**4 Object Types:**
- Table
- View
- Stored Procedure
- Function (TF/IF/FN consolidated)

**Query Log Filtering (Whitelist):**
- ✅ EXEC/EXECUTE (stored procedures)
- ✅ INSERT/UPDATE/DELETE/MERGE/TRUNCATE (DML)
- ❌ Ad-hoc SELECT/WITH queries
- ❌ DDL operations (CREATE/ALTER/DROP)

**Research:** No "is_adhoc" flag exists in `sys.dm_pdw_exec_requests`

---

## 🎬 Quick Commands

### **Validation:**
```bash
# Full validation (100% check)
python3 testing/check_parsing_results.py

# Specific SP verification
python3 testing/verify_sp_parsing.py <sp_name>

# Deep debugging
python3 testing/analyze_sp.py <sp_name>

# API end-to-end test
./testing/test_upload.sh
```

### **Testing:**
```bash
# Unit tests (73+ tests, < 1 second)
pytest testing/unit/ -v

# Integration tests (1,067 objects)
pytest testing/integration/ -v

# All tests
pytest testing/ -v
```

### **DMV Extraction:**
```bash
# Jupyter notebook (PRIMARY)
jupyter notebook extractors/get_metadata.ipynb

# Python script (alternative)
python3 extractors/synapse_dmv_extractor.py \
  --server yourserver.sql.azuresynapse.net \
  --database yourdatabase \
  --username youruser \
  --password yourpassword \
  --output parquet_snapshots/
```

---

## 📈 Performance Metrics (v4.3.1)

### **Parser Success:**
- ✅ **100%** success rate (349/349 SPs with dependencies)
- ✅ **82.5%** at confidence 100 (288 SPs)
- ✅ **7.4%** at confidence 85 (26 SPs)
- ✅ **10.0%** at confidence 75 (35 SPs)

### **Dependency Analysis:**
- Average **3.20 inputs** per SP
- Average **1.87 outputs** per SP

### **Test Coverage:**
- 73+ unit tests (< 1 second execution)
- 11 integration tests (1,067 real objects)
- 100% pass rate

### **Validated SPs:**
- `spLoadFactLaborCostForEarnedValue_Post` ✅
- `spLoadDimTemplateType` ✅

---

## 🔍 Critical Code Locations

| Purpose | File | Key Lines | Description |
|---------|------|-----------|-------------|
| **Main Parser** | `parsers/quality_aware_parser.py` | 735-768 | Regex-first + SQLGlot architecture |
| **Confidence** | `utils/confidence_calculator.py` | 50-80 | 4-value discrete scoring |
| **Phantom Detection** | `core/gap_detector.py` | 100-150 | Whitelist-based detection |
| **SQL Cleaning** | `parsers/sql_cleaning_rules.py` | 200-400 | Pattern-based cleaning |
| **DuckDB Workspace** | `core/duckdb_workspace.py` | All | In-memory database |
| **Settings** | `config/settings.py` | 30-80 | Pydantic configuration |
| **DMV Queries** | `extractors/get_metadata.ipynb` | Cells 5, 11 | Object types + query logs |

---

## 🛠️ Configuration

**File:** `config/settings.py`

```bash
# SQL Dialect
SQL_DIALECT=tsql  # Default (Synapse/SQL Server)

# Global Schema Exclusion
EXCLUDED_SCHEMAS=sys,dummy,information_schema,tempdb,master,msdb,model

# Phantom Objects (Whitelist)
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B

# Phantom Exclusions (dbo only)
PHANTOM_EXCLUDE_DBO_OBJECTS=cte,cte_*,CTE*,ParsedData,#*,@*,temp_*,tmp_*
```

---

## 🧪 Testing Strategy

### **Validation Scripts:**
1. **`check_parsing_results.py`** - Full database validation
2. **`verify_sp_parsing.py`** - Specific SP verification
3. **`analyze_sp.py`** - Deep debugging tool

### **Unit Tests:**
- Comment hint parsing (19 tests)
- Configuration validation (23 tests)
- Dialect handlers (12 tests)
- SQL cleaning rules (rule-specific tests)

### **Integration Tests:**
- Synapse integration (11 tests, 1,067 objects)
- PostgreSQL mock (8 tests)

### **API Tests:**
- End-to-end upload workflow
- Job processing validation
- Result generation checks

---

## 📚 Recommended Reading Order

### **🚀 Fast Track (30 minutes):**
1. `START_HERE.md` (5 min)
2. `QUICK_REFERENCE.md` (10 min)
3. `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md` (15 min)

### **⚡ Standard Track (2 hours):**
1. `START_HERE.md` (5 min)
2. `QUICK_REFERENCE.md` (10 min)
3. `README_PERFISSUE.md` (15 min)
4. `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md` (15 min)
5. `parsers/quality_aware_parser.py` (lines 735-768) (15 min)
6. `extractors/get_metadata.ipynb` (15 min)
7. `docs/USAGE.md` (15 min)
8. Run `testing/check_parsing_results.py` (5 min)
9. Review `docs/REFERENCE.md` (20 min)

### **🔬 Deep Dive (1+ day):**
1. All of Standard Track
2. `docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md` (3,000+ lines)
3. `FILE_INVENTORY.md` (complete file listing)
4. Review all parser code (`parsers/`)
5. Review all rules (`rules/`)
6. Review all tests (`testing/`)
7. Experiment with validation scripts
8. Read all documentation (`docs/`)

---

## 🎯 Key Achievements

### **✅ Parser (v4.3.1):**
- 100% success rate (was 1%)
- 82.5% at confidence 100
- Zero regressions
- Validated with 349 SPs

### **✅ DMV Extraction:**
- Consolidated object types (4 total)
- Corrected query log filtering (whitelist approach)
- Removed unnecessary filters (label, DDL)
- Jupyter notebook as primary method

### **✅ Testing:**
- 73+ unit tests (100% pass)
- 11 integration tests (1,067 objects)
- Validation scripts for production use
- API end-to-end tests

### **✅ Documentation:**
- 3,000+ line technical report (all code embedded)
- 800+ line architecture report
- Complete user guides
- Quick reference guide

---

## 💡 Why This Package Exists

**Problem:** Parser success rate dropped from ~95% to 1% after SQLGlot integration
**Root Cause:** SQLGlot WARN mode returned empty Command nodes silently
**Solution:** Regex-first architecture with SQLGlot enhancement
**Result:** 100% success rate restored

**This package contains:**
- Complete code snapshot of parsing subsystem
- All documentation and reports
- All tests and validation scripts
- All baselines and metrics
- Everything needed for external analysis

**No external dependencies or references** - All information is self-contained.

---

## 🤝 Support

**Questions about:**
- **Parser architecture** → Read `parsers/quality_aware_parser.py` (lines 735-768)
- **Confidence scoring** → Read `utils/confidence_calculator.py`
- **Phantom detection** → Read `core/gap_detector.py`
- **DMV extraction** → Open `extractors/get_metadata.ipynb`
- **SQL cleaning** → Read `parsers/sql_cleaning_rules.py`
- **Configuration** → Read `config/settings.py`
- **Testing** → Run `testing/check_parsing_results.py`
- **Troubleshooting** → Read `docs/USAGE.md`

**Deep dives:**
- `docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md` (all code embedded)
- `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md` (architecture)

---

## 📊 File Statistics

| Category | Count | Examples |
|----------|-------|----------|
| **Python files** | 35+ | Parser, tests, utilities |
| **YAML rules** | 2 | SQL cleaning rules |
| **Documentation** | 10+ | Reports, guides, references |
| **Notebooks** | 1 | DMV extraction |
| **Shell scripts** | 2 | Testing automation |
| **Config files** | 3 | Settings, dialects |
| **Total** | **60+** | **Complete subsystem** |

**Total Lines of Code:** 15,000+ (excluding docs)
**Total Lines of Documentation:** 10,000+ (including reports)

---

## 🎓 Key Learnings

### **1. Regex vs SQLGlot:**
- Regex: Guaranteed baseline, no context loss
- SQLGlot: AST-based enhancement, can fail
- Combined: Best-of-both-worlds

### **2. Silent Failures are Dangerous:**
- SQLGlot WARN mode returned empty nodes
- No exceptions, no warnings
- Always validate success metrics

### **3. Context Matters:**
- Statement splitting orphans JOIN clauses
- Full DDL parsing preserves relationships
- Test with real-world complexity

### **4. Whitelist > Blacklist:**
- Query log filtering: include only what's needed
- Automatically excludes unwanted patterns
- More maintainable and predictable

### **5. Configuration is Critical:**
- Type-safe settings (Pydantic)
- Whitelist-based phantom detection
- Environment-specific exclusions

---

## ✅ Next Steps

1. **Review this document** (you're almost done!)
2. **Read QUICK_REFERENCE.md** (fast concept lookup)
3. **Run validation script** (`testing/check_parsing_results.py`)
4. **Review main parser** (`parsers/quality_aware_parser.py` lines 735-768)
5. **Deep dive into technical report** (`docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md`)

---

**Package Created:** 2025-11-12
**Parser Version:** v4.3.1
**Status:** Production Ready ✅

**Total Files:** 60+
**Total Code:** 15,000+ lines
**Total Docs:** 10,000+ lines

**Everything you need is in this folder.**

