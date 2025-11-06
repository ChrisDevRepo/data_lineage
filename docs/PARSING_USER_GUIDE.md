# SQL Parsing User Guide

**Version:** 4.1.3
**Last Updated:** 2025-11-06
**For:** DBAs, Data Engineers, External Users

---

## Overview

The Data Lineage Parser extracts data lineage from Azure Synapse stored procedures, views, and tables using a **multi-source approach**:

| Source | Object Types | Confidence | Coverage |
|--------|--------------|------------|----------|
| **DMV** | Views | 1.0 | 100% |
| **Metadata + Reverse Lookup** | Tables | 1.0 | Referenced tables |
| **Parser** (SQLGlot + Regex + Rules) | Stored Procedures | 0.50-0.95 | 100% attempted |
| **Query Log Validation** | Validated SPs | 0.95 | Optional |

**Current Performance (v4.1.3):**
- Total Objects: 763 (202 SPs, 61 Views, 500 Tables)
- High Confidence (≥0.85): 95.5% (729/763 objects)
- SP Confidence: 97.0% (196/202 SPs)
- Industry Benchmark: 30-40% → **We're 3x better!**

---

## What Gets Parsed

### ✅ Fully Supported (Confidence ≥0.85)

| Pattern | Example | Confidence |
|---------|---------|-----------|
| **Views** | `CREATE VIEW v AS SELECT * FROM t` | 1.0 (DMV) |
| **Tables** | Referenced by SPs/Views | 1.0 (Metadata) |
| **Simple SELECT** | `SELECT * FROM dbo.Customers` | 0.85 |
| **JOINs** | `FROM t1 JOIN t2 ON ...` | 0.85 |
| **INSERT INTO** | `INSERT INTO target SELECT * FROM source` | 0.85 |
| **UPDATE** | `UPDATE target SET ... FROM source` | 0.85 |
| **MERGE** | `MERGE INTO target USING source` | 0.85 |
| **DELETE/TRUNCATE** | `DELETE FROM t` | 0.85 |
| **CTEs** | `WITH cte AS (...) SELECT * FROM cte` | 0.85 |
| **Subqueries** | `SELECT * FROM (SELECT ...) AS sub` | 0.85 |
| **EXEC SP Calls** | `EXEC [dbo].[spProcessOrders]` | 0.85 (v3.8.0+) |

### ⚙️ SP-to-SP Dependencies (NEW in v3.8.0)

The parser now tracks **stored procedure calls** via `EXEC`/`EXECUTE` statements:

```sql
-- Example: Master SP calling worker SPs
CREATE PROC [dbo].[spMasterETL] AS
BEGIN
    EXEC [dbo].[spLoadStaging]      -- ✅ Tracked as dependency
    EXEC [dbo].[spValidateData]     -- ✅ Tracked as dependency
    EXEC [dbo].[LogMessage] @msg    -- ❌ Filtered (utility SP)
END
```

**How It Works:**
- **Regex Detection**: Pattern matching finds `EXEC [schema].[sp_name]`
- **Selective Merge**: Only SPs from regex added (tables use SQLGlot)
- **Utility Filtering**: Logging/admin SPs excluded (LogMessage, spLastRowCount, etc.)

**Confidence Impact:**
- SPs with EXEC calls → Confidence increases (more complete lineage)
- ~63 SP-to-SP dependencies now captured
- High-confidence rate: 71 → 78 SPs (35% → 39%)

**What's Tracked:**
- ✅ `EXEC [schema].[sp_name]` (explicit calls)
- ✅ `EXECUTE [schema].[sp_name]` (full keyword)
- ❌ `EXEC (@variable)` (dynamic SQL - can't resolve)
- ❌ `EXEC sp_executesql` (dynamic SQL)

### 🚫 Filtered Utility SPs (Excluded from Lineage)

The parser automatically **excludes** utility and logging stored procedures from lineage tracking. These SPs don't represent data dependencies and would clutter the lineage graph if included.

#### Excluded Stored Procedures

| Category | SP Name | Why Excluded | Example Usage |
|----------|---------|--------------|---------------|
| **Logging** | LogMessage | Administrative logging only | `EXEC LogMessage @msg, @level` |
| **Logging** | LogError | Error logging only | `EXEC LogError @error, @proc` |
| **Logging** | LogInfo | Info logging only | `EXEC LogInfo @msg` |
| **Logging** | LogWarning | Warning logging only | `EXEC LogWarning @msg` |
| **Utility** | spLastRowCount | Returns row count (no data flow) | `EXEC spLastRowCount @count OUT` |

#### How Filtering Works

```sql
-- Example: ETL stored procedure with mixed calls
CREATE PROC [dbo].[spLoadCustomers] AS
BEGIN
    -- ✅ TRACKED: Business SP dependency
    EXEC [dbo].[spValidateCustomers]

    -- ❌ FILTERED: Logging (not data lineage)
    EXEC [dbo].[LogMessage] @msg = 'Starting load', @level = 'INFO'

    -- ✅ TRACKED: Business SP dependency
    EXEC [dbo].[spTransformCustomers]

    -- ❌ FILTERED: Utility SP (no data flow)
    EXEC [dbo].[spLastRowCount] @rowCount OUT

    -- ❌ FILTERED: Error logging
    EXEC [dbo].[LogError] @error = 'Failed', @proc = 'spLoadCustomers'
END
```

**Result in Lineage:**
- **Inputs:** 2 SPs (`spValidateCustomers`, `spTransformCustomers`)
- **Outputs:** Depends on table operations
- **Excluded:** 3 calls (LogMessage, spLastRowCount, LogError)

#### Why These SPs Are Filtered

**Logging SPs:**
- **Purpose:** Audit trail, debugging, monitoring
- **Not Data Lineage:** Don't transform or move data
- **Impact:** Would add ~682 noise edges to lineage graph
- **User Benefit:** Cleaner, more focused lineage visualization

**Utility SPs:**
- **Purpose:** Helper functions (row counts, metadata queries)
- **Not Data Lineage:** No table-to-table data flow
- **Example:** `spLastRowCount` only queries system DMVs (`sys.dm_pdw_*`)
- **User Benefit:** Focus on business data transformations

#### Verification Example

From smoke testing:

```sql
-- dbo.spLastRowCount (correctly excluded)
CREATE PROC [dbo].[spLastRowCount] @Count [BIGINT] OUT AS
BEGIN
    SELECT @Count = SUM(row_count)
    FROM sys.dm_pdw_sql_requests  -- System DMV (not business data)
    WHERE row_count <> -1
END
```

**Parser Result:**
- Inputs: 0 (no business dependencies) ✅
- Outputs: 0 (no table writes) ✅
- Excluded from lineage graph: Yes ✅

#### Adding Custom Filters

If you have additional utility SPs that should be filtered, they can be added to the exclusion list in `quality_aware_parser.py`:

```python
EXCLUDED_UTILITY_SPS = {
    # Logging
    'logmessage', 'logerror', 'loginfo', 'logwarning',
    # Utility
    'splastrowcount',
    # Add custom utility SPs here (lowercase)
    # 'your_utility_sp',
}
```

**Note:** SP names are case-insensitive in the filter.

### ❌ Out of Scope

| Pattern | Why | Current Behavior |
|---------|-----|------------------|
| **Dynamic SQL** | `EXEC('SELECT * FROM ' + @table)` | Runtime table name → Confidence 0.50 |
| **Temp Tables** | `#TempTable` | Session-specific → Excluded (traced through) |
| **Table Variables** | `@TableVar` | Batch-specific → Excluded (traced through) |
| **System Tables** | `sys.objects`, `INFORMATION_SCHEMA` | Out of scope → Filtered |
| **Cross-Database** | `OtherDB.dbo.Table` | May not resolve → Excluded if not found |

---

## Confidence Levels Explained

| Confidence | Meaning | What It Means |
|-----------|---------|---------------|
| **1.00** | Authoritative | DMV metadata or table existence (100% accurate) |
| **0.95** | Dual-Parser Agreement | Both SQLGlot and SQLLineage agree (≥90% match) |
| **0.85** | Single Parser Success | SQLGlot parsed successfully with quality validation |
| **0.75** | Moderate Agreement | Parsers mostly agree (≥70% match) |
| **0.50** | Low Confidence | Complex SQL or parser disagreement → **May need SQL refactoring** |
| **0.00** | Parse Failed | No lineage extracted → **Review SQL** |

---

## How to Improve Parsing Results

### Best Practices

#### ✅ DO

**1. Use Semicolons**
```sql
-- GOOD: Clear statement boundaries
TRUNCATE TABLE dbo.Staging;
INSERT INTO dbo.Target SELECT * FROM dbo.Source;
UPDATE dbo.Metrics SET LastLoad = GETDATE();
```

**2. Use Schema-Qualified Names**
```sql
-- BEST: Explicit schema
SELECT * FROM CONSUMPTION_FINANCE.DimCustomers;

-- OK: Defaults to dbo
SELECT * FROM Customers;
```

**3. Separate Business Logic from Error Handling**
```sql
-- GOOD: Parser focuses on TRY block
BEGIN TRY
    INSERT INTO dbo.Target SELECT * FROM dbo.Source;
END TRY
BEGIN CATCH
    EXEC dbo.LogError;  -- Automatically filtered
END CATCH
```

#### ❌ DON'T

**1. Mix Business Logic with Logging**
```sql
-- BAD: ErrorLog appears in lineage!
INSERT INTO dbo.ErrorLog VALUES ('Starting...');
INSERT INTO dbo.Target SELECT * FROM dbo.Source;
INSERT INTO dbo.ErrorLog VALUES ('Done');
```

**2. Use Dynamic SQL When Static SQL Works**
```sql
-- BAD: Can't parse at compile time
DECLARE @table NVARCHAR(50) = 'Customers';
EXEC('SELECT * FROM dbo.' + @table);

-- GOOD: Use static SQL
SELECT * FROM dbo.Customers;
```

**3. Add Logging After COMMIT**
```sql
-- BAD: Post-commit logging confuses parser
INSERT INTO dbo.Target SELECT * FROM dbo.Source;
COMMIT TRANSACTION;
INSERT INTO dbo.AuditLog VALUES ('Success');  -- Appears in lineage!

-- GOOD: Parser auto-removes post-COMMIT code
INSERT INTO dbo.Target SELECT * FROM dbo.Source;
COMMIT TRANSACTION;
-- Anything after COMMIT is ignored
```

---

## Using Comment Hints for Edge Cases (NEW in v4.2.0)

For scenarios where the parser cannot automatically extract dependencies (e.g., dynamic SQL, complex CATCH blocks), you can use **special comment syntax** to explicitly document table dependencies.

### Syntax

Add these comments anywhere in your stored procedure:

```sql
-- @LINEAGE_INPUTS: schema.table1, schema.table2
-- @LINEAGE_OUTPUTS: schema.table3
```

**Format:**
- Start with `--` (SQL comment)
- Keyword: `@LINEAGE_INPUTS:` or `@LINEAGE_OUTPUTS:`
- Comma-separated list of fully qualified table names (schema.table)
- One hint per line

### When to Use Comment Hints

Use comment hints for:

| Scenario | Why Parser Fails | Solution |
|----------|-----------------|----------|
| **Dynamic SQL** | Table name constructed at runtime | Add hint with actual table |
| **Complex CATCH Blocks** | Parser assumes logging only | Document data operations |
| **Conditional Logic** | Only one code path analyzed | Document all possible tables |
| **Cross-database Dependencies** | External references may not resolve | Explicit documentation |
| **Concatenated Table Names** | `'Table' + @suffix` patterns | List actual table variants |

### Example 1: Dynamic SQL

**Problem:** Parser can't resolve table names constructed at runtime.

```sql
CREATE PROC [dbo].[spDynamicLoad] @tableName VARCHAR(100)
AS
BEGIN
    -- @LINEAGE_INPUTS: dbo.SourceData
    -- @LINEAGE_OUTPUTS: dbo.Customers, dbo.Orders
    -- Reason: Table name from parameter - could be Customers or Orders

    DECLARE @sql NVARCHAR(MAX);
    SET @sql = 'INSERT INTO ' + @tableName + ' SELECT * FROM dbo.SourceData';
    EXEC sp_executesql @sql;
END
```

**Result:**
- Without hints: Confidence = 0.50 (dynamic SQL, no tables extracted)
- With hints: Confidence = 0.75 (hints provide missing dependencies)
- Lineage: `SourceData` → `spDynamicLoad` → `Customers`, `Orders`

### Example 2: CATCH Block Dependencies

**Problem:** Parser removes CATCH blocks assuming they only contain logging.

```sql
CREATE PROC [dbo].[spLoadWithRecovery]
AS
BEGIN TRY
    INSERT INTO dbo.Target SELECT * FROM dbo.Source;
END TRY
BEGIN CATCH
    -- @LINEAGE_INPUTS: dbo.Source
    -- @LINEAGE_OUTPUTS: dbo.ErrorRecoveryTable
    -- Reason: CATCH block has real data operation (not just logging)

    -- Move failed records to recovery table
    INSERT INTO dbo.ErrorRecoveryTable
    SELECT * FROM dbo.Source WHERE ValidationStatus = 'Failed';
END CATCH
```

**Result:**
- Without hints: Missing `ErrorRecoveryTable` dependency
- With hints: Complete lineage including error recovery path
- Confidence: 0.85 (parser + hints)

### Example 3: Conditional Table Access

**Problem:** Parser may only analyze one code path.

```sql
CREATE PROC [dbo].[spLoadByType] @type VARCHAR(20)
AS
BEGIN
    -- @LINEAGE_INPUTS: dbo.CustomerData, dbo.OrderData, dbo.ProductData
    -- @LINEAGE_OUTPUTS: dbo.TargetTable
    -- Reason: Conditional logic - different sources based on @type parameter

    IF @type = 'customers'
        INSERT INTO dbo.TargetTable SELECT * FROM dbo.CustomerData;
    ELSE IF @type = 'orders'
        INSERT INTO dbo.TargetTable SELECT * FROM dbo.OrderData;
    ELSE
        INSERT INTO dbo.TargetTable SELECT * FROM dbo.ProductData;
END
```

**Result:**
- Without hints: May only capture one branch
- With hints: All possible data flows documented
- Confidence: 0.85 (comprehensive lineage)

### Comment Hints Rules

#### ✅ DO

1. **Use Fully Qualified Names**
   ```sql
   -- ✅ GOOD: Explicit schema
   -- @LINEAGE_INPUTS: CONSUMPTION_FINANCE.DimCustomers, dbo.Staging

   -- ❌ BAD: No schema (ambiguous)
   -- @LINEAGE_INPUTS: DimCustomers, Staging
   ```

2. **Document the Reason**
   ```sql
   -- @LINEAGE_OUTPUTS: dbo.CustomerArchive
   -- Reason: Dynamic SQL in loop - iterates through customer partitions
   ```

3. **Place Hints Near Relevant Code**
   ```sql
   -- @LINEAGE_INPUTS: dbo.ExternalData
   BEGIN CATCH
       -- Hint is close to the operation it documents
       SELECT * FROM dbo.ExternalData WHERE Status = 'Error';
   END CATCH
   ```

4. **Use for Edge Cases Only**
   - Only add hints when parser actually fails
   - Most SPs don't need hints (97% parse successfully)
   - Check confidence first - only add if < 0.85

#### ❌ DON'T

1. **Include Temp Tables or Table Variables**
   ```sql
   -- ❌ BAD: Temp tables filtered automatically
   -- @LINEAGE_INPUTS: #TempStaging, @TableVar

   -- ✅ GOOD: Only persistent tables
   -- @LINEAGE_INPUTS: dbo.Staging
   ```

2. **Add Utility/Logging SPs**
   ```sql
   -- ❌ BAD: Utility SPs filtered automatically
   -- @LINEAGE_OUTPUTS: dbo.LogMessage

   -- ✅ GOOD: Business tables only
   -- @LINEAGE_OUTPUTS: dbo.FactSales
   ```

3. **Duplicate What Parser Already Found**
   ```sql
   -- ❌ UNNECESSARY: Parser handles this perfectly
   -- @LINEAGE_INPUTS: dbo.Source
   INSERT INTO dbo.Target SELECT * FROM dbo.Source;

   -- ✅ ONLY ADD if parser fails (confidence < 0.85)
   ```

4. **Use Hints as Primary Documentation**
   - Hints are for parser assistance, not code documentation
   - Use standard SQL comments for developer notes
   - Hints are stripped during parsing (not visible to other tools)

### How Hints Affect Confidence

| Scenario | Base Confidence | With Hints | Final Confidence | Explanation |
|----------|----------------|------------|------------------|-------------|
| Dynamic SQL only | 0.50 | ✅ | 0.75 | Hints fill complete gap |
| Parser success + hints agree | 0.85 | ✅ | 0.85 | Hints validate parser (no change) |
| Parser partial + hints fill gaps | 0.75 | ✅ | 0.85 | Hints complete missing deps |
| Parser fails + no hints | 0.50 | ❌ | 0.50 | No improvement |
| Parser success + hints conflict | 0.85 | ⚠️ | 0.75 | Conflict reduces confidence |

**Formula:**
- **Base Confidence:** Parser quality (0.50, 0.75, 0.85)
- **Hints Bonus:** +10% if hints validate parser, +25% if hints fill gaps
- **Hint Validation:** Only tables found in catalog are used
- **Conflict Penalty:** -10% if hints contradict parser results

### Validation Process

The parser validates comment hints against the database catalog:

```
Step 1: Extract hints from comments
Step 2: Parse table names (schema.table format)
Step 3: Check each table against objects table
Step 4: Keep only valid tables (exist in catalog)
Step 5: UNION hints with parsed results (no duplicates)
```

**Example Validation:**
```sql
-- @LINEAGE_INPUTS: dbo.Customers, dbo.NonExistentTable, FINANCE.Accounts
```

**Validation Results:**
- ✅ `dbo.Customers` → Valid (exists in catalog)
- ❌ `dbo.NonExistentTable` → Invalid (not in catalog, ignored)
- ✅ `FINANCE.Accounts` → Valid (exists in catalog)

**Final Hints Used:** `dbo.Customers`, `FINANCE.Accounts`

### Viewing Hint Results

Check if your hints were applied:

```bash
# Query lineage_metadata
python lineage_v3/utils/workspace_query_helper.py "
SELECT
    o.schema_name || '.' || o.object_name AS sp_name,
    m.confidence,
    m.primary_source,
    CASE WHEN m.primary_source LIKE '%hints%' THEN 'Yes' ELSE 'No' END AS hints_used
FROM lineage_metadata m
JOIN objects o ON m.object_id = o.object_id
WHERE o.object_type = 'Stored Procedure'
  AND m.confidence >= 0.75
ORDER BY hints_used DESC, m.confidence DESC
"
```

### UAT Feedback Integration

If parser misses a dependency:

1. **Report the issue** using UAT feedback system:
   ```bash
   cd temp/uat_feedback
   python capture_feedback.py \
       --sp "dbo.spYourProc" \
       --issue missing_input \
       --missing "dbo.MissingTable" \
       --notes "Table accessed in dynamic SQL"
   ```

2. **Add comment hint** to the stored procedure:
   ```sql
   -- @LINEAGE_INPUTS: dbo.MissingTable
   -- Reason: Dynamic SQL - reported via UAT feedback
   ```

3. **Re-run parser**:
   ```bash
   cd /home/user/sandbox
   python lineage_v3/main.py run --parquet parquet_snapshots/
   ```

4. **Verify fix**:
   - Check confidence improved (0.50 → 0.75)
   - Verify missing table now appears in lineage

### Best Practices Summary

1. **Check confidence first** - Only add hints if confidence < 0.85
2. **Document the reason** - Why is the hint needed?
3. **Use fully qualified names** - Always include schema
4. **Validate in catalog** - Ensure tables exist
5. **Keep hints close to code** - Near the operation they document
6. **Report issues** - Use UAT feedback for parser improvements
7. **Review regularly** - Remove hints if parser improves

### FAQ

**Q: Will comment hints work with old parser versions?**
A: No, this feature requires v4.2.0 or later. Old versions will ignore the comments harmlessly.

**Q: Can I use hints for views or functions?**
A: Views and functions use DMV metadata (confidence 1.0), so hints are unnecessary and ignored.

**Q: What if I typo a table name in a hint?**
A: Invalid table names are ignored with a warning in parser logs. Check spelling and catalog.

**Q: Do hints replace the need for good SQL practices?**
A: No! Use hints only when parser legitimately can't extract dependencies. Always prefer static SQL over dynamic SQL when possible.

**Q: How do I know if my hints are working?**
A: Check the `primary_source` field in lineage output - it will show "parser_with_hints" if hints were used.

---

## Troubleshooting Low Confidence

### Scenario 1: Confidence = 0.50

**Likely Causes:**
- Dynamic SQL (EXEC with variables)
- Complex error handling (nested TRY/CATCH)
- Mixed business logic and logging
- Parser disagreement

**Action:**
```bash
# Check parser comparison log
python lineage_v3/utils/workspace_query_helper.py "
SELECT object_name, final_confidence, dual_parser_decision
FROM parser_comparison_log
WHERE final_confidence < 0.75
ORDER BY dual_parser_agreement ASC
"
```

**Solution:**
- Review SP for patterns in "Out of Scope" section
- Refactor if possible (see Best Practices)
- Consider SQL simplification for better parsing

### Scenario 2: Missing Expected Tables

**Likely Causes:**
- Table name typo or wrong schema
- Table in CATCH block (filtered)
- Dynamic SQL (table constructed at runtime)

**Check:**
```bash
# List all tables in catalog
python lineage_v3/utils/workspace_query_helper.py "
SELECT schema_name || '.' || object_name AS full_name
FROM objects
WHERE object_type IN ('Table', 'View')
ORDER BY full_name
"
```

---

## Understanding Output Files

The parser generates 3 JSON files in `lineage_output/`:

### 1. `lineage.json` (Internal Format)
```json
{
  "id": 1986106116,
  "name": "spLoadFactGL",
  "object_type": "Stored Procedure",
  "inputs": [101, 102],
  "outputs": [789],
  "provenance": {
    "primary_source": "dual_parser",
    "confidence": 0.95
  }
}
```
**Uses:** DuckDB joins, internal processing
**ID Format:** Integer `object_id` from `sys.objects`

### 2. `frontend_lineage.json` (React Flow Format)
```json
{
  "id": "1986106116",
  "name": "spLoadFactGL",
  "description": "Confidence: 0.95",
  "inputs": ["101", "102"],
  "outputs": ["789"]
}
```
**Uses:** Frontend visualization
**ID Format:** String `object_id` (e.g., `"1986106116"`)
**Note:** Tables/Views always show "Confidence: 1.00"

### 3. `lineage_summary.json` (Statistics)
```json
{
  "total_objects": 85,
  "parsed_objects": 39,
  "coverage": 45.9,
  "confidence_statistics": {
    "high_confidence_count": 31,
    "low_confidence_count": 8
  }
}
```
**Uses:** Quality metrics, coverage reporting

---

## Quick Reference: Supported SQL Patterns

| Pattern | Supported | Notes |
|---------|-----------|-------|
| Simple SELECT | ✅ | |
| JOINs (all types) | ✅ | INNER, LEFT, RIGHT, FULL |
| INSERT INTO | ✅ | |
| UPDATE | ✅ | Including UPDATE FROM |
| MERGE | ✅ | Full MERGE syntax |
| DELETE | ✅ | |
| TRUNCATE | ✅ | |
| CTEs (WITH) | ✅ | Recognized, excluded from final lineage |
| Subqueries | ✅ | |
| Temp Tables (#) | ⚠️ | Traced through, not exposed |
| Table Variables (@) | ⚠️ | Traced through, not exposed |
| Dynamic SQL | ❌ | Runtime table names (0.50) |
| System Tables | ❌ | Filtered (out of scope) |

---

## Getting Help

### Check Parser Statistics
```bash
cd .
python lineage_v3/utils/workspace_query_helper.py
```

### View Low Confidence Objects
```bash
python lineage_v3/utils/workspace_query_helper.py "
SELECT
    o.schema_name || '.' || o.object_name AS full_name,
    m.confidence,
    m.primary_source
FROM lineage_metadata m
JOIN objects o ON m.object_id = o.object_id
WHERE m.confidence < 0.75 AND m.confidence > 0
ORDER BY m.confidence ASC
"
```

### Report Issues
- Low confidence for simple SQL? → Report to Vibecoding team
- Missing expected tables? → Check catalog first
- Parse errors? → Review [lineage_specs.md](../lineage_specs.md)

---

## Roadmap

### ✅ Current Version (v4.1.3)
- DMV dependencies for Views (Confidence 1.0)
- SQLGlot + Regex + Rule Engine for SPs (97% high confidence)
- Dataflow mode (DML only, filters admin queries)
- Global target exclusion (no false inputs)
- IF EXISTS filtering (no circular dependencies)
- SP-to-SP lineage tracking (EXEC/EXECUTE calls)

---

## Additional Documentation

- **Technical Specification:** [lineage_specs.md](../lineage_specs.md)
- **Parser Module Docs:** [lineage_v3/parsers/README.md](../lineage_v3/parsers/README.md)
- **Project Instructions:** [CLAUDE.md](../CLAUDE.md)
- **Phase 4 Summary:** [docs/PHASE_4_COMPLETE.md](PHASE_4_COMPLETE.md)

---

**Last Updated:** 2025-10-26
**Parser Version:** 3.0.0 (Phase 4 Complete)
**Questions?** Contact Vibecoding team

---

## Updates (v3.4.0 - 2025-10-27)

### SELECT INTO Statement Handling

**Fixed:** Parser now correctly captures source tables in SELECT INTO statements.

**Example:**
```sql
SELECT *
INTO #temp_results
FROM CONSUMPTION_FINANCE.vFactLaborCost  -- ✅ Now captured correctly
WHERE Account IN (...)
```

**Before Fix:**
- Parser treated #temp_results as a DML target
- Source table (vFactLaborCost) was incorrectly excluded
- Result: Missing dependencies

**After Fix:**
- SELECT INTO targets tracked separately from INSERT/UPDATE/MERGE targets
- Source tables in FROM clause are correctly identified as inputs
- Result: Complete dependency graph

### Query Log Validation (Step 5)

**New Feature:** Runtime validation of parsed stored procedures using query execution logs.

**How It Works:**
1. Parser generates lineage from stored procedure DDL (confidence 0.85)
2. Query log validator checks if parsed tables appear in actual DML queries
3. If matching queries found → Confidence boosted to 0.95
4. Result: "Parsed & Validated" vs "Parsed Only"

**Benefits:**
- ✅ Runtime confirmation of static parsing accuracy
- ✅ Distinguishes theoretical vs executed dependencies
- ✅ No false positives (only boosts correctly parsed SPs)
- ✅ Optional feature (graceful degradation if no query logs)

**Example Output:**
```
Step 5: Query Log Validation (Cross-Validation)
======================================================================
📊 Found 1,634 query log entries
🔍 Cross-validating parsed stored procedures...
✅ Validated 6 stored procedure(s)

📈 Confidence Boosts:
   - CONSUMPTION_FINANCE.spLoadDimAccount: 0.85 → 0.95
   - CONSUMPTION_FINANCE.spLoadFactGLSAP: 0.85 → 0.95
```

**Documentation:**
- [Query Logs Analysis](QUERY_LOGS_ANALYSIS.md) - Complete analysis & strategy
- [Parser Bug Report](PARSER_BUG_SELECT_INTO.md) - SELECT INTO fix details
- [Implementation Summary](IMPLEMENTATION_COMPLETE.md) - v3.4.0 overview

---

**Last Updated:** 2025-10-27
**Parser Version:** 3.4.0 (Query Log Validation Added)
**Questions?** Contact Vibecoding team
