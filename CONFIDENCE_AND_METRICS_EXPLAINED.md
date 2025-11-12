# Parser Confidence & Metrics Explanation

**Version:** v4.3.2
**Date:** 2025-11-12

---

## 🎯 How Confidence is Calculated

### Simplified 4-Value Model (v2.1.0)

**Formula:**
```python
completeness_pct = (found_tables / expected_tables) * 100

if parse_failed:
    confidence = 0
elif is_orchestrator:  # Only EXEC calls, no tables
    confidence = 100
elif completeness_pct >= 90:
    confidence = 100
elif completeness_pct >= 70:
    confidence = 85
elif completeness_pct >= 50:
    confidence = 75
else:
    confidence = 0
```

### Where Values Come From

**1. Expected Tables (Baseline)**
```python
# Runs on ORIGINAL DDL (full text, no preprocessing)
regex_sources, regex_targets = _regex_scan(original_ddl)
expected_tables = len(regex_sources_valid) + len(regex_targets_valid)
```

**Regex patterns:**
- Sources: `FROM`, `JOIN`, `INNER/LEFT/RIGHT/FULL/CROSS JOIN`
- Targets: `INSERT INTO`, `UPDATE ... SET`, `DELETE FROM`, `MERGE INTO`
- Validated against catalog (real objects only)

**2. Found Tables (Combined Results)**
```python
# STEP 1: Regex baseline (guaranteed coverage)
regex_sources, regex_targets = _regex_scan(original_ddl)

# STEP 2: SQLGlot enhancement (optional bonus)
sqlglot_sources, sqlglot_targets = _sqlglot_parse(cleaned_ddl)

# STEP 3: Combine (union of both)
combined_sources = regex_sources ∪ sqlglot_sources
combined_targets = regex_targets ∪ sqlglot_targets

# STEP 4: Validate against catalog
found_tables = len(combined_sources_valid) + len(combined_targets_valid)
```

**Key insight:** SQLGlot can only ADD tables (bonus), never subtract (regex is baseline).

---

## 📊 Tracked Metrics (v4.3.2)

### Per Stored Procedure

**1. Parsing Performance**
```
parse_time > 1.0 seconds → WARNING logged
```

**2. Regex Baseline**
```
regex_sources: X tables
regex_targets: Y tables
regex_sp_calls: Z stored procedures
regex_function_calls: W functions
```

**3. SQLGlot Enhancement**
```
sqlglot_total_stmts: N statements split from DDL
sqlglot_success_count: M statements parsed successfully
sqlglot_failed_count: F statements failed to parse
sqlglot_empty_command_count: E empty Command nodes skipped
sqlglot_success_rate: (M/N) * 100%
```

**4. Combined Results**
```
final_sources: A tables (after validation + hints)
final_targets: B tables (after validation + hints)
catalog_validation_rate: % of extracted tables found in catalog
```

**5. Confidence Calculation**
```
expected_count: regex baseline (validated)
found_count: combined results (validated)
completeness_pct: (found / expected) * 100
confidence: 0 | 75 | 85 | 100
```

### Aggregate Statistics

**Overall Parser Performance:**
```sql
SELECT
    COUNT(*) as total_sps,
    SUM(CASE WHEN confidence = 100 THEN 1 ELSE 0 END) as conf_100,
    SUM(CASE WHEN confidence = 85 THEN 1 ELSE 0 END) as conf_85,
    SUM(CASE WHEN confidence = 75 THEN 1 ELSE 0 END) as conf_75,
    SUM(CASE WHEN confidence = 0 THEN 1 ELSE 0 END) as conf_0,
    AVG(expected_count) as avg_expected,
    AVG(found_count) as avg_found
FROM lineage_metadata
WHERE primary_source = 'parser'
```

**Target Metrics (100% Success Rate):**
- Total SPs: 349 (with dependencies)
- Confidence 100: 82.5% (288 SPs)
- Confidence 85: 7.4% (26 SPs)
- Confidence 75: 10.0% (35 SPs)
- Confidence 0: 0% (0 SPs)
- Avg inputs: 3.20 per SP
- Avg outputs: 1.87 per SP

---

## 🔍 How to Check SQLGlot Performance

### During Parsing (Logs)

**Set log level to DEBUG:**
```python
import logging
logging.getLogger('lineage_v3.parsers.quality_aware_parser').setLevel(logging.DEBUG)
```

**Look for these log lines:**
```
# Per SP parsing
DEBUG: Regex baseline: X sources, Y targets, Z SP calls, W function calls (after filtering)
DEBUG: SQLGlot stats: M/N statements parsed (X% success), F failed, E empty
DEBUG: Slow parse for object_id 12345: 2.5s  # If >1 second

# Per statement (if failures)
DEBUG: SQLGlot parse failed: ParseError at line 42...
DEBUG: Skipped empty Command node, using regex baseline
```

### After Parsing (Database Query)

**Check overall success rate:**
```python
# From scripts/testing/check_parsing_results.py
import duckdb

conn = duckdb.connect('data/lineage_workspace.duckdb')

# Overall success
result = conn.execute("""
    SELECT
        COUNT(*) as total_sps,
        COUNT(*) FILTER (WHERE array_length(input_ids) > 0 OR array_length(output_ids) > 0) as sps_with_dependencies,
        AVG(confidence) as avg_confidence,
        AVG(expected_count) as avg_expected,
        AVG(found_count) as avg_found
    FROM lineage_metadata
    WHERE primary_source = 'parser'
""").fetchone()

print(f"Total SPs: {result[0]}")
print(f"SPs with dependencies: {result[1]} ({result[1]/result[0]*100:.1f}%)")
print(f"Average confidence: {result[2]:.1f}")
print(f"Average expected tables: {result[3]:.2f}")
print(f"Average found tables: {result[4]:.2f}")
```

**Confidence distribution:**
```sql
SELECT
    confidence,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM lineage_metadata
WHERE primary_source = 'parser'
GROUP BY confidence
ORDER BY confidence DESC
```

**Top SPs by expected tables (complex SPs):**
```sql
SELECT
    o.schema_name || '.' || o.object_name as sp_name,
    l.expected_count,
    l.found_count,
    l.confidence,
    ROUND(l.found_count * 100.0 / NULLIF(l.expected_count, 0), 1) as completeness_pct
FROM lineage_metadata l
JOIN objects o ON l.object_id = o.object_id
WHERE l.primary_source = 'parser'
  AND l.expected_count > 10  -- Complex SPs with many dependencies
ORDER BY l.expected_count DESC
LIMIT 20
```

---

## 📈 Interpreting Results

### Scenario 1: High Confidence (100)
```
Expected: 10 tables
Found: 10 tables
Completeness: 100%
Confidence: 100
```

**Meaning:**
- ✅ Regex found 10 tables
- ✅ Combined (regex + SQLGlot) found 10 tables
- ✅ Perfect match, no missing dependencies

**SQLGlot impact:** May have added 0-5 tables that regex missed

---

### Scenario 2: Good Confidence (85)
```
Expected: 10 tables
Found: 8 tables
Completeness: 80%
Confidence: 85
```

**Meaning:**
- ✅ Regex found 10 tables (baseline)
- ⚠️ Combined found only 8 tables (2 missing)
- ⚠️ Likely: 2 tables filtered out (temp tables, CTEs, phantom exclusions)

**Action:** Review excluded objects, may need `@LINEAGE_INPUTS` hints

---

### Scenario 3: Acceptable Confidence (75)
```
Expected: 10 tables
Found: 6 tables
Completeness: 60%
Confidence: 75
```

**Meaning:**
- ⚠️ Regex found 10 tables
- ⚠️ Combined found only 6 (4 missing)
- ⚠️ Significant gap, likely complex dynamic SQL

**Action:** Add `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` comment hints

---

### Scenario 4: Failed Parsing (0)
```
Expected: 10 tables
Found: 2 tables
Completeness: 20%
Confidence: 0
```

**Meaning:**
- ❌ Regex found 10 tables
- ❌ Combined found only 2 (8 missing)
- ❌ Completeness <50%, marked as failure

**Likely causes:**
- Dynamic SQL: `EXEC(@sql)` or `sp_executesql`
- Complex control flow: Deep nesting, WHILE loops, CURSORs
- String concatenation for table names

**Action:** Add `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints (required)

---

## 🛠️ SQLGlot Failure Analysis

### What Counts as "SQLGlot Failure"?

**1. Parse Exception**
```
SQLGlot raised exception during parse_one()
Example: "Unexpected token at line 42"
Result: Statement skipped, regex baseline used
```

**2. Empty Command Node**
```
SQLGlot returned exp.Command with no .expression
Example: WARN mode bug (now prevented by defensive check)
Result: Statement skipped, regex baseline used
```

**3. Statement Splitting Failure**
```
Error splitting DDL into individual statements
Example: Malformed GO batches
Result: All statements skipped, regex baseline used for entire DDL
```

### Why SQLGlot Fails (T-SQL Specific)

**Common causes:**
1. **T-SQL Extensions** - BEGIN TRY/CATCH, RAISERROR, etc.
2. **GO Batches** - SQLGlot doesn't recognize GO keyword
3. **Variables** - DECLARE @var, SET @var patterns
4. **Dynamic SQL** - EXEC(@sql) with string concatenation
5. **Complex Functions** - T-SQL specific functions (DATEADD, etc.)

**Mitigation:**
- ✅ Preprocessing removes most T-SQL syntax
- ✅ SELECT simplification reduces complexity (v4.3.2)
- ✅ Statement splitting handles GO batches
- ✅ Regex baseline provides guaranteed coverage

---

## 💡 Key Takeaways

**1. Regex Baseline = Guaranteed Coverage**
- Runs on FULL original DDL
- No preprocessing, no context loss
- Provides `expected_tables` count

**2. SQLGlot Enhancement = Optional Bonus**
- Runs on cleaned/simplified DDL
- Can only ADD tables, never subtract
- Failures are silent (regex baseline covers it)

**3. Confidence = How Complete is the Result**
```
100%: Perfect (≥90% of expected tables found)
85%:  Good (70-89% found)
75%:  Acceptable (50-69% found)
0%:   Failed (<50% found OR parse exception)
```

**4. SQLGlot Success Rate ≠ Parser Success Rate**
- SQLGlot may fail 50% of statements
- Parser can still be 100% successful
- Because: Regex baseline provides coverage

**5. Tracking Helps Optimization**
- Identify slow SPs (>1 second)
- Identify SQLGlot-unfriendly patterns
- Optimize preprocessing rules

---

## 🧪 Example Log Output

```
# SP with perfect parsing
DEBUG: Regex baseline: 5 sources, 2 targets, 1 SP calls, 0 function calls (after filtering)
DEBUG: SQLGlot stats: 8/10 statements parsed (80.0% success), 2 failed, 0 empty
DEBUG: Final: 5 sources, 2 targets, confidence 100

# SP with SQLGlot struggles
DEBUG: Regex baseline: 12 sources, 3 targets, 0 SP calls, 2 function calls (after filtering)
DEBUG: SQLGlot stats: 3/15 statements parsed (20.0% success), 10 failed, 2 empty
DEBUG: Final: 12 sources, 3 targets, confidence 100
# Note: Still 100% confidence because regex baseline provided coverage

# Slow SP
DEBUG: Regex baseline: 25 sources, 8 targets, 5 SP calls, 3 function calls (after filtering)
DEBUG: SQLGlot stats: 40/50 statements parsed (80.0% success), 8 failed, 2 empty
WARNING: Slow parse for object_id 12345: 2.3s
DEBUG: Final: 26 sources, 8 targets, confidence 100
```

---

**Last Updated:** 2025-11-12 (v4.3.2)
**File:** `lineage_v3/parsers/quality_aware_parser.py`
