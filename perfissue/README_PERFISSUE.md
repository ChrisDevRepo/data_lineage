# Performance Issue Investigation - Complete Parsing Subsystem

**Created:** 2025-11-12
**Purpose:** Complete snapshot of ALL parsing-related code, documentation, tests, and baselines for external analysis

---

## Directory Structure

```
perfissue/
├── README_PERFISSUE.md          # This file
├── CLAUDE.md                     # Full AI instructions and project context
├── README.md                     # Project overview
│
├── parsers/                      # Core parsing logic
│   ├── quality_aware_parser.py  # Main parser (regex-first + SQLGlot)
│   ├── base_parser.py           # Parser interface
│   └── __init__.py
│
├── core/                         # Core engine components
│   ├── sql_cleaner.py           # SQL cleaning with YAML rules
│   ├── confidence_calculator.py # Confidence scoring logic
│   ├── lineage_engine.py        # Main lineage engine
│   └── __init__.py
│
├── rules/                        # YAML cleaning rules
│   ├── tsql/                    # T-SQL (Synapse) rules
│   │   ├── 10_comments.yaml
│   │   ├── 15_print_statements.yaml
│   │   ├── 20_declare_variables.yaml
│   │   ├── 25_set_statements.yaml
│   │   ├── 30_if_blocks.yaml
│   │   ├── 35_drop_if_exists.yaml
│   │   ├── 40_exec_sp_executesql.yaml
│   │   └── ...
│   └── rule_engine.py           # Rule loading and execution
│
├── config/                       # Configuration
│   ├── settings.py              # Pydantic settings with validation
│   └── __init__.py
│
├── dialects/                     # SQL dialect handlers
│   ├── base.py                  # Base dialect
│   ├── tsql.py                  # T-SQL (Synapse/SQL Server)
│   ├── fabric.py                # Microsoft Fabric
│   ├── postgres.py              # PostgreSQL
│   └── ...
│
├── utils/                        # Utility functions
│   ├── regex_patterns.py        # Regex patterns for parsing
│   ├── validation.py            # Validation utilities
│   └── ...
│
├── testing/                      # All test code
│   ├── check_parsing_results.py # Database validation script
│   ├── verify_sp_parsing.py     # SP verification script
│   ├── analyze_sp.py            # Deep analysis tool
│   ├── test_upload.sh           # API upload test
│   ├── poll_job.sh              # Job polling script
│   │
│   ├── unit/                    # Unit tests (pytest)
│   │   ├── test_comment_hint_parser.py
│   │   ├── test_sql_cleaner.py
│   │   ├── test_confidence.py
│   │   └── rules/               # Rule tests
│   │
│   └── integration/             # Integration tests
│       ├── test_synapse_integration.py
│       └── ...
│
├── extractors/                   # Database metadata extractors
│   ├── synapse_dmv_extractor.py # Production Python script
│   └── get_metadata.ipynb       # Jupyter notebook (PRIMARY)
│
├── baselines/                    # Historical baselines and results
│   ├── baselines/               # Parser baselines over time
│   ├── real_data/               # Test Parquet files
│   └── results/                 # Analysis results
│
├── docs/                         # All documentation
│   ├── COMPLETE_TECHNICAL_REPORT_MASSIVE.md       # 3000+ line technical report
│   ├── COMPLETE_PARSING_ARCHITECTURE_REPORT.md    # Detailed architecture
│   ├── USAGE.md                                    # Parser usage guide
│   ├── REFERENCE.md                                # Technical reference
│   ├── RULE_DEVELOPMENT.md                         # YAML rule creation
│   ├── query_log_research.md                       # Ad-hoc query filtering research
│   ├── TESTING_SUMMARY.md                          # Test results summary
│   ├── UAT_READINESS_REPORT.md                     # UAT readiness
│   └── BUGS.md                                     # Known issues
│
├── api/                          # API integration
│   └── parser_job.py            # Parser job router
│
└── main.py                       # CLI entry point

```

---

## Key Files Overview

### **Parsing Architecture (Regex-First + SQLGlot)**

**Current Status:** ✅ **100% success rate** (349/349 SPs with dependencies)

#### **Main Parser:**
- **`parsers/quality_aware_parser.py`** (735-768)
  - Phase 1: Regex scan on FULL DDL (guaranteed baseline)
  - Phase 2: SQLGlot RAISE mode (optional enhancement)
  - Phase 3: Post-processing (deduplication, filtering)
  - Phase 4: Confidence calculation

**Key Technical Decisions:**
1. **Regex ALWAYS runs first** on full DDL (no statement splitting)
2. **SQLGlot in RAISE mode** (strict, fails fast)
3. **Combined results** provide best-of-both-worlds accuracy
4. **Patterns supported:** FROM, JOIN (all types including CROSS), INSERT, UPDATE, DELETE, MERGE

#### **Critical Fix (2025-11-12):**
**Before:** 1% success rate (SQLGlot WARN mode returned empty Command nodes)
**After:** 100% success rate (regex-first architecture restored)

---

### **SQL Cleaning (YAML Rules)**

#### **Rule Engine:**
- **`core/sql_cleaner.py`** - Rule execution engine
- **`rules/tsql/*.yaml`** - 15+ T-SQL cleaning rules

#### **Rule Categories:**
1. **Comments** (10_comments.yaml) - Remove SQL comments
2. **Print statements** (15_print_statements.yaml) - Remove PRINT
3. **Variables** (20_declare_variables.yaml) - Remove DECLARE
4. **SET statements** (25_set_statements.yaml) - Remove SET NOCOUNT etc.
5. **IF blocks** (30_if_blocks.yaml) - Remove IF EXISTS blocks
6. **DROP IF EXISTS** (35_drop_if_exists.yaml) - Clean DROP statements
7. **Dynamic SQL** (40_exec_sp_executesql.yaml) - Handle EXEC()

**Rule Format:**
```yaml
name: remove_print
description: Remove T-SQL PRINT statements
dialect: tsql
enabled: true
priority: 15
pattern: 'PRINT\s+.*'
replacement: ''
test_cases:
  - name: simple_print
    input: "PRINT 'Debug'"
    expected: ""
```

---

### **Confidence Scoring (v2.1.0)**

**4 discrete values:** 0, 75, 85, 100

#### **Algorithm:**
```python
completeness = (found_tables / expected_tables) * 100
if completeness >= 90: confidence = 100
elif completeness >= 70: confidence = 85
elif completeness >= 50: confidence = 75
else: confidence = 0
```

**Special Cases:**
- Orchestrators (only EXEC) → 100%
- Parse failures → 0%

**Implementation:** `core/confidence_calculator.py`

---

### **Testing Infrastructure**

#### **Validation Scripts:**
1. **`testing/check_parsing_results.py`** - Full database validation
   - Success rate, confidence distribution
   - Average dependencies per SP
   - Top SPs by complexity

2. **`testing/verify_sp_parsing.py`** - Specific SP verification
   - Actual vs expected tables
   - Phantom detection
   - Detailed analysis

3. **`testing/analyze_sp.py`** - Deep debugging
   - DDL preview
   - Regex match details
   - SQLGlot results
   - Problematic patterns

4. **`testing/test_upload.sh`** - API end-to-end test
   - File upload
   - Job processing
   - Result validation

#### **Unit Tests (pytest):**
- 73+ tests, < 1 second execution
- Comment hint parser: 19 tests
- SQL cleaner: Rule validation tests
- Confidence calculator: Edge case tests

#### **Integration Tests:**
- Synapse integration: 11 tests (1,067 real objects)
- Full pipeline validation

---

### **DMV Extraction (Synapse Metadata)**

#### **PRIMARY METHOD:**
**`extractors/get_metadata.ipynb`** - Jupyter notebook for Synapse admins

**4 Parquet Files Generated:**
1. **objects.parquet** - Tables, views, SPs, functions
2. **dependencies.parquet** - Object dependencies (sys.sql_expression_dependencies)
3. **definitions.parquet** - DDL definitions (sys.sql_modules)
4. **query_logs.parquet** - Execution logs (optional, requires elevated permissions)

#### **Key Changes (2025-11-12):**

**Object Types:** Consolidated to 4 types
- Table, View, Stored Procedure, Function (TF/IF/FN → "Function")

**Query Log Filtering:** Whitelist approach (no ad-hoc queries)
- ✅ **Includes:** EXEC, EXECUTE, INSERT, UPDATE, DELETE, MERGE, TRUNCATE
- ❌ **Excludes:** Ad-hoc SELECT, WITH/CTE, DDL operations
- **Research confirmed:** No "is_adhoc" flag exists in sys.dm_pdw_exec_requests

---

### **Documentation**

#### **Technical Reports:**
1. **`docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md`** (3000+ lines)
   - All code embedded directly (no references)
   - Complete parser architecture
   - Phantom object detection
   - Frontend dual filtering
   - DMV extractor fixes

2. **`docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md`**
   - Detailed architecture analysis
   - Root cause analysis of 1% → 100% fix
   - Testing validation results

3. **`docs/query_log_research.md`**
   - Ad-hoc query filtering research
   - Why whitelist approach is correct
   - DMV limitations documentation

#### **User Guides:**
- **`docs/USAGE.md`** - Parser usage and troubleshooting
- **`docs/REFERENCE.md`** - Technical specs, schema, API
- **`docs/RULE_DEVELOPMENT.md`** - YAML rule creation guide

#### **Status Reports:**
- **`docs/TESTING_SUMMARY.md`** - Test results and validation
- **`docs/UAT_READINESS_REPORT.md`** - UAT readiness checklist
- **`docs/BUGS.md`** - Known issues and feature requests

---

## Performance Results

### **Current Parser (v4.3.1):**
- ✅ **100% success rate** (349/349 SPs with dependencies)
- ✅ **82.5%** at confidence 100 (288 SPs)
- ✅ **7.4%** at confidence 85 (26 SPs)
- ✅ **10.0%** at confidence 75 (35 SPs)
- ✅ Average **3.20 inputs** and **1.87 outputs** per SP

### **Validated SPs:**
- `spLoadFactLaborCostForEarnedValue_Post` - ✅ Correct
- `spLoadDimTemplateType` - ✅ Correct

---

## Technical Stack

**Language:** Python 3.10+
**Parser:** SQLGlot (RAISE mode) + Regex (baseline)
**Database:** DuckDB (internal workspace)
**Configuration:** Pydantic Settings
**Testing:** pytest (73+ tests)
**SQL Dialect:** T-SQL (Azure Synapse)

---

## Critical Insights

### **Why Regex-First Architecture Works:**

1. **No Context Loss:**
   - Regex runs on FULL DDL (no statement splitting)
   - JOIN clauses stay with SELECT context
   - CROSS JOIN patterns detected correctly

2. **Guaranteed Baseline:**
   - Regex ALWAYS succeeds (provides minimum coverage)
   - SQLGlot failures don't impact baseline results

3. **Combined Accuracy:**
   - Regex catches patterns SQLGlot misses
   - SQLGlot adds AST-based enhancements
   - Best-of-both-worlds approach

### **Why SQLGlot WARN Mode Failed:**

1. **Silent Failures:**
   - Returned Command nodes with zero table extraction
   - No exceptions, no warnings, just empty results

2. **Statement Splitting Issues:**
   - Orphaned JOIN clauses from SELECT context
   - Lost relationship between tables

3. **Production Impact:**
   - 1% success rate (2/515 SPs)
   - Average confidence: 0.0
   - Complete parser breakdown

---

## Usage Examples

### **Validate Parsing Results:**
```bash
python3 testing/check_parsing_results.py
```

### **Verify Specific SP:**
```bash
python3 testing/verify_sp_parsing.py <sp_name>
```

### **API End-to-End Test:**
```bash
./testing/test_upload.sh
```

### **Extract Synapse Metadata:**
```bash
# Open Jupyter notebook
jupyter notebook extractors/get_metadata.ipynb

# Or use Python script
python3 extractors/synapse_dmv_extractor.py \
  --server yourserver.sql.azuresynapse.net \
  --database yourdatabase \
  --username youruser \
  --password yourpassword \
  --output parquet_snapshots/
```

### **Run Unit Tests:**
```bash
pytest testing/unit/ -v
```

---

## Configuration

**Environment Variables (.env):**
```bash
# SQL Dialect
SQL_DIALECT=tsql  # Default (Synapse/SQL Server)

# Global Schema Exclusion
EXCLUDED_SCHEMAS=sys,dummy,information_schema,tempdb,master,msdb,model

# Phantom Objects
PHANTOM_INCLUDE_SCHEMAS=CONSUMPTION*,STAGING*,TRANSFORMATION*,BB,B
PHANTOM_EXCLUDE_DBO_OBJECTS=cte,cte_*,CTE*,ParsedData,#*,@*,temp_*,tmp_*
```

**File:** `config/settings.py`

---

## Next Steps for External Analysis

1. **Review Parser Architecture:**
   - Read `parsers/quality_aware_parser.py` (lines 735-768)
   - Understand regex-first approach vs SQLGlot

2. **Examine Test Results:**
   - Run `testing/check_parsing_results.py`
   - Review `docs/TESTING_SUMMARY.md`

3. **Study Rule Engine:**
   - Review `rules/tsql/*.yaml` files
   - Understand SQL cleaning patterns

4. **Analyze Confidence Scoring:**
   - Read `core/confidence_calculator.py`
   - Review completeness thresholds

5. **Validate DMV Queries:**
   - Open `extractors/get_metadata.ipynb`
   - Verify object type consolidation
   - Confirm query log filtering

---

## Contact & Support

**Project:** Data Lineage Visualizer v4.3.1
**Author:** Christian Wagner
**Status:** Production Ready
**Last Updated:** 2025-11-12

For questions or issues, see `docs/USAGE.md` for troubleshooting guide.

---

**END OF PERFISSUE README**
