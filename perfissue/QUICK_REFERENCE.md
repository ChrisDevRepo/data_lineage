# Quick Reference Guide - Parser Subsystem

**Version:** v4.3.1
**Date:** 2025-11-12
**Status:** Production Ready ✅

---

## Critical Fix Summary (1% → 100%)

**Problem:** SQLGlot WARN mode returned empty Command nodes
**Solution:** Regex-first architecture with SQLGlot enhancement
**Result:** 100% success rate (349/349 SPs)

---

## Parser Architecture (Regex-First)

```
┌─────────────────────────────────────────────────────┐
│  Phase 1: Regex Scan (Guaranteed Baseline)          │
│  - Runs on FULL DDL (no statement splitting)        │
│  - Comprehensive patterns (FROM, JOIN, CROSS JOIN)  │
│  - ALWAYS succeeds, provides baseline                │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 2: SQLGlot Enhancement (Optional Bonus)      │
│  - RAISE mode (strict, fails fast)                  │
│  - AST-based parsing                                 │
│  - Failures ignored (regex has coverage)            │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 3: Post-Processing                           │
│  - Remove system schemas (sys, dummy)               │
│  - Remove temp tables (#temp, @variables)           │
│  - Remove CTEs (non-persistent)                     │
│  - Deduplicate results                              │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 4: Confidence Calculation                    │
│  - Compare found vs expected tables                 │
│  - Map completeness % to discrete scores            │
│  - Output: 0, 75, 85, or 100                        │
└─────────────────────────────────────────────────────┘
```

**Location:** `parsers/quality_aware_parser.py` (lines 735-768)

---

## Confidence Model (v2.1.0)

### **4 Discrete Values:**

| Score | Threshold | Meaning |
|-------|-----------|---------|
| **100** | ≥90% | Excellent match |
| **85** | 70-89% | Good match |
| **75** | 50-69% | Fair match |
| **0** | <50% | Poor match |

### **Algorithm:**
```python
completeness = (found_tables / expected_tables) * 100

if completeness >= 90:
    return 100
elif completeness >= 70:
    return 85
elif completeness >= 50:
    return 75
else:
    return 0
```

### **Special Cases:**
- **Orchestrators** (only EXEC) → **100%**
- **Parse failures** → **0%**

**Location:** `utils/confidence_calculator.py`

---

## DMV Extraction (Synapse)

### **PRIMARY METHOD:**
**File:** `extractors/get_metadata.ipynb` (Jupyter notebook)

### **4 Parquet Files:**
1. **objects.parquet** - Database objects
2. **dependencies.parquet** - Object dependencies
3. **definitions.parquet** - DDL definitions
4. **query_logs.parquet** - Execution logs (optional)

### **Object Types (4 consolidated):**
- Table
- View
- Stored Procedure
- Function (TF/IF/FN merged)

### **Query Log Filter (Whitelist):**
```sql
WHERE (
    r.command LIKE 'EXEC %'
    OR r.command LIKE 'EXECUTE %'
    OR r.command LIKE 'INSERT %'
    OR r.command LIKE 'UPDATE %'
    OR r.command LIKE 'DELETE %'
    OR r.command LIKE 'MERGE %'
    OR r.command LIKE 'TRUNCATE %'
)
-- Excludes: Ad-hoc SELECT, WITH/CTE, DDL (CREATE/ALTER/DROP)
```

**Research:** No "is_adhoc" flag exists in `sys.dm_pdw_exec_requests`

---

## Testing Quick Commands

```bash
# Full validation (100% check)
python3 testing/check_parsing_results.py

# Specific SP verification
python3 testing/verify_sp_parsing.py <sp_name>

# Deep debugging
python3 testing/analyze_sp.py <sp_name>

# API end-to-end test
./testing/test_upload.sh

# Unit tests (73+ tests)
pytest testing/unit/ -v

# Integration tests (1,067 objects)
pytest testing/integration/ -v
```

---

## Configuration (.env)

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

**Location:** `config/settings.py`

---

## Phantom Object Detection

### **What are Phantoms?**
Objects referenced in SQL but missing from catalog metadata

### **Features:**
- Negative IDs (-1 to -∞)
- Whitelist-based filtering
- Visual indicators (🔶 orange dashed border)
- Tracked in separate tables

### **Configuration:**
- **Include:** `PHANTOM_INCLUDE_SCHEMAS` (wildcard support)
- **Exclude:** `PHANTOM_EXCLUDE_DBO_OBJECTS` (dbo schema only)
- **Universal:** System schemas always excluded

**Location:** `core/gap_detector.py`

---

## SQL Cleaning Rules (YAML)

### **Rule Format:**
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

### **Rule Categories:**
1. Comments removal
2. PRINT statements
3. DECLARE variables
4. SET statements (SET NOCOUNT, etc.)
5. IF EXISTS blocks
6. DROP IF EXISTS cleanup
7. Dynamic SQL (EXEC sp_executesql)
8. RAISERROR statements
9. Whitespace normalization

**Location:** `rules/tsql/*.yaml`

---

## Performance Metrics (v4.3.1)

### **Parser Success:**
- ✅ **100%** success rate (349/349 SPs)
- ✅ **82.5%** at confidence 100 (288 SPs)
- ✅ **7.4%** at confidence 85 (26 SPs)
- ✅ **10.0%** at confidence 75 (35 SPs)

### **Dependency Analysis:**
- Average **3.20 inputs** per SP
- Average **1.87 outputs** per SP

### **Test Coverage:**
- 73+ unit tests (< 1 second)
- 11 integration tests (1,067 objects)
- 100% pass rate

---

## Key File Locations

| Purpose | File | Key Lines |
|---------|------|-----------|
| **Main Parser** | `parsers/quality_aware_parser.py` | 735-768 |
| **Confidence** | `utils/confidence_calculator.py` | 50-80 |
| **Phantom Detection** | `core/gap_detector.py` | 100-150 |
| **SQL Cleaning** | `parsers/sql_cleaning_rules.py` | 200-400 |
| **DuckDB Workspace** | `core/duckdb_workspace.py` | All |
| **Settings** | `config/settings.py` | 30-80 |
| **DMV Extraction** | `extractors/get_metadata.ipynb` | Cells 5, 11 |

---

## Why Regex-First Works

### **✅ Advantages:**

1. **No Context Loss**
   - Regex runs on FULL DDL
   - JOIN clauses stay with SELECT
   - CROSS JOIN patterns detected

2. **Guaranteed Baseline**
   - Regex ALWAYS succeeds
   - Provides minimum coverage
   - SQLGlot failures don't impact results

3. **Combined Accuracy**
   - Regex catches patterns SQLGlot misses
   - SQLGlot adds AST-based enhancements
   - Best-of-both-worlds

### **❌ Why SQLGlot WARN Failed:**

1. **Silent Failures**
   - Returned empty Command nodes
   - No exceptions, no warnings
   - Zero table extraction

2. **Statement Splitting**
   - Orphaned JOIN clauses
   - Lost SELECT context
   - Incorrect parsing

3. **Production Impact**
   - 1% success rate (2/515 SPs)
   - Average confidence: 0.0
   - Complete breakdown

---

## Regex Patterns (Key)

### **Source Patterns (FROM/JOIN):**
```regex
FROM\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
JOIN\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
INNER\s+JOIN\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
LEFT\s+JOIN\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
RIGHT\s+JOIN\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
FULL\s+JOIN\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
CROSS\s+JOIN\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
```

### **Target Patterns (INSERT/UPDATE/DELETE):**
```regex
INSERT\s+INTO\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
UPDATE\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
DELETE\s+FROM\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
MERGE\s+INTO\s+(\[?[\w\.]+\]?\.)?(\[?[\w]+\]?)
```

**Location:** `parsers/quality_aware_parser.py` (embedded in code)

---

## Troubleshooting

### **Low Confidence (<75):**
1. Add `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` comment hints
2. Check SQL cleaning rules (might be removing important code)
3. Verify DMV dependencies are correct
4. Use `analyze_sp.py` for deep debugging

### **Parse Failures (confidence = 0):**
1. Check for unsupported SQL syntax
2. Review regex patterns (might need expansion)
3. Add specific cleaning rule for problematic pattern
4. Use `verify_sp_parsing.py` for validation

### **Missing Dependencies:**
1. Verify DMV extraction completed successfully
2. Check `dependencies.parquet` has expected entries
3. Validate object exists in `objects.parquet`
4. Review phantom detection settings

### **Phantom Objects:**
1. Verify whitelist configuration (`PHANTOM_INCLUDE_SCHEMAS`)
2. Check exclude patterns (`PHANTOM_EXCLUDE_DBO_OBJECTS`)
3. Confirm object is truly missing from catalog
4. Review schema naming (wildcards supported)

---

## Documentation Index

| Document | Purpose | Size |
|----------|---------|------|
| `README_PERFISSUE.md` | Main overview and directory structure | 600+ lines |
| `FILE_INVENTORY.md` | Complete file listing with purposes | 800+ lines |
| `QUICK_REFERENCE.md` | This file - fast lookup | 400+ lines |
| `docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md` | All code embedded | 3,000+ lines |
| `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md` | Architecture analysis | 800+ lines |
| `docs/USAGE.md` | User guide | 500+ lines |
| `docs/REFERENCE.md` | Technical reference | 600+ lines |
| `docs/RULE_DEVELOPMENT.md` | Rule creation guide | 400+ lines |

---

## API Integration

### **Endpoints:**
```
POST   /api/upload-parquet      Upload Parquet files
GET    /api/parsing-job/{id}    Get job status
GET    /api/results             Get parsing results
DELETE /api/clear                Clear workspace
```

### **Upload Example:**
```bash
curl -X POST "http://localhost:8000/api/upload-parquet?incremental=true" \
  -F "files=@objects.parquet" \
  -F "files=@dependencies.parquet" \
  -F "files=@definitions.parquet"
```

**Location:** `api/parser_job.py`

---

## Supported SQL Dialects

| Dialect | Code | Data Warehouses |
|---------|------|-----------------|
| **T-SQL** | `tsql` | Azure Synapse, SQL Server, Azure SQL *(default)* |
| **Fabric** | `fabric` | Microsoft Fabric |
| **PostgreSQL** | `postgres` | PostgreSQL data warehouses |
| **Oracle** | `oracle` | Oracle Database |
| **Snowflake** | `snowflake` | Snowflake |
| **Redshift** | `redshift` | Amazon Redshift |
| **BigQuery** | `bigquery` | Google BigQuery |

**Location:** `dialects/`

---

## Comment Hints (Manual Override)

### **Format:**
```sql
-- @LINEAGE_INPUTS: schema.table1, schema.table2, schema.table3
-- @LINEAGE_OUTPUTS: schema.target_table
CREATE PROCEDURE schema.MyStoredProcedure
AS
BEGIN
    -- Procedure logic
END
```

### **Benefits:**
- 100% confidence for hinted SPs
- Override parser results
- Document complex dependencies
- Handle dynamic SQL

**Parser:** `parsers/comment_hints_parser.py`

---

## Next Steps

1. **Start Here:**
   - Read `README_PERFISSUE.md` (overview)
   - Review this `QUICK_REFERENCE.md` (concepts)

2. **Understand Parser:**
   - Read `parsers/quality_aware_parser.py` (lines 735-768)
   - Review `docs/COMPLETE_PARSING_ARCHITECTURE_REPORT.md`

3. **Run Tests:**
   - Execute `testing/check_parsing_results.py`
   - Verify 100% success rate

4. **Review Extractors:**
   - Open `extractors/get_metadata.ipynb`
   - Validate DMV queries

5. **Dive Deep:**
   - Read `docs/COMPLETE_TECHNICAL_REPORT_MASSIVE.md`
   - Study all embedded code

---

**Last Updated:** 2025-11-12
**Parser Version:** v4.3.1
**Status:** Production Ready ✅

