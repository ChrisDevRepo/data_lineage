# SQLGlot Parser Module

**Version:** 3.0.0
**Author:** Vibecoding
**Date:** 2025-10-26
**Status:** ✅ Complete (Phase 4)

---

## Overview

The SQLGlot Parser module provides SQL parsing capabilities using SQLGlot Abstract Syntax Tree (AST) traversal to extract table-level lineage from DDL definitions. This is Step 5 in the 8-step lineage construction pipeline.

**Purpose:** Fill gaps where DMV dependencies are missing or incomplete by parsing stored procedure DDL to extract source and target table references.

**Confidence Score:** 0.85 (static AST analysis)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Gap Detector (Step 4)                                       │
│ • Identifies objects with no DMV dependencies               │
│ • Returns list of object_ids needing parsing                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ SQLGlot Parser (Step 5)                                     │
│ For each gap:                                               │
│ 1. Fetch DDL from definitions table                         │
│ 2. Parse with SQLGlot (T-SQL dialect)                       │
│ 3. Traverse AST to extract:                                 │
│    • Source tables: FROM, JOIN clauses                      │
│    • Target tables: INSERT INTO, UPDATE, MERGE, DELETE      │
│ 4. Resolve table names → object_ids (via workspace)         │
│ 5. Return {object_id, inputs[], outputs[], confidence=0.85} │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Update lineage_metadata                                     │
│ • primary_source: "parser"                                  │
│ • confidence: 0.85                                          │
│ • inputs: List[int] (resolved object_ids)                   │
│ • outputs: List[int] (resolved object_ids)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. SQLGlotParser Class

**File:** [sqlglot_parser.py](sqlglot_parser.py)

Main parser class that extracts lineage from SQL DDL.

#### Methods

##### `parse_object(object_id: int) -> Dict[str, Any]`

Parse DDL for a single object.

**Returns:**
```python
{
    'object_id': int,
    'inputs': List[int],   # source tables (FROM/JOIN)
    'outputs': List[int],  # target tables (INSERT/UPDATE/MERGE)
    'confidence': 0.85,
    'source': 'parser',
    'parse_error': Optional[str]  # If parsing failed
}
```

**Example:**
```python
from engine.parsers import SQLGlotParser
from engine.core import DuckDBWorkspace

with DuckDBWorkspace('lineage.duckdb') as db:
    parser = SQLGlotParser(db)
    result = parser.parse_object(object_id=123)

    print(f"Inputs: {result['inputs']}")
    print(f"Outputs: {result['outputs']}")
```

##### `parse_batch(object_ids: List[int]) -> List[Dict[str, Any]]`

Parse multiple objects in batch.

##### `get_parse_statistics() -> Dict[str, Any]`

Get statistics about parser coverage.

**Returns:**
```python
{
    'total_parsed': int,
    'successful_parses': int,
    'failed_parses': int,
    'success_rate': float
}
```

---

## Supported SQL Patterns

### ✅ Fully Supported

The parser successfully extracts lineage from these SQL patterns:

#### 1. Simple SELECT
```sql
CREATE PROCEDURE dbo.spLoadCustomers AS
SELECT * FROM dbo.SourceTable
```
**Extracted:**
- Inputs: `dbo.SourceTable`

#### 2. JOINs (INNER, LEFT, RIGHT, FULL)
```sql
CREATE PROCEDURE dbo.spLoadCustomers AS
SELECT c.*, o.*
FROM dbo.Customers c
JOIN CONSUMPTION_FINANCE.Orders o ON c.id = o.customer_id
LEFT JOIN dbo.Products p ON o.product_id = p.id
```
**Extracted:**
- Inputs: `dbo.Customers`, `CONSUMPTION_FINANCE.Orders`, `dbo.Products`

#### 3. INSERT INTO
```sql
CREATE PROCEDURE dbo.spLoadCustomers AS
INSERT INTO dbo.TargetTable (col1, col2)
SELECT col1, col2 FROM dbo.SourceTable
```
**Extracted:**
- Inputs: `dbo.SourceTable`
- Outputs: `dbo.TargetTable`

#### 4. UPDATE
```sql
CREATE PROCEDURE dbo.spUpdateCustomers AS
UPDATE dbo.TargetTable
SET status = 'Active'
FROM dbo.SourceTable s
WHERE TargetTable.id = s.id
```
**Extracted:**
- Inputs: `dbo.SourceTable`
- Outputs: `dbo.TargetTable`

#### 5. MERGE
```sql
CREATE PROCEDURE dbo.spMergeCustomers AS
MERGE INTO dbo.TargetTable AS t
USING dbo.SourceTable AS s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.name = s.name
WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.name)
```
**Extracted:**
- Inputs: `dbo.SourceTable`
- Outputs: `dbo.TargetTable`

#### 6. DELETE
```sql
CREATE PROCEDURE dbo.spDeleteOldRecords AS
DELETE FROM dbo.TargetTable
WHERE created_date < '2020-01-01'
```
**Extracted:**
- Outputs: `dbo.TargetTable`

#### 7. TRUNCATE
```sql
CREATE PROCEDURE dbo.spTruncateStaging AS
TRUNCATE TABLE dbo.StagingTable
```
**Extracted:**
- Outputs: `dbo.StagingTable`

#### 8. Subqueries
```sql
CREATE PROCEDURE dbo.spLoadCustomers AS
SELECT *
FROM (SELECT id, name FROM dbo.Customers WHERE active = 1) AS ActiveCustomers
JOIN dbo.Orders ON ActiveCustomers.id = Orders.customer_id
```
**Extracted:**
- Inputs: `dbo.Customers`, `dbo.Orders`

#### 9. Common Table Expressions (CTEs)
```sql
CREATE PROCEDURE dbo.spLoadCustomers AS
WITH ActiveCustomers AS (
    SELECT * FROM dbo.Customers WHERE active = 1
),
RecentOrders AS (
    SELECT * FROM dbo.Orders WHERE order_date > '2024-01-01'
)
SELECT * FROM ActiveCustomers
JOIN RecentOrders ON ActiveCustomers.id = RecentOrders.customer_id
```
**Extracted:**
- Inputs: `dbo.Customers`, `dbo.Orders`

#### 10. Schema-Qualified Names
```sql
-- Explicit schema
SELECT * FROM CONSUMPTION_FINANCE.DimCustomers

-- Unqualified (defaults to dbo)
SELECT * FROM Customers  -- Treated as dbo.Customers
```

#### 11. Bracketed Identifiers
```sql
SELECT * FROM [CONSUMPTION_FINANCE].[DimCustomers]
SELECT * FROM [dbo].[My Table With Spaces]
```
**Note:** Brackets are stripped during parsing.

---

### ⚠️ Limitations

The following patterns are NOT supported in Phase 4:

#### 1. Dynamic SQL
```sql
-- Cannot be parsed statically
DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM ' + @tableName
EXEC(@sql)
```
**Solution:** Will be handled by AI fallback (Phase 5)

#### 2. Temp Tables
```sql
-- Excluded from lineage
CREATE TABLE #temp (id INT)
SELECT * FROM #temp
```
**Reason:** Temp tables are session-specific and out of scope

#### 3. Table Variables
```sql
-- Excluded from lineage
DECLARE @table TABLE (id INT)
INSERT INTO @table VALUES (1)
SELECT * FROM @table
```
**Reason:** Table variables are session-specific

#### 4. Cross-Database References
```sql
-- May not resolve if database not in workspace
SELECT * FROM OtherDB.dbo.Table1
```
**Behavior:** Will attempt to resolve, but likely excluded if not found

#### 5. System Tables
```sql
-- Automatically filtered out
SELECT * FROM sys.objects
SELECT * FROM INFORMATION_SCHEMA.TABLES
```
**Reason:** System metadata is out of scope for business lineage

#### 6. Complex Dynamic Queries
```sql
-- OPENQUERY, OPENDATASOURCE, etc.
SELECT * FROM OPENQUERY(LinkedServer, 'SELECT * FROM RemoteTable')
```
**Solution:** Will be handled by AI fallback (Phase 5)

---

## Table Name Resolution

### Schema Handling

1. **Explicit Schema:** `CONSUMPTION_FINANCE.DimCustomers` → resolved as-is
2. **Implicit Schema:** `Customers` → defaults to `dbo.Customers`
3. **Bracketed:** `[schema].[table]` → brackets stripped

### Case Sensitivity

Table name resolution is **case-insensitive**:
- `dbo.Customers` matches `DBO.CUSTOMERS`
- `CONSUMPTION_FINANCE.DimAccount` matches `consumption_finance.dimaccount`

### Unresolved Tables

If a table reference cannot be resolved to an `object_id`:
- The table is excluded from the result
- A debug log is written
- Other resolved tables are still included

**Example:**
```sql
SELECT * FROM dbo.ExistingTable
UNION ALL
SELECT * FROM dbo.NonExistentTable
```
**Result:** Only `ExistingTable` included in `inputs[]`

---

## Error Handling

### Parse Errors

If SQLGlot cannot parse the SQL (malformed syntax):
```python
{
    'object_id': 123,
    'inputs': [],
    'outputs': [],
    'confidence': 0.0,
    'source': 'parser',
    'parse_error': 'SQLGlot parse error: ...'
}
```

### Missing DDL

If no definition exists in the `definitions` table:
```python
{
    'object_id': 123,
    'inputs': [],
    'outputs': [],
    'confidence': 0.0,
    'source': 'parser',
    'parse_error': 'No DDL definition found'
}
```

### Unexpected Errors

All exceptions are caught and logged. Parser returns zero confidence:
```python
{
    'object_id': 123,
    'inputs': [],
    'outputs': [],
    'confidence': 0.0,
    'source': 'parser',
    'parse_error': str(exception)
}
```

---

## Integration with Pipeline

### Usage in main.py

The parser is integrated into the `run` command in Step 5:

```python
# Step 4: Detect gaps
from engine.core import GapDetector
gap_detector = GapDetector(db)
gaps = gap_detector.detect_gaps()

# Step 5: Run SQLGlot parser on gaps
from engine.parsers import SQLGlotParser
parser = SQLGlotParser(db)

for gap in gaps:
    result = parser.parse_object(gap['object_id'])

    if result['confidence'] > 0:
        db.update_metadata(
            object_id=result['object_id'],
            modify_date=gap['modify_date'],
            primary_source='parser',
            confidence=0.85,
            inputs=result['inputs'],
            outputs=result['outputs']
        )
```

---

## Testing

### Unit Tests

**File:** [tests/test_sqlglot_parser.py](../../tests/test_sqlglot_parser.py)

Run tests:
```bash
pytest tests/test_sqlglot_parser.py -v
```

**Coverage:**
- Simple SELECT
- JOINs (multiple types)
- INSERT INTO
- UPDATE
- MERGE
- DELETE
- TRUNCATE
- CTEs
- Subqueries
- Schema-qualified names
- Case-insensitive resolution
- System table filtering
- Temp table filtering
- Parse error handling
- Missing DDL handling
- Unresolved table handling
- Batch parsing
- Statistics retrieval

---

## Performance Considerations

### Parsing Speed

- **Typical SP:** ~10-50ms per object
- **Complex SP:** ~100-200ms per object
- **Large batch:** ~1-2 seconds per 100 objects

### Memory Usage

- SQLGlot AST parsing: ~5-10MB per complex object
- Workspace query overhead: minimal (indexed lookups)

### Optimization Tips

1. **Batch Processing:** Use `parse_batch()` for multiple objects
2. **Incremental Mode:** Only parse modified objects
3. **Parallel Processing:** (Future) Parse objects in parallel

---

## Example Output

### Input DDL
```sql
CREATE PROCEDURE CONSUMPTION_FINANCE.spLoadFactGL AS
BEGIN
    TRUNCATE TABLE CONSUMPTION_FINANCE.FactGL;

    INSERT INTO CONSUMPTION_FINANCE.FactGL
    SELECT
        gl.account_id,
        gl.amount,
        c.currency_code
    FROM dbo.GL_Staging gl
    JOIN CONSUMPTION_FINANCE.DimCurrency c
        ON gl.currency_id = c.currency_id
    WHERE gl.posted = 1;
END
```

### Parser Output
```python
{
    'object_id': 456,
    'inputs': [101, 102],  # dbo.GL_Staging, CONSUMPTION_FINANCE.DimCurrency
    'outputs': [789],      # CONSUMPTION_FINANCE.FactGL
    'confidence': 0.85,
    'source': 'parser',
    'parse_error': None
}
```

---

## Future Enhancements

### Phase 5 Integration
- Objects with `confidence=0.0` will be passed to AI fallback
- AI will handle dynamic SQL and complex patterns

### Potential Improvements
- **View Support:** Currently focuses on stored procedures
- **Function Support:** Extract lineage from table-valued functions
- **Recursive CTEs:** Better handling of recursive queries
- **Window Functions:** Track partition dependencies

---

## Troubleshooting

### Common Issues

#### Issue: Tables not resolving
**Symptom:** Parser returns empty `inputs[]` or `outputs[]`
**Cause:** Table names don't match objects in workspace
**Solution:**
- Verify table exists in `objects` table
- Check schema name matches (case-insensitive)
- Review debug logs for unresolved table names

#### Issue: Parse errors for valid SQL
**Symptom:** `parse_error` returned for syntactically correct SQL
**Cause:** SQLGlot T-SQL dialect limitations
**Solution:**
- These will be handled by AI fallback (Phase 5)
- Review error message to identify unsupported pattern
- Report new patterns to Vibecoding team

#### Issue: Low success rate
**Symptom:** Many objects with `confidence=0.0`
**Cause:** Complex SQL patterns or malformed DDL
**Solution:**
- Review parse errors in lineage_metadata
- Identify common error patterns
- Consider AI fallback for remaining gaps

---

## Dependencies

- **sqlglot:** SQL parser and AST library
- **DuckDB:** Workspace for table name resolution
- **Python:** 3.10+

---

## References

- **Specification:** [lineage_specs_v2.md](../../lineage_specs_v2.md)
- **Phase 4 Plan:** [docs/PHASE_4_PLAN.md](../../docs/PHASE_4_PLAN.md)
- **SQLGlot Docs:** https://sqlglot.com/

---

**Last Updated:** 2025-10-26
**Status:** ✅ Phase 4 Complete
