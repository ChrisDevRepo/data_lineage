# Complete File Inventory - perfissue/

**Generated:** 2025-11-12
**Total Files:** 50+ files covering all parsing subsystem components

---

## Root Level Files

| File | Purpose |
|------|---------|
| `README_PERFISSUE.md` | Main documentation index and overview |
| `FILE_INVENTORY.md` | This file - complete file listing |
| `CLAUDE.md` | AI instructions and project context |
| `README.md` | Project overview and quickstart |
| `main.py` | CLI entry point for parser |

---

## Parsing Core (`parsers/`)

| File | Lines | Purpose |
|------|-------|---------|
| `quality_aware_parser.py` | 2,800+ | **Main parser** - Regex-first + SQLGlot architecture |
| `comment_hints_parser.py` | 300+ | Parse `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints |
| `query_log_validator.py` | 350+ | Validate parsed results against query logs |
| `simplified_parser.py` | 550+ | Legacy simplified parser |
| `simplified_rule_engine.py` | 350+ | Legacy rule engine |
| `sql_cleaning_rules.py` | 1,200+ | **SQL cleaning logic** - Pattern-based rules |
| `sql_preprocessor.py` | 300+ | SQL preprocessing utilities |
| `README.md` | - | Parser documentation |

### **Key Functions in quality_aware_parser.py:**

**Lines 735-768:** Core parsing logic (regex-first architecture)
```python
def parse_stored_procedure(self, sp_name, sp_definition, expected_sources, expected_targets):
    # Phase 1: Regex scan (guaranteed baseline)
    regex_results = self._extract_with_regex(sp_definition)

    # Phase 2: SQLGlot enhancement (optional)
    try:
        sqlglot_results = self._extract_with_sqlglot(sp_definition)
    except:
        sqlglot_results = []

    # Phase 3: Combine and deduplicate
    combined = self._combine_results(regex_results, sqlglot_results)

    # Phase 4: Calculate confidence
    confidence = self._calculate_confidence(combined, expected_sources, expected_targets)
```

---

## Core Engine (`core/`)

| File | Lines | Purpose |
|------|-------|---------|
| `duckdb_workspace.py` | 1,200+ | **DuckDB workspace management** - In-memory database |
| `gap_detector.py` | 280+ | **Phantom object detection** - Find missing metadata |

### **Key Functions:**

**duckdb_workspace.py:**
- `create_tables()` - Initialize workspace schema
- `load_parquet_files()` - Load DMV Parquet files
- `save_results()` - Persist parsing results
- `detect_phantom_objects()` - Find references to non-existent objects

**gap_detector.py:**
- `find_phantom_objects()` - Identify phantom references
- `create_phantom_object()` - Create phantom with negative ID
- `apply_whitelist_filters()` - Filter by include/exclude patterns

---

## Configuration (`config/`)

| File | Lines | Purpose |
|------|-------|---------|
| `settings.py` | 350+ | **Pydantic settings** - Type-safe configuration |
| `dialect_config.py` | 150+ | SQL dialect configurations |

### **Key Settings (settings.py):**
```python
class Settings(BaseSettings):
    SQL_DIALECT: str = "tsql"
    EXCLUDED_SCHEMAS: str = "sys,dummy,information_schema"
    PHANTOM_INCLUDE_SCHEMAS: str = "CONSUMPTION*,STAGING*,TRANSFORMATION*"
    PHANTOM_EXCLUDE_DBO_OBJECTS: str = "cte,cte_*,CTE*,#*,@*"
```

---

## SQL Dialects (`dialects/`)

| File | Lines | Purpose |
|------|-------|---------|
| `base.py` | 200+ | Base dialect interface |
| `tsql.py` | 300+ | **T-SQL dialect** (Synapse, SQL Server) |
| `postgres.py` | 250+ | PostgreSQL dialect |
| `registry.py` | 100+ | Dialect registration and lookup |

### **Supported Dialects:**
- `tsql` - Azure Synapse, SQL Server, Azure SQL *(default)*
- `fabric` - Microsoft Fabric
- `postgres` - PostgreSQL data warehouses
- `oracle` - Oracle Database
- `snowflake` - Snowflake
- `redshift` - Amazon Redshift
- `bigquery` - Google BigQuery

---

## SQL Cleaning Rules (`rules/`)

| File | Lines | Purpose |
|------|-------|---------|
| `rule_loader.py` | 200+ | **Rule engine** - Load and execute YAML rules |
| `generic/01_whitespace.yaml` | 50+ | Generic whitespace normalization |
| `tsql/01_raiserror.yaml` | 120+ | Remove T-SQL RAISERROR statements |

### **Rule Format:**
```yaml
name: remove_raiserror
description: Remove T-SQL RAISERROR statements
dialect: tsql
enabled: true
priority: 10
pattern: 'RAISERROR\s*\([^)]+\)'
replacement: ''
test_cases:
  - name: simple_raiserror
    input: "RAISERROR('Error', 16, 1)"
    expected: ""
```

**Rule Categories (T-SQL):**
1. Comments removal
2. PRINT statements
3. DECLARE variables
4. SET statements (SET NOCOUNT, etc.)
5. IF EXISTS blocks
6. DROP IF EXISTS cleanup
7. Dynamic SQL (EXEC sp_executesql)
8. RAISERROR statements
9. Whitespace normalization

---

## Utilities (`utils/`)

| File | Lines | Purpose |
|------|-------|---------|
| `confidence_calculator.py` | 200+ | **Confidence scoring** - 4-value discrete system |
| `phantom_promotion.py` | 150+ | Phantom object promotion logic |
| `synapse_query_helper.py` | 250+ | Synapse-specific query utilities |
| `workspace_query_helper.py` | 200+ | DuckDB workspace queries |
| `validators.py` | 150+ | Input validation utilities |

### **Confidence Calculation (confidence_calculator.py):**
```python
def calculate_confidence(found_tables, expected_tables):
    completeness = (len(found_tables) / len(expected_tables)) * 100

    if completeness >= 90:
        return 100
    elif completeness >= 70:
        return 85
    elif completeness >= 50:
        return 75
    else:
        return 0
```

---

## Testing Infrastructure (`testing/`)

### **Validation Scripts:**

| File | Lines | Purpose |
|------|-------|---------|
| `check_parsing_results.py` | 400+ | **Database validation** - Full system check |
| `verify_sp_parsing.py` | 350+ | **SP verification** - Detailed single SP analysis |
| `analyze_sp.py` | 450+ | **Deep debugging** - DDL, regex, SQLGlot analysis |
| `test_upload.sh` | 100+ | API end-to-end test |
| `poll_job.sh` | 50+ | Job status polling |

**Usage:**
```bash
# Full validation
python3 testing/check_parsing_results.py

# Specific SP
python3 testing/verify_sp_parsing.py <sp_name>

# Deep analysis
python3 testing/analyze_sp.py <sp_name>

# API test
./testing/test_upload.sh
```

### **Unit Tests (`testing/unit/`):**

| Directory/File | Tests | Purpose |
|----------------|-------|---------|
| `test_comment_hints_parser.py` | 19 | Comment hint parsing |
| `config/test_settings.py` | 15 | Configuration validation |
| `config/test_dialect_config.py` | 8 | Dialect configuration |
| `dialects/test_dialects.py` | 12 | Dialect handlers |
| `run_hints_tests.py` | - | Test runner |

**Run tests:**
```bash
pytest testing/unit/ -v
```

### **Integration Tests (`testing/integration/`):**

| File | Tests | Purpose |
|------|-------|---------|
| `test_synapse_integration.py` | 11 | **Synapse integration** - 1,067 real objects |
| `test_postgres_mock.py` | 8 | PostgreSQL mock testing |

**Run integration tests:**
```bash
pytest testing/integration/ -v
```

---

## DMV Extractors (`extractors/`)

| File | Format | Purpose |
|------|--------|---------|
| `get_metadata.ipynb` | Jupyter | **PRIMARY** - Synapse metadata extraction notebook |
| `synapse_dmv_extractor.py` | Python | Production CLI script for Synapse |

### **Key Changes (2025-11-12):**

**Object Types:** 4 consolidated types
- Table, View, Stored Procedure, Function (TF/IF/FN → "Function")

**Query Log Filtering:** Whitelist approach
```sql
WHERE r.command IS NOT NULL
    AND r.command NOT LIKE '%sys.dm_pdw_exec_requests%'
    AND r.status IN ('Completed', 'Failed')
    AND r.submit_time >= DATEADD(day, -7, GETDATE())
    AND (
        -- Stored procedure executions
        r.command LIKE 'EXEC %'
        OR r.command LIKE 'EXECUTE %'
        -- DML operations
        OR r.command LIKE 'INSERT %'
        OR r.command LIKE 'UPDATE %'
        OR r.command LIKE 'DELETE %'
        OR r.command LIKE 'MERGE %'
        OR r.command LIKE 'TRUNCATE %'
    )
```

**Parquet Files Generated:**
1. `objects.parquet` - Database objects (tables, views, SPs, functions)
2. `dependencies.parquet` - Object dependencies (sys.sql_expression_dependencies)
3. `definitions.parquet` - DDL definitions (sys.sql_modules)
4. `query_logs.parquet` - Execution logs (optional, requires elevated permissions)

---

## Documentation (`docs/`)

### **Technical Reports:**

| File | Size | Purpose |
|------|------|---------|
| `COMPLETE_TECHNICAL_REPORT_MASSIVE.md` | 3,000+ lines | **Comprehensive technical report** - All code embedded |
| `COMPLETE_PARSING_ARCHITECTURE_REPORT.md` | 800+ lines | **Architecture analysis** - Root cause of 1% → 100% fix |
| `REGEX_SOLUTION_REPORT.md` | 400+ lines | Regex-first solution details |
| `query_log_research.md` | 80 lines | Ad-hoc query filtering research |

### **User Guides:**

| File | Purpose |
|------|---------|
| `USAGE.md` | Parser usage and troubleshooting |
| `REFERENCE.md` | Technical specs, schema, API reference |
| `RULE_DEVELOPMENT.md` | YAML rule creation guide |
| `SETUP.md` | Installation and deployment |

### **Key Documentation Sections:**

**COMPLETE_TECHNICAL_REPORT_MASSIVE.md:**
- Complete parser architecture (all code)
- Phantom object detection (all code)
- Frontend dual filtering (all code)
- DMV extractor fixes (all code)
- Testing validation results
- No references - everything embedded

**COMPLETE_PARSING_ARCHITECTURE_REPORT.md:**
- Root cause analysis (SQLGlot WARN mode failure)
- Regex-first architecture explanation
- Testing validation (100% success rate)
- Before/after comparison

**USAGE.md:**
- Configuration guide
- Comment hints (@LINEAGE_INPUTS/@LINEAGE_OUTPUTS)
- Troubleshooting (low confidence, parse failures)
- Performance tuning

**REFERENCE.md:**
- DuckDB schema documentation
- API endpoints
- Confidence model specification
- SQL dialect details

**RULE_DEVELOPMENT.md:**
- YAML rule format
- Test case structure
- Debugging rules
- Best practices

---

## Baselines & Evaluation (`baselines/`)

### **Historical Baselines:**

| Directory | Purpose |
|-----------|---------|
| `baselines/` | Historical parser baselines over time |
| `real_data/` | Test Parquet files from real Synapse instances |
| `results/` | Analysis results and performance metrics |

**Baseline Snapshots:**
- v4.0.0 - Initial SQLGlot integration (broken)
- v4.1.0 - SQLGlot WARN mode (1% success)
- v4.3.1 - Regex-first architecture (100% success) ✅

---

## API Integration (`api/`)

| File | Lines | Purpose |
|------|-------|---------|
| `parser_job.py` | 600+ | **FastAPI router** - Parser job management |

**Endpoints:**
- `POST /api/upload-parquet` - Upload Parquet files
- `GET /api/parsing-job/{job_id}` - Get job status
- `GET /api/results` - Get parsing results
- `DELETE /api/clear` - Clear workspace

---

## Critical Code Locations

### **Parser Fix (100% success rate):**
**File:** `parsers/quality_aware_parser.py`
**Lines:** 735-768
**What:** Regex-first architecture with SQLGlot enhancement

### **Confidence Calculation:**
**File:** `utils/confidence_calculator.py`
**Lines:** 50-80
**What:** 4-value discrete confidence scoring (0, 75, 85, 100)

### **Phantom Detection:**
**File:** `core/gap_detector.py`
**Lines:** 100-150
**What:** Whitelist-based phantom object detection

### **DMV Queries:**
**File:** `extractors/get_metadata.ipynb`
**Cells:** 5, 11
**What:** Object type consolidation + query log filtering

### **SQL Cleaning:**
**File:** `parsers/sql_cleaning_rules.py`
**Lines:** 200-400
**What:** Pattern-based SQL cleaning rules

### **Settings:**
**File:** `config/settings.py`
**Lines:** 30-80
**What:** Pydantic configuration with validation

---

## Performance Metrics

**Parser (v4.3.1):**
- ✅ **100% success rate** (349/349 SPs with dependencies)
- ✅ **82.5%** at confidence 100 (288 SPs)
- ✅ **7.4%** at confidence 85 (26 SPs)
- ✅ **10.0%** at confidence 75 (35 SPs)
- ✅ Average **3.20 inputs** and **1.87 outputs** per SP

**Testing:**
- 73+ unit tests (< 1 second)
- 11 integration tests (1,067 real objects)
- 100% test pass rate

---

## File Count by Category

| Category | Count | Purpose |
|----------|-------|---------|
| Python files (.py) | 35+ | Core logic, tests, utilities |
| YAML rules (.yaml) | 2 | SQL cleaning rules |
| Documentation (.md) | 10+ | Technical reports, guides |
| Notebooks (.ipynb) | 1 | DMV extraction |
| Shell scripts (.sh) | 2 | Testing automation |
| **Total** | **50+** | **Complete parsing subsystem** |

---

## Next Steps

1. **Review Parser:**
   - Start with `parsers/quality_aware_parser.py` (lines 735-768)
   - Understand regex-first + SQLGlot approach

2. **Run Validation:**
   - Execute `testing/check_parsing_results.py`
   - Verify 100% success rate

3. **Study Rules:**
   - Review `rules/tsql/01_raiserror.yaml`
   - Understand rule format and testing

4. **Examine Extractors:**
   - Open `extractors/get_metadata.ipynb`
   - Validate DMV queries

5. **Read Reports:**
   - Start with `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md`
   - Understand 1% → 100% fix

---

**Last Updated:** 2025-11-12
**Parser Version:** v4.3.1
**Status:** Production Ready ✅

